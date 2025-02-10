import { Handler } from 'aws-lambda';
import puppeteer from 'puppeteer-core';
import chromium from '@sparticuz/chromium';
import { Logger } from '@aws-lambda-powertools/logger';


const logger = new Logger({ serviceName: 'ai-agents' });

interface ScraperInput {
    url: string;
    selectors: {
        searchInput?: string;
        searchButton?: string;
        resultContainer?: string;
    };
    searchTerm?: string;
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
}

const SEARCH_RESULTS_TOOL = {
    name: "web_scrape",
    arguments: {
        type: "object",
        properties: {
            url: { type: "string" },
            searchTerm: { type: "string" },
            selectors: {
                type: "object",
                properties: {
                    searchInput: { type: "string" },
                    searchButton: { type: "string" },
                    resultContainer: { type: "string" }
                }
            }
        },
        required: ["searchTerm", "url", "selectors"]
    },
    description: "Search a website and return the results"
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

async function handleSearchResults(
    url: string,
    searchTerm: string,
    selectors?: { searchInput?: string, searchButton?: string, resultContainer?: string }
) {
    const browser = await getBrowser();
    logger.info("Using browser ", { browser });

    try {
        const page = await browser.newPage();

        logger.info(`Navigating to ${url}`);
        await page.goto(url, {
            waitUntil: 'networkidle0',
            timeout: 30000
        });

        // If search parameters are provided, perform search
        if (searchTerm && selectors && selectors.searchInput && selectors.searchButton) {
            logger.info(`Performing search for: ${searchTerm}`);
            await page.type(selectors.searchInput, searchTerm);
            await page.click(selectors.searchButton);
            await page.waitForNavigation({
                waitUntil: 'networkidle0',
                timeout: 30000
            });
        }

        // Extract content from the specified container
        let content = '';
        if (selectors && selectors.resultContainer) {
            console.log('Waiting for result container');
            await page.waitForSelector(selectors.resultContainer, { timeout: 30000 });
            content = await page.$eval(selectors.resultContainer, (el) => el.textContent || '');
        } else {
            content = await page.content();
        }

        console.log('Content extracted successfully');

        return JSON.stringify({
            status: 'success',
            url,
            searchTerm,
            content: content.trim()
        }, null, 2)

    } finally {
        await browser.close();
    }
}

export const handler: Handler<ToolEvent, ToolResponse> = async (event) => {

    logger.info("Received event", { event });
    const tool_use = event
    const tool_name = tool_use["name"]
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
                logger.info("Result", { result });

                break;
            }
            default:
                result = `Unknown tool: ${tool_name}`
        }
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


}