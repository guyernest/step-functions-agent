import os
import sys
from pathlib import Path

import shutil
import tempfile


def test_profiles_dir_env_override(monkeypatch):
    from profile_manager import ProfileManager

    with tempfile.TemporaryDirectory() as td:
        monkeypatch.setenv("BROWSER_AGENT_PROFILES_DIR", td)
        pm = ProfileManager()
        assert Path(pm.profiles_dir).resolve() == Path(td).resolve()
        assert Path(pm.profiles_dir).exists()


def test_profiles_dir_backwards_compat(monkeypatch, tmp_path):
    from profile_manager import ProfileManager

    # Work in a temp cwd
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        # Create legacy relative folder
        legacy = tmp_path / "browser-profiles"
        legacy.mkdir(parents=True)
        pm = ProfileManager()
        assert Path(pm.profiles_dir).resolve() == legacy.resolve()
    finally:
        os.chdir(old_cwd)


def test_profiles_dir_os_default(monkeypatch, tmp_path):
    from profile_manager import ProfileManager

    # Work in a clean temp cwd without legacy dir
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        pm = ProfileManager()
        # Should NOT default to the current directory
        assert Path(pm.profiles_dir).resolve() != tmp_path.resolve()
        # Directory should be created
        assert Path(pm.profiles_dir).exists()
    finally:
        os.chdir(old_cwd)

