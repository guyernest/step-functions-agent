# Getting Started with Local Browser Agent

**A step-by-step guide from installation to automation**

This guide will walk you through setting up the Local Browser Agent, testing it locally, and eventually connecting it to AWS Step Functions for cloud orchestration.

---

## 📋 Table of Contents

1. [Installation](#installation)
2. [Initial Configuration](#initial-configuration)
3. [Local Testing (No Profiles)](#local-testing-no-profiles)
4. [Creating Your First Profile](#creating-your-first-profile)
5. [Testing with Profiles](#testing-with-profiles)
6. [Advanced: Tag-Based Profile Matching](#advanced-tag-based-profile-matching)
7. [Cloud Integration](#cloud-integration)
8. [Troubleshooting](#troubleshooting)

---

## Installation

### Windows

1. **Download the installer**
   - Get `Local-Browser-Agent-Setup.exe` from the releases
   - Run the installer

2. **Run the setup script**
   ```powershell
   # Open PowerShell and navigate to the installation directory
   cd "%LOCALAPPDATA%\Programs\Local Browser Agent"

   # Run the Python environment setup
   .\SETUP.ps1
   ```

3. **Launch the application**
   - Find "Local Browser Agent" in Start Menu
   - Or double-click the desktop icon

### macOS

1. **Install the application**
   ```bash
   # Open the DMG file
   open Local-Browser-Agent.dmg

   # Drag to Applications folder
   ```

2. **Run the setup script**
   ```bash
   # Open Terminal and navigate to the app bundle
   cd "/Applications/Local Browser Agent.app/Contents/Resources/deployment-package"

   # Run the Python environment setup
   ./SETUP.sh
   ```

3. **Launch the application**
   - Open from Applications folder
   - Or use Spotlight: `⌘ + Space`, type "Local Browser Agent"

### What the Setup Script Does

- ✅ Installs/detects UV package manager
- ✅ Creates Python 3.11 virtual environment
- ✅ Installs required Python packages (NovaAct, boto3, etc.)
- ✅ Installs Chromium browser (fallback option)
- ✅ Takes 2-5 minutes depending on internet speed

---

## Initial Configuration

When you first launch the app, you'll see "Not Configured" status. Let's fix that!

### 1. Configure AWS Credentials

**Option A: Use existing AWS profile** (Recommended)
```bash
# Check your existing profiles
aws configure list-profiles

# The app will auto-detect these
```

**Option B: Create new profile for the agent**
```bash
# Create ~/.aws/credentials (Windows: %USERPROFILE%\.aws\credentials)
[browser-agent]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY
region = us-east-1
```

### 2. Get AWS Step Functions Activity ARN

If you've already deployed the cloud infrastructure:
```bash
# From your CDK deployment outputs
aws cloudformation describe-stacks \
  --stack-name BrowserAgentStack \
  --query 'Stacks[0].Outputs[?OutputKey==`ActivityArn`].OutputValue' \
  --output text
```

Copy this ARN - you'll need it in the next step.

### 3. Fill in Configuration Screen

1. Click **"Config"** tab in the app
2. Fill in required fields:
   - **AWS Profile**: Select from dropdown (e.g., `browser-agent`)
   - **AWS Region**: Leave empty to use profile default, or specify (e.g., `us-east-1`)
   - **Activity ARN**: Paste from CDK outputs (e.g., `arn:aws:states:us-east-1:123456789:activity:browser-remote-prod`)
   - **S3 Bucket**: For recordings (e.g., `browser-agent-recordings-prod-123456789`)
   - **Browser Channel**: Select browser:
     - Windows: **Microsoft Edge** (recommended - pre-installed)
     - macOS: **Google Chrome** (recommended)
     - Fallback: **Chromium** (installed by setup script)

3. Click **"Test Connection"** to verify AWS credentials
4. Click **"Validate ARN"** to verify Step Functions activity
5. Click **"Save Configuration"**

✅ Status should now show **"Configured"**!

---

## Local Testing (No Profiles)

Let's verify everything works before creating profiles.

### 1. Go to Test Tab

Click the **"Test"** tab in the sidebar.

### 2. Load Simple Example

1. Click **"Load Example"** button
2. Select **"simple_google_search.json"**
3. You'll see:
   ```json
   {
     "name": "Simple Google Search",
     "description": "Basic test - search Google",
     "starting_page": "https://www.google.com",
     "steps": [
       {
         "action": "act",
         "prompt": "Search for 'browser automation' and press Enter"
       }
     ]
   }
   ```

### 3. Run the Test

1. Click **"Execute Script"**
2. Watch the browser open automatically
3. See the automation in action
4. Check the results in the output panel

**Expected result**: ✅ Browser opens, searches Google, shows results

### 4. Check the Logs

In the output panel, you'll see:
```
→ Using temporary profile (no persistent session)
[INFO] Starting browser session with:
  - Script: Simple Google Search
  - Profile: None
  - Starting Page: https://www.google.com
  - Browser: msedge (or chrome/chromium)
✓ Step completed successfully
```

**What's happening?**
- No profile specified → uses temporary session
- No saved cookies → fresh browser state each time
- Perfect for testing basic functionality

---

## Creating Your First Profile

Profiles let you save login sessions so you don't have to log in every time.

### Why Create Profiles?

**Without profiles**:
- ❌ Log in every time
- ❌ Manual MFA every run
- ❌ Loses session between runs

**With profiles**:
- ✅ Log in once, use forever
- ✅ Handle MFA once during setup
- ✅ Persistent session across runs
- ✅ Support for multiple accounts

### Step-by-Step Profile Creation

#### 1. Go to Profiles Tab

Click the **"Profiles"** tab in the sidebar.

#### 2. Click "Create Profile"

Fill in the form:

**Example: Amazon Shopping Account**
```
Profile Name: My_Amazon_Shopping
Description: My personal Amazon account for shopping automation
Tags: amazon.com, authenticated, buyer, personal
Auto-Login Sites: amazon.com, smile.amazon.com
Session Timeout: 24 hours
```

**Tag Explanation**:
- `amazon.com` - Domain this profile is for
- `authenticated` - Has login credentials saved
- `buyer` - Can make purchases
- `personal` - My personal account (not shared)

#### 3. Click "Save"

✅ Profile created! But it has no session data yet.

#### 4. Setup Login for Profile

1. Select your new profile from the list
2. Click **"Setup Login"** button
3. In the popup:
   - **Starting URL**: `https://www.amazon.com`
   - **Timeout**: `300` seconds (5 minutes)
4. Click **"Start Setup"**

**What happens next**:
- Browser opens to Amazon.com
- You have 5 minutes to manually log in
- Complete any MFA/CAPTCHA challenges
- Browser stays open - do not close it
- When done, just wait for timeout or close the setup window

5. ✅ **Your login session is now saved!**

---

## Testing with Profiles

Now let's use the profile we just created.

### Example 1: Using Exact Profile Name

Create a test script:
```json
{
  "name": "Check My Amazon Orders",
  "description": "Uses my saved Amazon profile",
  "starting_page": "https://www.amazon.com/orders",
  "session": {
    "profile_name": "My_Amazon_Shopping"
  },
  "steps": [
    {
      "action": "act",
      "prompt": "Tell me the status of my most recent order"
    }
  ]
}
```

**Run it**:
1. Paste the JSON in Test tab
2. Click "Execute Script"
3. Watch it open already logged in! 🎉

**Logs will show**:
```
✓ Resolved profile by exact name: 'My_Amazon_Shopping'
[INFO] Starting browser session with:
  - Profile: My_Amazon_Shopping
  - Profile Path: ~/.local-browser-agent/profiles/My_Amazon_Shopping/chrome_data
✓ Already logged in - no authentication needed!
```

### Example 2: Multiple Profiles

Let's say you create multiple profiles:
- `Work_Amazon` - tags: `amazon.com, authenticated, work`
- `Personal_Amazon` - tags: `amazon.com, authenticated, personal`
- `Test_Amazon` - tags: `amazon.com, authenticated, testing`

You can specify which one to use:
```json
{
  "session": {
    "profile_name": "Work_Amazon"  // Uses work account
  }
}
```

---

## Advanced: Tag-Based Profile Matching

This is where the power of the system shines! 🌟

### The Problem with Names

Imagine you have 100 users, each with their own Amazon profile:
- Alice names hers: `"Alice_Personal_Amazon"`
- Bob names his: `"Bob_Amazon_Shopping"`
- Charlie names his: `"Amazon"`

**Question**: How does the cloud script reference "any authenticated Amazon account"?

**Answer**: Use **tags** instead of names!

### Tag-Based Resolution

Instead of specifying exact profile names, specify **capabilities** (tags):

```json
{
  "name": "Product Price Check",
  "description": "Check product price - works for ANY user with Amazon access",
  "starting_page": "https://www.amazon.com",
  "session": {
    "required_tags": ["amazon.com", "authenticated"],
    "allow_temp_profile": false
  },
  "steps": [
    {
      "action": "act",
      "prompt": "Go to product with ASIN B08J5F3G18 and tell me the current price"
    }
  ]
}
```

**What happens**:
- Alice's machine: Finds `"Alice_Personal_Amazon"` (has both tags) ✓
- Bob's machine: Finds `"Bob_Amazon_Shopping"` (has both tags) ✓
- Charlie's machine: Finds `"Amazon"` (has both tags) ✓
- Machine without Amazon profile: Error with helpful message ✗

**Try it yourself**:
1. Load `examples/tag_based_profile_example.json` in Test tab
2. Click Execute
3. Watch it automatically find your Amazon profile by tags!

### Resolution Priority

The system tries in this order:

1. **Exact name** (if `profile_name` provided) - "Use this specific profile"
2. **Tag matching** (if `required_tags` provided) - "Use any profile with these capabilities"
3. **Temporary profile** (if `allow_temp_profile: true`) - "Use temp session if no match"
4. **Error** (if nothing matches and temp not allowed) - "Show helpful error"

### Practical Example: Personal vs Pool Work

**Your profiles**:
```bash
# Personal Amazon account
Profile: "My_Amazon"
Tags: ["amazon.com", "authenticated", "buyer", "personal"]

# Company pool account (shared resource)
Profile: "Company_Amazon_Pool"
Tags: ["amazon.com", "authenticated", "read-only", "pool"]
```

**Personal work** (only runs on your machine):
```json
{
  "session": {
    "required_tags": ["amazon.com", "authenticated", "buyer"]
    // No "pool" tag - won't match pool accounts
  }
}
```

**Pool work** (can run on any pool machine):
```json
{
  "session": {
    "required_tags": ["amazon.com", "authenticated", "pool"]
    // Must have "pool" tag
  }
}
```

**Result**: Same machine, automatic isolation based on tags!

---

## Cloud Integration

Once local testing works, connect to AWS Step Functions.

### 1. Start Listening for Activities

1. Go to **"Listen"** tab
2. Click **"Start Polling"**
3. Status shows: "Polling for tasks..."

**What's happening**:
- App polls Step Functions Activity ARN
- When cloud sends work, it appears here
- Executes automatically
- Sends results back to cloud

### 2. Trigger from Cloud

From your AWS environment:
```bash
# Start a Step Functions execution
aws stepfunctions start-execution \
  --state-machine-arn arn:aws:states:us-east-1:123:stateMachine:BrowserAutomation \
  --input '{
    "url": "https://example.com",
    "action": "extract_data"
  }'
```

### 3. Watch Execution

In the Listen tab, you'll see:
```
📥 Received task: task-token-abc123
🔍 Resolving profile by tags: ["example.com", "authenticated"]
✓ Matched profile: "Example_Site_Profile"
🚀 Executing automation...
✅ Task completed successfully
📤 Sent results to cloud
```

### 4. Cloud Gets Results

Step Functions receives:
```json
{
  "success": true,
  "data": "...",
  "profile_used": "Example_Site_Profile",
  "session_id": "...",
  "duration": 12.5
}
```

---

## Troubleshooting

### "Not Configured" Status

**Problem**: Red dot, "Not Configured" in sidebar

**Fix**:
1. Go to Config tab
2. Fill in: Activity ARN, AWS Profile, S3 Bucket
3. Click "Save Configuration"
4. Status should turn green: "Configured"

### "Python venv not found"

**Problem**: Can't create profiles or run tests

**Fix**:
1. Run the setup script again:
   - Windows: `.\SETUP.ps1`
   - macOS: `./SETUP.sh`
2. Restart the application
3. Check Python Environment status in Config tab

### Browser Opens But Script Fails

**Problem**: Browser opens, but automation doesn't work

**Possible causes**:
1. **Wrong browser channel**:
   - Try different browser (Edge, Chrome, Chromium)
   - Config → Browser Channel → Select different option

2. **NovaAct API key missing**:
   - Check if you have `NOVA_ACT_API_KEY` environment variable
   - Or AWS IAM credentials configured

3. **Profile session expired**:
   - Go to Profiles tab
   - Click "Setup Login" again to refresh session

### "No suitable profile found"

**Problem**: Script requires profile with tags you don't have

**Error message shows**:
```
No suitable profile found. Required tags: ['amazon.com', 'authenticated']

Available profiles:
  • My_Google: tags=['google.com', 'authenticated']
    Missing: ['amazon.com']
```

**Fix**:
1. Create a profile with the required tags
2. Or update existing profile to add missing tags
3. Or allow temporary profile: `"allow_temp_profile": true`

### Connection to AWS Fails

**Problem**: "Test Connection" button fails

**Check**:
1. **AWS credentials**:
   ```bash
   aws sts get-caller-identity --profile browser-agent
   ```

2. **Network access**:
   - Can you reach AWS from this machine?
   - Corporate proxy/firewall blocking?

3. **IAM permissions**:
   - Does your user have `states:GetActivityTask` permission?
   - Does it have access to the S3 bucket?

---

## Next Steps

### Local Development Workflow

1. **Create profiles** for sites you'll automate
2. **Test scripts locally** using Test tab
3. **Iterate quickly** - no cloud deployment needed
4. **Once stable**, connect to cloud for orchestration

### Production Deployment

1. **Install on multiple machines** for scale
2. **Create pool profiles** for shared work
3. **Use tag-based resolution** for flexibility
4. **Monitor via Listen tab** during execution

### Advanced Features

- **Profile validation**: Check if session is still valid
- **Multiple profiles per site**: Switch between accounts
- **Session timeout**: Auto-expire after X hours
- **Profile export/import**: Share profiles (metadata only, no credentials)

---

## Key Concepts Summary

| Concept | Description | Example |
|---------|-------------|---------|
| **Temporary Profile** | Fresh browser session, no saved data | Testing, one-off tasks |
| **Named Profile** | Saved session with login credentials | Personal accounts, repeated tasks |
| **Exact Name Matching** | Script specifies profile by name | `"profile_name": "My_Amazon"` |
| **Tag Matching** | Script specifies required capabilities | `"required_tags": ["amazon.com", "authenticated"]` |
| **Profile Resolution** | Finding the right profile for a task | Automatic, based on name or tags |
| **Activity Worker** | Background process polling for cloud tasks | Listen tab |

---

## Support & Resources

- **Design Document**: See `PROFILE_RESOLUTION_DESIGN.md` for architecture details
- **Example Scripts**: Check `examples/` directory
- **GitHub Issues**: Report bugs at https://github.com/guyernest/step-functions-agent/issues
- **Documentation**: Full docs at `docs/` directory

---

## Quick Reference

### Common Tasks

```bash
# Check Python environment status
# Config → Check Status button

# Create new profile
# Profiles → Create Profile button

# Test profile works
# Profiles → Select profile → Setup Login

# Run local test
# Test → Load Example → Execute

# Start cloud integration
# Listen → Start Polling

# View active sessions
# Listen → View sessions list
```

### Example Scripts by Complexity

1. **Beginner**: `simple_google_search.json` - No profiles, basic action
2. **Intermediate**: `profile_based_example.json` - Uses named profile
3. **Advanced**: `tag_based_profile_example.json` - Tag-based matching
4. **Expert**: `multi_step_authenticated.json` - Complex workflow with profiles

### Tag Taxonomy

| Tag Category | Examples | Usage |
|--------------|----------|-------|
| **Domain** | `amazon.com`, `google.com` | Which site |
| **Auth** | `authenticated`, `unauthenticated` | Login state |
| **Permission** | `buyer`, `read-only`, `admin` | What it can do |
| **Purpose** | `personal`, `pool`, `testing` | Who/what it's for |

---

Happy automating! 🤖✨
