#!/usr/bin/env python3
"""
Spreadsheet Processor for Broadband Availability Checks
Integrates with Step Functions to process addresses from spreadsheets
"""

import json
import logging
import time
import pandas as pd
import boto3
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from datetime import datetime

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ============== Configuration ==============

@dataclass
class ProcessingConfig:
    """Configuration for spreadsheet processing"""
    input_bucket: str
    output_bucket: str
    input_key: str
    output_key: Optional[str] = None
    parallel_workers: int = 5
    batch_size: int = 10
    save_recordings: bool = True
    recording_bucket: Optional[str] = None
    
@dataclass
class AddressRecord:
    """Represents a row from the spreadsheet"""
    row_id: int
    building_number: Optional[str]
    building_name: Optional[str]
    street: Optional[str]
    town: Optional[str]
    postcode: str
    customer_reference: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "building_number": self.building_number,
            "building_name": self.building_name,
            "street": self.street,
            "town": self.town,
            "postcode": self.postcode
        }

# ============== Main Processor Class ==============

class BroadbandSpreadsheetProcessor:
    """
    Processes spreadsheets of addresses through the broadband checker
    """
    
    def __init__(self, config: ProcessingConfig):
        self.config = config
        self.s3_client = boto3.client('s3')
        self.lambda_client = boto3.client('lambda')
        self.results = []
        self.failed_records = []
        
    def process_spreadsheet(self, execution_id: str) -> Dict[str, Any]:
        """
        Main entry point for processing a spreadsheet
        
        Args:
            execution_id: Step Functions execution ID for tracking
            
        Returns:
            Processing summary with results location
        """
        start_time = time.time()
        
        try:
            # 1. Download and load spreadsheet
            logger.info(f"Loading spreadsheet from s3://{self.config.input_bucket}/{self.config.input_key}")
            df = self._load_spreadsheet()
            
            # 2. Convert to address records
            addresses = self._parse_addresses(df)
            logger.info(f"Found {len(addresses)} addresses to process")
            
            # 3. Process addresses in batches
            results = self._process_addresses(addresses, execution_id)
            
            # 4. Merge results back to dataframe
            df_results = self._merge_results(df, results)
            
            # 5. Save results to S3
            output_location = self._save_results(df_results, execution_id)
            
            # 6. Generate summary
            summary = self._generate_summary(results, start_time, output_location)
            
            return summary
            
        except Exception as e:
            logger.error(f"Error processing spreadsheet: {e}")
            return {
                "status": "error",
                "error": str(e),
                "execution_id": execution_id
            }
    
    def _load_spreadsheet(self) -> pd.DataFrame:
        """Download and load spreadsheet from S3"""
        
        # Download file from S3
        local_file = f"/tmp/input_{self.config.input_key.split('/')[-1]}"
        self.s3_client.download_file(
            self.config.input_bucket,
            self.config.input_key,
            local_file
        )
        
        # Load based on file extension
        if local_file.endswith('.xlsx'):
            df = pd.read_excel(local_file)
        elif local_file.endswith('.csv'):
            df = pd.read_csv(local_file)
        else:
            raise ValueError(f"Unsupported file format: {local_file}")
        
        return df
    
    def _parse_addresses(self, df: pd.DataFrame) -> List[AddressRecord]:
        """Parse addresses from dataframe"""
        
        addresses = []
        
        # Expected column mappings (can be configured)
        column_mapping = {
            'Building Number': 'building_number',
            'Building Name': 'building_name',
            'Street': 'street',
            'Town': 'town',
            'Postcode': 'postcode',
            'Customer Reference': 'customer_reference',
            'Reference': 'customer_reference',
            'ID': 'customer_reference'
        }
        
        for idx, row in df.iterrows():
            # Map columns to address fields
            address_data = {'row_id': idx}
            
            for col_name, field_name in column_mapping.items():
                if col_name in df.columns:
                    value = row.get(col_name)
                    if pd.notna(value):
                        address_data[field_name] = str(value)
            
            # Ensure we have at least a postcode
            if 'postcode' in address_data:
                addresses.append(AddressRecord(**address_data))
            else:
                logger.warning(f"Skipping row {idx}: No postcode found")
        
        return addresses
    
    def _process_addresses(self, addresses: List[AddressRecord], execution_id: str) -> List[Dict]:
        """Process addresses through the broadband checker"""
        
        results = []
        
        # Process in batches with parallel workers
        with ThreadPoolExecutor(max_workers=self.config.parallel_workers) as executor:
            
            # Submit batches
            futures = []
            for i in range(0, len(addresses), self.config.batch_size):
                batch = addresses[i:i+self.config.batch_size]
                future = executor.submit(self._process_batch, batch, execution_id)
                futures.append(future)
            
            # Collect results
            for future in as_completed(futures):
                try:
                    batch_results = future.result(timeout=300)
                    results.extend(batch_results)
                except Exception as e:
                    logger.error(f"Batch processing error: {e}")
        
        return results
    
    def _process_batch(self, batch: List[AddressRecord], execution_id: str) -> List[Dict]:
        """Process a batch of addresses"""
        
        batch_results = []
        
        for address in batch:
            try:
                # Invoke the broadband checker agent
                result = self._check_single_address(address, execution_id)
                batch_results.append(result)
                
                # Rate limiting
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error processing address {address.postcode}: {e}")
                batch_results.append({
                    'row_id': address.row_id,
                    'postcode': address.postcode,
                    'error': str(e),
                    'status': 'failed'
                })
        
        return batch_results
    
    def _check_single_address(self, address: AddressRecord, execution_id: str) -> Dict:
        """Check a single address using the broadband checker agent"""
        
        # Prepare the payload for the agent
        payload = {
            "address": address.to_dict(),
            "wait_for_completion": True,
            "extract_fields": [
                "vdsl_range_a_downstream_high",
                "vdsl_range_a_downstream_low",
                "fttp_available",
                "gfast_range_a_available",
                "exchange_name",
                "cabinet_number"
            ]
        }
        
        # Invoke the Lambda function
        response = self.lambda_client.invoke(
            FunctionName='broadband-checker-agent',
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        # Parse response
        result_data = json.loads(response['Payload'].read())
        
        # Get the actual results if task completed
        if result_data.get('task_id'):
            # Wait a bit for processing
            time.sleep(5)
            
            # Get results
            result_payload = {
                "task_id": result_data['task_id']
            }
            
            result_response = self.lambda_client.invoke(
                FunctionName='broadband-checker-agent',
                InvocationType='RequestResponse',
                Payload=json.dumps(result_payload)
            )
            
            final_result = json.loads(result_response['Payload'].read())
            
            # Add row ID for merging
            final_result['row_id'] = address.row_id
            final_result['customer_reference'] = address.customer_reference
            
            # Save recording if configured
            if self.config.save_recordings and final_result.get('recording_path'):
                recording_url = self._save_recording(
                    final_result['recording_path'],
                    address.postcode,
                    execution_id
                )
                final_result['recording_url'] = recording_url
            
            return final_result
        
        return {
            'row_id': address.row_id,
            'status': 'error',
            'error': 'No task ID returned'
        }
    
    def _save_recording(self, recording_path: str, postcode: str, execution_id: str) -> str:
        """Save recording to S3 and return URL"""
        
        if not self.config.recording_bucket:
            return recording_path
        
        try:
            # Copy recording file to S3
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            s3_key = f"recordings/{execution_id}/{postcode}_{timestamp}.html"
            
            # For now, just return the path reference
            # In production, you'd copy the actual file from the container
            return f"s3://{self.config.recording_bucket}/{s3_key}"
            
        except Exception as e:
            logger.error(f"Error saving recording: {e}")
            return recording_path
    
    def _merge_results(self, df: pd.DataFrame, results: List[Dict]) -> pd.DataFrame:
        """Merge results back into the original dataframe"""
        
        # Convert results to dataframe
        df_results = pd.DataFrame(results)
        
        # Merge on row_id (which is the original index)
        if 'row_id' in df_results.columns:
            df_results = df_results.set_index('row_id')
            
            # Add result columns to original dataframe
            result_columns = [
                'vdsl_range_a_downstream_high',
                'vdsl_range_a_downstream_low',
                'fttp_available',
                'gfast_range_a_available',
                'exchange_name',
                'cabinet_number',
                'recording_url',
                'error'
            ]
            
            for col in result_columns:
                if col in df_results.columns:
                    df[col] = df_results[col]
        
        return df
    
    def _save_results(self, df: pd.DataFrame, execution_id: str) -> str:
        """Save results to S3"""
        
        # Generate output filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if self.config.output_key:
            output_key = self.config.output_key
        else:
            # Generate based on input filename
            base_name = self.config.input_key.split('/')[-1].split('.')[0]
            output_key = f"results/{execution_id}/{base_name}_results_{timestamp}.xlsx"
        
        # Save to temporary file
        local_file = f"/tmp/output_{timestamp}.xlsx"
        df.to_excel(local_file, index=False)
        
        # Upload to S3
        self.s3_client.upload_file(
            local_file,
            self.config.output_bucket,
            output_key
        )
        
        output_location = f"s3://{self.config.output_bucket}/{output_key}"
        logger.info(f"Results saved to {output_location}")
        
        return output_location
    
    def _generate_summary(self, results: List[Dict], start_time: float, output_location: str) -> Dict:
        """Generate processing summary"""
        
        total_processed = len(results)
        successful = sum(1 for r in results if r.get('status') != 'error')
        failed = total_processed - successful
        processing_time = time.time() - start_time
        
        return {
            "status": "completed",
            "total_addresses": total_processed,
            "successful": successful,
            "failed": failed,
            "processing_time_seconds": round(processing_time, 2),
            "output_location": output_location,
            "timestamp": datetime.now().isoformat()
        }

# ============== Step Functions Handler ==============

def step_function_handler(event, context):
    """
    Handler for AWS Step Functions integration
    
    Expected event format:
    {
        "input_bucket": "my-bucket",
        "input_key": "addresses/input.xlsx",
        "output_bucket": "my-bucket",
        "execution_id": "step-function-execution-id"
    }
    """
    
    logger.info(f"Processing event: {json.dumps(event)}")
    
    try:
        # Create configuration
        config = ProcessingConfig(
            input_bucket=event['input_bucket'],
            output_bucket=event.get('output_bucket', event['input_bucket']),
            input_key=event['input_key'],
            output_key=event.get('output_key'),
            parallel_workers=event.get('parallel_workers', 5),
            batch_size=event.get('batch_size', 10),
            save_recordings=event.get('save_recordings', True),
            recording_bucket=event.get('recording_bucket')
        )
        
        # Process spreadsheet
        processor = BroadbandSpreadsheetProcessor(config)
        result = processor.process_spreadsheet(
            execution_id=event.get('execution_id', context.request_id)
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

# ============== Direct Invocation for Testing ==============

if __name__ == "__main__":
    # Test configuration
    test_event = {
        "input_bucket": "test-bucket",
        "input_key": "test-addresses.xlsx",
        "output_bucket": "test-bucket",
        "execution_id": "test-execution-001"
    }
    
    result = step_function_handler(test_event, type('Context', (), {'request_id': 'test'})())
    print(json.dumps(result, indent=2))