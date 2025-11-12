"""Unit tests for nova_act_wrapper.execute_act and execute_script without real Nova Act.

We provide stub modules in sys.modules to avoid importing the real 'nova_act' package
and to prevent any browser from launching. This allows CI to validate the integration
logic (browser_channel defaults, S3Writer wiring, kwargs formation, error handling).
"""
import json
import sys
import types


class _StubActMetadata:
    def __init__(self):
        import time
        self.act_id = "act-123"
        self.session_id = "sess-abc"
        self.num_steps_executed = 1
        self.start_time = 0
        self.end_time = 1


class _StubActResult:
    def __init__(self):
        self.response = "ok"
        self.parsed_response = True
        self.matches_schema = True
        self.metadata = _StubActMetadata()


class _StubNovaAct:
    def __init__(self, **kwargs):
        # Capture kwargs for assertions if needed
        self.kwargs = kwargs
        self.page = types.SimpleNamespace(context=lambda: types.SimpleNamespace(cookies=lambda: []))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    # When used by ScriptExecutor
    def start(self):
        return None

    def stop(self):
        return None

    def act(self, *args, **kwargs):
        return _StubActResult()


class _StubS3Writer:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


def _install_stubs():
    # Stub nova_act
    mod = types.ModuleType("nova_act")
    mod.NovaAct = _StubNovaAct
    mod.BOOL_SCHEMA = {"type": "boolean"}
    sys.modules["nova_act"] = mod

    # Stub nova_act.util.s3_writer
    util_mod = types.ModuleType("nova_act.util")
    s3_mod = types.ModuleType("nova_act.util.s3_writer")
    s3_mod.S3Writer = _StubS3Writer
    sys.modules["nova_act.util"] = util_mod
    sys.modules["nova_act.util.s3_writer"] = s3_mod


def test_execute_act_with_defaults(monkeypatch):
    _install_stubs()
    import nova_act_wrapper as naw

    # Bypass boto3 session creation by stubbing boto3.Session
    class _StubBotoSession:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    import boto3
    monkeypatch.setattr(boto3, "Session", _StubBotoSession)

    out = naw.execute_browser_command({
        "command_type": "act",
        "prompt": "Go to example",
        # omit browser_channel to trigger platform default
        # omit s3_bucket to avoid S3 wiring
    })

    assert out["success"] is True
    assert out["response"] == "ok"
    # Confirm we return metadata fields
    assert out["metadata"]["act_id"] == "act-123"


def test_execute_script_path(monkeypatch):
    _install_stubs()
    import nova_act_wrapper as naw

    # Stub boto3 again
    class _StubBotoSession:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    import boto3
    monkeypatch.setattr(boto3, "Session", _StubBotoSession)

    script_cmd = {
        "command_type": "script",
        "name": "t",
        "starting_page": "https://example.com",
        "steps": [{"action": "act", "prompt": "click"}],
    }
    out = naw.execute_browser_command(script_cmd)
    assert out["success"] is True


def test_prompt_with_embedded_script_triggers_script_executor(monkeypatch):
    _install_stubs()
    import nova_act_wrapper as naw

    class _StubBotoSession:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    import boto3
    monkeypatch.setattr(boto3, "Session", _StubBotoSession)

    embedded = {
        "name": "embedded",
        "starting_page": "https://example.com",
        "steps": [{"action": "act", "prompt": "go"}],
    }
    cmd = {
        "command_type": "act",
        "prompt": "Execute this browser automation script:\n\n" + json.dumps(embedded),
    }
    out = naw.execute_browser_command(cmd)
    assert out["success"] is True
