import { SFNClient, ListExecutionsCommand, ListStateMachinesCommand } from '@aws-sdk/client-sfn';

declare const process: { env: { AWS_REGION?: string } };

const client = new SFNClient({ region: process.env.AWS_REGION });

interface ExecutionStatistics {
  totalExecutions: number;
  runningExecutions: number;
  succeededExecutions: number;
  failedExecutions: number;
  abortedExecutions: number;
  averageDurationSeconds: number;
  executionsByAgent: Record<string, number>;
  recentFailures: Array<{
    agentName: string;
    executionName: string;
    startDate: string;
    error?: string;
  }>;
  successRate: number;
  todayExecutions: number;
  weekExecutions: number;
}

export const handler = async (event: any): Promise<any> => {
  console.log('Received event:', JSON.stringify(event, null, 2));

  try {
    // List all state machines
    const listSMCommand = new ListStateMachinesCommand({});
    const listSMResponse = await client.send(listSMCommand);
    
    const stateMachineArns = listSMResponse.stateMachines
      ?.map((sm: any) => sm.stateMachineArn)
      ?.filter((arn: any): arn is string => arn !== undefined) || [];
    
    console.log('Found state machines:', stateMachineArns.length);
    
    // Initialize statistics
    const stats: ExecutionStatistics = {
      totalExecutions: 0,
      runningExecutions: 0,
      succeededExecutions: 0,
      failedExecutions: 0,
      abortedExecutions: 0,
      averageDurationSeconds: 0,
      executionsByAgent: {},
      recentFailures: [],
      successRate: 0,
      todayExecutions: 0,
      weekExecutions: 0
    };
    
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const weekAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);
    
    let totalDuration = 0;
    let completedExecutions = 0;
    
    // Collect executions from all state machines
    for (const arn of stateMachineArns) {
      // Extract agent name from state machine ARN
      const arnParts = arn.split(':');
      const smName = arnParts[arnParts.length - 1];
      const agentName = smName.replace('-prod', '').replace('-dev', '');
      
      // Get all executions for this state machine
      const command = new ListExecutionsCommand({
        stateMachineArn: arn,
        maxResults: 100 // Get more for better statistics
      });
      
      const response = await client.send(command);
      const executions = response.executions || [];
      
      for (const exec of executions) {
        stats.totalExecutions++;
        
        // Count by status
        switch (exec.status) {
          case 'RUNNING':
            stats.runningExecutions++;
            break;
          case 'SUCCEEDED':
            stats.succeededExecutions++;
            break;
          case 'FAILED':
            stats.failedExecutions++;
            if (stats.recentFailures.length < 5) {
              stats.recentFailures.push({
                agentName,
                executionName: exec.name || 'Unknown',
                startDate: exec.startDate?.toISOString() || ''
              });
            }
            break;
          case 'ABORTED':
            stats.abortedExecutions++;
            break;
        }
        
        // Count by agent
        stats.executionsByAgent[agentName] = (stats.executionsByAgent[agentName] || 0) + 1;
        
        // Calculate duration for completed executions
        if (exec.stopDate && exec.startDate) {
          const duration = exec.stopDate.getTime() - exec.startDate.getTime();
          totalDuration += duration / 1000; // Convert to seconds
          completedExecutions++;
        }
        
        // Count executions by time period
        if (exec.startDate) {
          const execDate = new Date(exec.startDate);
          if (execDate >= today) {
            stats.todayExecutions++;
          }
          if (execDate >= weekAgo) {
            stats.weekExecutions++;
          }
        }
      }
    }
    
    // Calculate averages
    if (completedExecutions > 0) {
      stats.averageDurationSeconds = Math.round(totalDuration / completedExecutions);
    }
    
    // Calculate success rate
    const finishedExecutions = stats.succeededExecutions + stats.failedExecutions + stats.abortedExecutions;
    if (finishedExecutions > 0) {
      stats.successRate = Math.round((stats.succeededExecutions / finishedExecutions) * 100);
    }
    
    return {
      statistics: stats
    };
    
  } catch (error) {
    console.error('Error getting execution statistics:', error);
    return {
      error: 'Failed to get execution statistics',
      details: error instanceof Error ? error.message : 'Unknown error'
    };
  }
};