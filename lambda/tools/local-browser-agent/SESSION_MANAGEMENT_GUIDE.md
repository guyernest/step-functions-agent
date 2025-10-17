# Browser Session & Profile Management Guide

## Overview

The local browser agent now supports persistent browser sessions and profile management, allowing you to:

1. **Reuse authenticated sessions** across multiple automation runs
2. **Avoid repeated logins** that trigger CAPTCHAs and bot detection
3. **Support human-assisted login** for sensitive credentials or MFA
4. **Share profiles** across different scripts and workflows
5. **Manage multiple profiles** for different services or accounts

## Key Benefits

### Efficiency
- **No repeated logins**: Login once, reuse the session multiple times
- **Faster execution**: Skip authentication flows in subsequent runs
- **Avoid bot detection**: Real browser sessions appear more natural

### Security
- **Human-controlled login**: Manually enter sensitive credentials
- **MFA support**: Handle multi-factor authentication manually
- **CAPTCHA bypass**: Solve CAPTCHAs once, reuse the session

### Flexibility
- **Multiple profiles**: Separate profiles for different services
- **Tagged organization**: Categorize profiles (production, staging, personal)
- **Session expiration**: Configure how long sessions remain valid

## Architecture

### Components

1. **ProfileManager** (`profile_manager.py`)
   - Creates and manages browser profiles
   - Stores metadata about each profile
   - Handles session validation and expiration

2. **Enhanced ScriptExecutor** (`script_executor.py`)
   - Supports session configuration in scripts
   - Integrates with ProfileManager
   - Handles human login workflows

3. **Script Format**
   - Extended JSON format with `session` configuration
   - Supports profile creation and reuse
   - Configurable login workflows

## Usage Patterns

### Pattern 1: Create Profile with Manual Login

**Use Case**: Initial setup for a service requiring authentication

**Script**: `script_setup_login.json`
```json
{
  "name": "Setup Login Session",
  "description": "Create profile with manual login",
  "starting_page": "https://your-service.com/login",
  "session": {
    "mode": "create_profile",
    "profile_name": "my_service_profile",
    "profile_description": "Authenticated session for My Service",
    "profile_tags": ["production", "authenticated"],
    "clone_for_parallel": false,
    "requires_human_login": true,
    "wait_for_human_login": true,
    "login_timeout_minutes": 10,
    "post_login_verification": "Can you see the dashboard?",
    "auto_login_sites": [
      "https://your-service.com",
      "https://app.your-service.com"
    ]
  },
  "steps": [
    {
      "action": "act_with_schema",
      "prompt": "What is the user's display name?",
      "schema": {
        "type": "object",
        "properties": {
          "user_name": {"type": "string"}
        }
      },
      "description": "Verify login"
    }
  ]
}
```

**Execution**:
```bash
python script_executor.py --script examples/script_setup_login.json
```

**Workflow**:
1. Script creates a new profile
2. Browser opens to login page (non-headless)
3. Script pauses, waiting for human login
4. User manually logs in, enters credentials, solves CAPTCHA, completes MFA
5. User presses ENTER to continue
6. Script verifies login was successful
7. Session is saved in the profile for future use

### Pattern 2: Reuse Existing Profile

**Use Case**: Run automation using a previously authenticated session

**Script**: `script_with_profile_banking.json`
```json
{
  "name": "Check Bank Transactions",
  "description": "Extract transactions using saved session",
  "starting_page": "https://bank.com/dashboard",
  "session": {
    "profile_name": "banking_profile",
    "clone_for_parallel": false,
    "requires_human_login": false,
    "session_timeout_hours": 12
  },
  "steps": [
    {
      "action": "act",
      "prompt": "Navigate to transactions",
      "description": "Go to transactions page"
    },
    {
      "action": "act_with_schema",
      "prompt": "Extract last 5 transactions",
      "schema": {
        "type": "object",
        "properties": {
          "transactions": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "date": {"type": "string"},
                "description": {"type": "string"},
                "amount": {"type": "number"}
              }
            }
          }
        }
      }
    }
  ]
}
```

**Execution**:
```bash
python script_executor.py --script examples/script_with_profile_banking.json
```

**Workflow**:
1. Script loads the `banking_profile`
2. Browser starts with saved cookies and session data
3. Script navigates directly to dashboard (already authenticated)
4. Extracts transaction data
5. Completes without any login required

### Pattern 3: Parallel Execution with Cloning

**Use Case**: Run multiple automations in parallel using the same profile

**Script Configuration**:
```json
{
  "session": {
    "profile_name": "shared_profile",
    "clone_for_parallel": true
  }
}
```

**Workflow**:
- Each execution gets its own copy of the profile
- Prevents conflicts between parallel runs
- Preserves the original profile

## Profile Management CLI

The `profile_manager.py` can be used standalone for profile management:

### Create a Profile
```bash
python profile_manager.py create \
  --profile "banking_profile" \
  --description "Profile for banking automation" \
  --tags production authenticated
```

### List Profiles
```bash
# List all profiles
python profile_manager.py list

# List profiles by tag
python profile_manager.py list --tags production
```

### Delete a Profile
```bash
python profile_manager.py delete --profile "old_profile"
```

### Create Profile with Interactive Login
```bash
python profile_manager.py login \
  --profile "service_profile" \
  --url "https://service.com/login"
```

## Session Configuration Reference

### Session Object Properties

| Property | Type | Description | Default |
|----------|------|-------------|---------|
| `mode` | string | `"use_profile"` or `"create_profile"` | `"use_profile"` |
| `profile_name` | string | Name of the profile to use/create | Required |
| `profile_description` | string | Description for new profiles | `""` |
| `profile_tags` | array | Tags for categorization | `[]` |
| `clone_for_parallel` | boolean | Clone profile for parallel execution | `false` |
| `requires_human_login` | boolean | Indicates manual login needed | `false` |
| `wait_for_human_login` | boolean | Pause for user to log in | `false` |
| `login_timeout_minutes` | number | Max time to wait for login | `10` |
| `post_login_verification` | string | Prompt to verify successful login | `null` |
| `auto_login_sites` | array | Sites where auto-login applies | `[]` |
| `session_timeout_hours` | number | How long sessions are valid | `24` |

## Nova Act Integration

### User Data Directory

Profiles use Nova Act's `user_data_dir` parameter:

```python
NovaAct(
    starting_page="https://example.com",
    user_data_dir="/path/to/profile",
    clone_user_data_dir=False  # Preserves session
)
```

### Clone Behavior

- `clone_user_data_dir=False`: Reuses the same directory (session persistence)
- `clone_user_data_dir=True`: Creates a temporary copy (parallel execution)

## Best Practices

### Security

1. **Never commit profiles to Git**
   - Add `browser-profiles/` to `.gitignore`
   - Profiles contain session cookies and may include sensitive data

2. **Use separate profiles for different security levels**
   - Production vs. staging environments
   - Personal vs. business accounts

3. **Set appropriate session timeouts**
   - Shorter timeouts for sensitive services (banking: 12 hours)
   - Longer timeouts for low-risk services (news sites: 7 days)

### Reliability

1. **Always use `post_login_verification`**
   - Confirms login was successful
   - Catches session expiration issues

2. **Handle session expiration gracefully**
   - Check `session_expired_warning` in results
   - Re-run login script if needed

3. **Test profile creation separately**
   - Create and verify profiles before using in automation
   - Ensures credentials work and login flow is understood

### Performance

1. **Reuse profiles across scripts**
   - One login serves many automation tasks
   - Reduces overall execution time

2. **Use cloning for parallel execution**
   - Prevents profile corruption
   - Allows concurrent runs

3. **Clean up old profiles**
   - Delete unused profiles periodically
   - Prevents disk space issues

## Profile Validation

Use the built-in validation to assess a profile's readiness and authentication state:

- `static` checks: verify `user_data_dir` structure and presence of key files (Cookies DB, Local Storage, Preferences, Local State).
- `runtime` checks: open the profile and confirm login via UI prompt, expected cookies, or specific `localStorage` keys.

Ways to run validation:

- Script step in `script_executor.py`:
  - Add a step `{ "action": "validate_profile", "mode": "both", "ui_prompt": "Return true if logged in", "cookie_domains": ["example.com"], "cookie_names": ["session"] }`.
- Wrapper command (`nova_act_wrapper.py`):
  - Send `{ "command_type": "validate_profile", "user_data_dir": "/path/to/profile", "mode": "both", "starting_page": "https://example.com", "ui_prompt": "Return true if logged in" }`.

Recommendation: keep `clone_user_data_dir` set to `false` for normal runs to persist sessions; set to `true` only for parallel or throwaway runs.

## File Structure

```
browser-profiles/
├── profiles.json                    # Metadata for all profiles
├── banking_profile/                 # Profile directory
│   ├── Default/                     # Chromium user data
│   │   ├── Cookies                  # Session cookies
│   │   ├── Local Storage/
│   │   └── ...
│   └── ...
├── shopping_profile/
│   └── ...
└── ...
```

## Troubleshooting

### Session Expired

**Symptom**: Script shows "session_expired_warning"

**Solution**:
1. Re-run the login setup script
2. Manually log in again
3. Profile will be updated with new session

### Profile Not Found

**Symptom**: Error "Profile 'xxx' not found"

**Solutions**:
1. Check profile name spelling
2. List all profiles: `python profile_manager.py list`
3. Create the profile if it doesn't exist

### Login Verification Failed

**Symptom**: "login_verification_error" in results

**Solutions**:
1. Check the `post_login_verification` prompt is accurate
2. Ensure you're fully logged in before pressing ENTER
3. Verify the target page loaded correctly

### Parallel Execution Conflicts

**Symptom**: Unexpected behavior when running multiple scripts

**Solution**:
Set `clone_for_parallel: true` in session configuration

## Advanced: Sharing Profiles

### Export a Profile

```python
from profile_manager import ProfileManager

manager = ProfileManager()
archive_path = manager.export_profile(
    "my_profile",
    "/path/to/export"
)
```

### Import a Profile

```python
manager.import_profile(
    "/path/to/export.zip",
    new_profile_name="imported_profile"
)
```

**Use Cases**:
- Share authenticated sessions across team members
- Backup profiles before major changes
- Transfer profiles between machines

## Integration with UI

The browser agent UI will support:

1. **Profile Management Tab**
   - Create/delete profiles
   - View profile metadata
   - Trigger login workflows

2. **Script Editor**
   - Profile selector dropdown
   - Session configuration builder
   - Visual indicators for profile usage

3. **Execution Monitor**
   - Show which profile was used
   - Display session status
   - Alert on session expiration

## Examples

See `python/examples/` for complete example scripts:

- `script_setup_login.json` - Create profile with manual login
- `script_with_profile_banking.json` - Use existing profile for automation
- `script_information_extraction_demo.json` - Complex extraction workflow

## Support

For issues or questions:
1. Check this guide first
2. Review example scripts
3. Test with `profile_manager.py` CLI for profile-specific issues
4. Check Nova Act documentation for browser-specific issues
