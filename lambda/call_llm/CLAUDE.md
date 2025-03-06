# Step Functions Agent - LLM Wrappers - Claude Memory File

This section of the framework is responsible for interfacing with the various LMMs (Language Model Models) that are used to drive the execution of the AI agents with the various tools using the orchestration of the Step Functions. The framework is designed to be modular and flexible, allowing for the easy addition of new LLMs as they become available, and allow the users to switch between them as needed.

Since each LLM has a slightly different API, the framework is designed to abstract the differences away from the user, allowing them to interact with the LLMs in a consistent manner. This is done by creating a common interface that all LLMs must implement, and then creating a wrapper for each LLM that implements this interface. This allows to add the unique functionality of each LLM while keeping the common functionality consistent across all LLMs.

## Build & Test Commands

- Run all tests: `pytest tests/`
- Run a single test: `pytest tests/test_claude_handler.py`
- Test with events: `sam local invoke OpenAILambda -e tests/events/multiple-places-weather-event.json`

## Code Style Guidelines

- **Imports**: stdlib → third-party → local; specific imports preferred
- **Types**: Use typing annotations (Dict, List, Any) consistently
- **Naming**: PascalCase (classes), snake_case (functions/variables), UPPER_SNAKE_CASE (constants)
- **Error handling**: Try/except blocks with logging, then re-raise when appropriate
- **Class structure**: Follow abstract base class pattern with ABC and @abstractmethod
- **Handler pattern**: Each LLM has separate handler and lambda modules
- **Testing**: Pytest with test files corresponding to implementation files

## Project Structure

- Organized by LLM provider (anthropic_llm, openai_llm, etc.)
- Common functionality in lambda_layer/python/common
- Base abstract classes define interfaces implemented by provider-specific handlers
