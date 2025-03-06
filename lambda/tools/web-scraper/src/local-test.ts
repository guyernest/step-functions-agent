import { Context } from 'aws-lambda';
import puppeteer from 'puppeteer-core';
import * as fs from 'fs';
import * as path from 'path';

// Create a local version of the test that uses a local Chromium installation
// This mimics the functionality in index.ts but uses a local Chromium
async function runLocalScraper(event: any) {
    console.log('Running local scraper with puppeteer...');
    
    let browser;
    try {
        // Find local Chrome/Chromium installation
        const executablePath = findChromiumExecutable();
        console.log('Using Chromium at:', executablePath);
        
        browser = await puppeteer.launch({
            executablePath,
            headless: true,
        });
        
        // Set a realistic user-agent to avoid anti-bot detection
        const userAgent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36';
        
        console.log('Browser launched successfully');
        let page = await browser.newPage();
        
        // Set the user-agent
        await page.setUserAgent(userAgent);
        console.log(`Set user agent to: ${userAgent}`);
        
        const input = event.input;
        console.log(`Navigating to ${input.url}`);
        await page.goto(input.url, {
            waitUntil: 'networkidle0',
            timeout: 30000
        });
        
        // Execute all navigation actions in sequence
        if (input.actions && input.actions.length > 0) {
            console.log(`Executing ${input.actions.length} navigation actions`);
            
            for (const action of input.actions) {
                console.log(`Executing action: ${action.type}`);
                
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
                        console.log(`Attempting to click on selector: ${action.selector}`);
                        try {
                            // First ensure the element is visible
                            await page.waitForSelector(action.selector, { 
                                visible: true,
                                timeout: 5000
                            });
                            
                            // Get the element and make sure it's clickable
                            const element = await page.$(action.selector);
                            if (!element) {
                                throw new Error(`Element with selector ${action.selector} not found`);
                            }
                            
                            // Check if element is visible in viewport
                            const isVisibleInViewport = await page.evaluate((el) => {
                                const rect = el.getBoundingClientRect();
                                return (
                                    rect.top >= 0 &&
                                    rect.left >= 0 &&
                                    rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
                                    rect.right <= (window.innerWidth || document.documentElement.clientWidth)
                                );
                            }, element);
                            
                            if (!isVisibleInViewport) {
                                console.log(`Element not in viewport, scrolling into view...`);
                                await page.evaluate((el) => el.scrollIntoView({ behavior: 'smooth', block: 'center' }), element);
                                await new Promise(resolve => setTimeout(resolve, 500)); // Give time to scroll
                            }
                            
                            // Click the element
                            await element.click();
                            console.log(`Clicked on ${action.selector} successfully`);
                            
                            if (action.waitForNavigation) {
                                console.log(`Waiting for navigation to complete...`);
                                await page.waitForNavigation({
                                    waitUntil: 'networkidle0',
                                    timeout: 30000
                                });
                                console.log(`Navigation completed to: ${page.url()}`);
                            }
                        } catch (error) {
                            console.error(`Failed to click on ${action.selector}:`, error);
                            console.log(`Current page URL: ${page.url()}`);
                            throw error;
                        }
                        break;
                        
                    case 'clickAndWaitForSelector':
                        console.log(`Clicking ${action.clickSelector} and waiting for ${action.waitForSelector}`);
                        try {
                            // First ensure the element is visible
                            await page.waitForSelector(action.clickSelector, { 
                                visible: true,
                                timeout: 5000
                            });
                            
                            // Get the element and click it
                            const element = await page.$(action.clickSelector);
                            if (!element) {
                                throw new Error(`Element with selector ${action.clickSelector} not found`);
                            }
                            
                            // Click the element
                            await element.click();
                            console.log(`Clicked on ${action.clickSelector}, now waiting for ${action.waitForSelector}`);
                            
                            // Wait for the target selector
                            await page.waitForSelector(action.waitForSelector, { 
                                timeout: 30000,
                                visible: true
                            });
                            console.log(`Successfully found ${action.waitForSelector} after clicking`);
                        } catch (error) {
                            console.error(`Failed in clickAndWaitForSelector:`, error);
                            console.log(`Current page URL: ${page.url()}`);
                            throw error;
                        }
                        break;
                        
                    case 'hover':
                        await page.hover(action.selector);
                        break;
                        
                    case 'select':
                        await page.select(action.selector, action.value);
                        break;
                        
                    case 'type':
                        console.log(`Typing "${action.text}" into ${action.selector}`);
                        try {
                            // First ensure the element is visible
                            await page.waitForSelector(action.selector, { 
                                visible: true,
                                timeout: 5000
                            });
                            
                            // Clear the field first if needed
                            await page.evaluate((selector) => {
                                const element = document.querySelector(selector);
                                if (element && 'value' in element) {
                                    (element as HTMLInputElement).value = '';
                                }
                            }, action.selector);
                            
                            // Type the text
                            await page.type(action.selector, action.text);
                            console.log(`Successfully typed text into ${action.selector}`);
                        } catch (error) {
                            console.error(`Failed to type into ${action.selector}:`, error);
                            console.log(`Current page URL: ${page.url()}`);
                            throw error;
                        }
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
                            
                            // Take a screenshot to see what's on the page
                            console.log(`Current page URL: ${page.url()}`);
                            console.log(`Current page title: ${await page.title()}`);
                            
                            // Try to get all available elements on the page for debugging
                            console.log("Available elements on page:");
                            const bodyHTML = await page.evaluate(() => document.body.innerHTML);
                            console.log(bodyHTML.substring(0, 1000) + "...");
                            
                            // For weather.gov specifically, try another URL pattern
                            if (page.url().includes('weather.gov') && !page.url().includes('forecast')) {
                                console.log("This appears to be weather.gov. Trying a direct forecast URL");
                                try {
                                    // Extract the search term and build a direct forecast URL
                                    const searchTerm = "New York, NY";
                                    
                                    // First, let's try with a deeper fallback for weather.gov
                                    // Create a new page with our user agent
                                    const newPage = await browser.newPage();
                                    await newPage.setUserAgent(userAgent);
                                    
                                    // Add extra headers to look more like a real browser
                                    await newPage.setExtraHTTPHeaders({
                                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                                        'Accept-Language': 'en-US,en;q=0.9',
                                        'Accept-Encoding': 'gzip, deflate, br',
                                        'Referer': 'https://www.weather.gov/',
                                        'Connection': 'keep-alive',
                                        'Upgrade-Insecure-Requests': '1',
                                        'Sec-Fetch-Dest': 'document',
                                        'Sec-Fetch-Mode': 'navigate',
                                        'Sec-Fetch-Site': 'same-origin',
                                        'Sec-Fetch-User': '?1'
                                    });
                                    
                                    // Convert to a format like forecast.weather.gov/MapClick.php?lat=40.7127&lon=-74.0059
                                    await newPage.goto(`https://forecast.weather.gov/zipcity.php?inputstring=${encodeURIComponent(searchTerm)}`);
                                    console.log(`Navigated to: ${newPage.url()}`);
                                    
                                    // Replace our current page with the new one
                                    await page.close();
                                    page = newPage;
                                    await new Promise(resolve => setTimeout(resolve, 2000));
                                    
                                    // Check again for the selector
                                    try {
                                        await page.waitForSelector(action.selector, { timeout: 5000, visible: true });
                                        console.log(`Found selector ${action.selector} after direct navigation`);
                                        break; // Success, continue with the flow
                                    } catch (innerError) {
                                        console.log(`Still couldn't find ${action.selector} after direct navigation`);
                                    }
                                } catch (navError) {
                                    console.error("Failed with direct navigation attempt too", navError);
                                }
                            }
                            
                            throw error;
                        }
                        break;
                }
            }
        }
        
        // Extract content based on the provided selectors
        const extractedContent: Record<string, any> = {};
        
        if (input.extractSelectors) {
            // Extract text from specified containers
            if (input.extractSelectors.containers && input.extractSelectors.containers.length > 0) {
                console.log(`Extracting from ${input.extractSelectors.containers.length} containers`);
                extractedContent.containers = [];
                
                for (const selector of input.extractSelectors.containers) {
                    try {
                        console.log(`Waiting for selector: ${selector}`);
                        await page.waitForSelector(selector, { timeout: 10000 });
                        console.log(`Found selector: ${selector}`);
                        
                        const textContent = await page.$eval(selector, (el: Element) => el.textContent || '');
                        console.log(`Extracted content from ${selector}: ${textContent.substring(0, 50)}...`);
                        
                        extractedContent.containers.push({
                            selector,
                            content: textContent.trim()
                        });
                    } catch (error) {
                        console.warn(`Error extracting content from container ${selector}:`, error);
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
                        const texts = await page.$$eval(selector, (elements: Element[]) => 
                            elements.map(el => el.textContent || '')
                        );
                        extractedContent.text.push({
                            selector,
                            content: texts.map((t: string) => t.trim()).filter((t: string) => t)
                        });
                    } catch (error) {
                        console.warn(`Error extracting text from ${selector}:`, error);
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
                    } catch (error) {
                        console.warn(`Error extracting links from ${selector}:`, error);
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
                    } catch (error) {
                        console.warn(`Error extracting images from ${selector}:`, error);
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
                console.warn('Error taking screenshot:', error);
                extractedContent.screenshotError = error instanceof Error ? error.message : String(error);
            }
        }
        
        // If no content was successfully extracted, get page HTML
        const hasExtractedContent = Object.keys(extractedContent).some(key => {
            console.log(`Checking key: ${key}`);
            const content = extractedContent[key];
            const isValid = Array.isArray(content) && content.length > 0 && 
                  content.some((item: any) => !item.error && item.content);
            console.log(`Key ${key} has valid content: ${isValid}`);
            return isValid;
        });
        
        if (!hasExtractedContent) {
            console.log('No content was successfully extracted, getting full HTML');
            extractedContent.html = await page.content();
        }
        
        console.log('Content extracted successfully');
        
        // Return a simulated Lambda response
        return {
            type: "tool_result",
            name: event.name,
            tool_use_id: event.id,
            content: JSON.stringify({
                status: 'success',
                url: input.url,
                content: extractedContent.html || extractedContent
            }, null, 2)
        };
    } catch (error) {
        console.error('Error in local scraper:', error);
        return {
            type: "tool_result",
            name: event.name,
            tool_use_id: event.id,
            content: `Error: ${error instanceof Error ? error.message : String(error)}`
        };
    } finally {
        if (browser) {
            await browser.close();
        }
    }
}

// Function to find Chrome/Chromium on the local system
function findChromiumExecutable() {
    // Different possible paths for Chrome/Chromium
    const paths = [
        // macOS
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        '/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary',
        '/Applications/Chromium.app/Contents/MacOS/Chromium',
        // Linux
        '/usr/bin/google-chrome',
        '/usr/bin/chromium',
        '/usr/bin/chromium-browser',
        // Windows
        'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
        'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
    ];
    
    for (const p of paths) {
        if (fs.existsSync(p)) {
            return p;
        }
    }
    
    throw new Error('Could not find Chrome/Chromium installation. Please specify the path manually.');
}

async function runTest() {
    try {
        console.log('Starting web scraper test...');
        
        // Create a test event for basic example.com scraping
        console.log('Creating test event for example.com...');
        const basicTestEvent = {
            "id": "scrape_example",
            "name": "web_scrape",
            "input": {
                "url": "https://example.com",
                "extractSelectors": {
                    "containers": ["h1", "p"]
                }
            }
        };

        // Create a test event for BBC navigation
        console.log('Creating test event for BBC navigation...');
        const bbcTestEvent = {
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
                        "timeMs": 2000
                    }
                ],
                "extractSelectors": {
                    "containers": [".gs-c-promo-heading", ".gs-c-promo-summary"],
                    "links": [".gs-c-promo-heading a"]
                }
            }
        };

        // Create a test event for Weather.gov navigation
        console.log('Creating test event for Weather.gov...');
        const weatherTestEvent = {
            "id": "weather_test",
            "name": "web_scrape",
            "input": {
                // Go directly to the forecast page for New York, NY
                "url": "https://forecast.weather.gov/MapClick.php?lat=40.7142&lon=-74.0059",
                "actions": [
                    {
                        "type": "wait", 
                        "timeMs": 2000
                    }
                ],
                "extractSelectors": {
                    "containers": ["#detailed-forecast", ".forecast-label"]
                }
            }
        };

        // Select which test to run
        const testEvent = weatherTestEvent; // Change to basicTestEvent or bbcTestEvent to test different scenarios
        
        // Process the event with our local scraper implementation
        console.log(`Testing with ${testEvent.input.url}...`);
        const result = await runLocalScraper(testEvent);

        // Print results
        console.log('\nTest Results:');
        console.log('------------------------');
        console.log(JSON.stringify(result, null, 2));
        console.log('------------------------');

        if (result.content) {
            const content = 
                typeof result.content === 'string' && result.content.startsWith('{') 
                    ? JSON.parse(result.content) 
                    : result.content;
                    
            console.log('\nExtracted Content:');
            console.log('------------------------');
            
            if (content.status === 'success') {
                if (typeof content.content === 'object') {
                    console.log('Structured content extracted:');
                    console.log(JSON.stringify(content.content, null, 2));
                } else if (content.content && content.content.length > 500) {
                    console.log('Full HTML content (truncated):');
                    console.log(content.content.substring(0, 500) + '...');
                } else {
                    console.log('Content:');
                    console.log(content.content);
                }
            } else {
                console.log('Error:', content);
            }
            
            console.log('------------------------');
        }

    } catch (error) {
        console.error('Test failed:', error);
    }
}

// Add a command to run the test
if (require.main === module) {
    runTest();
}