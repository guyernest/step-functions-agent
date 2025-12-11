#!/usr/bin/env python3
"""
Settings store for Navigation Studio

Provides secure storage for API keys and configuration settings.
Settings are stored in a local JSON file with sensitive values encrypted.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
import base64
import hashlib


class SettingsStore:
    """Secure settings storage with encryption for sensitive values."""

    # Fields that should be encrypted
    SENSITIVE_FIELDS = {'anthropic_api_key', 'openai_api_key', 'aws_secret_key'}

    def __init__(self, settings_dir: Optional[str] = None):
        """Initialize the settings store.

        Args:
            settings_dir: Directory to store settings. Defaults to ~/.navigation_studio/
        """
        if settings_dir:
            self.settings_dir = Path(settings_dir)
        else:
            self.settings_dir = Path.home() / '.navigation_studio'

        self.settings_dir.mkdir(parents=True, exist_ok=True)
        self.settings_file = self.settings_dir / 'settings.json'
        self.key_file = self.settings_dir / '.key'

        self._fernet = self._get_or_create_key()
        self._settings: Dict[str, Any] = {}
        self._load()

    def _get_or_create_key(self) -> Fernet:
        """Get or create encryption key."""
        if self.key_file.exists():
            key = self.key_file.read_bytes()
        else:
            key = Fernet.generate_key()
            self.key_file.write_bytes(key)
            # Set restrictive permissions on key file
            os.chmod(self.key_file, 0o600)

        return Fernet(key)

    def _encrypt(self, value: str) -> str:
        """Encrypt a sensitive value."""
        encrypted = self._fernet.encrypt(value.encode())
        return base64.b64encode(encrypted).decode()

    def _decrypt(self, encrypted_value: str) -> str:
        """Decrypt a sensitive value."""
        try:
            encrypted = base64.b64decode(encrypted_value.encode())
            return self._fernet.decrypt(encrypted).decode()
        except Exception:
            return ''

    def _load(self):
        """Load settings from file."""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    self._settings = json.load(f)
            except Exception as e:
                print(f"Warning: Could not load settings: {e}")
                self._settings = {}
        else:
            self._settings = self._get_defaults()
            self._save()

    def _save(self):
        """Save settings to file."""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self._settings, f, indent=2)
            # Set restrictive permissions on settings file
            os.chmod(self.settings_file, 0o600)
        except Exception as e:
            print(f"Warning: Could not save settings: {e}")

    def _get_defaults(self) -> Dict[str, Any]:
        """Get default settings."""
        return {
            'backend_url': 'ws://localhost:8765/studio',
            'browser_profile': 'default',
            'ai_model': 'claude-sonnet-4-20250514',
            'auto_analyze': True,
            'anthropic_api_key': '',
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value.

        Args:
            key: Setting key
            default: Default value if not found

        Returns:
            The setting value, decrypted if sensitive
        """
        value = self._settings.get(key, default)

        if key in self.SENSITIVE_FIELDS and value:
            return self._decrypt(value)

        return value

    def set(self, key: str, value: Any):
        """Set a setting value.

        Args:
            key: Setting key
            value: Value to set (will be encrypted if sensitive)
        """
        if key in self.SENSITIVE_FIELDS and value:
            self._settings[key] = self._encrypt(str(value))
        else:
            self._settings[key] = value

        self._save()

    def get_all(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Get all settings.

        Args:
            include_sensitive: If True, include decrypted sensitive values.
                             If False, mask sensitive values.

        Returns:
            Dictionary of all settings
        """
        result = {}
        for key, value in self._settings.items():
            if key in self.SENSITIVE_FIELDS:
                if include_sensitive:
                    result[key] = self._decrypt(value) if value else ''
                else:
                    # Return masked version
                    decrypted = self._decrypt(value) if value else ''
                    if decrypted:
                        result[key] = decrypted[:8] + '...' + decrypted[-4:] if len(decrypted) > 12 else '****'
                    else:
                        result[key] = ''
            else:
                result[key] = value

        return result

    def update(self, settings: Dict[str, Any]):
        """Update multiple settings at once.

        Args:
            settings: Dictionary of settings to update
        """
        for key, value in settings.items():
            # Only update if value is provided (not empty string for sensitive fields)
            if key in self.SENSITIVE_FIELDS:
                # Only update API keys if a new value is actually provided
                if value and not value.startswith('****') and '...' not in value:
                    self.set(key, value)
            else:
                self.set(key, value)

    def has_api_key(self, key: str = 'anthropic_api_key') -> bool:
        """Check if an API key is configured.

        Args:
            key: The API key setting name

        Returns:
            True if the API key is set and non-empty
        """
        value = self.get(key)
        return bool(value and len(value) > 0)

    def clear(self, key: str):
        """Clear a specific setting.

        Args:
            key: Setting key to clear
        """
        if key in self._settings:
            del self._settings[key]
            self._save()


# Global settings instance
_settings_store: Optional[SettingsStore] = None


def get_settings_store() -> SettingsStore:
    """Get the global settings store instance."""
    global _settings_store
    if _settings_store is None:
        _settings_store = SettingsStore()
    return _settings_store
