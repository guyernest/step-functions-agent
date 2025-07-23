#!/usr/bin/env python3
"""
Step Functions Activity Worker for Testing Approval Workflows

This worker script polls Step Functions Activities and provides:
1. Human approval simulation for SQL/Python execution
2. Remote execution simulation for local automation tasks

Usage:
    python activity_worker.py approval    # Handle human approval activities
    python activity_worker.py remote      # Handle remote execution activities
    python activity_worker.py both        # Handle both types of activities
"""

import sys
import boto3
import json
import time
import threading
from datetime import datetime
from typing import Dict, Any


class ActivityWorker:
    """Base class for Step Functions Activity workers"""
    
    def __init__(self, activity_arn: str, worker_name: str):
        self.activity_arn = activity_arn
        self.worker_name = worker_name
        self.sf_client = boto3.client('stepfunctions')
        self.running = False
    
    def start(self):
        """Start polling for activity tasks"""
        self.running = True
        print(f"🚀 Starting worker '{self.worker_name}' for activity: {self.activity_arn}")
        
        while self.running:
            try:
                # Poll for activity task
                response = self.sf_client.get_activity_task(
                    activityArn=self.activity_arn,
                    workerName=self.worker_name
                )
                
                if response.get('taskToken'):
                    print(f"\n📋 Received task: {response['taskToken'][:20]}...")
                    self.handle_task(response['taskToken'], response.get('input', '{}'))
                else:
                    # No tasks available, wait before polling again
                    time.sleep(5)
                    
            except KeyboardInterrupt:
                print(f"\n⏹️ Stopping worker '{self.worker_name}'")
                self.running = False
                break
            except Exception as e:
                print(f"❌ Error in worker '{self.worker_name}': {e}")
                time.sleep(10)  # Wait before retrying
    
    def handle_task(self, task_token: str, task_input: str):
        """Handle an activity task - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement handle_task")
    
    def send_task_success(self, task_token: str, output: Dict[str, Any]):
        """Send task success response"""
        try:
            self.sf_client.send_task_success(
                taskToken=task_token,
                output=json.dumps(output)
            )
            print("✅ Task completed successfully")
        except Exception as e:
            print(f"❌ Error sending task success: {e}")
    
    def send_task_failure(self, task_token: str, error: str, cause: str):
        """Send task failure response"""
        try:
            self.sf_client.send_task_failure(
                taskToken=task_token,
                error=error,
                cause=cause
            )
            print(f"❌ Task failed: {error}")
        except Exception as e:
            print(f"❌ Error sending task failure: {e}")


class HumanApprovalWorker(ActivityWorker):
    """Worker for handling human approval activities"""
    
    def __init__(self, activity_arn: str):
        super().__init__(activity_arn, "approval-worker")
    
    def handle_task(self, task_token: str, task_input: str):
        """Handle human approval task"""
        try:
            task_data = json.loads(task_input)
            
            # Display approval request
            print("\n" + "="*60)
            print("🔔 HUMAN APPROVAL REQUIRED")
            print("="*60)
            print(f"Tool: {task_data.get('tool_name', 'Unknown')}")
            print(f"Agent: {task_data.get('agent_name', 'Unknown')}")
            print(f"Time: {task_data.get('timestamp', datetime.now().isoformat())}")
            print(f"Execution: {task_data.get('context', {}).get('execution_name', 'Unknown')}")
            print("\nTool Input:")
            print(json.dumps(task_data.get('tool_input', {}), indent=2))
            print("="*60)
            
            # Get user decision
            while True:
                decision = input("\n🤔 Approve this request? (y/n/details): ").lower().strip()
                
                if decision == 'details':
                    print("\nFull request details:")
                    print(json.dumps(task_data, indent=2))
                    continue
                elif decision in ['y', 'yes', 'approve']:
                    # Approved
                    reviewer = input("Enter your email/name: ").strip() or "test-reviewer@company.com"
                    notes = input("Review notes (optional): ").strip() or "Approved for testing"
                    
                    response = {
                        "approved": True,
                        "reviewer": reviewer, 
                        "timestamp": datetime.now().isoformat(),
                        "review_notes": notes
                    }
                    
                    self.send_task_success(task_token, response)
                    break
                    
                elif decision in ['n', 'no', 'reject']:
                    # Rejected
                    reviewer = input("Enter your email/name: ").strip() or "test-reviewer@company.com"
                    reason = input("Rejection reason: ").strip() or "Request rejected during testing"
                    notes = input("Review notes (optional): ").strip() or "Rejected for security reasons"
                    
                    response = {
                        "approved": False,
                        "rejection_reason": reason,
                        "reviewer": reviewer,
                        "timestamp": datetime.now().isoformat(),
                        "review_notes": notes
                    }
                    
                    self.send_task_success(task_token, response)
                    break
                else:
                    print("Please enter 'y' (yes), 'n' (no), or 'details'")
                    
        except Exception as e:
            self.send_task_failure(task_token, "ProcessingError", f"Error processing approval task: {e}")


class RemoteExecutionWorker(ActivityWorker):
    """Worker for handling remote execution activities"""
    
    def __init__(self, activity_arn: str):
        super().__init__(activity_arn, "remote-execution-worker")
    
    def handle_task(self, task_token: str, task_input: str):
        """Handle remote execution task"""
        try:
            task_data = json.loads(task_input)
            
            # Display execution request
            print("\n" + "="*60)
            print("🚀 REMOTE EXECUTION REQUEST")
            print("="*60)
            print(f"Tool: {task_data.get('tool_name', 'Unknown')}")
            print(f"Time: {task_data.get('timestamp', datetime.now().isoformat())}")
            print(f"Execution: {task_data.get('context', {}).get('execution_name', 'Unknown')}")
            print("\nExecution Input:")
            print(json.dumps(task_data.get('tool_input', {}), indent=2))
            print("="*60)
            
            # Simulate remote execution
            print("⏳ Simulating remote execution...")
            time.sleep(2)  # Simulate processing time
            
            # Ask user for execution result
            while True:
                result = input("\n🎯 Execution result (s=success, f=failure, c=custom): ").lower().strip()
                
                if result in ['s', 'success']:
                    # Successful execution
                    output = input("Execution output (optional): ").strip() or "Command executed successfully"
                    
                    response = {
                        "type": "tool_result",
                        "tool_use_id": task_data.get('tool_use_id', 'unknown'),
                        "name": task_data.get('tool_name', 'local_agent_execute'),
                        "content": {
                            "status": "success",
                            "output": output,
                            "execution_time_ms": 2000,
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                    
                    self.send_task_success(task_token, response)
                    break
                    
                elif result in ['f', 'failure']:
                    # Failed execution
                    error = input("Error message: ").strip() or "Execution failed"
                    
                    response = {
                        "type": "tool_result",
                        "tool_use_id": task_data.get('tool_use_id', 'unknown'),
                        "name": task_data.get('tool_name', 'local_agent_execute'),
                        "content": {
                            "status": "error",
                            "error": error,
                            "execution_time_ms": 1500,
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                    
                    self.send_task_success(task_token, response)
                    break
                    
                elif result in ['c', 'custom']:
                    # Custom response
                    print("Enter custom response (JSON format):")
                    try:
                        custom_response = json.loads(input())
                        self.send_task_success(task_token, custom_response)
                        break
                    except json.JSONDecodeError:
                        print("Invalid JSON format, please try again")
                else:
                    print("Please enter 's' (success), 'f' (failure), or 'c' (custom)")
                    
        except Exception as e:
            self.send_task_failure(task_token, "ExecutionError", f"Error during remote execution: {e}")


def get_activity_arns():
    """Get activity ARNs for the test environment"""
    try:
        account_id = boto3.client('sts').get_caller_identity()['Account']
        region = 'us-east-1'  # Adjust as needed
        
        return {
            'approval': f"arn:aws:states:{region}:{account_id}:activity:test-sql-approval-agent-approval-activity-prod",
            'remote': f"arn:aws:states:{region}:{account_id}:activity:local-automation-remote-activity-prod"
        }
    except Exception as e:
        print(f"❌ Error getting activity ARNs: {e}")
        return {}


def main():
    """Main function to handle command line arguments"""
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    mode = sys.argv[1].lower()
    activity_arns = get_activity_arns()
    
    if not activity_arns:
        print("❌ Could not determine activity ARNs. Make sure agents are deployed.")
        return
    
    workers = []
    
    try:
        if mode == 'approval':
            worker = HumanApprovalWorker(activity_arns['approval'])
            workers.append(worker)
            
        elif mode == 'remote':
            worker = RemoteExecutionWorker(activity_arns['remote'])
            workers.append(worker)
            
        elif mode == 'both':
            approval_worker = HumanApprovalWorker(activity_arns['approval'])
            remote_worker = RemoteExecutionWorker(activity_arns['remote'])
            workers.extend([approval_worker, remote_worker])
            
        else:
            print(f"Unknown mode: {mode}")
            print(__doc__)
            return
        
        # Start workers in separate threads
        threads = []
        for worker in workers:
            thread = threading.Thread(target=worker.start)
            thread.daemon = True
            thread.start()
            threads.append(thread)
        
        print(f"\n✅ Started {len(workers)} worker(s). Press Ctrl+C to stop.")
        
        # Wait for all threads
        for thread in threads:
            thread.join()
            
    except KeyboardInterrupt:
        print("\n⏹️ Stopping all workers...")
        for worker in workers:
            worker.running = False


if __name__ == "__main__":
    main()