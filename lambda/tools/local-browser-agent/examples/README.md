# Browser Automation Example Scripts

This directory contains example Nova Act browser automation scripts that you can use to test the Local Browser Agent locally before connecting to AWS Step Functions.

## Available Examples

### Basic Examples

#### `simple_test_example.json`
Simple test to verify Nova Act is working.
- Opens Google homepage
- Extracts page title using schema
- Good first test to verify environment setup
- **Use this to verify your installation is working**

#### `form_filling_example.json`
Demonstrates comprehensive form filling capabilities.
- Uses HTTPBin test form for safe practice
- Input text fields
- Select dropdowns
- Checkbox/radio button interaction
- Form validation and data extraction
- **Use this to learn form interaction patterns**

#### `information_extraction_example.json`
Extract structured data from web pages using schemas.
- Demonstrates different extraction patterns
- Array extraction (lists of items)
- Boolean extraction (yes/no questions)
- Nested object extraction
- Multi-page navigation with data extraction
- **Use this to learn data extraction techniques**

### Industry-Specific Examples

#### `bt_broadband_example.json`
BT Wholesale broadband availability checker.
- Navigate to BT Wholesale public site
- Fill address search form
- Handle address selection dropdown
- Extract structured availability data
- **Real-world use case demonstration**

For production BT Wholesale checks with authentication, see the template system:
- Template: `templates/broadband_availability_bt_wholesale_v1.0.1.json`
- Uses browser profiles with saved credentials
- Handles conditional login flow
- Extracts comprehensive FTTP/SOGEA data

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
  --script examples/simple_test_example.json \
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

All example scripts follow this structure:

```json
{
  "name": "Script Name",
  "description": "What this script does",
  "starting_page": "https://example.com",
  "abort_on_error": false,
  "steps": [
    {
      "action": "act",
      "prompt": "Natural language instruction for what to do",
      "description": "Brief description of this step"
    },
    {
      "action": "act_with_schema",
      "prompt": "Extract specific data from the page",
      "schema": {
        "type": "object",
        "properties": {
          "field_name": {"type": "string"}
        },
        "required": ["field_name"]
      },
      "description": "Extract structured data"
    }
  ]
}
```

### Key Fields

- **`name`**: Human-readable script name
- **`description`**: What the script does
- **`starting_page`**: The URL to start at
- **`abort_on_error`**: Stop execution on first error (default: false)
- **`steps`**: Array of actions to perform

### Step Actions

- **`act`**: Perform browser actions (click, type, navigate)
- **`act_with_schema`**: Extract structured data using JSON schema
- **`screenshot`**: Capture screenshot of current page

## Creating Your Own Examples

### Template

```json
{
  "name": "My Custom Script",
  "description": "Brief description of what this does",
  "starting_page": "https://your-target-site.com",
  "abort_on_error": false,
  "steps": [
    {
      "action": "act",
      "prompt": "Your natural language instruction here",
      "description": "Step description"
    }
  ]
}
```

### Best Practices from Nova Act Documentation

1. **Be prescriptive and succinct**: Tell the agent exactly what to do
   - ❌ "Let's see what routes are available"
   - ✅ "Navigate to the routes tab"

2. **Break up large acts into smaller ones**: One step per logical action
   - ❌ One step that searches, filters, and extracts data
   - ✅ Separate steps for search, filter, and extract

3. **Use numbered steps for multi-action prompts**:
   ```
   "IF you see a dropdown: (1) Click to open it, (2) Click the matching option, (3) Click Submit"
   ```

4. **Handle conditionals explicitly**:
   ```
   "IF condition A, do action 1. IF condition B, do action 2."
   ```

5. **Always use schemas for data extraction**:
   - Even for simple yes/no, define a boolean schema
   - Put extraction in its own separate `act_with_schema` step

### Example: Custom Script

```json
{
  "name": "News Headline Extractor",
  "description": "Extract top news headlines from Hacker News",
  "starting_page": "https://news.ycombinator.com",
  "abort_on_error": false,
  "steps": [
    {
      "action": "act_with_schema",
      "prompt": "Extract the top 5 story titles and their point counts",
      "schema": {
        "type": "object",
        "properties": {
          "stories": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "title": {"type": "string"},
                "points": {"type": "number"}
              },
              "required": ["title"]
            }
          }
        },
        "required": ["stories"]
      },
      "description": "Extract headline data"
    }
  ]
}
```

## Troubleshooting

### Script Fails Immediately

**Check**:
- Is the starting URL accessible?
- Is your internet connection working?
- Check logs for detailed error messages

### Script Times Out

**Reasons**:
- Page takes too long to load
- Prompt is too complex
- Navigation getting stuck

**Solutions**:
- Break complex tasks into smaller steps
- Use more prescriptive prompts with numbered steps
- Check if page requires authentication

### Bot Detection / CAPTCHA

**Solutions**:
- Use a real Chrome profile with browser history
- Set up authentication profile using Profile Manager
- Run in non-headless mode for testing
- Some sites may require manual intervention

### "Examples directory not found"

**Windows**:
```powershell
# Check if examples are bundled
Test-Path "C:\Users\<username>\AppData\Local\Local Browser Agent\_up_\examples"
```

**macOS**:
```bash
# Check if examples are bundled
ls "$HOME/Library/Application Support/Local Browser Agent/_up_/examples"
```

If examples are missing, they may not have been included in the build. Check the application bundle or source directory.

## Browser Profiles for Authentication

For sites requiring login (like BT Wholesale authenticated portal):

1. **Create a profile** using Profile Manager
2. **Manually login** in that profile
3. **Tag the profile** (e.g., `btwholesale.com`, `authenticated`)
4. **Use template system** to reference profile by tags

See template: `templates/broadband_availability_bt_wholesale_v1.0.1.json` for an example.

## Testing Before Production

Before using scripts in AWS Step Functions:

1. ✅ **Test Locally First**: Run via UI or CLI
2. ✅ **Verify Output**: Check that extracted data is correct
3. ✅ **Test with Profile**: If site requires auth, test with profile
4. ✅ **Check Recordings**: Review video recordings
5. ✅ **Optimize Prompts**: Refine instructions for better accuracy
6. ✅ **Test Edge Cases**: Handle dropdowns, popups, conditional flows

## Recordings

When running locally, recordings are saved to:
- **Windows**: `%LOCALAPPDATA%\Local Browser Agent\recordings\`
- **macOS**: `~/Library/Application Support/Local Browser Agent/recordings/`
- **Linux**: `~/.local/share/local-browser-agent/recordings/`

When running via Step Functions, recordings are uploaded to the S3 bucket configured in your `config.yaml`.

## Need Help?

- See main [README.md](../README.md) for setup instructions
- See Nova Act documentation for prompting best practices
- Check logs for detailed error messages

## Contributing Examples

Have a useful browser automation pattern? Consider adding it:

1. Create a descriptive filename (e.g., `github_issue_search.json`)
2. Test thoroughly with multiple runs
3. Add clear descriptions and comments
4. Follow Nova Act best practices
5. Keep it simple and focused on one pattern

Your example could help others learn browser automation!
