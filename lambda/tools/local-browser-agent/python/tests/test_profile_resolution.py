import os
from pathlib import Path


def test_create_and_resolve_by_name(tmp_path, monkeypatch):
    monkeypatch.setenv("BROWSER_AGENT_PROFILES_DIR", str(tmp_path / "profiles"))
    from profile_manager import ProfileManager

    pm = ProfileManager()
    pm.create_profile("acct_prod", tags=["banking", "prod"], description="Prod account")

    resolved = pm.resolve_profile({"profile_name": "acct_prod"}, verbose=False)
    assert resolved
    assert resolved["name"] == "acct_prod"


def test_resolve_by_tags_and_usage(tmp_path, monkeypatch):
    monkeypatch.setenv("BROWSER_AGENT_PROFILES_DIR", str(tmp_path / "profiles"))
    from profile_manager import ProfileManager

    pm = ProfileManager()
    pm.create_profile("p1", tags=["banking", "prod"])  # older
    pm.create_profile("p2", tags=["banking", "prod"])  # newer

    # Simulate usage to order by last_used
    pm.update_profile_usage("p2")

    resolved = pm.resolve_profile({"required_tags": ["banking", "prod"]}, verbose=False)
    assert resolved
    assert resolved["name"] == "p2"  # most recently used


def test_resolve_temp_allowed(tmp_path, monkeypatch):
    monkeypatch.setenv("BROWSER_AGENT_PROFILES_DIR", str(tmp_path / "profiles"))
    from profile_manager import ProfileManager

    pm = ProfileManager()

    # No profiles created; allow temp
    resolved = pm.resolve_profile({"required_tags": ["missing"], "allow_temp_profile": True}, verbose=False)
    assert resolved is None


def test_resolve_error_when_disallowed(tmp_path, monkeypatch):
    monkeypatch.setenv("BROWSER_AGENT_PROFILES_DIR", str(tmp_path / "profiles"))
    from profile_manager import ProfileManager

    pm = ProfileManager()

    try:
        pm.resolve_profile({"required_tags": ["missing"], "allow_temp_profile": False}, verbose=False)
    except ValueError as e:
        assert "No suitable profile" in str(e)
    else:
        assert False, "Expected ValueError when no profile matches and temp not allowed"

