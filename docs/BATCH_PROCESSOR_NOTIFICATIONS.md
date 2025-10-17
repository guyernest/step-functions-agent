# Batch Processor SNS Notifications

## Overview

The Batch Processor now publishes SNS notifications when batch processing completes successfully. This allows you to receive notifications via email, SMS, Lambda functions, or SQS queues without polling the state machine.

## Architecture

- **Pre-defined Topic**: All batch completions publish to a single SNS topic: `batch-processor-notifications-{env}`
- **Message Attributes**: Each notification includes attributes for filtering (execution_id, batch_name, status, target_agent, rows_processed)
- **Subscription Filtering**: Subscribers can use SNS filter policies to receive only relevant notifications

## SNS Topic Details

**Topic Name**: `batch-processor-notifications-{env}` (e.g., `batch-processor-notifications-prod`)

**Topic ARN**: Available as CloudFormation output `BatchProcessorNotificationTopicArn-{env}`

## Message Format

### Message Body
```
Batch processing completed successfully.

Execution ID: abc123-def456-ghi789
Batch Name: broadband_availability_check_v1
Target Agent: browser-automation-structured
Rows Processed: 150
Rows Successful: 148
Rows Failed: 2
Result S3 URI: s3://batch-processor-results-prod-123456789012/results/abc123-def456-ghi789/output.csv
Duration: 900 seconds

Started: 2025-10-16T10:00:00.000Z
Completed: 2025-10-16T10:15:00.000Z
```

### Message Attributes (for filtering)
- `execution_id` (String): Unique execution ID from Step Functions
- `batch_name` (String): User-provided batch identifier
- `status` (String): Always "SUCCESS" (failures don't send notifications)
- `target_agent` (String): Name of the agent that processed the batch
- `rows_processed` (Number): Total number of rows processed

## Usage

### 1. Include notification_config in Batch Input

When starting a batch execution, include the `notification_config` parameter:

```json
{
  "csv_s3_uri": "s3://my-bucket/input.csv",
  "target": {
    "type": "agent",
    "name": "browser-automation-structured"
  },
  "input_mapping": { ... },
  "output_mapping": { ... },
  "notification_config": {
    "batch_name": "broadband_availability_check_v1",
    "include_details": true
  }
}
```

**Required Fields:**
- `batch_name`: Identifier for this batch (used for filtering subscriptions)

**Optional Fields:**
- `include_details`: Whether to include detailed statistics (default: true)

### 2. Subscribe to Notifications

#### Option A: Email Notification (Simple)

Subscribe your email to receive all batch completions:

```bash
aws sns subscribe \
  --topic-arn arn:aws:sns:us-west-2:123456789012:batch-processor-notifications-prod \
  --protocol email \
  --notification-endpoint user@example.com
```

**Note**: You'll receive a confirmation email - click the link to confirm subscription.

#### Option B: Filtered Email Notification (Recommended)

Subscribe with a filter to only receive notifications for specific batches:

```bash
aws sns subscribe \
  --topic-arn arn:aws:sns:us-west-2:123456789012:batch-processor-notifications-prod \
  --protocol email \
  --notification-endpoint user@example.com \
  --attributes '{
    "FilterPolicy": "{\"batch_name\":[\"broadband_availability_check_v1\"]}"
  }'
```

This subscription will ONLY receive notifications where `batch_name` = `broadband_availability_check_v1`.

#### Option C: Lambda Function

Process notifications with a Lambda function:

```bash
aws sns subscribe \
  --topic-arn arn:aws:sns:us-west-2:123456789012:batch-processor-notifications-prod \
  --protocol lambda \
  --notification-endpoint arn:aws:lambda:us-west-2:123456789012:function:process-batch-completion
```

#### Option D: SQS Queue

Send notifications to an SQS queue for async processing:

```bash
aws sns subscribe \
  --topic-arn arn:aws:sns:us-west-2:123456789012:batch-processor-notifications-prod \
  --protocol sqs \
  --notification-endpoint arn:aws:sqs:us-west-2:123456789012:batch-completions
```

### 3. Advanced Filtering Examples

#### Filter by Multiple Batch Names
```json
{
  "batch_name": [
    "broadband_availability_check_v1",
    "broadband_availability_check_v2"
  ]
}
```

#### Filter by Target Agent
```json
{
  "target_agent": ["browser-automation-structured"]
}
```

#### Filter by Rows Processed (minimum threshold)
```json
{
  "rows_processed": [{"numeric": [">=", 100]}]
}
```

#### Combine Multiple Filters (AND logic)
```json
{
  "batch_name": ["broadband_availability_check_v1"],
  "target_agent": ["browser-automation-structured"],
  "status": ["SUCCESS"]
}
```

## Testing

### 1. Get the Topic ARN

```bash
aws cloudformation describe-stacks \
  --stack-name BatchProcessorToolStack-prod \
  --query "Stacks[0].Outputs[?OutputKey=='NotificationTopicArn'].OutputValue" \
  --output text
```

### 2. Subscribe Your Email

```bash
TOPIC_ARN="arn:aws:sns:us-west-2:123456789012:batch-processor-notifications-prod"

aws sns subscribe \
  --topic-arn $TOPIC_ARN \
  --protocol email \
  --notification-endpoint your-email@example.com
```

### 3. Confirm Subscription

Check your email and click the confirmation link.

### 4. Run a Test Batch

Execute a batch job with notification_config:

```bash
aws stepfunctions start-execution \
  --state-machine-arn arn:aws:states:us-west-2:123456789012:stateMachine:batch-processor-prod \
  --input '{
    "csv_s3_uri": "s3://my-bucket/test.csv",
    "target": {
      "type": "agent",
      "name": "browser-automation-structured"
    },
    "notification_config": {
      "batch_name": "test_batch_001"
    }
  }'
```

### 5. Check Your Email

When the batch completes, you should receive an email notification with the execution details.

## Troubleshooting

### Notification Not Received

1. **Check Subscription Status**:
   ```bash
   aws sns list-subscriptions-by-topic \
     --topic-arn $TOPIC_ARN
   ```
   Ensure your subscription shows `"SubscriptionArn": "arn:aws:sns:..."` (not "PendingConfirmation")

2. **Check Filter Policy**:
   If using filters, verify the filter matches your notification attributes:
   ```bash
   aws sns get-subscription-attributes \
     --subscription-arn $SUBSCRIPTION_ARN \
     --query "Attributes.FilterPolicy"
   ```

3. **Check Spam Folder**:
   SNS emails might be filtered as spam. Add `no-reply@sns.amazonaws.com` to your contacts.

4. **Test the Topic**:
   Publish a test message:
   ```bash
   aws sns publish \
     --topic-arn $TOPIC_ARN \
     --subject "Test Message" \
     --message "This is a test notification" \
     --message-attributes '{
       "batch_name": {"DataType":"String","StringValue":"test_batch_001"},
       "status": {"DataType":"String","StringValue":"SUCCESS"}
     }'
   ```

### Notification Missing batch_name

Ensure your batch execution input includes `notification_config.batch_name`:

```json
{
  "notification_config": {
    "batch_name": "your_unique_batch_name"
  }
}
```

Without this, the notification will fail (but the batch will still complete successfully).

## Best Practices

1. **Use Descriptive Batch Names**: Use meaningful identifiers like `broadband_check_2025_q1` instead of `batch1`

2. **Filter Subscriptions**: Always use filter policies to avoid notification overload

3. **One Topic, Multiple Filters**: Create separate subscriptions for different use cases:
   - Email to ops team for all completions
   - Lambda function for automatic post-processing
   - SQS queue for audit logging

4. **Test Filters First**: Use `aws sns publish` to test your filter policies before running large batches

5. **Monitor Failed Deliveries**: Check SNS delivery logs in CloudWatch if notifications aren't arriving

## Security Considerations

- The state machine has permission to publish ONLY to the batch processor topic
- Subscribers need `sns:Subscribe` permission on the topic
- Filter policies are evaluated server-side (subscribers cannot receive filtered-out messages)
- Message attributes are immutable once published

## Cost

SNS pricing (as of 2025):
- First 1,000 notifications/month: FREE
- Additional notifications: $0.50 per 1 million notifications
- Email/SMS notifications: Additional carrier fees may apply

For most batch processing use cases, SNS costs will be negligible.

## Examples

### Example 1: Email Notification for Specific Batch

```bash
# Subscribe with filter
aws sns subscribe \
  --topic-arn arn:aws:sns:us-west-2:123456789012:batch-processor-notifications-prod \
  --protocol email \
  --notification-endpoint data-team@company.com \
  --attributes '{
    "FilterPolicy": "{\"batch_name\":[\"daily_broadband_report\"]}"
  }'
```

### Example 2: Lambda Post-Processing

```python
# Lambda function triggered by SNS
import json
import boto3

def lambda_handler(event, context):
    # Parse SNS message
    message = json.loads(event['Records'][0]['Sns']['Message'])

    # Get message attributes
    attributes = event['Records'][0]['Sns']['MessageAttributes']
    batch_name = attributes['batch_name']['Value']
    result_s3_uri = message['result_s3_uri']

    # Process the results
    print(f"Batch {batch_name} completed. Results at: {result_s3_uri}")

    # Download and process results
    s3 = boto3.client('s3')
    # ... your processing logic ...

    return {'statusCode': 200}
```

### Example 3: SQS Queue with Dead Letter Queue

```bash
# Create DLQ
aws sqs create-queue \
  --queue-name batch-notifications-dlq

# Create main queue with DLQ
aws sqs create-queue \
  --queue-name batch-notifications \
  --attributes '{
    "RedrivePolicy": "{\"deadLetterTargetArn\":\"arn:aws:sqs:us-west-2:123456789012:batch-notifications-dlq\",\"maxReceiveCount\":\"3\"}"
  }'

# Subscribe queue to SNS topic
aws sns subscribe \
  --topic-arn arn:aws:sns:us-west-2:123456789012:batch-processor-notifications-prod \
  --protocol sqs \
  --notification-endpoint arn:aws:sqs:us-west-2:123456789012:batch-notifications
```

## Related Documentation

- [Batch Processor Overview](./BATCH_PROCESSOR.md)
- [SNS Message Filtering](https://docs.aws.amazon.com/sns/latest/dg/sns-message-filtering.html)
- [Step Functions SNS Integration](https://docs.aws.amazon.com/step-functions/latest/dg/connect-sns.html)
