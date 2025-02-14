import { Handler } from 'aws-lambda';
import { getSecret } from '@aws-lambda-powertools/parameters/secrets';
import { Logger } from '@aws-lambda-powertools/logger';
import fetch from 'node-fetch'

const logger = new Logger({ serviceName: 'NYT Books API Tools' });

// Response interface
interface BooksResponse {
    status: string;
    results: {
        list_name: string;
        bestsellers_date: string;
        books: Array<{
            rank: number;
            title: string;
            author: string;
            description: string;
            publisher: string;
            primary_isbn13: string;
            amazon_product_url: string;
        }>;
    };
}

// Tool definition
const GET_BOOKS_TOOL = {
    name: "get_nyt_books",
    description: "Get the New York Times Best Sellers list for a specified genre",
    inputSchema: {
        type: "object",
        properties: {
            genre: {
                type: "string",
                enum: [
                    "combined-print-and-e-book-fiction",
                    "combined-print-and-e-book-nonfiction",
                    "hardcover-fiction",
                    "hardcover-nonfiction",
                    "trade-fiction-paperback",
                    "paperback-nonfiction",
                    "advice-how-to-and-miscellaneous",
                    "childrens-middle-grade-hardcover",
                    "picture-books",
                    "series-books",
                    "young-adult-hardcover",
                    "audio-fiction",
                    "audio-nonfiction",
                    "business-books",
                    "graphic-books-and-manga",
                    "mass-market-monthly",
                    "middle-grade-paperback-monthly",
                    "young-adult-paperback-monthly"
                ],
                description: "The genre/category of books to retrieve (e.g., 'hardcover-fiction')"
            }
        },
        required: ["genre"]
    }
};

// Global API key
let NYT_BOOKS_API_KEY: string;

async function initializeApiKey(): Promise<void> {
    try {
        const apiKeySecret = await getSecret("/ai-agent/book-tool/api-key");
        if (!apiKeySecret) {
            throw new Error("Failed to retrieve NYT API key from Secrets Manager");
        }
        NYT_BOOKS_API_KEY = JSON.parse(apiKeySecret.toString())["NYT_BOOKS_API_KEY"];
        logger.info("API key initialized successfully");
    } catch (error) {
        logger.error('Failed to initialize API key', { error });
        throw error;
    }
}

async function handleGetBooks(genre: string): Promise<string> {
    const url = new URL(`https://api.nytimes.com/svc/books/v3/lists/current/${genre}.json`);
    url.searchParams.append("api-key", NYT_BOOKS_API_KEY);

    try {
        const response = await fetch(url.toString());
        
        if (!response.ok) {
            const errorData = await response.json();
            return JSON.stringify({
                error: `NYT API request failed: ${JSON.stringify(errorData)}`
            });
        }

        const data = await response.json() as BooksResponse;
        
        return JSON.stringify({
            list_name: data.results.list_name,
            bestsellers_date: data.results.bestsellers_date,
            books: data.results.books.map(book => ({
                rank: book.rank,
                title: book.title,
                author: book.author,
                description: book.description,
                publisher: book.publisher,
                isbn13: book.primary_isbn13,
                amazon_url: book.amazon_product_url
            }))
        }, null, 2);
    } catch (error) {
        logger.error('Error fetching books data:', { error });
        return JSON.stringify({
            error: `Error fetching books data: ${error instanceof Error ? error.message : String(error)}`
        });
    }
}

exports.handler = async (event:any, context:any) => {
    // Initialize API key if not already set
    if (!NYT_BOOKS_API_KEY) {
        await initializeApiKey();
    }

    logger.info("Received event", { event });
    const tool_use = event;
    const tool_name = tool_use["name"];

    try {
        let result: string;
        switch (tool_name) {
            case "get_nyt_books": {
                const { genre } = tool_use.input as { genre: string };
                result = await handleGetBooks(genre);
                break;
            }
            default:
                result = JSON.stringify({
                    error: `Unknown tool: ${tool_name}`
                });
        }

        logger.info("Result", { result });
        return {
            "type": "tool_result",
            "name": tool_name,
            "tool_use_id": tool_use["id"],
            "content": result
        };
    } catch (error) {
        return {
            "type": "tool_result",
            "name": tool_name,
            "tool_use_id": tool_use["id"],
            "content": JSON.stringify({
                error: error instanceof Error ? error.message : String(error)
            })
        };
    }
};