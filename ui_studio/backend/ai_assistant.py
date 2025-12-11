#!/usr/bin/env python3
"""
AI Assistant for Navigation Studio

Uses Claude SDK to provide intelligent script building assistance.
Implements MCP-style tools for browser control and script generation.
"""

import os
import json
import asyncio
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("Warning: anthropic package not available")


# Tool definitions for Claude
BROWSER_TOOLS = [
    {
        "name": "navigate",
        "description": "Navigate the browser to a URL",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL to navigate to"
                }
            },
            "required": ["url"]
        }
    },
    {
        "name": "click",
        "description": "Click on an element in the page. Use CSS selectors, text content, or role selectors.",
        "input_schema": {
            "type": "object",
            "properties": {
                "selector": {
                    "type": "string",
                    "description": "CSS selector, text selector (text=...), or role selector (role=button[name='Submit'])"
                },
                "description": {
                    "type": "string",
                    "description": "Human-readable description of what is being clicked"
                }
            },
            "required": ["selector"]
        }
    },
    {
        "name": "fill",
        "description": "Fill text into an input field",
        "input_schema": {
            "type": "object",
            "properties": {
                "selector": {
                    "type": "string",
                    "description": "CSS selector for the input field"
                },
                "value": {
                    "type": "string",
                    "description": "The text to fill into the field"
                },
                "description": {
                    "type": "string",
                    "description": "Human-readable description of the field"
                }
            },
            "required": ["selector", "value"]
        }
    },
    {
        "name": "screenshot",
        "description": "Take a screenshot of the current page to see what's visible",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "wait",
        "description": "Wait for an element to appear or for a delay",
        "input_schema": {
            "type": "object",
            "properties": {
                "selector": {
                    "type": "string",
                    "description": "CSS selector to wait for (optional)"
                },
                "delay_ms": {
                    "type": "integer",
                    "description": "Milliseconds to wait (if no selector)"
                }
            },
            "required": []
        }
    },
    {
        "name": "extract_text",
        "description": "Extract text content from an element",
        "input_schema": {
            "type": "object",
            "properties": {
                "selector": {
                    "type": "string",
                    "description": "CSS selector for the element"
                }
            },
            "required": ["selector"]
        }
    },
    {
        "name": "get_page_info",
        "description": "Get information about the current page (URL, title)",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "add_script_step",
        "description": "Add a step to the automation script being built",
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["navigate", "click", "fill", "wait", "screenshot", "extract", "execute_js", "select", "hover", "press"],
                    "description": "The type of action"
                },
                "description": {
                    "type": "string",
                    "description": "Human-readable description of the step"
                },
                "locator": {
                    "type": "object",
                    "properties": {
                        "strategy": {
                            "type": "string",
                            "enum": ["selector", "xpath", "text", "role", "id", "class"]
                        },
                        "value": {"type": "string"}
                    },
                    "description": "Element locator (for click, fill, wait, etc.)"
                },
                "url": {
                    "type": "string",
                    "description": "URL for navigate action"
                },
                "value": {
                    "type": "string",
                    "description": "Value for fill action"
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in milliseconds for wait action"
                }
            },
            "required": ["action", "description"]
        }
    }
]

SYSTEM_PROMPT = """You are an AI assistant helping users create browser automation scripts in Navigation Studio.

Your role is to:
1. Help users navigate websites and understand page structure
2. Build automation scripts step-by-step
3. Suggest reliable selectors for elements
4. Test actions before adding them to scripts

When the user asks you to automate something:
1. First take a screenshot to see the current page state
2. Identify the elements needed for the task
3. Execute actions one at a time, verifying each works
4. Add successful actions to the script using add_script_step

Always prefer:
- Stable selectors (IDs, data attributes) over fragile ones (nth-child, complex paths)
- Text-based selectors for buttons and links when text is unique
- Role selectors for semantic elements (buttons, links, inputs)

When you encounter errors:
- Take a screenshot to see the current state
- Try alternative selectors
- Explain the issue to the user

Be concise but informative. Show the user what you're doing at each step."""


class AIAssistant:
    """AI Assistant powered by Claude for script building."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514",
        on_tool_call: Optional[Callable] = None,
        on_message: Optional[Callable] = None,
    ):
        if not ANTHROPIC_AVAILABLE:
            raise RuntimeError("anthropic package not installed")

        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = model
        self.on_tool_call = on_tool_call
        self.on_message = on_message

        # Conversation history
        self.messages: List[Dict[str, Any]] = []

        # Script being built
        self.script_steps: List[Dict[str, Any]] = []
        self.script_name: str = "New Script"

    async def chat(
        self,
        user_message: str,
        browser_session=None,  # BrowserSession for executing tools
    ) -> Dict[str, Any]:
        """
        Send a message and get a response, executing any tool calls.

        Args:
            user_message: The user's message
            browser_session: Optional browser session for executing browser tools

        Returns:
            Dict with 'response' text and 'tool_results' list
        """
        # Add user message to history
        self.messages.append({
            "role": "user",
            "content": user_message
        })

        tool_results = []
        final_response = ""

        # Keep processing until we get a final response (no more tool calls)
        while True:
            # Call Claude
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=BROWSER_TOOLS,
                messages=self.messages
            )

            # Process the response
            assistant_content = []
            has_tool_use = False

            for block in response.content:
                if block.type == "text":
                    final_response = block.text
                    assistant_content.append({
                        "type": "text",
                        "text": block.text
                    })
                    if self.on_message:
                        await self.on_message({"type": "text", "content": block.text})

                elif block.type == "tool_use":
                    has_tool_use = True
                    tool_name = block.name
                    tool_input = block.input
                    tool_use_id = block.id

                    assistant_content.append({
                        "type": "tool_use",
                        "id": tool_use_id,
                        "name": tool_name,
                        "input": tool_input
                    })

                    # Execute the tool
                    if self.on_tool_call:
                        await self.on_tool_call({
                            "tool": tool_name,
                            "input": tool_input
                        })

                    tool_result = await self._execute_tool(
                        tool_name,
                        tool_input,
                        browser_session
                    )
                    tool_results.append({
                        "tool": tool_name,
                        "input": tool_input,
                        "result": tool_result
                    })

                    # Add tool result to messages
                    self.messages.append({
                        "role": "assistant",
                        "content": assistant_content
                    })
                    self.messages.append({
                        "role": "user",
                        "content": [{
                            "type": "tool_result",
                            "tool_use_id": tool_use_id,
                            "content": json.dumps(tool_result) if isinstance(tool_result, dict) else str(tool_result)
                        }]
                    })
                    assistant_content = []  # Reset for next iteration

            # If no tool use, we're done
            if not has_tool_use:
                self.messages.append({
                    "role": "assistant",
                    "content": assistant_content
                })
                break

            # Check for stop reason
            if response.stop_reason == "end_turn":
                break

        return {
            "response": final_response,
            "tool_results": tool_results,
            "script_steps": self.script_steps
        }

    async def _execute_tool(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        browser_session
    ) -> Dict[str, Any]:
        """Execute a tool and return the result."""

        if tool_name == "add_script_step":
            # Add step to the script being built
            step = {
                "action": tool_input.get("action"),
                "description": tool_input.get("description", ""),
            }
            if tool_input.get("locator"):
                step["locator"] = tool_input["locator"]
            if tool_input.get("url"):
                step["url"] = tool_input["url"]
            if tool_input.get("value"):
                step["value"] = tool_input["value"]
            if tool_input.get("timeout"):
                step["timeout"] = tool_input["timeout"]

            self.script_steps.append(step)
            return {
                "status": "success",
                "message": f"Added step {len(self.script_steps)}: {step['description']}",
                "step_index": len(self.script_steps) - 1
            }

        # Browser tools require a session
        if not browser_session:
            return {"error": "No browser session available"}

        if tool_name == "navigate":
            result = await browser_session.navigate(tool_input.get("url", ""))
            return result

        elif tool_name == "click":
            result = await browser_session.click(tool_input.get("selector", ""))
            return result

        elif tool_name == "fill":
            result = await browser_session.fill(
                tool_input.get("selector", ""),
                tool_input.get("value", "")
            )
            return result

        elif tool_name == "screenshot":
            result = await browser_session.screenshot()
            # Don't return the full base64 in tool result, just status
            if result.get("screenshot"):
                return {
                    "status": "success",
                    "message": "Screenshot taken",
                    "url": result.get("url")
                }
            return result

        elif tool_name == "wait":
            if tool_input.get("selector"):
                try:
                    await browser_session.page.wait_for_selector(
                        tool_input["selector"],
                        timeout=tool_input.get("timeout", 5000)
                    )
                    return {"status": "success", "message": "Element found"}
                except Exception as e:
                    return {"status": "error", "error": str(e)}
            else:
                delay = tool_input.get("delay_ms", 1000)
                await asyncio.sleep(delay / 1000)
                return {"status": "success", "message": f"Waited {delay}ms"}

        elif tool_name == "extract_text":
            try:
                element = await browser_session.page.query_selector(tool_input.get("selector", ""))
                if element:
                    text = await element.text_content()
                    return {"status": "success", "text": text}
                return {"status": "error", "error": "Element not found"}
            except Exception as e:
                return {"status": "error", "error": str(e)}

        elif tool_name == "get_page_info":
            return await browser_session.get_page_info()

        else:
            return {"error": f"Unknown tool: {tool_name}"}

    def get_script(self) -> Dict[str, Any]:
        """Get the current script being built."""
        return {
            "name": self.script_name,
            "steps": self.script_steps,
            "created_at": datetime.now().isoformat()
        }

    def clear_script(self):
        """Clear the current script."""
        self.script_steps = []

    def set_script_name(self, name: str):
        """Set the script name."""
        self.script_name = name

    def clear_history(self):
        """Clear conversation history."""
        self.messages = []


# Factory function
def create_assistant(
    api_key: Optional[str] = None,
    model: str = "claude-sonnet-4-20250514",
    **kwargs
) -> AIAssistant:
    """Create an AI assistant instance."""
    return AIAssistant(api_key=api_key, model=model, **kwargs)
