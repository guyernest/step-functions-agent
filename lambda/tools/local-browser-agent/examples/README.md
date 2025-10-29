# Browser Automation Example Scripts

This directory contains example Nova Act browser automation scripts that you can use to test the Local Browser Agent locally before connecting to AWS Step Functions.

## Available Examples

### Simple Tests

#### `simple_test_example.json`
Basic test to verify browser automation is working.
- Opens a simple webpage
- Takes a screenshot
- Validates the environment

#### `wikipedia_search_example.json`
Search for information on Wikipedia.
- Navigates to Wikipedia
- Performs a search
- Extracts information from results
- Good first test for navigation and information extraction

### E-commerce Examples

#### `product_search_example.json`
Search for products on an e-commerce site.
- Demonstrates search functionality
- Shows result filtering
- Extracts product information

#### `search_filter_example.json`
Advanced search with filters and sorting.
- Multi-step navigation
- Form interaction
- Data extraction from filtered results

### Form Interaction

#### `form_filling_example.json`
Demonstrates form filling capabilities.
- Input text fields
- Select dropdowns
- Checkbox/radio button interaction
- Form submission

#### `login_check_example.json`
Test login functionality.
- Navigate to login page
- Fill credentials
- Submit form
- Verify login success

### Multi-Page Navigation

#### `multi_page_navigation_example.json`
Navigate across multiple pages.
- Click links and buttons
- Wait for page loads
- Extract data from different pages
- Maintain session state

#### `information_extraction_example.json`
Extract structured data from web pages.
- Navigate to target page
- Locate specific elements
- Extract text, attributes, and metadata
- Return structured JSON

### Industry-Specific Examples

#### `bt_broadband_example.json`
BT broadband availability checker.
- Navigate to BT Wholesale site
- Search for address
- Extract availability information

#### `script_bt_broadband_test.json`
Simplified BT broadband test.
- Quick availability check
- Demonstrates real-world use case

#### `script_bt_broadband_login_full.json`
Full BT broadband login and search.
- Login with credentials
- Navigate authenticated sections
- Perform availability check
- Demonstrates session management

## How to Use Examples Locally

### Method 1: Via Application UI

1. **Open Local Browser Agent**
2. **Go to Test Scripts Tab**
3. **Select an Example** from the dropdown
4. **Click "Load Example"** to populate the script editor
5. **Click "Run Script"** to execute locally

The script will run on your local machine without connecting to AWS.

### Method 2: Via Command Line (Development)

```bash
# Navigate to the local-browser-agent directory
cd lambda/tools/local-browser-agent

# Run an example script directly
python python/script_executor.py \
  --script examples/wikipedia_search_example.json \
  --config config.yaml
```

### Method 3: Via API (if running in server mode)

```bash
# POST to the local API endpoint
curl -X POST http://localhost:3000/api/execute \
  -H "Content-Type: application/json" \
  -d @examples/simple_test_example.json
```

## Script Structure

All example scripts follow the Nova Act command format:

```json
{
  "starting_page": "https://example.com",
  "prompt": "Navigate to the homepage and click the search button",
  "max_steps": 10,
  "timeout": 60,
  "user_data_dir": null,
  "headless": false,
  "session_id": null
}
```

### Key Fields

- **`starting_page`**: The URL to start at
- **`prompt`**: Natural language instruction for what to do
- **`max_steps`**: Maximum automation steps (default: 10)
- **`timeout`**: Timeout in seconds (default: 300)
- **`user_data_dir`**: Chrome profile path (null = temporary profile)
- **`headless`**: Run browser in headless mode (false = visible)
- **`session_id`**: Resume existing session (null = new session)

## Creating Your Own Examples

### Template

```json
{
  "starting_page": "https://your-target-site.com",
  "prompt": "Your natural language instruction here",
  "max_steps": 15,
  "timeout": 120
}
```

### Best Practices

1. **Start Simple**: Begin with navigation to a single page
2. **Clear Instructions**: Write specific, step-by-step prompts
3. **Set Realistic Limits**:
   - `max_steps`: 10-20 for simple tasks, 30-50 for complex ones
   - `timeout`: 60-300 seconds depending on page load times
4. **Test Without Headless**: Run with `headless: false` first to see what happens
5. **Use Profiles for Auth**: If the site requires login, create a profile with saved credentials

### Example: Custom Script

```json
{
  "starting_page": "https://news.ycombinator.com",
  "prompt": "Find the top 5 stories on the front page and extract their titles and URLs",
  "max_steps": 10,
  "timeout": 60,
  "headless": false
}
```

## Troubleshooting

### Script Fails Immediately

**Check**:
- Is the starting URL accessible?
- Is your internet connection working?
- Try increasing `timeout` value

### Script Times Out

**Reasons**:
- Page takes too long to load
- Prompt is too complex
- Max steps too low for the task

**Solutions**:
- Increase `timeout` and `max_steps`
- Break complex tasks into smaller scripts
- Use session_id to chain multiple scripts

### Bot Detection / CAPTCHA

**Solutions**:
- Use a real Chrome profile: Set `user_data_dir`
- Run in non-headless mode: Set `headless: false`
- Use authenticated profile with saved cookies
- Some sites may require manual intervention

### "Examples directory not found"

**Windows**:
```powershell
# Check if examples are bundled
Test-Path "C:\Program Files\Local Browser Agent\_up_\examples"
```

**macOS**:
```bash
# Check if examples are bundled
ls "/Applications/Local Browser Agent.app/Contents/Resources/_up_/examples"
```

If examples are missing, they may not have been included in the build. Reinstall from the latest release.

## Session Management

For multi-step workflows that require maintaining state:

### Step 1: Start Session
```json
{
  "command": "start_session",
  "starting_page": "https://example.com/login",
  "user_data_dir": "/path/to/profile"
}
```

Returns: `{ "session_id": "abc-123" }`

### Step 2: Use Session
```json
{
  "command": "act",
  "session_id": "abc-123",
  "prompt": "Navigate to the dashboard"
}
```

### Step 3: End Session
```json
{
  "command": "end_session",
  "session_id": "abc-123"
}
```

## Testing Before Production

Before using these scripts in AWS Step Functions:

1. ✅ **Test Locally First**: Run via UI or CLI
2. ✅ **Verify Output**: Check that extracted data is correct
3. ✅ **Test with Profile**: If site requires auth, test with profile
4. ✅ **Check Recordings**: Review S3 uploads work correctly
5. ✅ **Optimize Prompts**: Refine instructions for better accuracy
6. ✅ **Set Appropriate Limits**: Tune `max_steps` and `timeout`

## S3 Recordings

When running locally, recordings are saved to:
- **Windows**: `%LOCALAPPDATA%\local-browser-agent\recordings\`
- **macOS**: `~/Library/Application Support/local-browser-agent/recordings/`
- **Linux**: `~/.local/share/local-browser-agent/recordings/`

When running via Step Functions, recordings are uploaded to the S3 bucket configured in your `config.yaml`.

## Need Help?

- See main [README.md](../README.md) for setup instructions
- See [IAM_PERMISSIONS.md](../docs/IAM_PERMISSIONS.md) for AWS permissions
- Check logs for detailed error messages
- Create an issue if you find bugs in examples

## Contributing Examples

Have a useful browser automation script? Consider contributing!

1. Create a descriptive filename (e.g., `github_issue_search.json`)
2. Test thoroughly
3. Add clear comments in the prompt
4. Submit a pull request

Your example could help others learn browser automation!
