# Local Browser Agent - Test Examples

This folder contains example scripts for testing the Local Browser Agent installation before connecting to the server.

## Testing Sequence

Follow this sequence to verify your installation:

### Step 1: Basic Connectivity Test (No LLM Required)

Run `01_simple_test.json` first to verify:
- Browser launches correctly
- Screenshots are captured
- DOM extraction works

**Expected output:**
- Screenshot saved as `example_page.png`
- Extracted: page_title="Example Domain", main_heading="Example Domain"

### Step 2: Form Filling Test (No LLM Required)

Run `02_form_filling.json` to verify:
- Form field filling works
- Click actions work
- Multi-step workflows execute correctly

**Expected output:**
- Screenshot of filled form
- Extracted field values matching input

### Step 3: BT Broadband Tests (Requires Browser Profile)

These tests require:
1. A configured browser profile named `Bt_broadband`
2. Saved BT Wholesale credentials in the browser's password manager
3. LLM provider configured (OpenAI recommended)

Run in order:
- `03_bt_broadband_bournemouth.json` - Tests BH6 3EN
- `04_bt_broadband_bolton.json` - Tests BL5 3AN
- `05_bt_broadband_peacehaven.json` - Tests BN10 8LA
- `06_bt_broadband_template_test.json` - Tests BH8 8BN (template pipeline test)

**Expected output for each:**

| Test | Exchange Code | L2SID (New ONT) |
|------|---------------|-----------------|
| Bournemouth | STSTHBN | BAAOEA |
| Bolton | LCBOL | BAAMUH |
| Peacehaven | SDPCHVN | BAANTY |
| Template Test | STSTHBN | BAAOEA |

**Error handling:** If the BT checker is temporarily unavailable, the workflow will retry up to 5 times with 5-second delays, then report a clear `BT Checker service unavailable` error.

---

## Configuration Requirements

### For Tests 01-02 (Basic Tests)

No special configuration needed. These tests work with:
- Default browser (no profile)
- No LLM provider
- No AWS credentials

### For Tests 03-05 (BT Broadband)

1. **Browser Profile Setup**
   - Create a browser profile named `Bt_broadband`
   - Log into BT Wholesale manually once
   - Save credentials in the browser's password manager
   - Add tags: `bt.com`, `authenticated`

2. **LLM Provider** (for vision-based fallbacks)
   - Configure OpenAI API key in settings
   - Model: `gpt-4o-mini` (default)

3. **AWS Credentials** (optional, for S3 screenshots)
   - Only needed if `upload_to_s3: true` in the workflow

---

## Running Tests

### From the UI

1. Launch Local Browser Agent
2. Go to Scripts tab
3. Select an example script
4. Click "Run"
5. Monitor progress in the activity log

### From Command Line

```bash
# Run a test script directly
./local-browser-agent --script examples/01_simple_test.json
```

---

## Troubleshooting

### Test 01/02 Fails

- **Browser doesn't launch**: Check Playwright installation
- **Screenshot not saved**: Check write permissions in output directory
- **DOM extraction returns null**: Check selectors in browser DevTools

### Test 03-05 Fails

- **Login fails**:
  - Verify browser profile exists
  - Check password manager has saved credentials
  - Try manual login first to ensure credentials work

- **Address not found**:
  - Address list may have changed
  - Check if BT Wholesale site structure changed
  - Review logs for the address matching step

- **Extract returns null**:
  - Page may not have loaded completely
  - Check if DOM structure changed
  - See `docs/WORKFLOW_DEBUGGING.md` for debugging steps

---

## File Reference

| File | Purpose | Requirements |
|------|---------|--------------|
| `01_simple_test.json` | Basic browser/screenshot test | None |
| `02_form_filling.json` | Form filling test | None |
| `03_bt_broadband_bournemouth.json` | BT test - BH6 3EN | Profile + LLM |
| `04_bt_broadband_bolton.json` | BT test - BL5 3AN | Profile + LLM |
| `05_bt_broadband_peacehaven.json` | BT test - BN10 8LA | Profile + LLM |
| `06_bt_broadband_template_test.json` | BT template pipeline test - BH6 3EN | Profile + LLM |

---

## After Testing

Once all tests pass:

1. **Configure Activity ARN** in settings
2. **Enable "Listen for Tasks"** to connect to Step Functions
3. The agent will poll for and execute remote tasks

See the main documentation for server-side setup.
