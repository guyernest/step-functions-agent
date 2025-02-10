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

* `web_scrape`: Initial implementation of the web scraping tool using URL, Search Query, and CSS Selector as input.

## Input and output

The Lambda function for the tools receive the input as a JSON object, and return the output as a JSON object.

```typescript
export const handler: Handler = async (event, context) => {

    logger.info("Received event", { event });
    const tool_use = event
    const tool_name = tool_use["name"]
    const tool_input = tool_use["input"]

    try {
        let result: string
        switch (tool_name) {
            case "web_scrape": {
                const { url, selectors, searchTerm } = tool_use.input as {
                    url: string;
                    searchTerm: string;
                    selectors?: {
                        searchInput?: string;
                        searchButton?: string;
                        resultContainer?: string;
                    };
                }
                result = await handleSearchResults(url, searchTerm, selectors);
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
        logger.info("Result", { result });
        return {
            "type": "tool_result",
            "name": tool_name,
            "tool_use_id": tool_use["id"],
            "content": result
        }
      } catch (error) {
        return {
            "type": "tool_result",
            "name": tool_name,
            "tool_use_id": tool_use["id"],
            "content": `Error: ${error instanceof Error ? error.message : String(error)}`
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

To test the Lambda function locally, run the following command:

```bash
npm run test
```

or using SAM CLI:

```bash
cd lambda/tools/web-scraper
sam build && sam local invoke WebScraperFunction --event tests/test-event.json```

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
