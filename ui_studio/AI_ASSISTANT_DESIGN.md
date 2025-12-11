# AI Assistant Design

## Overview

The AI Assistant is the core intelligence of Navigation Studio, powered by Claude Agent SDK. It maintains a continuous conversation with the user, understands the script being built, analyzes web pages, and provides actionable guidance for creating browser automation scripts.

## Design Principles

1. **Conversational Context** - Claude remembers the entire session, building understanding over time
2. **Tool-Augmented** - Claude has tools to analyze pages, not just respond to text
3. **Proactive Assistance** - Automatically analyze elements and suggest locators during recording
4. **Actionable Output** - Suggestions are specific and can be applied with one click

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Navigation Studio UI                         │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                  AI Assistant Panel                       │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │ Chat Messages                                      │  │   │
│  │  │ ─────────────────────────────────────────────────  │  │   │
│  │  │ [User]: How do I handle the address dropdown?      │  │   │
│  │  │ [Assistant]: I can see the page has a dropdown...  │  │   │
│  │  │ [Tool: analyze_page] ✓                             │  │   │
│  │  │ [Assistant]: Here are 3 strategies...              │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │ Suggestion Cards                                   │  │   │
│  │  │ ┌──────────────────┐ ┌──────────────────┐         │  │   │
│  │  │ │ Locator Option 1 │ │ Locator Option 2 │         │  │   │
│  │  │ │ ✅ HIGH stability│ │ ⚠️ MEDIUM        │         │  │   │
│  │  │ │ [Apply]          │ │ [Apply]          │         │  │   │
│  │  │ └──────────────────┘ └──────────────────┘         │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │ 💬 Ask a question...                    [Send]     │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────┘   │
└───────────────────────────────┬─────────────────────────────────┘
                                │ WebSocket
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Python Backend                               │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                 NavigationAssistant                       │   │
│  │  ┌─────────────────┐  ┌─────────────────────────────┐    │   │
│  │  │ ClaudeSDKClient │  │ StudioContext               │    │   │
│  │  │ ───────────────  │  │ ─────────────────────────   │    │   │
│  │  │ • Conversation  │  │ • current_page (HTML)       │    │   │
│  │  │ • Tool dispatch │  │ • page_history              │    │   │
│  │  │ • Streaming     │  │ • selected_element          │    │   │
│  │  └─────────────────┘  │ • script (being edited)     │    │   │
│  │                       │ • failed_steps              │    │   │
│  │  ┌─────────────────┐  └─────────────────────────────┘    │   │
│  │  │ MCP Tools       │                                      │   │
│  │  │ ─────────────   │  ┌─────────────────────────────┐    │   │
│  │  │ • analyze_page  │  │ HTMLContextManager          │    │   │
│  │  │ • analyze_elem  │  │ ─────────────────────────   │    │   │
│  │  │ • gen_locators  │  │ • Page compression          │    │   │
│  │  │ • suggest_step  │  │ • Structure extraction      │    │   │
│  │  │ • diagnose_fail │  │ • Focus context             │    │   │
│  │  │ • modify_script │  │ • Diff computation          │    │   │
│  │  └─────────────────┘  └─────────────────────────────┘    │   │
│  └──────────────────────────────────────────────────────────┘   │
└───────────────────────────────┬─────────────────────────────────┘
                                │ Claude API
                                ▼
                    ┌─────────────────────┐
                    │   Anthropic Cloud   │
                    │   (Claude Sonnet)   │
                    └─────────────────────┘
```

## Claude Agent SDK Integration

### Client Setup

```python
from claude_sdk import ClaudeSDKClient, ClaudeAgentOptions

class NavigationAssistant:
    SYSTEM_PROMPT = """You are an AI assistant helping domain experts create
    browser automation scripts in Navigation Studio.

    ## Your Role
    - Analyze web pages and suggest reliable element locators
    - Help users build navigation scripts step by step
    - Diagnose failures and suggest fixes
    - Explain technical concepts in simple terms

    ## Script Format (v2)
    Scripts use a declarative format where each step has:
    - Action type (click, fill, wait, etc.)
    - Description for humans
    - Locators array with stability rankings

    ## Locator Stability (prefer top to bottom)
    1. test_id, data-testid, data-cy (HIGH - stable across deploys)
    2. aria-label, name attribute (HIGH - accessibility)
    3. text content (MEDIUM - may change with i18n)
    4. CSS class (LOW - often generated/utility classes)

    ## Tools Available
    Use these tools to gather information before responding:
    - analyze_page: Understand page structure
    - analyze_element: Deep dive on specific element
    - generate_locators: Get ranked locator strategies
    - suggest_step: Create a script step
    - validate_script: Check script for issues
    - diagnose_failure: Analyze why step failed
    - get_script: View current script
    - modify_script: Add/edit/remove steps

    Be concise but thorough. Focus on actionable advice."""

    async def start_session(self):
        options = ClaudeAgentOptions(
            system_prompt=self.SYSTEM_PROMPT,
            model="claude-sonnet-4-20250514",
            allowed_tools=[
                "mcp__studio__analyze_page",
                "mcp__studio__analyze_element",
                "mcp__studio__generate_locators",
                "mcp__studio__suggest_step",
                "mcp__studio__validate_script",
                "mcp__studio__diagnose_failure",
                "mcp__studio__get_script",
                "mcp__studio__modify_script",
            ]
        )
        self.client = ClaudeSDKClient(options=options)
        await self.client.connect()
```

### Conversation Flow

```python
async def chat(self, message: str) -> AsyncIterator[BackendMessage]:
    """Send message to Claude and stream responses."""

    # Enrich message with current context
    enriched = self._build_context_message(message)

    # Send to Claude
    await self.client.query(enriched)

    # Stream responses
    async for event in self.client.receive_response():
        if event.type == "text":
            yield BackendMessage(
                type=BackendMessageType.ASSISTANT_CHUNK,
                payload={"text": event.content}
            )

        elif event.type == "tool_use":
            # Execute tool and return result to Claude
            result = await self._execute_tool(event.name, event.input)
            yield BackendMessage(
                type=BackendMessageType.TOOL_RESULT,
                payload={"tool": event.name, "result": result}
            )
```

## MCP Tools Specification

### 1. analyze_page

**Purpose**: Understand the structure of the current page

**Input**:
```json
{
  "focus_area": "forms" | "buttons" | "navigation" | "all"
}
```

**Output**:
```json
{
  "url": "https://example.com/login",
  "title": "Login | Example",
  "forms": [
    {
      "id": "login-form",
      "action": "/auth",
      "method": "POST",
      "fields": [
        {"tag": "input", "type": "email", "name": "email", "required": true},
        {"tag": "input", "type": "password", "name": "password", "required": true}
      ]
    }
  ],
  "buttons": [
    {"tag": "button", "text": "Sign In", "type": "submit", "data_testid": "login-btn"}
  ],
  "detected_framework": "React"
}
```

**When Claude Uses It**:
- User asks about page structure
- Before suggesting locators
- When diagnosing navigation issues

---

### 2. analyze_element

**Purpose**: Deep analysis of the currently selected element

**Input**:
```json
{
  "include_siblings": true,
  "include_parent_chain": true
}
```

**Output**:
```json
{
  "element": {
    "tag": "button",
    "text": "Submit",
    "attributes": {
      "type": "submit",
      "class": "btn btn-primary",
      "data-testid": "submit-btn"
    }
  },
  "locators": [
    {
      "type": "test_id",
      "value": "submit-btn",
      "confidence": 0.95,
      "stability": "high",
      "reasoning": "Test ID attributes are stable across deployments"
    },
    {
      "type": "text",
      "value": "Submit",
      "confidence": 0.75,
      "stability": "medium",
      "reasoning": "Text may change with i18n"
    }
  ],
  "parent_context": "<form><button>Submit</button></form>",
  "stability_assessment": {
    "score": 4,
    "grade": "HIGH",
    "factors": ["Has test ID attribute (+3)", "Has semantic text (+1)"],
    "recommendation": "Element has stable attributes. Safe to automate."
  }
}
```

**When Claude Uses It**:
- User selects an element in recording mode
- User asks "how do I click this button?"
- Before generating step suggestions

---

### 3. generate_locators

**Purpose**: Generate ranked locator strategies for any element

**Input**:
```json
{
  "description": "the login button",
  "element_selector": "button[type='submit']"
}
```

**Output**:
```json
{
  "description": "the login button",
  "locators": [
    {
      "type": "test_id",
      "attribute": "data-testid",
      "value": "login-btn",
      "confidence": 0.95,
      "stability": "high",
      "reasoning": "Test ID is stable across deployments"
    },
    {
      "type": "aria_label",
      "value": "Sign in to your account",
      "confidence": 0.90,
      "stability": "high",
      "reasoning": "Accessibility labels are typically maintained"
    },
    {
      "type": "text",
      "value": "Sign In",
      "confidence": 0.75,
      "stability": "medium",
      "reasoning": "Text content may change with i18n or updates"
    },
    {
      "type": "selector",
      "value": "form button[type='submit']",
      "confidence": 0.70,
      "stability": "medium",
      "reasoning": "Structural selector depends on form structure"
    }
  ]
}
```

**When Claude Uses It**:
- User asks for locator options
- During recording to suggest best strategies
- When fixing failed locators

---

### 4. suggest_step

**Purpose**: Create a complete script step for an action

**Input**:
```json
{
  "action_type": "click",
  "description": "Click the login button",
  "value": null
}
```

**Output**:
```json
{
  "suggested_step": {
    "click": "Click the login button",
    "locators": [
      {"test_id": "login-btn", "confidence": 0.95, "stability": "high"},
      {"text": "Sign In", "confidence": 0.75, "stability": "medium"}
    ]
  }
}
```

**When Claude Uses It**:
- User confirms a recorded action
- User asks "add a step to click X"
- Building script from description

---

### 5. validate_script

**Purpose**: Check script for issues and warnings

**Input**:
```json
{}
```

**Output**:
```json
{
  "valid": true,
  "issues": [],
  "warnings": [
    "Step 3 (click) uses only low-stability locators",
    "Step 7 has no locators defined"
  ],
  "step_count": 12,
  "suggestions": [
    "Consider adding data-testid locator to step 3",
    "Add locator strategies to step 7"
  ]
}
```

**When Claude Uses It**:
- User asks to review the script
- Before test execution
- After major script changes

---

### 6. diagnose_failure

**Purpose**: Analyze why a step failed during execution

**Input**:
```json
{
  "step_index": 3,
  "error_message": "Element not found: button[type='submit']",
  "screenshot_available": true
}
```

**Output**:
```json
{
  "error_type": "element_not_found",
  "possible_causes": [
    "Element may not exist on current page",
    "Element may be dynamically loaded",
    "Selector may be incorrect or changed",
    "Element may be inside iframe"
  ],
  "suggested_fixes": [
    {
      "type": "add_wait",
      "description": "Add wait for element before interaction",
      "step_modification": {
        "wait": "Wait for submit button",
        "locator": {"text": "Submit"},
        "timeout": 10000
      }
    },
    {
      "type": "change_locator",
      "description": "Use more stable locator strategy",
      "new_locators": [
        {"test_id": "submit-btn"},
        {"aria_label": "Submit form"}
      ]
    }
  ],
  "page_state_hint": "Page appears to be showing an error modal"
}
```

**When Claude Uses It**:
- Automatically when step execution fails
- User asks "why did step X fail?"
- Debugging script issues

---

### 7. get_script

**Purpose**: Retrieve the current script being edited

**Input**:
```json
{
  "include_metadata": true
}
```

**Output**:
```json
{
  "script": {
    "name": "BT Broadband Checker",
    "start_url": "https://bt.com/broadband",
    "inputs": {
      "postcode": {"type": "string", "description": "UK postcode"}
    },
    "steps": [
      {"navigate": "https://bt.com/broadband"},
      {"fill": "Enter postcode", "value": "{{postcode}}", "locators": [...]},
      {"click": "Check availability", "locators": [...]}
    ]
  },
  "metadata": {
    "step_count": 3,
    "has_conditions": false,
    "variables_used": ["postcode"]
  }
}
```

**When Claude Uses It**:
- User asks about the script
- Before making suggestions
- Validating context

---

### 8. modify_script

**Purpose**: Add, edit, or remove steps from the script

**Input**:
```json
{
  "operation": "add",
  "step_index": 3,
  "step_data": {
    "click": "Click submit button",
    "locators": [
      {"test_id": "submit-btn", "confidence": 0.95}
    ]
  }
}
```

**Output**:
```json
{
  "success": true,
  "step_index": 3,
  "action": "added",
  "script_step_count": 4
}
```

**Operations**:
- `add` - Insert step at index (or append if null)
- `edit` - Replace step at index
- `remove` - Delete step at index

**When Claude Uses It**:
- User confirms a suggested step
- User asks "add a click step for X"
- Applying suggested fixes

## Context Management

### StudioContext Class

```python
@dataclass
class StudioContext:
    """All context available to the AI assistant"""

    # Current script being edited
    script: dict = field(default_factory=dict)

    # Page history (last N pages)
    page_history: list[PageContext] = field(default_factory=list)
    max_page_history: int = 5

    # Current page (always available)
    current_page: PageContext | None = None

    # Selected element details
    selected_element: dict | None = None

    # Recording state
    is_recording: bool = False
    recorded_actions: list[dict] = field(default_factory=list)

    # Execution state
    last_execution_result: dict | None = None
    failed_steps: list[dict] = field(default_factory=list)
```

### HTML Context Management

Large HTML pages are compressed before including in Claude's context:

```python
class HTMLContextManager:
    """Efficiently manage HTML for Claude's context window"""

    def prepare_page_context(self, html: str) -> dict:
        """
        Convert HTML to efficient representation:
        1. Strip scripts, styles, comments
        2. Extract forms, buttons, inputs
        3. Build structural tree
        4. Compress whitespace
        """

    def extract_focus_context(self, html: str, selector: str) -> dict:
        """
        Extract expanded context around selected element:
        - Element details
        - Parent chain
        - Sibling elements
        """
```

### Context Size Limits

| Context Type | Max Size | Strategy |
|--------------|----------|----------|
| Current page HTML | 50KB | Compression, structure extraction |
| Page history | 5 pages | Summaries only for older pages |
| Selected element | 5KB | Full detail with parent context |
| Script | Unlimited | Full script always included |
| Failed steps | 10 steps | Most recent failures |

## Interaction Patterns

### Pattern 1: Proactive Element Analysis (Recording Mode)

```
User clicks element in browser
        │
        ▼
UI sends ELEMENT_SELECTED message
        │
        ▼
Backend calls analyze_element tool
        │
        ▼
Claude receives element analysis
        │
        ▼
Claude generates locator suggestions
        │
        ▼
UI displays suggestion cards
        │
        ▼
User accepts/modifies and adds to script
```

### Pattern 2: Chat-Based Assistance

```
User: "How should I handle the address dropdown?"
        │
        ▼
Backend sends message with page context
        │
        ▼
Claude calls analyze_page tool
        │
        ▼
Claude identifies dropdown structure
        │
        ▼
Claude suggests approach with code example
        │
        ▼
UI displays response with actionable buttons
```

### Pattern 3: Failure Diagnosis

```
Step execution fails
        │
        ▼
Backend calls diagnose_failure tool
        │
        ▼
Claude analyzes error + page state
        │
        ▼
Claude identifies likely causes
        │
        ▼
Claude suggests specific fixes
        │
        ▼
UI displays fix options with "Apply" buttons
        │
        ▼
User clicks "Apply" → modify_script called
```

## Response Formatting

Claude's responses should be structured for easy UI rendering:

### Text Response
```
I analyzed the page and found 2 forms. The login form has...
```

### Suggestion Response
```json
{
  "type": "locator_suggestions",
  "for_element": "Submit button",
  "suggestions": [
    {"locator": {"test_id": "submit"}, "confidence": 0.95, "recommended": true},
    {"locator": {"text": "Submit"}, "confidence": 0.75}
  ]
}
```

### Fix Response
```json
{
  "type": "fix_suggestion",
  "problem": "Element not found",
  "fixes": [
    {
      "description": "Add wait before click",
      "apply_action": {"operation": "insert", "index": 3, "step": {...}}
    }
  ]
}
```

## Cost Optimization

### Strategies

1. **Context Pruning** - Only include relevant HTML sections
2. **Tool Batching** - Combine related tool calls when possible
3. **Caching** - Cache page analysis results
4. **Streaming** - Show results as they arrive, don't wait for full response

### Estimated Costs

| Interaction Type | Tokens (est.) | Cost (est.) |
|------------------|---------------|-------------|
| Simple question | 2K | $0.006 |
| Page analysis | 10K | $0.03 |
| Element + locators | 5K | $0.015 |
| Failure diagnosis | 8K | $0.024 |

Target: < $0.10 per script development session

## Error Handling

### Claude API Errors
- Retry with exponential backoff
- Fallback to cached suggestions
- Show user-friendly error message

### Tool Execution Errors
- Return error to Claude for handling
- Claude can try alternative approaches
- Log for debugging

### Context Overflow
- Summarize older page history
- Truncate HTML with priority preservation
- Warn user if context too large

## Testing Strategy

### Unit Tests
- Tool input/output validation
- Context management
- HTML parsing

### Integration Tests
- Full conversation flows
- Tool execution chains
- Error scenarios

### Manual Testing
- Real website recordings
- Edge case elements
- Multi-step scripts

---

**Version**: 1.0
**Created**: 2025-01-16
**Status**: Design Complete
