const { handler } = require('./index');
import { Context } from 'aws-lambda';

async function runTest() {
    try {
        console.log('Starting integration test...');
        
        // Create a test event
        console.log('Creating test event...');
        const testEvent = {
            "name": "query_earthquakes",
            "id": "unique_request_id",
            "input": {
                "start_date": "2024-01-01",
                "end_date": "2024-01-02"
            }
        };

        // Create a mock context object
        const mockContext: Context = {
            callbackWaitsForEmptyEventLoop: true,
            functionName: 'BooksAPILambda',
            functionVersion: '1',
            invokedFunctionArn: 'arn:aws:lambda:local:000000000000:function:EarthQuakeQueryTS',
            memoryLimitInMB: '128',
            awsRequestId: 'local-test',
            logGroupName: '/aws/lambda/EarthQuakeQueryTS',
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

    } catch (error) {
        console.error('Test failed:', error);
    }
}

runTest();