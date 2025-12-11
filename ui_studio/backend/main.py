#!/usr/bin/env python3
"""
Navigation Studio Backend

FastAPI server with WebSocket support for real-time browser automation.
Integrates with existing local-browser-agent code for Playwright execution.
"""

import os
import sys
import json
import asyncio
import traceback
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add local-browser-agent to path
BROWSER_AGENT_PATH = Path(__file__).parent.parent.parent / "lambda/tools/local-browser-agent/python"
sys.path.insert(0, str(BROWSER_AGENT_PATH))

# Import browser agent modules
try:
    from browser_launch_config import get_launch_options, get_default_browser_channel
    from profile_manager import ProfileManager
    BROWSER_AGENT_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Browser agent modules not available: {e}")
    BROWSER_AGENT_AVAILABLE = False

# Import script executor
from studio_executor import StudioScriptExecutor

# Import AI assistant
try:
    from ai_assistant import AIAssistant, ANTHROPIC_AVAILABLE
except ImportError:
    ANTHROPIC_AVAILABLE = False
    AIAssistant = None

# Import settings store
try:
    from settings_store import get_settings_store, SettingsStore
    SETTINGS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Settings store not available: {e}")
    SETTINGS_AVAILABLE = False
    get_settings_store = None

# Active AI assistants (one per websocket connection)
ai_assistants: Dict[str, "AIAssistant"] = {}


# Connection manager for WebSocket clients
class ConnectionManager:
    """Manages WebSocket connections for real-time communication."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"Client connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print(f"Client disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: Dict[str, Any]):
        """Send message to all connected clients."""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error broadcasting to client: {e}")

    async def send_to(self, websocket: WebSocket, message: Dict[str, Any]):
        """Send message to specific client."""
        await websocket.send_json(message)


manager = ConnectionManager()


# Browser session manager
class BrowserSession:
    """Manages a Playwright browser session."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.is_recording = False
        self.recorded_steps = []
        self.current_url = None
        self.script_executor = None
        self.execution_callbacks = {}

    async def start(
        self,
        headless: bool = False,
        profile_name: Optional[str] = None,
        browser_channel: Optional[str] = None
    ):
        """Start browser session."""
        from playwright.async_api import async_playwright

        self.playwright = await async_playwright().start()

        # Get launch options from browser_launch_config
        if BROWSER_AGENT_AVAILABLE:
            launch_options = get_launch_options(
                headless=headless,
                browser_channel=browser_channel or get_default_browser_channel(),
                is_persistent_context=profile_name is not None,
                ignore_https_errors=True
            )
        else:
            launch_options = {"headless": headless}

        # Separate browser launch options from context options
        # ignore_https_errors is only valid for context, not browser.launch()
        context_only_options = ["ignore_https_errors"]
        browser_launch_options = {k: v for k, v in launch_options.items() if k not in context_only_options}
        context_options = {k: v for k, v in launch_options.items() if k in context_only_options}

        # Launch browser
        if profile_name:
            # Use persistent context with profile
            profile_manager = ProfileManager() if BROWSER_AGENT_AVAILABLE else None
            if profile_manager:
                profile_info = profile_manager.resolve_profile(profile_name)
                user_data_dir = profile_info.get("user_data_dir")
            else:
                user_data_dir = Path.home() / ".navigation-studio" / "profiles" / profile_name
                user_data_dir.mkdir(parents=True, exist_ok=True)

            # For persistent context, all options go together
            self.context = await self.playwright.chromium.launch_persistent_context(
                str(user_data_dir),
                **launch_options
            )
            self.page = self.context.pages[0] if self.context.pages else await self.context.new_page()
        else:
            # Ephemeral session - separate browser launch from context creation
            self.browser = await self.playwright.chromium.launch(**browser_launch_options)
            self.context = await self.browser.new_context(**context_options)
            self.page = await self.context.new_page()

        # Set up event listeners for recording
        await self._setup_event_listeners()

        return {"status": "started", "session_id": self.session_id}

    async def _setup_event_listeners(self):
        """Set up page event listeners for recording."""
        if not self.page:
            return

        # Listen for navigation events
        self.page.on("framenavigated", self._on_navigate)

    def _on_navigate(self, frame):
        """Handle navigation events."""
        if frame == self.page.main_frame:
            self.current_url = frame.url

    async def navigate(self, url: str) -> Dict[str, Any]:
        """Navigate to URL."""
        if not self.page:
            return {"error": "Browser not started"}

        try:
            await self.page.goto(url, wait_until="domcontentloaded")
            self.current_url = url

            if self.is_recording:
                self.recorded_steps.append({
                    "action": "navigate",
                    "url": url,
                    "timestamp": datetime.now().isoformat()
                })

            return {"status": "success", "url": url}
        except Exception as e:
            return {"error": str(e)}

    async def click(self, selector: str) -> Dict[str, Any]:
        """Click element by selector."""
        if not self.page:
            return {"error": "Browser not started"}

        try:
            await self.page.click(selector)

            if self.is_recording:
                self.recorded_steps.append({
                    "action": "click",
                    "locator": {"strategy": "selector", "value": selector},
                    "timestamp": datetime.now().isoformat()
                })

            return {"status": "success"}
        except Exception as e:
            return {"error": str(e)}

    async def fill(self, selector: str, value: str) -> Dict[str, Any]:
        """Fill input field."""
        if not self.page:
            return {"error": "Browser not started"}

        try:
            await self.page.fill(selector, value)

            if self.is_recording:
                self.recorded_steps.append({
                    "action": "fill",
                    "locator": {"strategy": "selector", "value": selector},
                    "value": value,
                    "timestamp": datetime.now().isoformat()
                })

            return {"status": "success"}
        except Exception as e:
            return {"error": str(e)}

    async def screenshot(self) -> Dict[str, Any]:
        """Take screenshot and return as base64."""
        if not self.page:
            return {"error": "Browser not started"}

        try:
            screenshot_bytes = await self.page.screenshot(type="png")
            import base64
            screenshot_b64 = base64.b64encode(screenshot_bytes).decode("utf-8")
            return {
                "status": "success",
                "screenshot": screenshot_b64,
                "url": self.current_url
            }
        except Exception as e:
            return {"error": str(e)}

    async def get_page_info(self) -> Dict[str, Any]:
        """Get current page information."""
        if not self.page:
            return {"error": "Browser not started"}

        try:
            title = await self.page.title()
            url = self.page.url
            return {
                "title": title,
                "url": url,
                "is_recording": self.is_recording
            }
        except Exception as e:
            return {"error": str(e)}

    def start_recording(self):
        """Start recording user interactions."""
        self.is_recording = True
        self.recorded_steps = []
        return {"status": "recording_started"}

    def stop_recording(self) -> Dict[str, Any]:
        """Stop recording and return recorded steps."""
        self.is_recording = False
        steps = self.recorded_steps.copy()
        return {
            "status": "recording_stopped",
            "steps": steps
        }

    async def close(self):
        """Close browser session."""
        if self.script_executor and self.script_executor.is_running:
            self.script_executor.stop()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def execute_script(
        self,
        script: Dict[str, Any],
        on_step_start=None,
        on_step_complete=None,
        on_screenshot=None,
        on_error=None
    ) -> Dict[str, Any]:
        """Execute a script with callbacks for progress reporting."""
        if not self.page:
            return {"error": "Browser not started"}

        self.script_executor = StudioScriptExecutor(
            page=self.page,
            on_step_start=on_step_start,
            on_step_complete=on_step_complete,
            on_screenshot=on_screenshot,
            on_error=on_error
        )

        return await self.script_executor.execute_script(script)

    async def execute_single_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single step."""
        if not self.page:
            return {"error": "Browser not started"}

        executor = StudioScriptExecutor(page=self.page)
        return await executor._execute_step(0, step)

    def pause_script(self):
        """Pause script execution."""
        if self.script_executor:
            self.script_executor.pause()
            return {"status": "paused"}
        return {"error": "No script running"}

    def resume_script(self):
        """Resume script execution."""
        if self.script_executor:
            self.script_executor.resume()
            return {"status": "resumed"}
        return {"error": "No script running"}

    def stop_script(self):
        """Stop script execution."""
        if self.script_executor:
            self.script_executor.stop()
            return {"status": "stopped"}
        return {"error": "No script running"}


# Active browser sessions
browser_sessions: Dict[str, BrowserSession] = {}


# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    print("Navigation Studio Backend starting...")
    yield
    # Cleanup: close all browser sessions
    print("Shutting down, closing browser sessions...")
    for session in browser_sessions.values():
        await session.close()
    browser_sessions.clear()


# FastAPI app
app = FastAPI(
    title="Navigation Studio Backend",
    description="WebSocket-based browser automation server",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:1420", "tauri://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for REST API
class StartSessionRequest(BaseModel):
    headless: bool = False
    profile_name: Optional[str] = None
    browser_channel: Optional[str] = None


class NavigateRequest(BaseModel):
    url: str


class ClickRequest(BaseModel):
    selector: str


class FillRequest(BaseModel):
    selector: str
    value: str


# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "browser_agent_available": BROWSER_AGENT_AVAILABLE,
        "ai_assistant_available": ANTHROPIC_AVAILABLE,
        "active_sessions": len(browser_sessions),
        "active_assistants": len(ai_assistants),
        "settings_available": SETTINGS_AVAILABLE,
        "api_key_configured": SETTINGS_AVAILABLE and get_settings_store().has_api_key() if get_settings_store else False
    }


# Settings API endpoints
class SettingsUpdateRequest(BaseModel):
    """Request model for updating settings."""
    anthropic_api_key: Optional[str] = None
    ai_model: Optional[str] = None
    backend_url: Optional[str] = None
    browser_profile: Optional[str] = None
    auto_analyze: Optional[bool] = None


@app.get("/api/settings")
async def get_settings():
    """Get current settings (sensitive values masked)."""
    if not SETTINGS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Settings store not available")

    store = get_settings_store()
    settings = store.get_all(include_sensitive=False)

    return {
        "status": "success",
        "settings": settings,
        "api_key_configured": store.has_api_key()
    }


@app.put("/api/settings")
async def update_settings(request: SettingsUpdateRequest):
    """Update settings."""
    if not SETTINGS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Settings store not available")

    store = get_settings_store()

    # Update only provided fields
    updates = {}
    if request.anthropic_api_key is not None:
        updates['anthropic_api_key'] = request.anthropic_api_key
    if request.ai_model is not None:
        updates['ai_model'] = request.ai_model
    if request.backend_url is not None:
        updates['backend_url'] = request.backend_url
    if request.browser_profile is not None:
        updates['browser_profile'] = request.browser_profile
    if request.auto_analyze is not None:
        updates['auto_analyze'] = request.auto_analyze

    store.update(updates)

    return {
        "status": "success",
        "message": "Settings updated",
        "api_key_configured": store.has_api_key()
    }


@app.post("/api/settings/test-api-key")
async def test_api_key():
    """Test if the configured API key is valid."""
    if not SETTINGS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Settings store not available")

    if not ANTHROPIC_AVAILABLE:
        raise HTTPException(status_code=503, detail="Anthropic SDK not available")

    store = get_settings_store()
    api_key = store.get('anthropic_api_key')

    if not api_key:
        return {"status": "error", "message": "No API key configured"}

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        # Make a minimal API call to test the key
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=10,
            messages=[{"role": "user", "content": "Hi"}]
        )
        return {"status": "success", "message": "API key is valid"}
    except anthropic.AuthenticationError:
        return {"status": "error", "message": "Invalid API key"}
    except Exception as e:
        return {"status": "error", "message": f"Error testing API key: {str(e)}"}


# REST API endpoints
@app.post("/api/sessions")
async def create_session(request: StartSessionRequest):
    """Create new browser session."""
    session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    session = BrowserSession(session_id)

    try:
        result = await session.start(
            headless=request.headless,
            profile_name=request.profile_name,
            browser_channel=request.browser_channel
        )
        browser_sessions[session_id] = session
        return {**result, "session_id": session_id}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """Close and delete browser session."""
    if session_id not in browser_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = browser_sessions.pop(session_id)
    await session.close()
    return {"status": "closed", "session_id": session_id}


@app.get("/api/sessions/{session_id}/screenshot")
async def get_screenshot(session_id: str):
    """Get screenshot from session."""
    if session_id not in browser_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = browser_sessions[session_id]
    return await session.screenshot()


# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time browser control."""
    await manager.connect(websocket)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()

            action = data.get("action")
            session_id = data.get("session_id")

            # Handle different actions
            if action == "start_session":
                # Create new browser session
                session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
                session = BrowserSession(session_id)

                try:
                    result = await session.start(
                        headless=data.get("headless", False),
                        profile_name=data.get("profile_name"),
                        browser_channel=data.get("browser_channel")
                    )
                    browser_sessions[session_id] = session
                    await manager.send_to(websocket, {
                        "type": "session_started",
                        "session_id": session_id,
                        **result
                    })
                except Exception as e:
                    await manager.send_to(websocket, {
                        "type": "error",
                        "error": str(e)
                    })

            elif action == "navigate":
                if session_id and session_id in browser_sessions:
                    session = browser_sessions[session_id]
                    result = await session.navigate(data.get("url", ""))
                    await manager.send_to(websocket, {
                        "type": "navigate_complete",
                        "session_id": session_id,
                        **result
                    })

            elif action == "click":
                if session_id and session_id in browser_sessions:
                    session = browser_sessions[session_id]
                    result = await session.click(data.get("selector", ""))
                    await manager.send_to(websocket, {
                        "type": "click_complete",
                        "session_id": session_id,
                        **result
                    })

            elif action == "fill":
                if session_id and session_id in browser_sessions:
                    session = browser_sessions[session_id]
                    result = await session.fill(
                        data.get("selector", ""),
                        data.get("value", "")
                    )
                    await manager.send_to(websocket, {
                        "type": "fill_complete",
                        "session_id": session_id,
                        **result
                    })

            elif action == "screenshot":
                if session_id and session_id in browser_sessions:
                    session = browser_sessions[session_id]
                    result = await session.screenshot()
                    await manager.send_to(websocket, {
                        "type": "screenshot",
                        "session_id": session_id,
                        **result
                    })

            elif action == "start_recording":
                if session_id and session_id in browser_sessions:
                    session = browser_sessions[session_id]
                    result = session.start_recording()
                    await manager.send_to(websocket, {
                        "type": "recording_status",
                        "session_id": session_id,
                        **result
                    })

            elif action == "stop_recording":
                if session_id and session_id in browser_sessions:
                    session = browser_sessions[session_id]
                    result = session.stop_recording()
                    await manager.send_to(websocket, {
                        "type": "recording_complete",
                        "session_id": session_id,
                        **result
                    })

            elif action == "get_page_info":
                if session_id and session_id in browser_sessions:
                    session = browser_sessions[session_id]
                    result = await session.get_page_info()
                    await manager.send_to(websocket, {
                        "type": "page_info",
                        "session_id": session_id,
                        **result
                    })

            elif action == "close_session":
                if session_id and session_id in browser_sessions:
                    session = browser_sessions.pop(session_id)
                    await session.close()
                    await manager.send_to(websocket, {
                        "type": "session_closed",
                        "session_id": session_id
                    })

            elif action == "ping":
                await manager.send_to(websocket, {"type": "pong"})

            # Script execution actions
            elif action == "execute_script":
                if session_id and session_id in browser_sessions:
                    session = browser_sessions[session_id]
                    script = data.get("script", {})

                    # Define callbacks that send WebSocket messages
                    async def on_step_start(step_info):
                        await manager.send_to(websocket, {
                            "type": "step_start",
                            "session_id": session_id,
                            **step_info
                        })

                    async def on_step_complete(step_info):
                        await manager.send_to(websocket, {
                            "type": "step_complete",
                            "session_id": session_id,
                            **step_info
                        })

                    async def on_screenshot(screenshot_b64):
                        await manager.send_to(websocket, {
                            "type": "screenshot",
                            "session_id": session_id,
                            "screenshot": screenshot_b64
                        })

                    async def on_error(error_info):
                        await manager.send_to(websocket, {
                            "type": "script_error",
                            "session_id": session_id,
                            **error_info
                        })

                    # Start execution in background task
                    await manager.send_to(websocket, {
                        "type": "script_started",
                        "session_id": session_id,
                        "script_name": script.get("name", "Unnamed")
                    })

                    result = await session.execute_script(
                        script,
                        on_step_start=on_step_start,
                        on_step_complete=on_step_complete,
                        on_screenshot=on_screenshot,
                        on_error=on_error
                    )

                    await manager.send_to(websocket, {
                        "type": "script_complete",
                        "session_id": session_id,
                        **result
                    })

            elif action == "execute_step":
                if session_id and session_id in browser_sessions:
                    session = browser_sessions[session_id]
                    step = data.get("step", {})
                    result = await session.execute_single_step(step)
                    await manager.send_to(websocket, {
                        "type": "step_result",
                        "session_id": session_id,
                        **result
                    })
                    # Send updated screenshot
                    screenshot_result = await session.screenshot()
                    if screenshot_result.get("screenshot"):
                        await manager.send_to(websocket, {
                            "type": "screenshot",
                            "session_id": session_id,
                            **screenshot_result
                        })

            elif action == "pause_script":
                if session_id and session_id in browser_sessions:
                    session = browser_sessions[session_id]
                    result = session.pause_script()
                    await manager.send_to(websocket, {
                        "type": "script_paused",
                        "session_id": session_id,
                        **result
                    })

            elif action == "resume_script":
                if session_id and session_id in browser_sessions:
                    session = browser_sessions[session_id]
                    result = session.resume_script()
                    await manager.send_to(websocket, {
                        "type": "script_resumed",
                        "session_id": session_id,
                        **result
                    })

            elif action == "stop_script":
                if session_id and session_id in browser_sessions:
                    session = browser_sessions[session_id]
                    result = session.stop_script()
                    await manager.send_to(websocket, {
                        "type": "script_stopped",
                        "session_id": session_id,
                        **result
                    })

            # AI Assistant actions
            elif action == "ai_chat":
                if not ANTHROPIC_AVAILABLE:
                    await manager.send_to(websocket, {
                        "type": "error",
                        "error": "AI assistant not available (anthropic package not installed)"
                    })
                    continue

                message = data.get("message", "")
                assistant_id = data.get("assistant_id", "default")

                # Get or create assistant for this connection
                if assistant_id not in ai_assistants:
                    try:
                        # Get API key from settings store or environment
                        api_key = None
                        model = "claude-sonnet-4-20250514"
                        if SETTINGS_AVAILABLE and get_settings_store:
                            store = get_settings_store()
                            api_key = store.get('anthropic_api_key')
                            model = store.get('ai_model', model)

                        ai_assistants[assistant_id] = AIAssistant(
                            api_key=api_key,
                            model=model,
                            on_tool_call=lambda tc: manager.send_to(websocket, {
                                "type": "ai_tool_call",
                                "assistant_id": assistant_id,
                                **tc
                            }),
                            on_message=lambda msg: manager.send_to(websocket, {
                                "type": "ai_message",
                                "assistant_id": assistant_id,
                                **msg
                            })
                        )
                    except Exception as e:
                        await manager.send_to(websocket, {
                            "type": "ai_error",
                            "error": f"Failed to create AI assistant: {e}"
                        })
                        continue

                assistant = ai_assistants[assistant_id]

                # Get browser session if available
                browser_session = None
                if session_id and session_id in browser_sessions:
                    browser_session = browser_sessions[session_id]

                await manager.send_to(websocket, {
                    "type": "ai_thinking",
                    "assistant_id": assistant_id
                })

                try:
                    result = await assistant.chat(message, browser_session)
                    await manager.send_to(websocket, {
                        "type": "ai_response",
                        "assistant_id": assistant_id,
                        "response": result["response"],
                        "tool_results": result["tool_results"],
                        "script_steps": result["script_steps"]
                    })
                    # If browser tools were used, send updated screenshot
                    if browser_session and any(
                        tr["tool"] in ["navigate", "click", "fill", "screenshot"]
                        for tr in result["tool_results"]
                    ):
                        screenshot_result = await browser_session.screenshot()
                        if screenshot_result.get("screenshot"):
                            await manager.send_to(websocket, {
                                "type": "screenshot",
                                "session_id": session_id,
                                **screenshot_result
                            })
                except Exception as e:
                    traceback.print_exc()
                    await manager.send_to(websocket, {
                        "type": "ai_error",
                        "assistant_id": assistant_id,
                        "error": str(e)
                    })

            elif action == "ai_get_script":
                assistant_id = data.get("assistant_id", "default")
                if assistant_id in ai_assistants:
                    script = ai_assistants[assistant_id].get_script()
                    await manager.send_to(websocket, {
                        "type": "ai_script",
                        "assistant_id": assistant_id,
                        "script": script
                    })

            elif action == "ai_clear_script":
                assistant_id = data.get("assistant_id", "default")
                if assistant_id in ai_assistants:
                    ai_assistants[assistant_id].clear_script()
                    await manager.send_to(websocket, {
                        "type": "ai_script_cleared",
                        "assistant_id": assistant_id
                    })

            elif action == "ai_clear_history":
                assistant_id = data.get("assistant_id", "default")
                if assistant_id in ai_assistants:
                    ai_assistants[assistant_id].clear_history()
                    await manager.send_to(websocket, {
                        "type": "ai_history_cleared",
                        "assistant_id": assistant_id
                    })

            else:
                await manager.send_to(websocket, {
                    "type": "error",
                    "error": f"Unknown action: {action}"
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        traceback.print_exc()
        manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8765)
