import { Handler } from 'aws-lambda';
import puppeteer from 'puppeteer-core';
import chromium from '@sparticuz/chromium';
import { Logger } from '@aws-lambda-powertools/logger';


const logger = new Logger({ serviceName: 'ai-agents' });

// Navigation action types
type NavigationAction = 
    | { type: 'search'; searchInput: string; searchButton: string; searchTerm: string }
    | { type: 'click'; selector: string; waitForNavigation?: boolean }
    | { type: 'clickAndWaitForSelector'; clickSelector: string; waitForSelector: string }
    | { type: 'hover'; selector: string }
    | { type: 'select'; selector: string; value: string }
    | { type: 'type'; selector: string; text: string }
    | { type: 'wait'; timeMs: number }
    | { type: 'waitForSelector'; selector: string };

interface ScraperInput {
    url: string;
    actions?: NavigationAction[];
    extractSelectors?: {
        containers?: string[];
        text?: string[];
        links?: string[];
        images?: string[];
    };
    screenshotSelector?: string;
    fullPageScreenshot?: boolean;
}

interface ToolEvent {
    id: string;
    name: string;
    input: ScraperInput;
}

interface ToolResponse {
    type: string;
    tool_use_id: string;
    content: string;
    name: string;
}

const WEB_SCRAPE_TOOL = {
    name: "web_scrape",
    arguments: {
        type: "object",
        properties: {
            url: { type: "string" },
            actions: {
                type: "array",
                items: {
                    type: "object",
                    oneOf: [
                        {
                            properties: {
                                type: { enum: ["search"] },
                                searchInput: { type: "string" },
                                searchButton: { type: "string" },
                                searchTerm: { type: "string" }
                            },
                            required: ["type", "searchInput", "searchButton", "searchTerm"]
                        },
                        {
                            properties: {
                                type: { enum: ["click"] },
                                selector: { type: "string" },
                                waitForNavigation: { type: "boolean" }
                            },
                            required: ["type", "selector"]
                        },
                        {
                            properties: {
                                type: { enum: ["clickAndWaitForSelector"] },
                                clickSelector: { type: "string" },
                                waitForSelector: { type: "string" }
                            },
                            required: ["type", "clickSelector", "waitForSelector"]
                        },
                        {
                            properties: {
                                type: { enum: ["hover"] },
                                selector: { type: "string" }
                            },
                            required: ["type", "selector"]
                        },
                        {
                            properties: {
                                type: { enum: ["select"] },
                                selector: { type: "string" },
                                value: { type: "string" }
                            },
                            required: ["type", "selector", "value"]
                        },
                        {
                            properties: {
                                type: { enum: ["type"] },
                                selector: { type: "string" },
                                text: { type: "string" }
                            },
                            required: ["type", "selector", "text"]
                        },
                        {
                            properties: {
                                type: { enum: ["wait"] },
                                timeMs: { type: "number" }
                            },
                            required: ["type", "timeMs"]
                        },
                        {
                            properties: {
                                type: { enum: ["waitForSelector"] },
                                selector: { type: "string" }
                            },
                            required: ["type", "selector"]
                        }
                    ]
                }
            },
            extractSelectors: {
                type: "object",
                properties: {
                    containers: { type: "array", items: { type: "string" } },
                    text: { type: "array", items: { type: "string" } },
                    links: { type: "array", items: { type: "string" } },
                    images: { type: "array", items: { type: "string" } }
                }
            },
            screenshotSelector: { type: "string" },
            fullPageScreenshot: { type: "boolean" }
        },
        required: ["url"]
    },
    description: "Navigate a website and extract content"
};

async function getBrowser() {
    let browser;
    try {
        // Get the path and set permissions
        const executablePath = await chromium.executablePath()
        logger.info('Executable path:', executablePath);

        browser = await puppeteer.launch({
            args: [
                ...chromium.args,
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--single-process'
            ],
            defaultViewport: chromium.defaultViewport,
            executablePath,
            headless: "shell",
        });

        logger.info('Browser launched successfully');

        const version = await browser.version();
        logger.info('Browser version:', version);

        return browser;

    } catch (error) {
        logger.error('Error launching browser:', { error });
        throw error;
    }
}

async function handleWebScrape(input: ScraperInput): Promise<string> {
    // Create a timeout promise that rejects after 25 seconds
    const timeoutPromise = new Promise<string>((_, reject) => {
        setTimeout(() => {
            reject(new Error('Operation timed out after 25 seconds. Some selectors may not exist on the page.'));
        }, 25000);
    });
    
    // Execute the scraping operation with the timeout
    try {
        return await Promise.race([
            executeWebScrape(input),
            timeoutPromise
        ]);
    } catch (error) {
        logger.error('Web scrape operation timed out or failed', { error });
        return JSON.stringify({
            status: 'error',
            url: input.url,
            error: error instanceof Error ? error.message : String(error),
            message: 'The operation timed out. This may happen when selectors do not exist on the page or the page is taking too long to load.'
        }, null, 2);
    }
}

async function executeWebScrape(input: ScraperInput): Promise<string> {
    const browser = await getBrowser();
    logger.info("Using browser", { browser });

    try {
        const page = await browser.newPage();
        
        // Set a realistic user-agent to avoid being blocked
        const userAgent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36';
        await page.setUserAgent(userAgent);
        logger.info(`Set user agent to: ${userAgent}`);
        
        // Add extra headers to look more like a real browser
        await page.setExtraHTTPHeaders({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1'
        });

        logger.info(`Navigating to ${input.url}`);
        try {
            await page.goto(input.url, {
                // Using 'domcontentloaded' is faster than 'networkidle0' and less likely to time out
                waitUntil: 'domcontentloaded',
                timeout: 15000 // Shorter timeout to fail faster
            });
            logger.info(`Initial page load complete for ${input.url}`);
            
            // Wait a bit for any dynamic content to load
            await new Promise(resolve => setTimeout(resolve, 2000));
        } catch (error) {
            logger.warn(`Initial page.goto failed with error: ${error instanceof Error ? error.message : String(error)}`);
            logger.info('Retrying with less restrictive options...');
            
            // Retry with even less restrictive options
            await page.goto(input.url, {
                timeout: 15000
            });
        }

        // Execute all navigation actions in sequence
        if (input.actions && input.actions.length > 0) {
            logger.info(`Executing ${input.actions.length} navigation actions`);
            
            for (const action of input.actions) {
                logger.info(`Executing action: ${action.type}`);
                
                switch (action.type) {
                    case 'search':
                        await page.type(action.searchInput, action.searchTerm);
                        await page.click(action.searchButton);
                        await page.waitForNavigation({
                            waitUntil: 'networkidle0',
                            timeout: 30000
                        });
                        break;
                        
                    case 'click':
                        console.log(`Clicking selector: ${action.selector}`);
                        try {
                            // First ensure the element is visible
                            await page.waitForSelector(action.selector, { 
                                visible: true,
                                timeout: 5000
                            });
                            
                            // Click the element
                            await page.click(action.selector);
                            console.log(`Clicked on ${action.selector} successfully`);
                            
                            if (action.waitForNavigation) {
                                console.log(`Waiting for navigation to complete...`);
                                await page.waitForNavigation({
                                    waitUntil: 'networkidle0',
                                    timeout: 30000
                                });
                                console.log(`Navigation completed to: ${page.url()}`);
                            } else {
                                // Wait a short time anyway to let any AJAX complete
                                await new Promise(resolve => setTimeout(resolve, 1000));
                                console.log(`After click, current URL: ${page.url()}`);
                            }
                        } catch (error) {
                            console.error(`Failed to click on ${action.selector}:`, error);
                            console.log(`Current page URL: ${page.url()}`);
                            throw error;
                        }
                        break;
                        
                    case 'clickAndWaitForSelector':
                        await page.click(action.clickSelector);
                        await page.waitForSelector(action.waitForSelector, { 
                            timeout: 30000 
                        });
                        break;
                        
                    case 'hover':
                        await page.hover(action.selector);
                        break;
                        
                    case 'select':
                        await page.select(action.selector, action.value);
                        break;
                        
                    case 'type':
                        await page.type(action.selector, action.text);
                        break;
                        
                    case 'wait':
                        await new Promise(resolve => setTimeout(resolve, action.timeMs));
                        break;
                        
                    case 'waitForSelector':
                        console.log(`Waiting for selector: ${action.selector} with timeout 30000ms`);
                        try {
                            await page.waitForSelector(action.selector, { 
                                timeout: 30000,
                                visible: true
                            });
                            console.log(`Successfully found selector: ${action.selector}`);
                            
                            // Wait a moment after finding the selector
                            await new Promise(resolve => setTimeout(resolve, 500)); 
                        } catch (error) {
                            console.error(`Failed to find selector: ${action.selector}`, error);
                            console.log(`Current page URL: ${page.url()}`);
                            console.log(`Current page title: ${await page.title()}`);
                            throw error;
                        }
                        break;
                }
            }
        }

        // Extract content based on the provided selectors
        const extractedContent: Record<string, any> = {};
        
        logger.info(`Extract selectors: ${JSON.stringify(input.extractSelectors)}`);
        if (input.extractSelectors) {
            // Extract text from specified containers
            if (input.extractSelectors.containers && input.extractSelectors.containers.length > 0) {
                logger.info(`Extracting from ${input.extractSelectors.containers.length} containers`);
                extractedContent.containers = [];
                
                for (const selector of input.extractSelectors.containers) {
                    try {
                        logger.info(`Checking for selector existence: ${selector}`);
                        // Just check if the selector exists without waiting
                        const exists = await page.$(selector) !== null;
                        
                        if (exists) {
                            logger.info(`Found selector: ${selector}`);
                            const textContent = await page.$eval(selector, (el) => el.textContent || '');
                            logger.info(`Extracted content from ${selector}: ${textContent.substring(0, 50)}...`);
                            
                            extractedContent.containers.push({
                                selector,
                                content: textContent.trim()
                            });
                        } else {
                            logger.warn(`Selector not found: ${selector}`);
                            extractedContent.containers.push({
                                selector,
                                error: `Selector not found on page`
                            });
                        }
                    } catch (error) {
                        logger.warn(`Error extracting content from container ${selector}:`, { error });
                        extractedContent.containers.push({
                            selector,
                            error: error instanceof Error ? error.message : String(error)
                        });
                    }
                }
            }
            
            // Extract specific text elements
            if (input.extractSelectors.text && input.extractSelectors.text.length > 0) {
                extractedContent.text = [];
                
                for (const selector of input.extractSelectors.text) {
                    try {
                        // Check if selector exists first
                        const elements = await page.$$(selector);
                        
                        if (elements.length > 0) {
                            const texts = await page.$$eval(selector, elements => 
                                elements.map(el => el.textContent || '')
                            );
                            extractedContent.text.push({
                                selector,
                                content: texts.map(t => t.trim()).filter(t => t)
                            });
                        } else {
                            logger.warn(`No elements found for text selector: ${selector}`);
                            extractedContent.text.push({
                                selector,
                                error: `No elements found matching this selector`
                            });
                        }
                    } catch (error) {
                        logger.warn(`Error extracting text from ${selector}:`, { error });
                        extractedContent.text.push({
                            selector,
                            error: error instanceof Error ? error.message : String(error)
                        });
                    }
                }
            }
            
            // Extract links
            if (input.extractSelectors.links && input.extractSelectors.links.length > 0) {
                extractedContent.links = [];
                
                for (const selector of input.extractSelectors.links) {
                    try {
                        // Check if selector exists first
                        const elements = await page.$$(selector);
                        
                        if (elements.length > 0) {
                            const links = await page.$$eval(selector, (elements: Element[]) => 
                                elements.map(el => {
                                    const anchor = el as HTMLAnchorElement;
                                    return {
                                        href: anchor.href,
                                        text: anchor.textContent?.trim() || ''
                                    };
                                })
                            );
                            extractedContent.links.push({
                                selector,
                                content: links
                            });
                        } else {
                            logger.warn(`No elements found for link selector: ${selector}`);
                            extractedContent.links.push({
                                selector,
                                error: `No elements found matching this selector`
                            });
                        }
                    } catch (error) {
                        logger.warn(`Error extracting links from ${selector}:`, { error });
                        extractedContent.links.push({
                            selector,
                            error: error instanceof Error ? error.message : String(error)
                        });
                    }
                }
            }
            
            // Extract images
            if (input.extractSelectors.images && input.extractSelectors.images.length > 0) {
                extractedContent.images = [];
                
                for (const selector of input.extractSelectors.images) {
                    try {
                        // Check if selector exists first
                        const elements = await page.$$(selector);
                        
                        if (elements.length > 0) {
                            const images = await page.$$eval(selector, (elements: Element[]) => 
                                elements.map(el => {
                                    const img = el as HTMLImageElement;
                                    return {
                                        src: img.src,
                                        alt: img.alt || ''
                                    };
                                })
                            );
                            extractedContent.images.push({
                                selector,
                                content: images
                            });
                        } else {
                            logger.warn(`No elements found for image selector: ${selector}`);
                            extractedContent.images.push({
                                selector,
                                error: `No elements found matching this selector`
                            });
                        }
                    } catch (error) {
                        logger.warn(`Error extracting images from ${selector}:`, { error });
                        extractedContent.images.push({
                            selector,
                            error: error instanceof Error ? error.message : String(error)
                        });
                    }
                }
            }
        }
        
        // Take screenshot if requested
        if (input.screenshotSelector || input.fullPageScreenshot) {
            try {
                let screenshot;
                
                if (input.screenshotSelector) {
                    await page.waitForSelector(input.screenshotSelector, { timeout: 10000 });
                    const element = await page.$(input.screenshotSelector);
                    if (element) {
                        screenshot = await element.screenshot({
                            encoding: "base64"
                        });
                    }
                } else if (input.fullPageScreenshot) {
                    screenshot = await page.screenshot({
                        fullPage: true,
                        encoding: "base64"
                    });
                }
                
                if (screenshot) {
                    extractedContent.screenshot = `data:image/png;base64,${screenshot}`;
                }
            } catch (error) {
                logger.warn('Error taking screenshot:', { error });
                extractedContent.screenshotError = error instanceof Error ? error.message : String(error);
            }
        }

        logger.info(`Extracted content: ${JSON.stringify(extractedContent)}`);
        
        // If no content was successfully extracted, get page HTML
        const hasExtractedContent = Object.keys(extractedContent).some(key => {
            logger.info(`Checking key: ${key}`);
            const content = extractedContent[key];
            const isValid = Array.isArray(content) && content.length > 0 && 
                  content.some(item => !item.error && item.content);
            logger.info(`Key ${key} has valid content: ${isValid}`);
            return isValid;
        });
        
        if (!hasExtractedContent) {
            logger.info('No content was successfully extracted, getting full HTML');
            extractedContent.html = await page.content();
        }

        logger.info('Content extracted successfully');

        // Convert entire response to an object with consistent structure
        const result = {
            status: 'success',
            url: input.url,
            content: extractedContent.html || extractedContent 
        };
        
        await browser.close();
        return JSON.stringify(result, null, 2);

    } catch (error) {
        await browser.close();
        throw error;
    }
}

export const handler: Handler<ToolEvent, ToolResponse> = async (event) => {
    logger.info("Received event", { event });
    const tool_use = event;
    const tool_name = tool_use["name"];

    try {
        let result: string;
        switch (tool_name) {
            case "web_scrape": {
                result = await handleWebScrape(tool_use.input);
                logger.info("Result", { result });
                break;
            }
            default:
                result = `Unknown tool: ${tool_name}`;
        }
        
        return {
            "type": "tool_result",
            "name": tool_name,
            "tool_use_id": tool_use["id"],
            "content": result
        };
    } catch (error) {
        logger.error("Error in handler", { error });
        const errorMessage = error instanceof Error ? error.message : String(error);
        
        // Check if this is a timeout error and provide better guidance
        const isTimeoutError = errorMessage.includes('timeout') || 
                             errorMessage.includes('Timed out');
        
        let userFriendlyMessage = `Error: ${errorMessage}`;
        
        if (isTimeoutError) {
            userFriendlyMessage = JSON.stringify({
                status: 'error',
                url: tool_use.input.url,
                error: errorMessage,
                suggestions: [
                    "Some of the CSS selectors you provided might not exist on the page",
                    "Try using more general selectors like 'body', 'h1', '.main', '#content'", 
                    "Simplify your request by reducing the number of selectors",
                    "Check if the website has anti-scraping measures",
                    "The page might be very large or have complex scripts causing slow loading"
                ]
            }, null, 2);
        }
        
        return {
            "type": "tool_result",
            "name": tool_name,
            "tool_use_id": tool_use["id"],
            "content": userFriendlyMessage
        };
    }
}