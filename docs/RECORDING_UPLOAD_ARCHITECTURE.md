# Recording Upload Architecture - Ultrathink Analysis

## Executive Summary

**Current State**: Manual IAM setup, always-on recording, no levels
**Proposed State**: Automated IAM via CDK, recording levels (TRACE/INFO/ERROR), cleaner architecture

---

## Current Implementation Analysis

### 1. What We Have Today

#### S3 Bucket (✅ GOOD)
```python
# stacks/tools/browser_remote_tool_stack.py:48-63
self.recordings_bucket = s3.Bucket(
    self, "BrowserRecordingsBucket",
    bucket_name=f"browser-agent-recordings-{env_name}-{self.account}",
    encryption=s3.BucketEncryption.S3_MANAGED,
    lifecycle_rules=[
        s3.LifecycleRule(expiration=Duration.days(90))
    ]
)
```
✅ **Already automated** - Created by CDK
✅ **Secure** - Encrypted, private, auto-cleanup
✅ **Multi-environment** - Separate buckets per env (dev/prod)

#### Recording Upload (✅ GOOD)
```python
# lambda/tools/local-browser-agent/python/nova_act_wrapper.py:203-216
if s3_bucket and record_video:
    s3_writer = S3Writer(
        boto_session=boto_session,
        s3_bucket_name=s3_bucket,
        s3_prefix=f"browser-sessions/{session_id}/",
        metadata={"task_id": task_id}
    )
    stop_hooks.append(s3_writer)
```
✅ **Automatic** - NovaAct's S3Writer handles uploads
✅ **Structured** - Organized by session ID
✅ **Metadata-rich** - Includes task context

#### IAM Permissions (❌ BAD - Manual)
```bash
# docs/IAM_PERMISSIONS.md:18-23
# MANUAL PROCESS:
aws iam create-user --user-name browser-agent-user
aws iam create-access-key --user-name browser-agent-user
aws iam create-policy --policy-document file://browser-agent-policy.json
aws iam attach-user-policy ...
# Copy access keys to Windows environment variables
```
❌ **Completely manual** - No automation
❌ **Error-prone** - Easy to misconfigure
❌ **Not scalable** - Each user/machine requires manual setup
❌ **Security risk** - Long-lived access keys

#### Recording Control (❌ BAD - Binary On/Off)
```python
# Only two states:
record_video=True   # Upload everything
record_video=False  # Upload nothing
```
❌ **No granularity** - Can't control what gets uploaded
❌ **Storage waste** - May upload unnecessary intermediate steps
❌ **Privacy concerns** - No way to upload only errors

---

## Problems to Solve

### Problem 1: Manual IAM Setup
**Impact**: HIGH
**Complexity**: Each new local agent requires:
1. Create IAM user
2. Generate access keys
3. Create/attach policy
4. Configure environment variables
5. Test permissions

**User Experience**:
- Takes 15-20 minutes per setup
- Requires AWS IAM knowledge
- Easy to make mistakes (wrong ARN, wrong policy)
- Difficult to troubleshoot

### Problem 2: No Recording Levels
**Impact**: MEDIUM
**Use Cases Not Supported**:
- "Only upload if there's an error" (debugging)
- "Only upload the final extraction page" (audit trail)
- "Upload everything" (development/troubleshooting)

**Current Workaround**: Toggle `record_video` on/off manually

### Problem 3: Permissions Scope
**Impact**: MEDIUM
**Current Policy**:
```json
{
  "Resource": [
    "arn:aws:states:*:ACCOUNT_ID:activity:browser-remote-*",
    "arn:aws:s3:::browser-agent-recordings-*/*"
  ]
}
```
✅ **Good**: Wildcard allows multi-environment (dev/staging/prod)
⚠️ **Risk**: User can access ANY browser-remote activity or recording bucket

---

## Proposed Architecture

### Solution 1: Automated IAM with CDK

#### A. IAM User Creation in CDK Stack

```python
# stacks/tools/browser_remote_tool_stack.py

class BrowserRemoteToolStack(Stack):
    def __init__(self, ...):
        # ... existing bucket and activity ...

        # Create IAM user for local agents
        self.local_agent_user = iam.User(
            self, "LocalAgentUser",
            user_name=f"browser-agent-local-{env_name}",
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "ReadOnlyAccess"  # For STS GetCallerIdentity
                )
            ]
        )

        # Create inline policy with minimal permissions
        self.local_agent_user.add_to_policy(
            iam.PolicyStatement(
                sid="StepFunctionsActivityAccess",
                actions=[
                    "states:GetActivityTask",
                    "states:SendTaskSuccess",
                    "states:SendTaskFailure",
                    "states:SendTaskHeartbeat",
                    "states:DescribeActivity"
                ],
                resources=[self.browser_activity.activity_arn]  # Specific activity only
            )
        )

        # Grant S3 upload permissions
        self.recordings_bucket.grant_put(self.local_agent_user)
        self.recordings_bucket.grant_read(self.local_agent_user)  # For verification

        # Create access key
        self.access_key = iam.CfnAccessKey(
            self, "LocalAgentAccessKey",
            user_name=self.local_agent_user.user_name
        )

        # Store in Secrets Manager
        self.credentials_secret = secretsmanager.Secret(
            self, "LocalAgentCredentials",
            secret_name=f"browser-agent-credentials-{env_name}",
            secret_object_value={
                "AWS_ACCESS_KEY_ID": SecretValue.unsafe_plain_text(
                    self.access_key.ref
                ),
                "AWS_SECRET_ACCESS_KEY": self.access_key.attr_secret_access_key,
                "AWS_DEFAULT_REGION": self.region,
                "ACTIVITY_ARN": SecretValue.unsafe_plain_text(
                    self.browser_activity.activity_arn
                ),
                "S3_BUCKET": SecretValue.unsafe_plain_text(
                    self.recordings_bucket.bucket_name
                )
            }
        )
```

**Benefits**:
✅ **Fully automated** - One CDK deploy creates everything
✅ **Consistent** - Same setup for all environments
✅ **Least privilege** - Only permissions needed
✅ **Secure storage** - Credentials in Secrets Manager
✅ **Easy rotation** - Delete/recreate stack to rotate keys

#### B. Local Agent Configuration via Secrets Manager

```python
# lambda/tools/local-browser-agent/python/config_helper.py

import boto3
import json

class AwsConfigHelper:
    """Helper to fetch configuration from AWS Secrets Manager"""

    @staticmethod
    def setup_credentials(env_name="prod", profile_name=None):
        """
        Fetch credentials from Secrets Manager and set environment variables

        Usage:
            # One-time setup in local agent
            setup_credentials(env_name="prod")
            # Now can use boto3 without manual credential configuration
        """
        session = boto3.Session(profile_name=profile_name) if profile_name else boto3.Session()
        secrets = session.client('secretsmanager')

        secret_name = f"browser-agent-credentials-{env_name}"

        try:
            response = secrets.get_secret_value(SecretId=secret_name)
            creds = json.loads(response['SecretString'])

            # Set environment variables
            os.environ['AWS_ACCESS_KEY_ID'] = creds['AWS_ACCESS_KEY_ID']
            os.environ['AWS_SECRET_ACCESS_KEY'] = creds['AWS_SECRET_ACCESS_KEY']
            os.environ['AWS_DEFAULT_REGION'] = creds['AWS_DEFAULT_REGION']

            return {
                "activity_arn": creds['ACTIVITY_ARN'],
                "s3_bucket": creds['S3_BUCKET'],
                "region": creds['AWS_DEFAULT_REGION']
            }
        except Exception as e:
            raise ValueError(f"Failed to fetch credentials: {e}")
```

**Setup Process** (User Perspective):
```bash
# OLD (Manual - 15 minutes):
aws iam create-user --user-name browser-agent-user
aws iam create-access-key --user-name browser-agent-user
# ... 10 more commands ...
set AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
set AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG...

# NEW (Automated - 30 seconds):
# 1. User assumes role with secretsmanager:GetSecretValue permission
# 2. Local agent fetches credentials automatically from Secrets Manager
python -m local_browser_agent --setup --env prod
# Done!
```

**Alternative: AWS Systems Manager (SSM) Parameter Store**
```python
# Even simpler for public (non-sensitive) values
# Activity ARN and S3 bucket are not secrets, just configuration

ssm = boto3.client('ssm')

activity_arn = ssm.get_parameter(
    Name=f"/browser-agent/{env_name}/activity-arn"
)['Parameter']['Value']

s3_bucket = ssm.get_parameter(
    Name=f"/browser-agent/{env_name}/s3-bucket"
)['Parameter']['Value']
```

---

### Solution 2: Recording Levels (Like Logging Levels)

#### A. Define Recording Levels

```python
# lambda/tools/local-browser-agent/python/recording_levels.py

from enum import Enum

class RecordingLevel(Enum):
    """Recording levels for browser automation - similar to logging levels"""

    NONE = 0      # No recording uploads
    ERROR = 1     # Upload only on errors/failures
    INFO = 2      # Upload final extraction/result pages only
    DEBUG = 3     # Upload key intermediate steps
    TRACE = 4     # Upload everything (all steps, full video)

    @classmethod
    def from_string(cls, level_str: str):
        """Parse from string (case-insensitive)"""
        return cls[level_str.upper()]
```

**Level Descriptions**:

| Level | What Gets Uploaded | Use Case | Storage Impact |
|-------|-------------------|----------|----------------|
| `NONE` | Nothing | Privacy-sensitive, local testing | 0% |
| `ERROR` | Error screenshots, error state HTML | Production - only debug failures | ~1-5% |
| `INFO` | Final result page screenshot, extraction data | Audit trail, compliance | ~10-20% |
| `DEBUG` | Key steps (login, form submission, extraction) | Development, troubleshooting | ~40-60% |
| `TRACE` | Full video + all screenshots + all HTML | Full debugging, training data | 100% |

#### B. Implementation in Script Executor

```python
# lambda/tools/local-browser-agent/python/script_executor.py

class ScriptExecutor:
    def __init__(
        self,
        s3_bucket: Optional[str] = None,
        recording_level: RecordingLevel = RecordingLevel.INFO,  # NEW
        ...
    ):
        self.recording_level = recording_level

    def execute_script(self, script: Dict[str, Any]) -> Dict[str, Any]:
        """Execute script with recording level control"""

        # Determine what to record based on level
        if self.recording_level == RecordingLevel.NONE:
            # Don't initialize S3Writer at all
            stop_hooks = []
            record_video = False

        elif self.recording_level == RecordingLevel.ERROR:
            # Initialize S3Writer, but only upload on errors
            # Use conditional upload logic
            stop_hooks = []
            record_video = True  # Record locally
            upload_on_error_only = True

        elif self.recording_level == RecordingLevel.INFO:
            # Upload only final extraction step
            stop_hooks = []
            record_video = False  # Don't record full video
            capture_final_screenshot = True

        elif self.recording_level == RecordingLevel.DEBUG:
            # Upload key steps only
            stop_hooks = []
            record_video = True  # Partial recording
            upload_key_steps_only = True

        elif self.recording_level == RecordingLevel.TRACE:
            # Upload everything (current behavior)
            s3_writer = S3Writer(...)
            stop_hooks = [s3_writer]
            record_video = True
```

#### C. Step-Level Upload Control

```python
def execute_step(self, step, nova, step_num):
    """Execute a single step with conditional recording"""

    action = step.get('action')
    is_final_step = (step_num == len(steps))
    is_error_screenshot = False

    try:
        # Execute step
        if action == "act":
            result = nova.act(...)

        elif action == "act_with_schema":
            result = nova.act(...)
            is_extraction_step = True  # Mark as important

    except Exception as e:
        is_error_screenshot = True
        raise

    finally:
        # Decide whether to upload this step's recording
        should_upload = self._should_upload_step(
            is_error=is_error_screenshot,
            is_final=is_final_step,
            is_extraction=is_extraction_step,
            action=action
        )

        if should_upload:
            self._upload_step_recording(step_num, result)

def _should_upload_step(self, is_error, is_final, is_extraction, action):
    """Determine if this step should be uploaded based on recording level"""

    if self.recording_level == RecordingLevel.NONE:
        return False

    if self.recording_level == RecordingLevel.ERROR:
        return is_error  # Only errors

    if self.recording_level == RecordingLevel.INFO:
        return is_final or is_extraction or action == "screenshot"  # Final/extraction only

    if self.recording_level == RecordingLevel.DEBUG:
        return is_error or is_extraction or action in ["act_with_schema", "screenshot"]

    if self.recording_level == RecordingLevel.TRACE:
        return True  # Everything
```

#### D. Configuration in Templates

```json
{
  "name": "BT Wholesale Broadband Availability Check",
  "session": {
    "required_tags": ["btwholesale.com", "authenticated"],
    "recording_level": "INFO"  // NEW: per-template configuration
  },
  "steps": [...]
}
```

#### E. Environment-Based Defaults

```yaml
# config.yaml
recording:
  default_level: INFO

  # Override by environment
  level_by_env:
    dev: TRACE       # Full recording in development
    staging: DEBUG   # Detailed recording in staging
    prod: INFO       # Minimal recording in production

  # Override by agent
  level_by_agent:
    broadband-availability: INFO      # Audit trail only
    web-scraper-dev: TRACE            # Full debugging
    form-filler-prod: ERROR           # Only failures
```

---

### Solution 3: Improved Permission Scoping

#### A. Environment-Specific Policies

```python
# stacks/tools/browser_remote_tool_stack.py

# CURRENT (Too broad):
"Resource": "arn:aws:states:*:*:activity:browser-remote-*"

# PROPOSED (Scoped to environment):
"Resource": self.browser_activity.activity_arn  # Exact ARN
```

#### B. Conditional S3 Access

```python
# Only grant S3 permissions if recording level > NONE
if recording_level != RecordingLevel.NONE:
    self.recordings_bucket.grant_put(self.local_agent_user)
```

---

## Implementation Plan

### Phase 1: Automated IAM (Week 1)
**Goal**: Eliminate manual IAM setup

1. ✅ Add IAM User creation to `BrowserRemoteToolStack`
2. ✅ Store credentials in Secrets Manager
3. ✅ Add `config_helper.py` for credential fetching
4. ✅ Update local agent to use Secrets Manager
5. ✅ Update documentation (replace manual steps)

**Testing**:
- Deploy stack to dev environment
- Run local agent with `--setup` flag
- Verify automatic credential fetch
- Test Activity polling and S3 upload

### Phase 2: Recording Levels (Week 2)
**Goal**: Add INFO/DEBUG/TRACE/ERROR levels

1. ✅ Add `RecordingLevel` enum
2. ✅ Update `ScriptExecutor` with level logic
3. ✅ Add `_should_upload_step()` method
4. ✅ Update templates with `recording_level` field
5. ✅ Add config file support for defaults

**Testing**:
- Run same script with TRACE vs INFO vs ERROR
- Verify storage usage differences
- Measure upload times

### Phase 3: UI Integration (Week 3)
**Goal**: User-friendly configuration

1. ✅ Add "Recording Level" dropdown in local agent UI
2. ✅ Add "Fetch AWS Config" button (calls Secrets Manager)
3. ✅ Show estimated storage impact per level
4. ✅ Add recording level to activity task input

### Phase 4: Documentation & Migration (Week 4)
**Goal**: Update all docs and migrate existing users

1. ✅ Update `IAM_PERMISSIONS.md` with new automated flow
2. ✅ Add `RECORDING_LEVELS.md` guide
3. ✅ Create migration script for existing users
4. ✅ Update CDK deployment guide

---

## Storage Impact Analysis

### Current State (TRACE equivalent):
```
Average session: 5 minutes, 15 steps
- Video: 50 MB (full screen recording)
- Screenshots: 15 × 500 KB = 7.5 MB
- HTML snapshots: 15 × 100 KB = 1.5 MB
Total: ~59 MB per session
```

**With 100 sessions/day**:
- Daily: 5.9 GB
- Monthly: 177 GB
- Yearly: 2.1 TB
- Cost (S3 Standard): ~$50/month

### Proposed with INFO level:
```
Average session: 5 minutes, 15 steps
- Final screenshot only: 500 KB
- Final HTML snapshot: 100 KB
- Extraction JSON: 10 KB
Total: ~610 KB per session (99% reduction!)
```

**With 100 sessions/day**:
- Daily: 61 MB
- Monthly: 1.8 GB
- Yearly: 22 GB
- Cost (S3 Standard): ~$0.50/month (100x cheaper!)

### Level Comparison:

| Level | Per Session | 100 sessions/day | Monthly Cost | Use Case |
|-------|-------------|------------------|--------------|----------|
| NONE | 0 MB | 0 MB | $0 | Privacy/testing |
| ERROR | ~1 MB | 100 MB | $0.02 | Production |
| INFO | ~0.6 MB | 61 MB | $0.50 | Audit trail |
| DEBUG | ~20 MB | 2 GB | $10 | Development |
| TRACE | ~59 MB | 5.9 GB | $50 | Full debugging |

---

## Security Considerations

### 1. Secrets Manager Access
**Requirement**: Local agent needs `secretsmanager:GetSecretValue`

**Options**:
- **A. User's personal AWS profile** (recommended for individual developers)
  - User assumes role with `secretsmanager:GetSecretValue` once
  - Fetches credentials, stores locally
  - Uses stored credentials for Activity polling

- **B. EC2 instance role** (for hosted agents)
  - Agent running on EC2 uses instance role
  - No credential management needed

- **C. Initial bootstrap** (for zero-trust environments)
  - Admin provides one-time bootstrap token
  - Token grants temporary access to fetch credentials
  - Token expires after first use

### 2. Credential Rotation
```python
# Automated rotation via CDK
class BrowserRemoteToolStack(Stack):
    def enable_auto_rotation(self):
        # Rotate access keys every 90 days
        self.access_key_rotation = lambda_.Function(
            self, "RotateAccessKeys",
            handler="rotate_keys.handler",
            schedule=events.Schedule.rate(Duration.days(90))
        )
```

### 3. Audit Logging
```python
# Enable CloudTrail for Activity API calls
trail = cloudtrail.Trail(
    self, "BrowserAgentTrail",
    include_global_service_events=True,
    management_events=ReadWriteType.WRITE_ONLY
)
```

---

## Migration Guide

### For Existing Users

**Before (Manual Setup)**:
```bash
# 15 minutes of work
aws iam create-user ...
aws iam create-policy ...
aws iam attach-user-policy ...
aws iam create-access-key ...
set AWS_ACCESS_KEY_ID=...
set AWS_SECRET_ACCESS_KEY=...
```

**After (Automated Setup)**:
```bash
# 30 seconds
# 1. Deploy CDK stack (creates IAM user + credentials)
cdk deploy BrowserRemoteToolStack-prod

# 2. Fetch credentials (one-time, using your AWS profile)
local-browser-agent --setup --env prod --aws-profile YOUR_PROFILE

# 3. Done! Credentials stored securely
```

### Backward Compatibility

The new system is **fully backward compatible**:
- Environment variables still work (for existing setups)
- Profile files still work
- New Secrets Manager method is optional

---

## Open Questions

1. **Secrets Manager Cost**: ~$0.40/secret/month. Worth it for automation?
   - **Answer**: Yes for prod, optional for dev (can use SSM Parameter Store for free)

2. **Recording Level Override**: Should agents be able to override template's recording level?
   - **Answer**: Yes via environment variable `RECORDING_LEVEL_OVERRIDE=TRACE`

3. **Partial Video Upload**: Can we upload only certain time ranges of video?
   - **Answer**: NovaAct S3Writer uploads full video. Need custom post-processing.

4. **Credential Sharing**: Can multiple local agents share same IAM user?
   - **Answer**: Yes, but consider security. Better: one user per machine/developer.

---

## Summary

### Current State:
❌ Manual IAM setup (15 minutes per agent)
❌ Binary recording (all or nothing)
❌ No granular control
❌ High storage costs

### Proposed State:
✅ Automated IAM via CDK (30 seconds setup)
✅ Recording levels (NONE/ERROR/INFO/DEBUG/TRACE)
✅ 99% storage reduction with INFO level
✅ Template-level and environment-level defaults
✅ Secure credential management (Secrets Manager)
✅ Backward compatible

### Next Steps:
1. Review and approve this design
2. Implement Phase 1 (Automated IAM)
3. Test in dev environment
4. Roll out to production
