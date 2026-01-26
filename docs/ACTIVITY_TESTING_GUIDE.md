# Activity Support Testing Guide

This guide demonstrates how to test the approval activity feature with two test agents that showcase different workflow patterns.

## Test Agents Overview

### 1. TestSQLApprovalAgent
- **Purpose**: Demonstrates human approval workflow for database operations
- **Tools**: 
  - `get_db_schema` (no approval needed)
  - `execute_sql_query` (requires human approval)
  - `execute_python` (requires human approval)
- **Activity Type**: Human approval (agent-owned)
- **Timeout**: 1 hour for approvals

### 2. TestAutomationRemoteAgent  
- **Purpose**: Demonstrates remote execution workflow for local automation
- **Tools**:
  - `local_agent` (remote execution via activity)
- **Activity Type**: Remote execution (tool-owned)
- **Timeout**: 5 minutes for remote operations

## Quick Start

### 1. Deploy Test Infrastructure

```bash
# Activate virtual environment
source cpython-3.12.3-macos-aarch64-none/bin/activate

# Configure AWS credentials
assume CGI-PoC

# Deploy test agents and dependencies
python test_approval_agents.py deploy
```

This will deploy:
- Shared infrastructure (LLM services, registries)
- Required tool stacks (DB Interface, E2B, Local Automation)
- Both test agents with their approval activities

### 2. Start Activity Workers

In a separate terminal, start the activity workers:

```bash
# For human approval testing
python activity_worker.py approval

# For remote execution testing  
python activity_worker.py remote

# For both (runs in separate threads)
python activity_worker.py both
```

### 3. Test the Workflows

```bash
# Test SQL approval workflow
python test_approval_agents.py test-sql

# Test remote execution workflow
python test_approval_agents.py test-remote

# Run both tests
python test_approval_agents.py test
```

## Detailed Testing Scenarios

### Human Approval Workflow Test

1. **Start the SQL approval agent test**:
   ```bash
   python test_approval_agents.py test-sql
   ```

2. **Expected Flow**:
   ```
   User Request → LLM → get_db_schema (executes immediately)
                     → execute_sql_query (waits for approval)
   ```

3. **Approval Worker Response**:
   The worker will display:
   ```
   🔔 HUMAN APPROVAL REQUIRED
   Tool: execute_sql_query
   Agent: test-sql-approval-agent
   Tool Input: {"sql_query": "SELECT COUNT(*) FROM table_name"}
   
   🤔 Approve this request? (y/n/details):
   ```

4. **Test Scenarios**:
   - **Approve**: Enter `y`, provide reviewer info, see SQL execution
   - **Reject**: Enter `n`, provide rejection reason, see feedback to LLM
   - **Details**: Enter `details` to see full request context

### Remote Execution Workflow Test

1. **Start the remote execution agent test**:
   ```bash
   python test_approval_agents.py test-remote
   ```

2. **Expected Flow**:
   ```
   User Request → LLM → local_agent (sent to remote activity)
                             → Remote Worker executes → Returns result
   ```

3. **Remote Worker Response**:
   The worker will display:
   ```
   🚀 REMOTE EXECUTION REQUEST
   Tool: local_agent
   Execution Input: {"script": {"action": "open_text_editor"}}
   
   🎯 Execution result (s=success, f=failure, c=custom):
   ```

4. **Test Scenarios**:
   - **Success**: Enter `s`, provide output, see successful completion
   - **Failure**: Enter `f`, provide error message, see error handling
   - **Custom**: Enter `c`, provide JSON response for complex scenarios

## Step Functions Integration

### Generated Workflow States

The approval workflows generate these Step Functions states:

#### Human Approval Pattern
{% raw %}
```json
{
  "Request Approval execute_sql_query": {
    "Type": "Task",
    "Resource": "arn:aws:states:::activity:test-sql-approval-agent-approval-activity-prod",
    "TimeoutSeconds": 3600,
    "Next": "Check Approval execute_sql_query"
  },
  "Check Approval execute_sql_query": {
    "Type": "Choice",
    "Choices": [{"Condition": "{% $states.result.approved = true %}", "Next": "Execute execute_sql_query"}],
    "Default": "Handle Rejection execute_sql_query"
  }
}
```
{% endraw %}

#### Remote Execution Pattern
```json
{
  "Execute Remote local_agent": {
    "Type": "Task", 
    "Resource": "arn:aws:states:::activity:local-automation-remote-activity-prod",
    "TimeoutSeconds": 300,
    "Catch": [{"ErrorEquals": ["States.Timeout"], "Next": "Remote Timeout local_agent"}]
  }
}
```

### Activity Request/Response Examples

#### Human Approval Request
```json
{
  "tool_name": "execute_sql_query",
  "tool_use_id": "tool_123456789",
  "tool_input": {"sql_query": "SELECT * FROM users LIMIT 10"},
  "agent_name": "test-sql-approval-agent",
  "timestamp": "2025-01-15T10:30:00.000Z",
  "context": {
    "execution_name": "test-sql-approval-12345",
    "state_machine": "test-sql-approval-agent-prod"
  }
}
```

#### Approval Response (Approved)
```json
{
  "approved": true,
  "reviewer": "john.doe@company.com",
  "timestamp": "2025-01-15T10:32:00.000Z", 
  "review_notes": "Query looks safe for testing"
}
```

#### Approval Response (Rejected)
```json
{
  "approved": false,
  "rejection_reason": "Missing WHERE clause - could return too much data",
  "reviewer": "security@company.com",
  "timestamp": "2025-01-15T10:33:00.000Z",
  "review_notes": "Add LIMIT or WHERE clause for safety"
}
```

## Monitoring and Debugging

### Check Deployment Status
```bash
python test_approval_agents.py status
```

### AWS Console Monitoring

1. **Step Functions Console**:
   - View execution graphs and state transitions
   - Monitor approval workflow states
   - Check timeout and error handling

2. **CloudWatch Logs**:
   - Agent execution logs: `/aws/stepfunctions/test-*-agent-prod`
   - Lambda function logs for tool execution

3. **Activities Console**:
   - Monitor activity task polling
   - Check worker heartbeats
   - View task completion rates

### Common Issues

1. **Activities Not Found**: Ensure tool stacks are deployed before agents
2. **Timeout Errors**: Check that activity workers are running
3. **Permission Errors**: Verify IAM roles have activity permissions
4. **Activity ARN Mismatches**: Check exports are correctly imported

## Advanced Testing

### Custom Approval Scenarios

Test different approval patterns by modifying the worker responses:

```python
# In activity_worker.py, modify the approval response
response = {
    "approved": True,
    "reviewer": "custom-tester@company.com",
    "timestamp": datetime.now().isoformat(),
    "review_notes": "Custom approval for specific test scenario",
    "approval_conditions": ["add_limit_clause", "log_query"]
}
```

### Remote Execution Simulation

Test complex remote execution scenarios:

```python
# Simulate partial success
response = {
    "type": "tool_result",
    "tool_use_id": task_data.get('tool_use_id'),
    "name": "local_agent",
    "content": {
        "status": "partial_success",
        "output": "Task completed with warnings",
        "warnings": ["Screenshot capture failed", "Window focus timeout"],
        "execution_time_ms": 3500
    }
}
```

## Integration with Production

### Production Considerations

1. **Activity Workers**: Deploy as containerized services or Lambda functions
2. **Approval UI**: Build web interface for human reviewers
3. **Activity Monitoring**: Set up CloudWatch alarms for activity timeouts
4. **Security**: Implement proper authentication for approval workflows

### Worker Scaling

For production, consider:
- Multiple worker instances for high availability
- Load balancing across worker pools
- Automatic scaling based on activity task volume
- Worker health monitoring and alerting

This testing framework provides a solid foundation for validating approval workflows before production deployment.