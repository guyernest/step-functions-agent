"""Tests for nova_act_helpers module."""

import pytest
import platform
from nova_act_helpers import build_nova_act_kwargs, get_default_browser_channel


def test_get_default_browser_channel():
    """Test that default browser channel matches the platform."""
    expected = 'msedge' if platform.system() == 'Windows' else 'chrome'
    assert get_default_browser_channel() == expected


def test_build_nova_act_kwargs_minimal():
    """Test building kwargs with minimal parameters."""
    kwargs = build_nova_act_kwargs()

    # Should have defaults
    assert kwargs["headless"] is True
    assert kwargs["ignore_https_errors"] is True

    # Should have platform default browser channel
    expected_channel = get_default_browser_channel()
    assert kwargs.get("chrome_channel") == expected_channel


def test_build_nova_act_kwargs_full():
    """Test building kwargs with all parameters."""
    kwargs = build_nova_act_kwargs(
        starting_page="https://example.com",
        user_data_dir="/path/to/profile",
        clone_user_data_dir=False,
        headless=False,
        record_video=True,
        browser_channel="msedge",
        nova_act_api_key="test-key",
        go_to_url_timeout=120,
        ignore_https_errors=False,
    )

    assert kwargs["starting_page"] == "https://example.com"
    assert kwargs["user_data_dir"] == "/path/to/profile"
    assert kwargs["clone_user_data_dir"] is False
    assert kwargs["headless"] is False
    assert kwargs["record_video"] is True
    assert kwargs["chrome_channel"] == "msedge"
    assert kwargs["nova_act_api_key"] == "test-key"
    assert kwargs["go_to_url_timeout"] == 120
    assert kwargs["ignore_https_errors"] is False


def test_build_nova_act_kwargs_clone_none():
    """Test that clone_user_data_dir=None is not included in kwargs."""
    kwargs = build_nova_act_kwargs(
        user_data_dir="/path/to/profile",
        clone_user_data_dir=None
    )

    assert "clone_user_data_dir" not in kwargs


def test_build_nova_act_kwargs_explicit_browser_channel():
    """Test that explicit browser_channel overrides platform default."""
    kwargs = build_nova_act_kwargs(browser_channel="chromium")

    assert kwargs["chrome_channel"] == "chromium"


def test_build_nova_act_kwargs_stop_hooks():
    """Test that stop_hooks are passed through."""
    mock_hook = object()
    kwargs = build_nova_act_kwargs(stop_hooks=[mock_hook])

    assert kwargs["stop_hooks"] == [mock_hook]


def test_build_nova_act_kwargs_boto_session():
    """Test that boto_session is passed through."""
    mock_session = object()
    kwargs = build_nova_act_kwargs(boto_session=mock_session)

    assert kwargs["boto_session"] == mock_session
    assert "nova_act_api_key" not in kwargs  # Shouldn't set both


def test_build_nova_act_kwargs_prefers_api_key_over_session():
    """Test that nova_act_api_key takes precedence over boto_session."""
    mock_session = object()
    kwargs = build_nova_act_kwargs(
        nova_act_api_key="test-key",
        boto_session=mock_session
    )

    assert kwargs["nova_act_api_key"] == "test-key"
    assert "boto_session" not in kwargs  # API key takes precedence
