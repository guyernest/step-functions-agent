---
sidebar_position: 2
---

# Understanding AI Agents

## Tool Calling: Extending the Capabilities of LLMs

While large language models (LLMs) are incredibly powerful, they work primarily as next-token predictors—generating text based on patterns learned during training. This means that, on their own, LLMs don’t have access to real-time data or the ability to interact with external systems. That’s where tool calling comes into play.

### The difference between Workflow and AI Agents

Anthropic published an article on [Building effective agents](https://www.anthropic.com/research/building-effective-agents) where they explain the difference between workflows and agents:

> At Anthropic, we categorize all these variations as agentic systems, but draw an important architectural distinction between workflows and agents:
>
> * Workflows are systems where LLMs and tools are orchestrated through predefined code paths.
> * Agents, on the other hand, are systems where LLMs dynamically direct their own processes and tool usage, maintaining control over how they accomplish tasks.

### Schematic Flow

The following diagram illustrates the schematic flow of an AI agent:

<div style={{ textAlign: "center" }}>
  <img src={require('../../static/img/AgentSchamticFlow.png').default} alt="Schematic Flow" style={{ width: "60%", maxWidth: "600px" }} />
</div>

### What Are Tools?

In the context of AI agents, tools refer to external functions, APIs, or services that can be called to retrieve or manipulate data in the external world and are outside the LLM’s training corpus. These tools enable agents to:

* Access real-time information: For example, fetching the current weather, stock prices, or a customer’s order status.
* Perform actions: Such as updating a record in a database, sending an email, or controlling a smart device.

### How Do LLMs Use Tools?

Since LLMs lack intrinsic awareness of the current state of the world, they rely on a process that involves tool calling to bridge this gap. Here’s a typical workflow:

1. Tool Detection:
The LLM identifies that the user’s query requires up-to-date or specialized information (e.g., “What’s the weather like today?” or “Update my order status”), which is not available within its current context or training data.
2. Tool Invocation:
Instead of trying to fabricate ("hallucinate") an answer from its internal training data, the LLM outputs a structured command or instruction that indicates the need to call a specific tool. For instance:

    ```json
    {
        "action": "get_weather",
        "parameters": {
            "location": "New York"
        }
    }
    ```

3. Tool Execution:
The agent’s execution environment (e.g., AWS Step Functions) interprets this command, calls the appropriate tool (e.g., a weather API), and retrieves the necessary data.
4. Tool Response:
The tool’s output is then fed back into the LLM, which uses this information to generate a additional tool calls or a final, accurate response to the user’s query.
The system intercepts this command, calls the appropriate external service (like a weather API), and retrieves the current data.

## Example Scenario

Consider a scenario where a user asks, “What’s the weather like in New York today?” The agent’s process would be as follows:

* Step 1: The LLM detects that it needs real-time weather data for New York.
* Step 2: It generates a tool call similar to the JSON snippet shown above.
* Step 3: An external weather API is called, and the current weather information for New York is fetched.
* Step 4: The LLM receives the weather data and crafts a final response such as, “Today in New York, it’s partly cloudy with a high of 75°F.”

## Benefits of Tool Calling

* **Real-Time Accuracy**: The integration of external data sources means that responses are based on the most current information available.
* **Extended Functionality**: Tools allow AI agents to perform actions and retrieve data that go well beyond the LLM’s training data.
* **Enhanced User Experience**: By combining natural language understanding with up-to-date, actionable data, AI agents can provide more relevant and useful responses.

## Challenges and Considerations

While tool calling greatly enhances the capabilities of AI agents, it also introduces some challenges:

* **Latency**: Calling external tools can introduce delays, especially if the API responses are slow.
* **Error Handling**: External services might fail or return unexpected results, so robust error handling mechanisms are essential.
* **Security**: Exposing systems to external calls requires careful consideration of authentication, data privacy, and potential misuse.

## Conclusion

Tool calling is a key mechanism that allows AI agents to overcome the limitations of pre-trained LLMs by incorporating real-time data and external functionality. This not only makes the agents more dynamic and accurate but also expands the range of tasks they can perform. By understanding how to integrate and manage these tools, developers can build AI systems that are both powerful and contextually aware.
