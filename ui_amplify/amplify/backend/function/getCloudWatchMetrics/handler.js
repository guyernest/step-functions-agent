// Default model pricing per 1M tokens
const DEFAULT_MODEL_PRICING = {
    'gpt-4o': { input: 2.50, output: 10.00 },
    'gpt-4o-mini': { input: 0.15, output: 0.60 },
    'claude-3-7-sonnet-latest': { input: 3.00, output: 15.00 },
    'claude-3-7': { input: 3.00, output: 15.00 }, // Alias for backward compatibility
    'gemini-2.0-flash-001': { input: 0.10, output: 0.40 },
    'gemini-2.0-flash': { input: 0.10, output: 0.40 }, // Alias for backward compatibility
    'amazon.nova-pro': { input: 0.80, output: 3.20 },
    'grok-2': { input: 2.00, output: 10.00 }
};
// Function to get model costs from DynamoDB
async function getModelCosts() {
    try {
        const { DynamoDBClient, ScanCommand } = require('@aws-sdk/client-dynamodb');
        const dynamoClient = new DynamoDBClient({ region: process.env.AWS_REGION });
        // Use environment variable or fallback to finding the table
        let modelCostTableName = process.env.MODEL_COST_TABLE_NAME;
        if (!modelCostTableName) {
            // Fallback: Find the ModelCost table name (it includes a hash suffix in sandbox)
            const { ListTablesCommand } = require('@aws-sdk/client-dynamodb');
            const listTablesResponse = await dynamoClient.send(new ListTablesCommand({}));
            modelCostTableName = listTablesResponse.TableNames?.find((name) => name.startsWith('ModelCost-'));
        }
        if (!modelCostTableName) {
            console.log('ModelCost table not found, using defaults');
            return DEFAULT_MODEL_PRICING;
        }
        console.log('Using ModelCost table:', modelCostTableName);
        // Scan the ModelCost table
        const scanCommand = new ScanCommand({
            TableName: modelCostTableName
        });
        const scanResponse = await dynamoClient.send(scanCommand);
        const modelPricing = { ...DEFAULT_MODEL_PRICING };
        if (scanResponse.Items) {
            scanResponse.Items.forEach((item) => {
                if (item.modelName?.S && item.inputPrice?.N && item.outputPrice?.N) {
                    // Only include active models
                    if (item.isActive?.BOOL !== false) {
                        modelPricing[item.modelName.S] = {
                            input: parseFloat(item.inputPrice.N),
                            output: parseFloat(item.outputPrice.N)
                        };
                    }
                }
            });
        }
        console.log('Loaded model pricing:', modelPricing);
        return modelPricing;
    }
    catch (error) {
        console.error('Error fetching model costs from DynamoDB:', error);
        return DEFAULT_MODEL_PRICING;
    }
}
export const handler = async (event) => {
    console.log('Received event:', JSON.stringify(event, null, 2));
    try {
        // Load CloudWatch client
        const { CloudWatchClient, GetMetricDataCommand, ListMetricsCommand } = require('@aws-sdk/client-cloudwatch');
        const REGION = process.env.AWS_REGION;
        const client = new CloudWatchClient({ region: REGION });
        const request = event.arguments || {};
        // Calculate time range
        const endTime = new Date(request.endTime || Date.now());
        const startTime = new Date(request.startTime || endTime.getTime() - 3 * 60 * 60 * 1000); // Default 3 hours
        const period = request.period || 300; // 5 minutes default
        let formattedData = {};
        if (request.metricType === 'cost') {
            // Get current model pricing from DynamoDB
            const modelPricing = await getModelCosts();
            // First, list all available metrics to get actual dimensions
            const [inputMetricsResponse, outputMetricsResponse] = await Promise.all([
                client.send(new ListMetricsCommand({
                    Namespace: 'AI-Agents',
                    MetricName: 'InputTokens'
                })),
                client.send(new ListMetricsCommand({
                    Namespace: 'AI-Agents',
                    MetricName: 'OutputTokens'
                }))
            ]);
            const inputMetrics = inputMetricsResponse.Metrics || [];
            const outputMetrics = outputMetricsResponse.Metrics || [];
            console.log(`Found ${inputMetrics.length} input metrics and ${outputMetrics.length} output metrics`);
            // Prepare queries for all metrics
            const metricQueries = [];
            const idToMetricInfo = {};
            let queryIndex = 0;
            // Process input metrics
            for (const metric of inputMetrics) {
                const modelDim = metric.Dimensions?.find((d) => d.Name === 'model');
                const agentDim = metric.Dimensions?.find((d) => d.Name === 'agent');
                if (modelDim?.Value && agentDim?.Value && modelPricing[modelDim.Value]) {
                    const id = `input_${queryIndex++}`;
                    idToMetricInfo[id] = {
                        model: modelDim.Value,
                        agent: agentDim.Value,
                        isInput: true
                    };
                    metricQueries.push({
                        Id: id,
                        MetricStat: {
                            Metric: {
                                Namespace: 'AI-Agents',
                                MetricName: 'InputTokens',
                                Dimensions: metric.Dimensions
                            },
                            Period: period,
                            Stat: 'Sum'
                        },
                        ReturnData: true
                    });
                }
            }
            // Process output metrics
            for (const metric of outputMetrics) {
                const modelDim = metric.Dimensions?.find((d) => d.Name === 'model');
                const agentDim = metric.Dimensions?.find((d) => d.Name === 'agent');
                if (modelDim?.Value && agentDim?.Value && modelPricing[modelDim.Value]) {
                    const id = `output_${queryIndex++}`;
                    idToMetricInfo[id] = {
                        model: modelDim.Value,
                        agent: agentDim.Value,
                        isInput: false
                    };
                    metricQueries.push({
                        Id: id,
                        MetricStat: {
                            Metric: {
                                Namespace: 'AI-Agents',
                                MetricName: 'OutputTokens',
                                Dimensions: metric.Dimensions
                            },
                            Period: period,
                            Stat: 'Sum'
                        },
                        ReturnData: true
                    });
                }
            }
            console.log(`Built ${metricQueries.length} metric queries`);
            // Initialize data structures for breakdown
            const totalCostData = {};
            const costByModel = {};
            const costByAgent = {};
            const totalCostByModel = {};
            const totalCostByAgent = {};
            // If we have queries, fetch the data
            if (metricQueries.length > 0) {
                // Get metric data in batches of 500 (CloudWatch limit)
                const batchSize = 500;
                for (let i = 0; i < metricQueries.length; i += batchSize) {
                    const batch = metricQueries.slice(i, i + batchSize);
                    const params = {
                        MetricDataQueries: batch,
                        StartTime: startTime,
                        EndTime: endTime
                    };
                    console.log(`Fetching batch ${i / batchSize + 1} with ${batch.length} queries`);
                    const command = new GetMetricDataCommand(params);
                    const response = await client.send(command);
                    console.log(`Batch response contains ${response.MetricDataResults?.length || 0} results`);
                    // Process the response
                    if (response.MetricDataResults) {
                        for (const result of response.MetricDataResults) {
                            if (!result.Id || !result.Timestamps || !result.Values)
                                continue;
                            const metricInfo = idToMetricInfo[result.Id];
                            if (!metricInfo)
                                continue;
                            const { model, agent, isInput } = metricInfo;
                            const pricing = isInput ? modelPricing[model].input : modelPricing[model].output;
                            // Initialize model and agent data structures if needed
                            if (!costByModel[model])
                                costByModel[model] = {};
                            if (!costByAgent[agent])
                                costByAgent[agent] = {};
                            if (!totalCostByModel[model])
                                totalCostByModel[model] = 0;
                            if (!totalCostByAgent[agent])
                                totalCostByAgent[agent] = 0;
                            // Process each data point
                            result.Timestamps.forEach((timestamp, i) => {
                                const tokens = result.Values[i] || 0;
                                if (tokens > 0) {
                                    const cost = (tokens * pricing) / 1000000; // Convert to cost per million tokens
                                    const timeKey = timestamp.toISOString();
                                    // Update total cost
                                    totalCostData[timeKey] = (totalCostData[timeKey] || 0) + cost;
                                    // Update cost by model
                                    costByModel[model][timeKey] = (costByModel[model][timeKey] || 0) + cost;
                                    totalCostByModel[model] += cost;
                                    // Update cost by agent
                                    costByAgent[agent][timeKey] = (costByAgent[agent][timeKey] || 0) + cost;
                                    totalCostByAgent[agent] += cost;
                                    console.log(`${agent}/${model} ${isInput ? 'input' : 'output'} at ${timeKey}: ${tokens} tokens = $${cost.toFixed(6)}`);
                                }
                            });
                        }
                    }
                }
            }
            // Convert to arrays for the response
            const timestamps = Object.keys(totalCostData).sort();
            // Format total cost data
            const totalCost = {
                id: 'total_cost',
                label: 'Total Cost (USD)',
                timestamps,
                values: timestamps.map(t => totalCostData[t] || 0),
                statusCode: timestamps.length > 0 ? 'Complete' : 'NoData'
            };
            // Format cost by model
            const costByModelFormatted = {};
            Object.keys(costByModel).forEach(model => {
                costByModelFormatted[model] = {
                    id: `cost_model_${model}`,
                    label: model,
                    timestamps,
                    values: timestamps.map(t => costByModel[model][t] || 0),
                    statusCode: 'Complete'
                };
            });
            // Format cost by agent
            const costByAgentFormatted = {};
            Object.keys(costByAgent).forEach(agent => {
                costByAgentFormatted[agent] = {
                    id: `cost_agent_${agent}`,
                    label: agent,
                    timestamps,
                    values: timestamps.map(t => costByAgent[agent][t] || 0),
                    statusCode: 'Complete'
                };
            });
            // Calculate summary statistics
            const totalSpent = Object.values(totalCostData).reduce((a, b) => a + b, 0);
            // Find top model and agent
            const topModel = Object.entries(totalCostByModel)
                .sort(([, a], [, b]) => b - a)[0];
            const topAgent = Object.entries(totalCostByAgent)
                .sort(([, a], [, b]) => b - a)[0];
            const summary = {
                totalSpent,
                topModel: topModel ? {
                    name: topModel[0],
                    cost: topModel[1],
                    percentage: totalSpent > 0 ? (topModel[1] / totalSpent * 100) : 0
                } : null,
                topAgent: topAgent ? {
                    name: topAgent[0],
                    cost: topAgent[1],
                    percentage: totalSpent > 0 ? (topAgent[1] / totalSpent * 100) : 0
                } : null,
                modelBreakdown: Object.entries(totalCostByModel).map(([name, cost]) => ({
                    name,
                    cost,
                    percentage: totalSpent > 0 ? (cost / totalSpent * 100) : 0
                })),
                agentBreakdown: Object.entries(totalCostByAgent).map(([name, cost]) => ({
                    name,
                    cost,
                    percentage: totalSpent > 0 ? (cost / totalSpent * 100) : 0
                }))
            };
            console.log(`Total cost: $${totalSpent.toFixed(2)}, Top model: ${topModel?.[0]}, Top agent: ${topAgent?.[0]}`);
            formattedData = {
                totalCost,
                costByModel: costByModelFormatted,
                costByAgent: costByAgentFormatted,
                summary,
                startTime: startTime.toISOString(),
                endTime: endTime.toISOString(),
                period
            };
        }
        else if (request.metricType === 'tokens' && request.agentName) {
            // Keep existing token logic for backward compatibility
            // First, list metrics for this specific agent
            const [inputMetricsResponse, outputMetricsResponse] = await Promise.all([
                client.send(new ListMetricsCommand({
                    Namespace: 'AI-Agents',
                    MetricName: 'InputTokens',
                    Dimensions: [
                        { Name: 'agent', Value: request.agentName }
                    ]
                })),
                client.send(new ListMetricsCommand({
                    Namespace: 'AI-Agents',
                    MetricName: 'OutputTokens',
                    Dimensions: [
                        { Name: 'agent', Value: request.agentName }
                    ]
                }))
            ]);
            const inputMetrics = inputMetricsResponse.Metrics || [];
            const outputMetrics = outputMetricsResponse.Metrics || [];
            console.log(`Found ${inputMetrics.length} input and ${outputMetrics.length} output metrics for agent ${request.agentName}`);
            // Aggregate tokens by timestamp across all models for this agent
            const inputTokensByTime = {};
            const outputTokensByTime = {};
            // Build queries for all metrics
            const metricQueries = [];
            let queryIndex = 0;
            // Add input metrics
            for (const metric of inputMetrics) {
                metricQueries.push({
                    Id: `input_${queryIndex++}`,
                    MetricStat: {
                        Metric: {
                            Namespace: 'AI-Agents',
                            MetricName: 'InputTokens',
                            Dimensions: metric.Dimensions
                        },
                        Period: period,
                        Stat: 'Sum'
                    },
                    ReturnData: true
                });
            }
            // Add output metrics
            for (const metric of outputMetrics) {
                metricQueries.push({
                    Id: `output_${queryIndex++}`,
                    MetricStat: {
                        Metric: {
                            Namespace: 'AI-Agents',
                            MetricName: 'OutputTokens',
                            Dimensions: metric.Dimensions
                        },
                        Period: period,
                        Stat: 'Sum'
                    },
                    ReturnData: true
                });
            }
            if (metricQueries.length > 0) {
                const params = {
                    MetricDataQueries: metricQueries,
                    StartTime: startTime,
                    EndTime: endTime
                };
                const command = new GetMetricDataCommand(params);
                const response = await client.send(command);
                // Process results
                if (response.MetricDataResults) {
                    for (const result of response.MetricDataResults) {
                        if (!result.Id || !result.Timestamps || !result.Values)
                            continue;
                        const isInput = result.Id.startsWith('input_');
                        const tokenMap = isInput ? inputTokensByTime : outputTokensByTime;
                        result.Timestamps.forEach((timestamp, i) => {
                            const tokens = result.Values[i] || 0;
                            const timeKey = timestamp.toISOString();
                            tokenMap[timeKey] = (tokenMap[timeKey] || 0) + tokens;
                        });
                    }
                }
            }
            // Convert to arrays
            const allTimestamps = new Set([...Object.keys(inputTokensByTime), ...Object.keys(outputTokensByTime)]);
            const timestamps = Array.from(allTimestamps).sort();
            formattedData = {
                data: [
                    {
                        id: 'input_tokens',
                        label: 'Input Tokens',
                        timestamps,
                        values: timestamps.map(t => inputTokensByTime[t] || 0),
                        statusCode: timestamps.length > 0 ? 'Complete' : 'NoData'
                    },
                    {
                        id: 'output_tokens',
                        label: 'Output Tokens',
                        timestamps,
                        values: timestamps.map(t => outputTokensByTime[t] || 0),
                        statusCode: timestamps.length > 0 ? 'Complete' : 'NoData'
                    }
                ],
                startTime: startTime.toISOString(),
                endTime: endTime.toISOString(),
                period
            };
        }
        return formattedData;
    }
    catch (error) {
        console.error('Error fetching CloudWatch metrics:', error);
        return {
            error: 'Failed to fetch metrics',
            details: error instanceof Error ? error.message : 'Unknown error'
        };
    }
};
