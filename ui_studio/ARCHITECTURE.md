# Navigation Studio Architecture

## Overview

Navigation Studio is a desktop application for domain experts to create browser automation scripts without coding. It provides an embedded browser with recording capabilities, visual script editing, and an AI assistant powered by Claude Agent SDK.

## Goals

1. **Simplify script creation** - Domain experts create scripts by interacting with websites, not writing code
2. **Intelligent locator generation** - AI analyzes elements and suggests stable automation strategies
3. **Progressive escalation** - Scripts try cheap methods first (Playwright), escalate to vision AI only when needed
4. **Real-time feedback** - Test scripts immediately with clear error diagnosis

## Non-Goals

- Full IDE features (syntax highlighting, debugging breakpoints)
- Visual programming with drag-and-drop flowcharts
- Multi-user collaboration features (v1)
- Cloud deployment (desktop-first)

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Navigation Studio Desktop App                         │
│                              (Tauri + React)                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────────────────┐    ┌─────────────────────────────────┐  │
│  │      Embedded Browser          │    │      AI Assistant Panel         │  │
│  │      ────────────────          │    │      ─────────────────          │  │
│  │                                │    │                                 │  │
│  │  • Chromium via Playwright     │    │  • Chat interface               │  │
│  │  • Element overlay/highlight   │    │  • Context display              │  │
│  │  • Recording mode capture      │    │  • Suggestion cards             │  │
│  │  • Page state inspection       │    │  • Tool activity indicator      │  │
│  │                                │    │                                 │  │
│  └────────────────────────────────┘    └─────────────────────────────────┘  │
│                                                                              │
│  ┌────────────────────────────────┐    ┌─────────────────────────────────┐  │
│  │      Script Editor             │    │      Test Runner                │  │
│  │      ─────────────             │    │      ───────────                │  │
│  │                                │    │                                 │  │
│  │  • Visual step list            │    │  • Step-by-step execution       │  │
│  │  • Locator configuration       │    │  • Screenshot capture           │  │
│  │  • Condition builder           │    │  • Error highlighting           │  │
│  │  • Variable management         │    │  • Execution timeline           │  │
│  │                                │    │                                 │  │
│  └────────────────────────────────┘    └─────────────────────────────────┘  │
│                                                                              │
├──────────────────────────────────────┬──────────────────────────────────────┤
│           Frontend (React/TS)        │         Backend (Python)             │
├──────────────────────────────────────┼──────────────────────────────────────┤
│                                      │                                      │
│  • UI Components (Shadcn/Radix)      │  • NavigationAssistant               │
│  • State Management (Zustand)        │    (Claude Agent SDK)                │
│  • WebSocket Client                  │  • HTMLContextManager                │
│  • Script YAML Editor                │  • PlaywrightController              │
│  • Recording State Machine           │  • ScriptExecutor                    │
│                                      │  • WebSocket Server                  │
│                                      │                                      │
└──────────────────────────────────────┴──────────────────────────────────────┘
                                       │
                                       ▼
                          ┌─────────────────────────┐
                          │    External Services    │
                          ├─────────────────────────┤
                          │ • Claude API (Anthropic)│
                          │ • Target Websites       │
                          │ • Local File System     │
                          └─────────────────────────┘
```

## Technology Stack

### Frontend
| Component | Technology | Rationale |
|-----------|------------|-----------|
| Desktop Framework | Tauri 2.0 | Lightweight, Rust-based, native performance |
| UI Framework | React 18 | Component model, ecosystem, team familiarity |
| Styling | Tailwind CSS | Utility-first, rapid development |
| Components | Shadcn/ui | Accessible, customizable, no lock-in |
| State | Zustand | Simple, no boilerplate, good DevTools |
| Editor | Monaco (optional) | For raw YAML editing mode |

### Backend
| Component | Technology | Rationale |
|-----------|------------|-----------|
| Language | Python 3.12 | AI ecosystem, existing codebase |
| AI Client | Claude Agent SDK | Official SDK, conversation management |
| Browser | Playwright | Best-in-class automation, async support |
| Server | FastAPI + WebSockets | Async, type hints, auto docs |
| HTML Parsing | BeautifulSoup4 | Robust, forgiving parser |

### Communication
| Protocol | Use Case |
|----------|----------|
| WebSocket | Real-time UI ↔ Backend (chat, events) |
| HTTP/REST | Script CRUD, configuration |
| IPC (Tauri) | Native file dialogs, system integration |

## Module Breakdown

### Frontend Modules

```
src/
├── components/
│   ├── browser/
│   │   ├── EmbeddedBrowser.tsx      # Playwright browser view
│   │   ├── ElementOverlay.tsx       # Highlight selected elements
│   │   ├── RecordingIndicator.tsx   # Recording mode status
│   │   └── PageInfoBar.tsx          # URL, title, status
│   │
│   ├── assistant/
│   │   ├── AssistantPanel.tsx       # Main AI panel
│   │   ├── ChatMessage.tsx          # Message bubbles
│   │   ├── SuggestionCard.tsx       # Locator/step suggestions
│   │   ├── ToolActivity.tsx         # Shows when Claude uses tools
│   │   └── ContextDisplay.tsx       # Shows current context
│   │
│   ├── editor/
│   │   ├── ScriptEditor.tsx         # Main editor container
│   │   ├── StepList.tsx             # Visual step list
│   │   ├── StepCard.tsx             # Individual step display
│   │   ├── LocatorEditor.tsx        # Edit locator strategies
│   │   ├── ConditionBuilder.tsx     # Build if/switch conditions
│   │   └── VariablePanel.tsx        # Script inputs/variables
│   │
│   └── runner/
│       ├── TestRunner.tsx           # Execution controls
│       ├── ExecutionTimeline.tsx    # Step-by-step progress
│       ├── ScreenshotViewer.tsx     # View captured screenshots
│       └── ErrorDetails.tsx         # Failure diagnosis display
│
├── hooks/
│   ├── useAssistant.ts              # AI assistant connection
│   ├── useBrowser.ts                # Browser control
│   ├── useRecording.ts              # Recording mode state
│   └── useScript.ts                 # Script state management
│
├── services/
│   ├── websocket.ts                 # WebSocket client
│   ├── scriptStorage.ts             # Local script persistence
│   └── api.ts                       # REST API client
│
├── stores/
│   ├── scriptStore.ts               # Current script state
│   ├── browserStore.ts              # Browser/page state
│   ├── assistantStore.ts            # Chat history, suggestions
│   └── executionStore.ts            # Test run state
│
└── types/
    ├── script.ts                    # Script v2 types
    ├── messages.ts                  # WebSocket message types
    └── assistant.ts                 # AI response types
```

### Backend Modules

```
backend/
├── assistant/
│   ├── __init__.py
│   ├── navigation_assistant.py      # Main Claude SDK client
│   ├── tools.py                     # MCP tool definitions
│   ├── context.py                   # StudioContext management
│   └── html_context.py              # HTMLContextManager
│
├── browser/
│   ├── __init__.py
│   ├── controller.py                # PlaywrightController
│   ├── recorder.py                  # Recording mode logic
│   └── element_analyzer.py          # Element inspection
│
├── executor/
│   ├── __init__.py
│   ├── script_executor.py           # Run scripts
│   ├── step_handlers.py             # Individual step execution
│   └── escalation.py                # Progressive escalation logic
│
├── server/
│   ├── __init__.py
│   ├── main.py                      # FastAPI app entry
│   ├── websocket.py                 # WebSocket handlers
│   ├── routes.py                    # REST endpoints
│   └── messages.py                  # Message type definitions
│
├── script/
│   ├── __init__.py
│   ├── parser.py                    # Parse v2 script format
│   ├── validator.py                 # Validate script structure
│   └── migrator.py                  # Convert v1 → v2 format
│
└── utils/
    ├── __init__.py
    ├── locator_generator.py         # Generate locator strategies
    └── stability_scorer.py          # Score element stability
```

## Data Flow

### 1. Recording Mode Flow

```
User clicks element in browser
        │
        ▼
┌───────────────────┐
│ Browser captures  │
│ click event +     │
│ element details   │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ Frontend sends    │
│ ELEMENT_SELECTED  │
│ via WebSocket     │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ Backend analyzes  │
│ element, generates│
│ locator strategies│
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ AI Assistant      │
│ reviews & ranks   │
│ locators          │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ LOCATOR_SUGGESTION│
│ sent to frontend  │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ User confirms or  │
│ modifies locators │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ Step added to     │
│ script            │
└───────────────────┘
```

### 2. Test Execution Flow

```
User clicks "Run Test"
        │
        ▼
┌───────────────────┐
│ Frontend sends    │
│ RUN_SCRIPT        │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ ScriptExecutor    │
│ starts execution  │
└─────────┬─────────┘
          │
          ▼
┌─────────────────────────────────────┐
│ For each step:                      │
│                                     │
│  1. STEP_STARTED → Frontend         │
│  2. Execute with escalation chain   │
│  3. STEP_COMPLETED or STEP_FAILED   │
│  4. Screenshot captured             │
│                                     │
└─────────┬───────────────────────────┘
          │
          ▼ (on failure)
┌───────────────────┐
│ AI diagnoses      │
│ failure cause     │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ Suggestions sent  │
│ to frontend       │
└───────────────────┘
```

## Key Design Decisions

### 1. Desktop App vs Web App

**Decision**: Desktop (Tauri)

**Rationale**:
- Browser automation requires system-level access
- Password manager integration needs native browser profiles
- File system access for scripts without cloud dependency
- Better performance for embedded browser

### 2. Python Backend vs Node.js

**Decision**: Python

**Rationale**:
- Claude Agent SDK is Python-native
- Existing browser automation code is Python/Playwright
- AI/ML ecosystem (BeautifulSoup, future vision processing)
- Team expertise

### 3. WebSocket vs REST for Real-time

**Decision**: WebSocket for events, REST for CRUD

**Rationale**:
- WebSocket: Chat streaming, execution events, page changes
- REST: Script save/load, configuration, simpler operations

### 4. Script Format: YAML vs JSON

**Decision**: YAML with JSON support

**Rationale**:
- YAML more readable for humans
- JSON for machine processing / API
- Both can represent same structure

### 5. Embedded Browser: Electron Webview vs Playwright

**Decision**: Playwright browser connected to UI

**Rationale**:
- Playwright provides automation API we need
- Can use real Chrome profiles (password managers)
- Consistent with execution environment
- Screenshots and element inspection built-in

## Security Considerations

### Credentials
- Scripts reference credentials by variable name, not value
- Credentials stored in secure local store (OS keychain)
- Browser profiles with saved passwords used for authentication
- No credentials transmitted to Claude API

### AI Context
- HTML sent to Claude is stripped of sensitive data patterns
- Screenshots NOT sent to Claude by default (user opt-in)
- Local LLM option for sensitive environments (future)

### Script Storage
- Scripts stored locally by default
- Optional encryption for sensitive scripts
- No automatic cloud sync

## Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| App startup | < 3s | Including backend |
| Page load in browser | < 2s | After navigation |
| Recording latency | < 200ms | Click to locator suggestion |
| AI response start | < 1s | Time to first token |
| Script execution | Varies | Depends on target site |

## Future Considerations

### Phase 2
- Extraction mode with vision AI
- Evaluation framework integration
- Script versioning and diff

### Phase 3
- Team sharing (local network)
- Script templates library
- Custom locator strategies

### Phase 4
- Cloud deployment option
- Multi-browser support (Firefox, Safari)
- Mobile browser automation

## Related Documents

- [AI_ASSISTANT_DESIGN.md](./AI_ASSISTANT_DESIGN.md) - Claude SDK integration
- [SCRIPT_FORMAT_V2.md](./SCRIPT_FORMAT_V2.md) - Script specification
- [MESSAGE_PROTOCOL.md](./MESSAGE_PROTOCOL.md) - WebSocket protocol
- [UI_COMPONENTS.md](./UI_COMPONENTS.md) - Component specifications

---

**Version**: 1.0
**Created**: 2025-01-16
**Status**: Design Complete
