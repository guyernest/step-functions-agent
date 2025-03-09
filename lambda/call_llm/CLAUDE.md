# Step Functions Agent - LLM Wrappers - Claude Memory File

This section implements interfaces with various LLMs (Language Model Models) used to drive AI agents with Step Functions orchestration. The framework abstracts provider-specific APIs behind consistent interfaces to make switching between models seamless.

## Build & Test Commands

- Run all tests: `pytest tests/`
- Run specific test: `pytest tests/test_claude_handler.py -v`
- Test with events: `sam local invoke OpenAILambda -e tests/events/multiple-places-weather-event.json`
- Update dependencies: `pip-compile requirements.in`

## Code Style Guidelines

- **Imports**: stdlib → third-party → local; explicit imports preferred over wildcard
- **Formatting**: Maintain consistent indentation (4 spaces)
- **Types**: Use typing annotations (Dict, List, Any, Optional) for all public interfaces
- **Naming**: 
  - Classes: PascalCase (e.g., `ClaudeHandler`)
  - Functions/variables: snake_case (e.g., `process_message`)
  - Constants: UPPER_SNAKE_CASE (e.g., `MAX_TOKENS`)
- **Error handling**: Try/except with specific exceptions, proper logging, re-raise when appropriate
- **Documentation**: Docstrings for all public methods/functions
- **Class structure**: Follow abstract base class pattern with ABC and @abstractmethod
- **Handler pattern**: Each LLM has separate handler (business logic) and lambda (entry point) modules

## Project Structure

- Organized by LLM provider (anthropic_llm, openai_llm, bedrock_llm, gemini_llm)
- Each provider package follows identical structure (handler, lambda, requirements)
- Common functionality in lambda_layer/python/common
- Provider-specific handlers implement common interface for consistent usage