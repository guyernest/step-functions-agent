const { handler } = require('./index');
import { Context } from 'aws-lambda';

async function runTest() {
    try {
        console.log('Starting integration test...');
        
        // Create a test event
        console.log('Creating test event...');
        const testEvent = {
            "name": "get_nyt_books",
            "id": "unique_request_id",
            "input": {
                "genre": "hardcover-fiction"
            }
        };

        // Create a mock context object
        const mockContext: Context = {
            callbackWaitsForEmptyEventLoop: true,
            functionName: 'BooksAPILambda',
            functionVersion: '1',
            invokedFunctionArn: 'arn:aws:lambda:local:000000000000:function:BooksAPILambda',
            memoryLimitInMB: '128',
            awsRequestId: 'local-test',
            logGroupName: '/aws/lambda/BooksAPILambda',
            logStreamName: 'local-test',
            getRemainingTimeInMillis: () => 30000,
            done: () => {},
            fail: () => {},
            succeed: () => {},
        };
        const mockCallback = () => null;  // Simple null callback

        // Then process it with our handler
        console.log('Testing handler...');
        const result = await handler(testEvent, mockContext, );

        // Print results
        console.log('\nTest Results:');
        console.log('------------------------');
        console.log('result:', result);
        console.log('------------------------');
        // if (result.statusCode === 200) {
        //     console.log('\nExtracted Text:');
        //     console.log('------------------------');
        //     console.log(result.body.text);
        //     console.log('------------------------');
        // } else {
        //     console.log('Error:', result.body);
        // }

    } catch (error) {
        console.error('Test failed:', error);
    }
}

runTest();
