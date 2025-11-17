# Local Browser Agent - Test Plan

## Test Session: Python Execution Fix Validation

### Prerequisites
- macOS 10.15+ (Catalina or later)
- Internet connection
- Console.app or terminal for viewing logs
- Test DMG: `Local Browser Agent_0.1.0_aarch64.dmg`

### Test Environment
- **Machine**: Current Mac (local testing)
- **Package**: `browser-agent-deployment.tar.gz` (7.5MB)

---

## Test Case 1: Fresh Installation

### Objective
Verify the app installs correctly and Python setup works.

### Steps
1. **Install DMG**
   ```bash
   open "Local Browser Agent_0.1.0_aarch64.dmg"
   ```
   - Drag app to Applications folder
   - Eject DMG

2. **Open Console Logs**
   ```bash
   # Option A: Use Console.app
   open -a Console
   # Filter for "Local Browser Agent"

   # Option B: Use log command
   log stream --predicate 'process == "Local Browser Agent"' --level info
   ```

3. **Launch App**
   ```bash
   open "/Applications/Local Browser Agent.app"
   ```

4. **Check Status (Should Fail - No Setup Yet)**
   - Go to Configuration screen
   - Click "Check Status" button
   - **Expected**: Red error showing venv not found
   - **Log**: Should show which paths were checked

5. **Setup Python Environment**
   - Click "Setup Python Environment" button
   - Wait for completion (2-5 minutes)
   - **Expected**: Green success with 5 checkmarks:
     - ✓ Locate application
     - ✓ Locate Python scripts
     - ✓ Create Python virtual environment
     - ✓ Install Python dependencies
     - ✓ Install Chromium browser

6. **Check Status (Should Succeed)**
   - Click "Check Status" button again
   - **Expected**: Green success with 5 checkmarks
   - **Log**: Should show venv found at correct path

### Expected Results
- ✓ App installs without errors
- ✓ Status check fails before setup
- ✓ Setup completes successfully
- ✓ Status check passes after setup
- ✓ Console logs show all setup steps

---

## Test Case 2: Simple Script Execution

### Objective
Verify the Python execution fix works with a basic example.

### Steps
1. **Navigate to Test Screen**
   - Click "Test" in sidebar

2. **Load Simple Example**
   - Click "Load Example" dropdown
   - Select `simple_test_example.json`
   - **Expected**: Script loads in editor

3. **Validate Script**
   - Click "Validate Script" button
   - **Expected**: Green success message

4. **Run Script**
   - Click "Run Example" button
   - **Watch Console Logs for**:
     ```
     INFO: Executing browser script: Simple Navigation Test
     INFO: Step 1: Finding Python executable...
     INFO: Executable path: /Applications/Local Browser Agent.app/Contents/MacOS/Local Browser Agent
     INFO: Executable directory: /Applications/Local Browser Agent.app/Contents/MacOS
     INFO: Searching for Python venv in app bundle...
     INFO: Checking: /Applications/Local Browser Agent.app/Contents/Resources/_up_/python/.venv/bin/python
     INFO: ✓ Found Python venv at: ...
     INFO: ✓ Found Python executable: ...
     INFO: Step 2: Preparing command...
     INFO: Step 3: Running in visible mode (headless disabled)
     INFO: Step 4: ...
     INFO: Step 5: ...
     INFO: Step 6: Spawning Python subprocess...
     INFO: Step 7: Python subprocess completed
     INFO: Step 8: Processing execution results...
     INFO: ✓ Script execution completed successfully!
     ```

### Expected Results
- ✓ Script loads successfully
- ✓ Validation passes
- ✓ Console shows all 8 execution steps
- ✓ Python venv is found (Step 1)
- ✓ Subprocess spawns successfully (Step 6)
- ✓ Execution completes successfully (Step 8)
- ✓ No crash or SIGABRT error
- ✓ Browser opens (if not headless)
- ✓ Script output appears in UI

---

## Test Case 3: Wikipedia Search Example

### Objective
Test a more complex script with Nova Act interactions.

### Prerequisites
- `NOVA_ACT_API_KEY` environment variable set
- OR API key configured in app settings

### Steps
1. **Set API Key**
   ```bash
   export NOVA_ACT_API_KEY="your-key-here"
   # OR
   # Enter in Configuration screen → Nova Act Configuration
   ```

2. **Load Example**
   - Go to Test screen
   - Load `wikipedia_search_example.json`

3. **Run Script**
   - Click "Run Example"
   - Watch console for 8 execution steps
   - Watch browser open and navigate to Wikipedia
   - Watch Nova Act perform search

### Expected Results
- ✓ Console shows all 8 steps
- ✓ Browser opens to Wikipedia
- ✓ Search is performed automatically
- ✓ Results are extracted
- ✓ Script completes successfully
- ✓ Output JSON appears in UI

---

## Test Case 4: Error Handling

### Objective
Verify proper error messages if venv is missing.

### Steps
1. **Simulate Missing venv**
   ```bash
   # Rename the venv directory
   sudo mv "/Applications/Local Browser Agent.app/Contents/Resources/_up_/python/.venv" \
            "/Applications/Local Browser Agent.app/Contents/Resources/_up_/python/.venv.backup"
   ```

2. **Try to Run Script**
   - Load any example
   - Click "Run Example"
   - **Watch Console for**:
     ```
     INFO: Step 1: Finding Python executable...
     INFO: Checking: /Applications/Local Browser Agent.app/Contents/Resources/_up_/python/.venv/bin/python
     ERROR: None of the expected venv paths exist
     ERROR: Python venv not found in app bundle
     ```

3. **Check Error Message in UI**
   - **Expected**: Error message with instructions:
     ```
     Failed to find Python executable: Python virtual environment not found.
     Please run setup: Use the 'Setup Python Environment' button in the Configuration screen
     ```

4. **Restore venv**
   ```bash
   sudo mv "/Applications/Local Browser Agent.app/Contents/Resources/_up_/python/.venv.backup" \
            "/Applications/Local Browser Agent.app/Contents/Resources/_up_/python/.venv"
   ```

### Expected Results
- ✓ Clear error message in console
- ✓ Helpful error message in UI
- ✓ No crash or SIGABRT
- ✓ User knows exactly how to fix it

---

## Test Case 5: Headless Mode

### Objective
Test headless execution mode.

### Steps
1. **Enable Headless Mode**
   - Go to Configuration screen
   - Check "Run browser in headless mode" checkbox
   - Save configuration
   - Restart app

2. **Run Script**
   - Load `simple_test_example.json`
   - Click "Run Example"
   - **Watch Console for**:
     ```
     INFO: Step 3: Running in headless mode
     ```

3. **Verify No Browser Window**
   - **Expected**: No browser window appears
   - Script still executes successfully

### Expected Results
- ✓ Console shows "Running in headless mode"
- ✓ No browser window appears
- ✓ Script executes successfully
- ✓ Output appears in UI

---

## Test Case 6: Configuration Options

### Objective
Verify all configuration options are logged correctly.

### Steps
1. **Configure All Options**
   - Set AWS Profile
   - Set S3 Bucket
   - Set Nova Act API Key in config (not env var)
   - Enable/disable headless

2. **Run Script**
   - Load any example
   - Click "Run Example"
   - **Watch Console for**:
     ```
     INFO: Step 3: Running in [headless/visible] mode
     INFO: Step 4: S3 recording bucket configured: [bucket-name]
     INFO: Step 5: Nova Act API key provided
     ```

### Expected Results
- ✓ All configuration options appear in logs
- ✓ API key source is logged (config vs env var)
- ✓ S3 bucket is passed to script
- ✓ Headless mode is respected

---

## Test Case 7: Multiple Executions

### Objective
Test running multiple scripts in sequence.

### Steps
1. **Run First Script**
   - Load `simple_test_example.json`
   - Click "Run Example"
   - Wait for completion

2. **Run Second Script**
   - Load `wikipedia_search_example.json`
   - Click "Run Example"
   - Wait for completion

3. **Run Third Script**
   - Load `form_filling_example.json`
   - Click "Run Example"
   - Wait for completion

### Expected Results
- ✓ Each script finds Python venv successfully
- ✓ Console shows 8 steps for each execution
- ✓ No degradation in performance
- ✓ No leftover processes
- ✓ All scripts complete successfully

---

## Success Criteria

### Must Pass
- [ ] Fresh installation works
- [ ] Python setup completes successfully
- [ ] Status check works before and after setup
- [ ] Simple script executes without crash
- [ ] Console shows all 8 execution steps
- [ ] Python venv is found correctly (Step 1)
- [ ] No SIGABRT crash

### Should Pass
- [ ] Wikipedia example works with Nova Act
- [ ] Error handling shows helpful messages
- [ ] Headless mode works correctly
- [ ] All configuration options are respected
- [ ] Multiple executions work reliably

### Nice to Have
- [ ] Logs are easy to read and understand
- [ ] Performance is acceptable (scripts start quickly)
- [ ] UI is responsive during execution

---

## Known Issues to Watch For

1. **SIGABRT Crash** - Should NOT happen anymore
2. **"Python not found" errors** - Should be fixed
3. **Dependencies missing** - Should use venv dependencies
4. **Path resolution failures** - Logs should help debug

---

## Reporting

### If Tests Pass
Document:
- macOS version
- Test duration
- Any warnings (non-critical)
- Performance observations

### If Tests Fail
Capture:
- Console logs (full output)
- Crash report (if any)
- Screenshot of error in UI
- Specific step where failure occurred
- Environment details (macOS version, etc.)

---

## Next Steps After Testing

If all tests pass:
1. Deploy to UK Mac for remote testing
2. Test with real Step Functions Activity
3. Test with actual AWS credentials
4. Test long-running scripts
5. Test network error handling

If tests fail:
1. Review console logs for crash point
2. Check venv path resolution logic
3. Verify Python dependencies are installed
4. Re-test with additional logging if needed
