# ![TypeScript Logo](https://cdn.simpleicons.org/typescript?size=48) TypeScript: Web Scraper AI Agent Tools

This directory contains the implementation of the tools for Web Scraping  AI Agent in **TypeScript**, based on [Chromium](https://github.com/Sparticuz/chromium). The decision to use TypeScript is based on the size limitation of AWS Lambda functions, which is 250 MB. Using Python and Chrome Driver, the size of the Lambda function exceeds the limit.

The AI Agent that is created using these tools is implemented in the [step_functions_web_scraper_agent_stack.py](../../../step_functions_agent/step_functions_web_scraper_agent_stack.py) file.

## Folder structure

```txt
web-scraper/
├── src/
│   └── index.ts
|   └── local-test.ts
├── tests/
│   └── test-event.json
├── package.json
├── tsconfig.json
├── template.yaml (for SAM CLI)
└── README.md (This file)
```

## Tool list

The tools are:

* `web_scrape`: Web scraping tool that supports complex navigation actions and content extraction:
  * Navigate websites using various interactions (click, search, hover, etc.)
  * Extract structured content (text, links, images)
  * Take full page or element screenshots

## Input and output

The Lambda function for the tools receive the input as a JSON object, and return the output as a JSON object.

```typescript
export const handler: Handler = async (event, context) => {
    logger.info("Received event", { event });
    const tool_use = event;
    const tool_name = tool_use["name"];

    try {
        let result: string;
        switch (tool_name) {
            case "web_scrape": {
                // Input structure with navigation actions and extraction selectors
                const input = tool_use.input as {
                    url: string;
                    actions?: Array<{
                        type: 'search' | 'click' | 'hover' | 'select' | 'type' | 'wait' | 'waitForSelector' | 'clickAndWaitForSelector';
                        [key: string]: any;
                    }>;
                    extractSelectors?: {
                        containers?: string[];
                        text?: string[];
                        links?: string[];
                        images?: string[];
                    };
                    screenshotSelector?: string;
                    fullPageScreenshot?: boolean;
                };
                
                result = await handleWebScrape(input);
            break;
          }
          ...
          default: {
            result = `Unknown tool name: ${tool_name}`;
          }
        }
```

The tools return the output as a JSON object, with the result in the `content` field as a string.

```typescript
        ...
        // The result is a JSON string containing the extracted content
        // {
        //   status: 'success',
        //   url: 'https://example.com',
        //   content: {
        //     containers: [{ selector: '.header', content: 'Example Domain' }, ...],
        //     text: [{ selector: 'p', content: ['Example text content', ...] }, ...],
        //     links: [{ selector: 'a', content: [{ href: 'https://example.com/link', text: 'Link text' }, ...] }, ...],
        //     images: [{ selector: 'img', content: [{ src: 'https://example.com/image.jpg', alt: 'Image alt text' }, ...] }, ...],
        //     screenshot: 'data:image/png;base64,...' // (if requested)
        //   }
        // }
        
        logger.info("Result", { result });
        return {
            "type": "tool_result",
            "name": tool_name,
            "tool_use_id": tool_use["id"],
            "content": result
        }
      } catch (error) {
        logger.error("Error in handler", { error });
        return {
            "type": "tool_result",
            "name": tool_name,
            "tool_use_id": tool_use["id"],
            "content": `Error: ${error instanceof Error ? error.message : String(error)}`
        }
      }
```

## Web Scraper Features

### Navigation Actions

The web scraper supports various navigation actions:

```json
// Click a link or button
{ "type": "click", "selector": "#submit-button", "waitForNavigation": true }

// Search using a form
{ "type": "search", "searchInput": "#search-box", "searchButton": "#search-submit", "searchTerm": "query" }

// Click and wait for a specific element to appear
{ "type": "clickAndWaitForSelector", "clickSelector": ".load-more", "waitForSelector": ".results-item" }

// Hover over an element (useful for dropdown menus)
{ "type": "hover", "selector": ".dropdown-menu" }

// Select an option from a dropdown
{ "type": "select", "selector": "#country-select", "value": "USA" }

// Type text into an input field
{ "type": "type", "selector": "#username", "text": "johndoe" }

// Wait for a specific amount of time (in milliseconds)
{ "type": "wait", "timeMs": 2000 }

// Wait for a specific element to appear
{ "type": "waitForSelector", "selector": ".lazy-loaded-content" }
```

### Content Extraction

You can extract different types of content using CSS selectors:

```json
"extractSelectors": {
  // Extract text content from container elements
  "containers": [".article-header", ".article-body", ".footer"],
  
  // Extract text from elements (returns an array of text content for each matching element)
  "text": [".news-item h3", ".product-price"],
  
  // Extract links with their href and text
  "links": ["nav a", ".pagination a"],
  
  // Extract images with their src and alt attributes
  "images": [".gallery img", ".product-image"]
}
```

### Browser Configuration

The scraper includes several features to make web pages render correctly:

1. **User-Agent**: Sets a realistic browser user-agent to avoid being blocked by sites
2. **Extra Headers**: Adds common browser headers like Accept, Accept-Language, etc.
3. **Wait Times**: Configurable wait times for page loads and element rendering
4. **Error Handling**: Graceful handling of navigation issues with useful debug information

### Screenshots

You can also capture screenshots:

```json
// Screenshot a specific element
"screenshotSelector": ".main-content"

// Screenshot the entire page
"fullPageScreenshot": true
```

### Direct URL Navigation

For sites with complex forms or search functionality, it's often better to navigate directly to the target URL rather than trying to fill out forms. For example, to get weather for New York:

```json
// Instead of this (which might not work due to form behavior):
"actions": [
  { "type": "type", "selector": "#searchbox", "text": "New York, NY" },
  { "type": "click", "selector": "#submit" }
]

// Use direct URL navigation instead:
"url": "https://forecast.weather.gov/MapClick.php?lat=40.7142&lon=-74.0059"
```

## Using the Web Scraper Tool with LLMs

### Tool Interface for LLMs

You can use this tool to navigate websites, interact with web pages, and extract content. The web_scrape tool has the following interface:

```javascript
{
  "id": "unique_id",           // Unique identifier for this tool usage
  "name": "web_scrape",        // Must be "web_scrape" to use this tool
  "input": {
    "url": "https://example.com",  // Starting URL
    
    // Optional list of navigation actions to perform in sequence
    "actions": [
      { 
        "type": "click|search|type|wait|...",  // Action type
        // Additional parameters based on action type
      }
    ],
    
    // Optional selectors to extract content
    "extractSelectors": {
      "containers": ["#main", ".article"], // Text containers
      "text": [".title", "p"],            // Text elements
      "links": ["a.menu", "nav a"],       // Link elements
      "images": ["img.hero", ".gallery img"] // Image elements
    },
    
    // Optional screenshot requests
    "screenshotSelector": ".main-content", // Screenshot specific element
    "fullPageScreenshot": true            // Take full page screenshot
  }
}
```

### Guidelines for LLMs Using This Tool

1. **Exploration Phase**:

* Start with a basic request to understand the site structure
* Request a full page screenshot to see the visual layout
* Examine HTML content to identify key selectors and elements
* Look for forms, navigation elements, and content containers

1. **Refinement Phase**:

* Create more targeted requests with specific selectors
* Use navigation actions to reach deeper content
* Extract only the relevant information
* Create a reusable script for similar future tasks

1. **Documentation Phase**:

* Document the selectors and navigation steps that worked
* Create a template for similar websites
* Note any challenges or anti-bot measures encountered

### Example: Exploring an Unknown Website

1. **Initial Exploration**:

   ```json
   {
     "id": "explore_1",
     "name": "web_scrape",
     "input": {
       "url": "https://example-news-site.com",
       "fullPageScreenshot": true
     }
   }
   ```

1. **Analyze Results**:

* Examine the screenshot to identify UI elements
* Look at the HTML structure to find key selectors
* Identify search forms, navigation menus, and content areas

1. **Targeted Navigation**:

   ```json
   {
     "id": "explore_2",
     "name": "web_scrape",
     "input": {
       "url": "https://example-news-site.com",
       "actions": [
         { "type": "click", "selector": ".menu-item-technology" }
       ],
       "extractSelectors": {
         "containers": [".article-list"],
         "links": [".article-title a"]
       }
     }
   }
   ```

1. **Create Reusable Template**:

   ```json
   {
     "id": "reusable_template",
     "name": "web_scrape",
     "input": {
       "url": "https://example-news-site.com",
       "actions": [
         { "type": "type", "selector": "#search-input", "text": "{SEARCH_TERM}" },
         { "type": "click", "selector": "#search-button" },
         { "type": "waitForSelector", "selector": ".search-results" }
       ],
       "extractSelectors": {
         "containers": [".search-results"],
         "links": [".result-item a"],
         "text": [".result-summary"]
       }
     }
   }
   ```

### Use Case Examples

#### News Article Extraction

```json
{
  "id": "news_1",
  "name": "web_scrape",
  "input": {
    "url": "https://news-website.com/article/12345",
    "extractSelectors": {
      "containers": [".article-content", ".article-header"],
      "text": ["h1.title", ".byline", ".published-date"],
      "images": [".featured-image"]
    }
  }
}
```

#### E-commerce Product Search

```json
{
  "id": "ecommerce_1",
  "name": "web_scrape",
  "input": {
    "url": "https://shop-website.com",
    "actions": [
      { "type": "type", "selector": "#search", "text": "wireless headphones" },
      { "type": "click", "selector": ".search-button" },
      { "type": "waitForSelector", "selector": ".product-grid" }
    ],
    "extractSelectors": {
      "containers": [".product-item"],
      "text": [".product-title", ".product-price"],
      "links": [".product-link"],
      "images": [".product-image"]
    }
  }
}
```

#### Sports Scores Extraction

```json
{
  "id": "bbc_sports_1",
  "name": "web_scrape",
  "input": {
    "url": "https://www.bbc.com",
    "actions": [
      {
        "type": "click",
        "selector": "a[href*='sport']",
        "waitForNavigation": true
      },
      {
        "type": "wait",
        "timeMs": 1000
      }
    ],
    "extractSelectors": {
      "containers": [".gs-c-promo-heading", ".gs-c-promo-summary"],
      "links": [".gs-c-promo-heading a"],
      "images": [".gs-c-promo-image img"]
    },
    "fullPageScreenshot": true
  }
}
```

## Building

To build the TypeScript code, run the following command:

```bash
npm install
npm run build
```

## Testing

To test the Lambda function locally, you can use the provided local test script:

```bash
npm run test
```

This script uses your local Chrome/Chromium installation to run the web scraper directly, without requiring the Lambda environment or SAM CLI.

You can also test using SAM CLI:

```bash
cd lambda/tools/web-scraper
sam build && sam local invoke WebScraperFunction --event tests/test-event.json
```

Additional test events are available in the `tests` directory:

* `test-event.json` - Basic example.com test
* `bbc-sports-news.json` - BBC Sports navigation test
* `bbc-news-article.json` - BBC News article search test
* `navigation-example.json` - Weather.gov navigation test

## Deployment

### Using CDK

The Lambda Function uses a Lambda Layer that contains the Chromium binary. The Lambda Layer is created using the following CDK code:

```python
        # Chromium Lambda Layer
        chromium_layer = _lambda.LayerVersion(
            self,
            "ChromiumLayer",
            code=_lambda.Code.from_asset(
                path=".",  # Path where the bundling will occur
                bundling=BundlingOptions(
                    image=DockerImage.from_registry("node:18"),
                    command=[
                        "bash", "-c",
                        """
                        # Create working directory
                        mkdir -p /asset-output/nodejs
                        cd /asset-output/nodejs
                        
                        # Create package.json
                        echo '{"dependencies":{"@sparticuz/chromium":"132.0.0"}}' > package.json
                        
                        # Install dependencies
                        npm install --arch=x86_64 --platform=linux
                        
                        # Clean up unnecessary files to reduce layer size
                        find . -type d -name "test" -exec rm -rf {} +
                        find . -type f -name "*.md" -delete
                        find . -type f -name "*.ts" -delete
                        find . -type f -name "*.map" -delete
                        """
                    ],
                    user="root"
                )
            ),
            compatible_runtimes=[_lambda.Runtime.NODEJS_18_X],
            description="Layer containing Chromium binary for web scraping"
        )
```

Then, you can use this layer in your Lambda function like this:

```python
from aws_cdk import (
    ...
    aws_lambda as _lambda,
    aws_lambda_nodejs as nodejs_lambda,
)
...
        # Web Scraper Lambda
        web_scraper_lambda = nodejs_lambda.NodejsFunction(
            self, 
            "WebScraperLambda",
            function_name="WebScraper",
            description="Lambda function to execute web scraping.",
            timeout=Duration.seconds(30),
            entry="lambda/tools/web-scraper/src/index.ts", 
            handler="handler",  # Name of the exported function
            runtime=_lambda.Runtime.NODEJS_18_X,
            # The TypeScript library doesn't support ARM architecture yet, so we use x86_64
            architecture=_lambda.Architecture.X86_64,
            memory_size=512,            
            # Optional: Bundle settings
            bundling=nodejs_lambda.BundlingOptions(
                minify=True,
                source_map=True,
            ),
            role=web_scraper_lambda_role,
            layers=[chromium_layer]
        )   
```

### Using SAM CLI

If you prefer to use the SAM CLI, you can create a `template.yaml` file with the following content:

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31
Description: SAM template for Web Scraper Lambda function using @sparticuz/chromium

Globals:
  Function:
    Timeout: 300
    MemorySize: 2048
    Runtime: nodejs18.x
    Architectures:
      - x86_64

Resources:
  WebScraperFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: web-scraper
      CodeUri: dist/
      Handler: index.handler
      Layers:
        - !Ref ChromiumLayer

  ChromiumLayer:
    Type: AWS::Serverless::LayerVersion
    Properties:
      LayerName: chromium-layer
      Description: Layer containing Chromium binary
      ContentUri: layers/chromium/chromium.zip
      CompatibleRuntimes:
        - nodejs18.x
      CompatibleArchitectures:
        - x86_64

Outputs:
  WebScraperFunction:
    Description: Web Scraper Lambda Function ARN
    Value: !GetAtt WebScraperFunction.Arn
```

Then, you can build and deploy the Lambda function using the following commands:

```bash
cd lambda/tools/web-scraper
npm install
npm run build
sam build
sam deploy --guided
```
