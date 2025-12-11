# Message Protocol Specification

## Overview

This document defines the WebSocket message protocol between the Navigation Studio frontend (React/Tauri) and the Python backend. The protocol supports real-time bidirectional communication for chat, events, and streaming responses.

## Connection

### WebSocket Endpoint

```
ws://localhost:8765/studio
```

### Connection Lifecycle

```
┌──────────┐                    ┌──────────┐
│ Frontend │                    │ Backend  │
└────┬─────┘                    └────┬─────┘
     │                               │
     │ WebSocket Connect             │
     │──────────────────────────────>│
     │                               │
     │ CONNECTION_ACK                │
     │<──────────────────────────────│
     │                               │
     │ START_SESSION                 │
     │──────────────────────────────>│
     │                               │
     │ SESSION_STARTED               │
     │<──────────────────────────────│
     │                               │
     │         ... messages ...      │
     │<─────────────────────────────>│
     │                               │
     │ END_SESSION                   │
     │──────────────────────────────>│
     │                               │
     │ SESSION_ENDED                 │
     │<──────────────────────────────│
     │                               │
     │ WebSocket Close               │
     │──────────────────────────────>│
```

## Message Format

All messages use JSON with this envelope:

```typescript
interface Message {
  type: string;           // Message type identifier
  payload: object;        // Type-specific payload
  correlationId: string;  // Request/response matching
  timestamp: number;      // Unix timestamp (ms)
}
```

## Message Types: Frontend → Backend

### Session Management

#### START_SESSION

Start a new AI assistant session.

```json
{
  "type": "START_SESSION",
  "payload": {
    "scriptPath": "/path/to/script.nav.yaml",  // Optional: load existing script
    "browserProfile": "default"                 // Browser profile to use
  },
  "correlationId": "sess_001",
  "timestamp": 1705420800000
}
```

#### END_SESSION

End the current session.

```json
{
  "type": "END_SESSION",
  "payload": {},
  "correlationId": "sess_002",
  "timestamp": 1705420900000
}
```

---

### Chat Interaction

#### CHAT_MESSAGE

Send a message to the AI assistant.

```json
{
  "type": "CHAT_MESSAGE",
  "payload": {
    "message": "How do I handle the address dropdown?",
    "includePageContext": true,   // Attach current page HTML
    "includeScript": true,        // Attach current script
    "attachments": []             // Future: file attachments
  },
  "correlationId": "chat_001",
  "timestamp": 1705420800000
}
```

---

### Browser Events

#### PAGE_CHANGED

Sent when browser navigates to a new page.

```json
{
  "type": "PAGE_CHANGED",
  "payload": {
    "url": "https://example.com/login",
    "title": "Login | Example",
    "html": "<html>...</html>",
    "meta": {
      "formsCount": 1,
      "buttonsCount": 3,
      "inputsCount": 2,
      "linksCount": 15
    }
  },
  "correlationId": "page_001",
  "timestamp": 1705420800000
}
```

#### ELEMENT_SELECTED

Sent when user clicks an element in recording mode.

```json
{
  "type": "ELEMENT_SELECTED",
  "payload": {
    "tag": "button",
    "text": "Submit",
    "attributes": {
      "type": "submit",
      "class": "btn btn-primary",
      "data-testid": "submit-btn",
      "aria-label": "Submit form"
    },
    "boundingBox": {
      "x": 100,
      "y": 200,
      "width": 80,
      "height": 32
    },
    "xpath": "/html/body/form/button[1]",
    "cssSelector": "form > button.btn-primary",
    "parentHtml": "<form><button>Submit</button></form>",
    "interactionType": "click"    // click | fill | select
  },
  "correlationId": "elem_001",
  "timestamp": 1705420800000
}
```

#### ELEMENT_HOVERED

Sent when user hovers over an element (for preview).

```json
{
  "type": "ELEMENT_HOVERED",
  "payload": {
    "tag": "input",
    "attributes": {
      "type": "email",
      "name": "email"
    },
    "boundingBox": {
      "x": 100,
      "y": 150,
      "width": 200,
      "height": 40
    }
  },
  "correlationId": "hover_001",
  "timestamp": 1705420800000
}
```

---

### Script Events

#### STEP_ADDED

Sent when user adds a step to the script.

```json
{
  "type": "STEP_ADDED",
  "payload": {
    "stepIndex": 3,
    "step": {
      "click": "Submit button",
      "locators": [
        {"test_id": "submit-btn"},
        {"text": "Submit"}
      ]
    }
  },
  "correlationId": "step_001",
  "timestamp": 1705420800000
}
```

#### STEP_MODIFIED

Sent when user modifies a step.

```json
{
  "type": "STEP_MODIFIED",
  "payload": {
    "stepIndex": 3,
    "oldStep": { "click": "Submit" },
    "newStep": {
      "click": "Submit button",
      "locators": [{"test_id": "submit-btn"}]
    }
  },
  "correlationId": "step_002",
  "timestamp": 1705420800000
}
```

#### STEP_REMOVED

Sent when user removes a step.

```json
{
  "type": "STEP_REMOVED",
  "payload": {
    "stepIndex": 3,
    "removedStep": { "click": "Submit" }
  },
  "correlationId": "step_003",
  "timestamp": 1705420800000
}
```

---

### Execution Events

#### RUN_SCRIPT

Request to execute the script.

```json
{
  "type": "RUN_SCRIPT",
  "payload": {
    "inputs": {
      "postcode": "SW1A 1AA",
      "buildingNumber": "10"
    },
    "startFromStep": 0,          // Optional: resume from step
    "stopAtStep": null,          // Optional: stop at step
    "slowMode": false            // Add delays for observation
  },
  "correlationId": "run_001",
  "timestamp": 1705420800000
}
```

#### STOP_EXECUTION

Request to stop script execution.

```json
{
  "type": "STOP_EXECUTION",
  "payload": {},
  "correlationId": "stop_001",
  "timestamp": 1705420800000
}
```

#### STEP_FAILED

Sent when a step fails during execution (triggers AI diagnosis).

```json
{
  "type": "STEP_FAILED",
  "payload": {
    "stepIndex": 3,
    "stepType": "click",
    "stepDescription": "Click Next button",
    "errorMessage": "Element not found: button[type='submit']",
    "errorType": "locator_failed",
    "attemptedLocators": [
      {"strategy": "selector", "value": "button[type='submit']", "result": "not_found"},
      {"strategy": "text", "value": "Next", "result": "not_found"}
    ],
    "pageUrl": "https://example.com/form",
    "pageHtml": "<html>...",
    "screenshotBase64": "iVBORw0KGgo..."
  },
  "correlationId": "fail_001",
  "timestamp": 1705420800000
}
```

---

### Explicit Requests

#### REQUEST_ANALYSIS

Request AI to analyze the current page.

```json
{
  "type": "REQUEST_ANALYSIS",
  "payload": {
    "focusArea": "forms",         // forms | buttons | navigation | all
    "question": "What forms are on this page?"
  },
  "correlationId": "analyze_001",
  "timestamp": 1705420800000
}
```

#### REQUEST_LOCATORS

Request locator suggestions for selected element.

```json
{
  "type": "REQUEST_LOCATORS",
  "payload": {
    "description": "the submit button",
    "elementSelector": "button[type='submit']"
  },
  "correlationId": "loc_001",
  "timestamp": 1705420800000
}
```

#### REQUEST_STEP_SUGGESTION

Request AI to suggest a step.

```json
{
  "type": "REQUEST_STEP_SUGGESTION",
  "payload": {
    "actionType": "click",
    "description": "Click the login button"
  },
  "correlationId": "suggest_001",
  "timestamp": 1705420800000
}
```

---

## Message Types: Backend → Frontend

### Session Responses

#### SESSION_STARTED

Confirms session started successfully.

```json
{
  "type": "SESSION_STARTED",
  "payload": {
    "sessionId": "sess_abc123",
    "browserReady": true,
    "scriptLoaded": true,
    "scriptName": "BT Broadband Checker"
  },
  "correlationId": "sess_001",
  "timestamp": 1705420800100
}
```

#### SESSION_ENDED

Confirms session ended.

```json
{
  "type": "SESSION_ENDED",
  "payload": {
    "sessionId": "sess_abc123",
    "reason": "user_requested"
  },
  "correlationId": "sess_002",
  "timestamp": 1705420900100
}
```

---

### Assistant Responses (Streaming)

#### ASSISTANT_THINKING

Indicates Claude is processing.

```json
{
  "type": "ASSISTANT_THINKING",
  "payload": {
    "status": "analyzing_page"    // analyzing_page | generating_locators | diagnosing_error
  },
  "correlationId": "chat_001",
  "timestamp": 1705420800100
}
```

#### ASSISTANT_CHUNK

Streaming text chunk from Claude.

```json
{
  "type": "ASSISTANT_CHUNK",
  "payload": {
    "text": "I can see the page has a form with ",
    "chunkIndex": 0
  },
  "correlationId": "chat_001",
  "timestamp": 1705420800150
}
```

#### ASSISTANT_COMPLETE

Indicates Claude finished responding.

```json
{
  "type": "ASSISTANT_COMPLETE",
  "payload": {
    "totalChunks": 5,
    "totalTokens": 250
  },
  "correlationId": "chat_001",
  "timestamp": 1705420801000
}
```

---

### Tool Activity

#### TOOL_STARTED

Claude is using a tool.

```json
{
  "type": "TOOL_STARTED",
  "payload": {
    "toolName": "analyze_page",
    "toolArgs": {
      "focusArea": "forms"
    }
  },
  "correlationId": "chat_001",
  "timestamp": 1705420800200
}
```

#### TOOL_RESULT

Tool execution completed.

```json
{
  "type": "TOOL_RESULT",
  "payload": {
    "toolName": "analyze_page",
    "result": {
      "forms": [
        {
          "id": "login-form",
          "fields": [
            {"name": "email", "type": "email"},
            {"name": "password", "type": "password"}
          ]
        }
      ],
      "detectedFramework": "React"
    },
    "durationMs": 150
  },
  "correlationId": "chat_001",
  "timestamp": 1705420800350
}
```

---

### Suggestions

#### LOCATOR_SUGGESTION

Locator options for an element.

```json
{
  "type": "LOCATOR_SUGGESTION",
  "payload": {
    "forElement": "Submit button",
    "locators": [
      {
        "type": "test_id",
        "value": "submit-btn",
        "confidence": 0.95,
        "stability": "high",
        "reasoning": "data-testid attribute is stable across deployments"
      },
      {
        "type": "text",
        "value": "Submit",
        "confidence": 0.75,
        "stability": "medium",
        "reasoning": "Text may change with i18n"
      },
      {
        "type": "selector",
        "value": "form button[type='submit']",
        "confidence": 0.70,
        "stability": "medium",
        "reasoning": "Depends on form structure"
      }
    ],
    "recommendedIndex": 0
  },
  "correlationId": "elem_001",
  "timestamp": 1705420800500
}
```

#### STEP_SUGGESTION

Suggested script step.

```json
{
  "type": "STEP_SUGGESTION",
  "payload": {
    "suggestedStep": {
      "click": "Submit the form",
      "locators": [
        {"test_id": "submit-btn", "confidence": 0.95, "stability": "high"},
        {"text": "Submit", "confidence": 0.75, "stability": "medium"}
      ]
    },
    "reasoning": "Using test_id as primary locator for stability"
  },
  "correlationId": "suggest_001",
  "timestamp": 1705420800500
}
```

#### SCRIPT_MODIFICATION

Claude suggests/makes a script change.

```json
{
  "type": "SCRIPT_MODIFICATION",
  "payload": {
    "action": "add_step",         // add_step | edit_step | remove_step
    "stepIndex": 4,
    "stepData": {
      "click": "Submit form",
      "locators": [
        {"test_id": "submit-btn"}
      ]
    },
    "reasoning": "Added submit button click with stable test_id locator",
    "autoApply": false            // If true, already applied
  },
  "correlationId": "chat_001",
  "timestamp": 1705420800500
}
```

#### FIX_SUGGESTION

Suggested fix for a failed step.

```json
{
  "type": "FIX_SUGGESTION",
  "payload": {
    "stepIndex": 3,
    "problem": "Element not found",
    "diagnosis": {
      "errorType": "element_not_found",
      "possibleCauses": [
        "Element may be dynamically loaded",
        "Selector may have changed"
      ]
    },
    "fixes": [
      {
        "type": "add_wait",
        "description": "Add wait for element before click",
        "modification": {
          "action": "insert_before",
          "stepIndex": 3,
          "step": {
            "wait": {
              "visible": "button[type='submit']",
              "timeout": 10000
            }
          }
        }
      },
      {
        "type": "change_locator",
        "description": "Use more stable locator",
        "modification": {
          "action": "edit_step",
          "stepIndex": 3,
          "step": {
            "click": "Submit button",
            "locators": [
              {"test_id": "submit-btn"},
              {"aria_label": "Submit form"}
            ]
          }
        }
      }
    ]
  },
  "correlationId": "fail_001",
  "timestamp": 1705420800500
}
```

---

### Execution Updates

#### EXECUTION_STARTED

Script execution began.

```json
{
  "type": "EXECUTION_STARTED",
  "payload": {
    "executionId": "exec_001",
    "totalSteps": 12,
    "inputs": {
      "postcode": "SW1A 1AA"
    }
  },
  "correlationId": "run_001",
  "timestamp": 1705420800000
}
```

#### STEP_STARTED

A step is about to execute.

```json
{
  "type": "STEP_STARTED",
  "payload": {
    "stepIndex": 3,
    "stepType": "click",
    "stepDescription": "Click submit button"
  },
  "correlationId": "run_001",
  "timestamp": 1705420801000
}
```

#### STEP_COMPLETED

A step completed successfully.

```json
{
  "type": "STEP_COMPLETED",
  "payload": {
    "stepIndex": 3,
    "stepType": "click",
    "durationMs": 250,
    "escalationLevel": 0,         // 0=first locator, 1=second, etc.
    "locatorUsed": {"test_id": "submit-btn"},
    "screenshotBase64": "iVBORw0KGgo..."
  },
  "correlationId": "run_001",
  "timestamp": 1705420801250
}
```

#### EXECUTION_COMPLETED

Script finished executing.

```json
{
  "type": "EXECUTION_COMPLETED",
  "payload": {
    "executionId": "exec_001",
    "success": true,
    "stepsCompleted": 12,
    "stepsFailed": 0,
    "totalDurationMs": 15000,
    "extractedData": {
      "packages": [...]
    },
    "escalationStats": {
      "level0": 10,
      "level1": 1,
      "level2": 1,
      "visionCalls": 1,
      "estimatedCost": 0.01
    }
  },
  "correlationId": "run_001",
  "timestamp": 1705420815000
}
```

#### EXECUTION_FAILED

Script execution failed.

```json
{
  "type": "EXECUTION_FAILED",
  "payload": {
    "executionId": "exec_001",
    "failedAtStep": 7,
    "error": "Element not found after all escalation attempts",
    "stepsCompleted": 6,
    "screenshotBase64": "iVBORw0KGgo..."
  },
  "correlationId": "run_001",
  "timestamp": 1705420810000
}
```

#### EXECUTION_STOPPED

Script execution was stopped by user.

```json
{
  "type": "EXECUTION_STOPPED",
  "payload": {
    "executionId": "exec_001",
    "stoppedAtStep": 5,
    "stepsCompleted": 5
  },
  "correlationId": "stop_001",
  "timestamp": 1705420805000
}
```

---

### Error Messages

#### ERROR

General error message.

```json
{
  "type": "ERROR",
  "payload": {
    "code": "BROWSER_NOT_READY",
    "message": "Browser is not ready. Please wait...",
    "recoverable": true,
    "details": {}
  },
  "correlationId": "chat_001",
  "timestamp": 1705420800000
}
```

### Error Codes

| Code | Description | Recoverable |
|------|-------------|-------------|
| `SESSION_NOT_STARTED` | No active session | Yes |
| `BROWSER_NOT_READY` | Browser not initialized | Yes |
| `CLAUDE_API_ERROR` | Claude API call failed | Yes (retry) |
| `CLAUDE_RATE_LIMITED` | Rate limited by Claude | Yes (wait) |
| `SCRIPT_INVALID` | Script validation failed | Yes |
| `EXECUTION_TIMEOUT` | Step timed out | Yes |
| `INTERNAL_ERROR` | Unexpected error | Maybe |

---

## Correlation ID Usage

Every request includes a `correlationId`. All related responses include the same ID.

```
Frontend                          Backend
   │                                 │
   │ CHAT_MESSAGE (corr: "chat_001") │
   │────────────────────────────────>│
   │                                 │
   │ ASSISTANT_THINKING (chat_001)   │
   │<────────────────────────────────│
   │                                 │
   │ TOOL_STARTED (chat_001)         │
   │<────────────────────────────────│
   │                                 │
   │ TOOL_RESULT (chat_001)          │
   │<────────────────────────────────│
   │                                 │
   │ ASSISTANT_CHUNK (chat_001)      │
   │<────────────────────────────────│
   │                                 │
   │ ASSISTANT_COMPLETE (chat_001)   │
   │<────────────────────────────────│
```

## TypeScript Types

```typescript
// Message envelope
interface Message<T = unknown> {
  type: string;
  payload: T;
  correlationId: string;
  timestamp: number;
}

// Frontend → Backend message types
type UIMessageType =
  | 'START_SESSION'
  | 'END_SESSION'
  | 'CHAT_MESSAGE'
  | 'PAGE_CHANGED'
  | 'ELEMENT_SELECTED'
  | 'ELEMENT_HOVERED'
  | 'STEP_ADDED'
  | 'STEP_MODIFIED'
  | 'STEP_REMOVED'
  | 'RUN_SCRIPT'
  | 'STOP_EXECUTION'
  | 'STEP_FAILED'
  | 'REQUEST_ANALYSIS'
  | 'REQUEST_LOCATORS'
  | 'REQUEST_STEP_SUGGESTION';

// Backend → Frontend message types
type BackendMessageType =
  | 'SESSION_STARTED'
  | 'SESSION_ENDED'
  | 'ASSISTANT_THINKING'
  | 'ASSISTANT_CHUNK'
  | 'ASSISTANT_COMPLETE'
  | 'TOOL_STARTED'
  | 'TOOL_RESULT'
  | 'LOCATOR_SUGGESTION'
  | 'STEP_SUGGESTION'
  | 'SCRIPT_MODIFICATION'
  | 'FIX_SUGGESTION'
  | 'EXECUTION_STARTED'
  | 'STEP_STARTED'
  | 'STEP_COMPLETED'
  | 'EXECUTION_COMPLETED'
  | 'EXECUTION_FAILED'
  | 'EXECUTION_STOPPED'
  | 'ERROR';

// Specific payload types
interface ChatMessagePayload {
  message: string;
  includePageContext?: boolean;
  includeScript?: boolean;
}

interface ElementSelectedPayload {
  tag: string;
  text: string;
  attributes: Record<string, string>;
  boundingBox: { x: number; y: number; width: number; height: number };
  xpath: string;
  cssSelector: string;
  parentHtml: string;
  interactionType: 'click' | 'fill' | 'select';
}

interface LocatorSuggestionPayload {
  forElement: string;
  locators: Array<{
    type: string;
    value: string;
    confidence: number;
    stability: 'high' | 'medium' | 'low';
    reasoning: string;
  }>;
  recommendedIndex: number;
}
```

## Python Types

```python
from enum import Enum
from dataclasses import dataclass
from typing import Any, Optional

class UIMessageType(str, Enum):
    START_SESSION = "START_SESSION"
    END_SESSION = "END_SESSION"
    CHAT_MESSAGE = "CHAT_MESSAGE"
    PAGE_CHANGED = "PAGE_CHANGED"
    ELEMENT_SELECTED = "ELEMENT_SELECTED"
    # ... etc

class BackendMessageType(str, Enum):
    SESSION_STARTED = "SESSION_STARTED"
    ASSISTANT_CHUNK = "ASSISTANT_CHUNK"
    LOCATOR_SUGGESTION = "LOCATOR_SUGGESTION"
    # ... etc

@dataclass
class Message:
    type: str
    payload: dict[str, Any]
    correlation_id: str
    timestamp: int

@dataclass
class UIMessage(Message):
    pass

@dataclass
class BackendMessage(Message):
    pass
```

---

**Version**: 1.0
**Created**: 2025-01-16
**Status**: Specification Complete
