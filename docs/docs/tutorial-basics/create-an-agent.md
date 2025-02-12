---
sidebar_position: 2
---

# Building a New AI Agent

This tutorial will walk you through creating a new AI agent using AWS Step Functions and Lambda. We'll create a simple agent that can analyze customer feedback using sentiment analysis.

## 1. Set Up Project Structure

First, create the necessary directory structure:

  ```bash
  mkdir -p my-agent/{lambda/call_llm,lambda/tools,cdk}
  cd my-agent
  ```

## 2. Create the LLM Call Lambda

First, we'll define the Lambda function that will call our LLM (we'll use Claude in this example).

  ```python title="customer_agent_stack.py"
  from aws_cdk import (
      Stack,
      aws_lambda as _lambda,
      aws_lambda_python_alpha as _lambda_python,
      Duration
  )
  from constructs import Construct

  class CustomerAgentStack(Stack):
      def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
          super().__init__(scope, construct_id, **kwargs)

          # Create the Claude LLM caller Lambda
          call_llm_lambda_function = _lambda_python.PythonFunction(
              self, "CallLLMLambdaClaude",
              function_name="CustomerAgentLLMCaller",
              description="Lambda function to Call Claude LLM for customer feedback analysis",
              entry="lambda/call_llm/functions/anthropic_llm",
              runtime=_lambda.Runtime.PYTHON_3_12,
              timeout=Duration.seconds(90),
              memory_size=256,
              index="claude_handler.py",
              handler="lambda_handler",
              architecture=_lambda.Architecture.ARM_64,
              role=self.create_llm_role()  # You'll need to implement this method
          )
  ```

## 3. Define Tools

Let's create a sentiment analysis tool for our agent:

  ```python title="customer_agent_stack.py"
        # Create sentiment analysis tool Lambda
        sentiment_tool_lambda = _lambda_python.PythonFunction(
            self, "SentimentAnalysisTool",
            function_name="CustomerAgentSentimentTool",
            description="Lambda function for sentiment analysis",
            entry="lambda/tools/sentiment",
            runtime=_lambda.Runtime.PYTHON_3_12,
            timeout=Duration.seconds(30),
            memory_size=256,
            index="index.py",
            handler="lambda_handler",
            architecture=_lambda.Architecture.ARM_64,
            role=self.create_tool_role()  # You'll need to implement this method
        )

        # Define the tool for the agent
        from step_functions_agent.constructs import Tool
        
        agent_tools = [
            Tool(
                "analyze_sentiment",
                "Analyze the sentiment of customer feedback text.",
                sentiment_tool_lambda,
                input_schema={
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "The customer feedback text to analyze"
                        }
                    },
                    "required": ["text"]
                }
            )
        ]
  ```

## 4. Define System Prompt

Create a system prompt that defines the agent's role and capabilities:

  ```python title="customer_agent_stack.py"
        system_prompt = """
        You are a customer feedback analysis expert. Your job is to help analyze customer feedback
        and provide insights about customer sentiment and key themes.
        
        You have access to a sentiment analysis tool that can help determine the emotional tone
        of feedback. Use this tool when you need to get specific sentiment scores for feedback.
        
        Always:
        1. Break down the feedback into key points
        2. Analyze the sentiment when relevant
        3. Provide actionable insights
        4. Be concise and clear in your responses
        """
  ```

## 5. Create the Step Functions State Machine

Now let's create the state machine that will orchestrate our agent:

  ```python title="customer_agent_stack.py"
        from step_functions_agent.constructs import ConfigurableStepFunctionsConstruct

        customer_agent_flow = ConfigurableStepFunctionsConstruct(
            self,
            "CustomerAgentStateMachine",
            state_machine_name="CustomerFeedbackAnalysisAgent",
            state_machine_template_path="step-functions/agent-with-tools-flow-template.json",
            llm_caller=call_llm_lambda_function,
            tools=agent_tools,
            system_prompt=system_prompt,
            output_schema={
                "type": "object",
                "properties": {
                    "analysis": {
                        "type": "string",
                        "description": "The detailed analysis of the customer feedback"
                    },
                    "sentiment_score": {
                        "type": "number",
                        "description": "The calculated sentiment score"
                    },
                    "key_themes": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of key themes identified in the feedback"
                    }
                },
                "required": ["analysis", "sentiment_score", "key_themes"]
            }
        )
  ```

## 6. Update App Entry Point

Create or update your app.py file:

  ```python title="app.py"
  import aws_cdk as cdk
  from customer_agent_stack import CustomerAgentStack

  app = cdk.App()

  # Create the customer agent stack
  customer_agent = CustomerAgentStack(app, "CustomerFeedbackAgent")

  app.synth()
  ```

## 7. Deploy the Agent

Deploy the stack using the CDK CLI:

  ```bash
  cdk deploy CustomerFeedbackAgent
  ```

## 8. Testing the Agent

After deployment, you can test your agent by invoking the Step Functions state machine with a sample input:

```json
{
  {
    "messages": [
      {
        "role": "user",
        "content": "I recently used your product and while the features are great, the customer service response time was quite slow. However, I appreciate the quality of the product itself."
      }
    ]
  }
}
```

:::tip[Agent Input]
Please note that the agents are designed to get a list of messages as input. The messages can be as simple as a single user message or a complex conversation with multiple messages.
:::

The agent will:

Process the input using the LLM
Use the sentiment analysis tool when needed
Return a structured analysis following the output schema
This tutorial creates a basic customer feedback analysis agent. You can extend it by:

Adding more tools (e.g., categorization, language detection)
Enhancing the system prompt
Adding human approval steps for sensitive actions
Implementing more sophisticated analysis patterns
Remember to implement proper error handling, logging, and monitoring for production use.
