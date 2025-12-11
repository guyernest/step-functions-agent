# Navigation Studio

A desktop application for domain experts to create browser automation scripts without coding.

## Vision

Navigation Studio enables non-technical users to build robust browser automation workflows by:

1. **Recording interactions** - Click through websites and let AI suggest reliable locators
2. **AI-assisted development** - Claude helps analyze pages, diagnose failures, and improve scripts
3. **Progressive escalation** - Scripts automatically try fast methods first, falling back to AI vision only when needed
4. **Instant testing** - Run scripts immediately and see step-by-step execution

## Key Features

- **Embedded Browser** - Navigate real websites with Chromium (supports saved passwords)
- **Recording Mode** - Click elements to capture them with ranked locator strategies
- **AI Assistant** - Chat with Claude to get help building and debugging scripts
- **Visual Script Editor** - Build scripts visually without writing code
- **Test Runner** - Execute scripts with live feedback and screenshot capture
- **Script Format v2** - Concise, human-readable YAML format

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Navigation Studio (Tauri + React)          │
├────────────────────────┬────────────────────────────────┤
│   Embedded Browser     │     AI Assistant Panel         │
│   Visual Script Editor │     Test Runner                │
├────────────────────────┴────────────────────────────────┤
│                    Python Backend                        │
│   NavigationAssistant (Claude SDK) │ PlaywrightController│
└─────────────────────────────────────────────────────────┘
```

## Documentation

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](./ARCHITECTURE.md) | System architecture and design decisions |
| [AI_ASSISTANT_DESIGN.md](./AI_ASSISTANT_DESIGN.md) | Claude Agent SDK integration |
| [SCRIPT_FORMAT_V2.md](./SCRIPT_FORMAT_V2.md) | Script format specification |
| [MESSAGE_PROTOCOL.md](./MESSAGE_PROTOCOL.md) | WebSocket protocol between UI and backend |

## Technology Stack

### Frontend
- **Tauri 2.0** - Desktop framework (Rust-based)
- **React 18** - UI framework
- **Tailwind CSS** - Styling
- **Shadcn/ui** - Component library
- **Zustand** - State management

### Backend
- **Python 3.12** - Runtime
- **Claude Agent SDK** - AI assistant
- **Playwright** - Browser automation
- **FastAPI** - WebSocket server
- **BeautifulSoup4** - HTML parsing

## Script Example

```yaml
name: Login and Search
version: 2.0.0
start_url: https://example.com

inputs:
  username:
    type: string
    description: Login username

steps:
  - fill: Username field
    value: "{{username}}"
    locators:
      - test_id: username-input
      - form_field: username

  - fill: Password field
    value: "{{password}}"
    locators:
      - form_field: password

  - click: Sign In button
    locators:
      - test_id: login-btn
      - text: Sign In

  - wait: networkidle

  - screenshot: After login
```

## Project Structure

```
ui_studio/
├── README.md                    # This file
├── ARCHITECTURE.md              # System architecture
├── AI_ASSISTANT_DESIGN.md       # AI assistant design
├── SCRIPT_FORMAT_V2.md          # Script format spec
├── MESSAGE_PROTOCOL.md          # WebSocket protocol
│
├── frontend/                    # React/Tauri app (TODO)
│   ├── src/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── stores/
│   │   └── services/
│   └── package.json
│
├── backend/                     # Python backend (TODO)
│   ├── assistant/
│   ├── browser/
│   ├── executor/
│   ├── server/
│   └── requirements.txt
│
└── scripts/                     # Example scripts (TODO)
    └── examples/
```

## Development Status

| Phase | Status | Description |
|-------|--------|-------------|
| Design | ✅ Complete | Architecture and specifications |
| Frontend Setup | 🔲 Planned | Tauri + React scaffolding |
| Backend Setup | 🔲 Planned | Python server with Claude SDK |
| Recording Mode | 🔲 Planned | Element capture and locator generation |
| Script Editor | 🔲 Planned | Visual step management |
| Test Runner | 🔲 Planned | Script execution with feedback |
| AI Integration | 🔲 Planned | Full Claude assistant features |

## Getting Started

(Coming soon - Development setup instructions)

## Related Projects

- [Local Browser Agent](../lambda/tools/local-browser-agent/) - The runtime that executes scripts
- [Progressive Escalation Design](../lambda/tools/local-browser-agent/PROGRESSIVE_ESCALATION_DESIGN.md) - Escalation architecture

---

**Created**: 2025-01-16
**Status**: Design Phase
