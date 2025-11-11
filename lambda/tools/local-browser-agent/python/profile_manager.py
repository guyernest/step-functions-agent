#!/usr/bin/env python3
"""
Browser Profile Manager for Nova Act

Manages browser profiles for session persistence, authentication, and reuse.
Supports:
- Creating and managing named profiles
- Session persistence across executions
- Human-assisted login flows
- Profile metadata and usage tracking
"""

import os
import json
import shutil
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime, timedelta
try:
    # Optional import; only used for runtime validation helper
    from nova_act import NovaAct, BOOL_SCHEMA  # type: ignore
except Exception:
    NovaAct = None  # type: ignore
    BOOL_SCHEMA = None  # type: ignore


class ProfileManager:
    """Manages browser profiles for Nova Act sessions"""

    def __init__(self, profiles_dir: str = None):
        """
        Initialize profile manager

        Args:
            profiles_dir: Directory to store profiles (default: ./browser-profiles)
        """
        self.profiles_dir = Path(profiles_dir or "./browser-profiles")
        self.profiles_dir.mkdir(parents=True, exist_ok=True)

        # Metadata file tracks all profiles
        self.metadata_file = self.profiles_dir / "profiles.json"
        self._load_metadata()

    def _load_metadata(self):
        """Load profiles metadata"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                self.metadata = json.load(f)
        else:
            self.metadata = {
                "profiles": {},
                "version": "1.0"
            }

    def _save_metadata(self):
        """Save profiles metadata"""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)

    def create_profile(
        self,
        profile_name: str,
        description: str = "",
        tags: List[str] = None,
        auto_login_sites: List[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new browser profile

        Args:
            profile_name: Unique name for the profile
            description: Description of the profile's purpose
            tags: Tags for categorization (e.g., ['banking', 'production'])
            auto_login_sites: Sites where auto-login should be attempted

        Returns:
            Profile configuration dict
        """
        if profile_name in self.metadata["profiles"]:
            raise ValueError(f"Profile '{profile_name}' already exists")

        # Create profile directory
        profile_dir = self.profiles_dir / profile_name
        profile_dir.mkdir(parents=True, exist_ok=True)

        # Create profile metadata
        profile_config = {
            "name": profile_name,
            "description": description,
            "tags": tags or [],
            "auto_login_sites": auto_login_sites or [],
            "user_data_dir": str(profile_dir),
            "created_at": datetime.now().isoformat(),
            "last_used": None,
            "usage_count": 0,
            "requires_human_login": False,  # Set to True if manual login needed
            "login_notes": "",  # Notes about login process
            "session_timeout_hours": 24,  # How long sessions are valid
        }

        # Save to metadata
        self.metadata["profiles"][profile_name] = profile_config
        self._save_metadata()

        return profile_config

    def get_profile(self, profile_name: str) -> Optional[Dict[str, Any]]:
        """
        Get profile configuration

        Args:
            profile_name: Name of the profile

        Returns:
            Profile configuration dict or None if not found
        """
        return self.metadata["profiles"].get(profile_name)

    def list_profiles(self, tags: List[str] = None) -> List[Dict[str, Any]]:
        """
        List all profiles, optionally filtered by tags

        Args:
            tags: Filter by tags (returns profiles matching ANY tag)

        Returns:
            List of profile configuration dicts
        """
        profiles = list(self.metadata["profiles"].values())

        if tags:
            profiles = [
                p for p in profiles
                if any(tag in p.get("tags", []) for tag in tags)
            ]

        return profiles

    def find_profiles_by_tags(
        self,
        required_tags: List[str],
        match_all: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Find profiles that match the required tags.

        Args:
            required_tags: List of tags to match
            match_all: If True, profile must have ALL required tags (AND logic)
                       If False, profile must have ANY required tag (OR logic)

        Returns:
            List of profile dicts that match the criteria, sorted by last_used (most recent first)
        """
        profiles = list(self.metadata["profiles"].values())
        matched = []

        for profile in profiles:
            profile_tags = set(profile.get("tags", []))
            required_set = set(required_tags)

            if match_all:
                # AND logic: profile must have ALL required tags
                if required_set.issubset(profile_tags):
                    matched.append(profile)
            else:
                # OR logic: profile must have ANY required tag
                if required_set.intersection(profile_tags):
                    matched.append(profile)

        # Sort by last_used (most recent first), profiles never used go to end
        matched.sort(
            key=lambda p: datetime.fromisoformat(p["last_used"]) if p.get("last_used") else datetime.min,
            reverse=True
        )

        return matched

    def resolve_profile(
        self,
        session_config: Dict[str, Any],
        verbose: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Resolve which local profile to use based on session requirements.

        This is the centralized profile resolution logic used by both
        script_executor.py and nova_act_wrapper.py.

        Priority:
        1. Exact profile_name match (if provided)
        2. Tag-based matching (required_tags with AND logic)
        3. Temporary profile (if allowed)
        4. Error (no suitable profile found)

        Args:
            session_config: Session configuration dict with optional keys:
                - profile_name: Exact profile name to use
                - required_tags: List of tags to match (AND logic)
                - allow_temp_profile: Whether to allow temporary profile (default: True)
            verbose: If True, print resolution progress to stderr

        Returns:
            Profile dict with name, user_data_dir, tags, etc.
            None if using temporary profile

        Raises:
            ValueError: No suitable profile found and temp not allowed
        """
        import sys

        # Priority 1: Try exact name match (backward compatibility)
        profile_name = session_config.get('profile_name')
        if profile_name:
            profile = self.get_profile(profile_name)
            if profile:
                if verbose:
                    print(f"✓ Resolved profile by exact name: '{profile_name}'", file=sys.stderr)
                return profile
            else:
                if verbose:
                    print(f"⚠ Profile '{profile_name}' not found, trying tag matching...", file=sys.stderr)

        # Priority 2: Try tag-based matching (all required tags must match)
        required_tags = session_config.get('required_tags', [])
        if required_tags:
            if verbose:
                print(f"Looking for profiles with tags: {required_tags}", file=sys.stderr)

            matched_profiles = self.find_profiles_by_tags(
                required_tags=required_tags,
                match_all=True  # AND logic
            )

            if matched_profiles:
                selected_profile = matched_profiles[0]  # Most recently used
                if verbose:
                    profile_path = self.get_profile_path(selected_profile['name'])
                    abs_profile_path = os.path.abspath(profile_path)
                    profile_exists = os.path.exists(abs_profile_path)

                    print(
                        f"✓ Resolved profile by tags: '{selected_profile['name']}' "
                        f"(matched tags: {required_tags})",
                        file=sys.stderr
                    )
                    print(f"  Profile directory (absolute): {abs_profile_path}", file=sys.stderr)
                    print(f"  Profile exists: {'✓' if profile_exists else '✗'}", file=sys.stderr)

                return selected_profile

            if verbose:
                print(f"⚠ No profiles found matching all required tags: {required_tags}", file=sys.stderr)

        # Priority 3: Check if temporary profile allowed
        allow_temp = session_config.get('allow_temp_profile', True)
        if allow_temp:
            if verbose:
                print("→ Using temporary profile (no persistent session)", file=sys.stderr)
            return None  # None signals temp profile

        # Priority 4: Nothing matched and temp not allowed - ERROR
        all_profiles = self.list_profiles()
        error_msg = f"No suitable profile found. Required tags: {required_tags}"
        if profile_name:
            error_msg += f", Requested name: {profile_name}"

        # Show available profiles to help user
        if all_profiles and verbose:
            print(f"\nAvailable profiles:", file=sys.stderr)
            for p in all_profiles:
                profile_tags = p.get('tags', [])
                missing_tags = list(set(required_tags) - set(profile_tags)) if required_tags else []
                print(f"  • {p['name']}: tags={profile_tags}", file=sys.stderr)
                if missing_tags:
                    print(f"    Missing: {missing_tags}", file=sys.stderr)

        raise ValueError(error_msg)

    def update_profile_usage(self, profile_name: str):
        """
        Update profile usage statistics

        Args:
            profile_name: Name of the profile
        """
        if profile_name in self.metadata["profiles"]:
            profile = self.metadata["profiles"][profile_name]
            profile["last_used"] = datetime.now().isoformat()
            profile["usage_count"] = profile.get("usage_count", 0) + 1
            self._save_metadata()

    def delete_profile(self, profile_name: str, keep_data: bool = False) -> bool:
        """
        Delete a profile

        Args:
            profile_name: Name of the profile to delete
            keep_data: If True, keep the user data directory

        Returns:
            True if deleted successfully
        """
        if profile_name not in self.metadata["profiles"]:
            return False

        profile = self.metadata["profiles"][profile_name]

        # Remove user data directory if requested
        if not keep_data:
            profile_dir = Path(profile["user_data_dir"])
            if profile_dir.exists():
                shutil.rmtree(profile_dir)

        # Remove from metadata
        del self.metadata["profiles"][profile_name]
        self._save_metadata()

        return True

    def is_session_valid(self, profile_name: str) -> bool:
        """
        Check if profile's session is still valid

        Args:
            profile_name: Name of the profile

        Returns:
            True if session is valid (not expired)
        """
        profile = self.get_profile(profile_name)
        if not profile or not profile.get("last_used"):
            return False

        last_used = datetime.fromisoformat(profile["last_used"])
        timeout_hours = profile.get("session_timeout_hours", 24)
        timeout = timedelta(hours=timeout_hours)

        return datetime.now() - last_used < timeout

    def get_nova_act_config(
        self,
        profile_name: str,
        clone_for_parallel: bool = False
    ) -> Dict[str, Any]:
        """
        Get Nova Act configuration for a profile

        Args:
            profile_name: Name of the profile
            clone_for_parallel: If True, enable cloning for parallel execution

        Returns:
            Configuration dict for Nova Act initialization
        """
        profile = self.get_profile(profile_name)
        if not profile:
            raise ValueError(f"Profile '{profile_name}' not found")

        # Update usage statistics
        self.update_profile_usage(profile_name)

        return {
            "user_data_dir": profile["user_data_dir"],
            "clone_user_data_dir": clone_for_parallel,  # False for session reuse
            "profile_metadata": {
                "name": profile_name,
                "description": profile.get("description", ""),
                "requires_human_login": profile.get("requires_human_login", False),
                "auto_login_sites": profile.get("auto_login_sites", []),
            }
        }

    def mark_profile_for_login(
        self,
        profile_name: str,
        requires_human: bool = True,
        notes: str = ""
    ):
        """
        Mark a profile as requiring human login

        Args:
            profile_name: Name of the profile
            requires_human: Whether human intervention is needed
            notes: Notes about the login process
        """
        if profile_name in self.metadata["profiles"]:
            profile = self.metadata["profiles"][profile_name]
            profile["requires_human_login"] = requires_human
            profile["login_notes"] = notes
            self._save_metadata()

    def update_profile_tags(self, profile_name: str, tags: List[str]) -> bool:
        """
        Update the tags for an existing profile

        Args:
            profile_name: Name of the profile to update
            tags: New list of tags to set

        Returns:
            True if updated successfully, False if profile not found
        """
        if profile_name not in self.metadata["profiles"]:
            return False

        profile = self.metadata["profiles"][profile_name]
        profile["tags"] = tags
        self._save_metadata()
        return True

    def export_profile(self, profile_name: str, export_path: str) -> str:
        """
        Export a profile for sharing or backup

        Args:
            profile_name: Name of the profile to export
            export_path: Path where to save the export

        Returns:
            Path to exported archive
        """
        profile = self.get_profile(profile_name)
        if not profile:
            raise ValueError(f"Profile '{profile_name}' not found")

        # Create archive of user data directory
        profile_dir = Path(profile["user_data_dir"])
        archive_path = shutil.make_archive(
            export_path,
            'zip',
            profile_dir.parent,
            profile_dir.name
        )

        # Export metadata
        metadata_export = {
            "profile": profile,
            "exported_at": datetime.now().isoformat()
        }

        metadata_path = f"{export_path}_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata_export, f, indent=2)

        return archive_path

    def import_profile(
        self,
        archive_path: str,
        new_profile_name: str = None
    ) -> Dict[str, Any]:
        """
        Import a profile from an archive

        Args:
            archive_path: Path to the exported profile archive
            new_profile_name: Name for the imported profile (optional)

        Returns:
            Imported profile configuration
        """
        # Extract archive
        import zipfile

        # Read metadata
        metadata_path = f"{archive_path}_metadata.json"
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata_export = json.load(f)
                profile = metadata_export["profile"]
        else:
            # Create default profile metadata
            profile = {
                "name": new_profile_name or "imported_profile",
                "description": "Imported profile",
                "tags": ["imported"],
            }

        # Use new name if provided
        if new_profile_name:
            profile["name"] = new_profile_name

        # Create profile directory
        profile_dir = self.profiles_dir / profile["name"]
        profile_dir.mkdir(parents=True, exist_ok=True)

        # Extract archive to profile directory
        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            zip_ref.extractall(profile_dir)

        # Update profile metadata
        profile["user_data_dir"] = str(profile_dir)
        profile["created_at"] = datetime.now().isoformat()
        profile["last_used"] = None
        profile["usage_count"] = 0

        # Save to metadata
        self.metadata["profiles"][profile["name"]] = profile
        self._save_metadata()

        return profile

    # ---------------------------
    # Validation helpers
    # ---------------------------
    def validate_user_data_dir(self, user_data_dir: str) -> Dict[str, Any]:
        """Static validation of a Chromium user data directory.

        Returns a dict with presence and heuristic checks that indicate whether
        the profile directory looks complete and potentially authenticated.
        """
        p = Path(user_data_dir) if user_data_dir else None
        exists = p.exists() if p else False
        details: Dict[str, Any] = {
            "path": str(p) if p else None,
            "path_exists": exists,
            "has_default_dir": False,
            "has_cookies_db": False,
            "has_local_storage": False,
            "has_preferences": False,
            "has_local_state": False,
            "size_bytes": 0,
            "last_modified": None,
            "status": "missing",
        }

        if not exists:
            return details

        default_dir = p / "Default"
        details["has_default_dir"] = default_dir.exists()

        # Support both legacy (Default/Cookies) and current (Default/Network/Cookies)
        # and cases where the provided path already points at the profile directory
        profile_dir_candidates: List[Path] = []
        if default_dir.exists():
            profile_dir_candidates.append(default_dir)
        if (p / "Preferences").exists() or (p / "Network").exists() or (p / "Cookies").exists():
            profile_dir_candidates.append(p)

        def first_exists(paths):
            for path in paths:
                if path.exists():
                    return path
            return None

        cookies_path = first_exists([
            *[d / "Network" / "Cookies" for d in profile_dir_candidates],
            *[d / "Cookies" for d in profile_dir_candidates],
        ])
        local_storage_dir = first_exists([
            *[d / "Local Storage" / "leveldb" for d in profile_dir_candidates]
        ])
        preferences_path = first_exists([
            *[d / "Preferences" for d in profile_dir_candidates]
        ])
        local_state_path = p / "Local State"

        details["has_cookies_db"] = bool(cookies_path)
        details["has_local_storage"] = bool(local_storage_dir)
        details["has_preferences"] = bool(preferences_path)
        details["has_local_state"] = local_state_path.exists()

        # Compute simple stats
        last_modified = None
        size_bytes = 0
        try:
            for root, _, files in os.walk(p):
                for f in files:
                    fp = os.path.join(root, f)
                    try:
                        size_bytes += os.path.getsize(fp)
                        mtime = os.path.getmtime(fp)
                        if last_modified is None or mtime > last_modified:
                            last_modified = mtime
                    except Exception:
                        pass
        except Exception:
            pass

        details["size_bytes"] = size_bytes
        details["last_modified"] = datetime.fromtimestamp(last_modified).isoformat() if last_modified else None

        status = "ok" if details["has_default_dir"] or details["has_local_state"] else "missing"
        if status == "ok" and not (details["has_cookies_db"] or details["has_local_storage"]):
            status = "warn"
        details["status"] = status
        return details

    def validate_profile(self, profile_name: str) -> Dict[str, Any]:
        """Validate a named profile's user_data_dir (static checks only)."""
        profile = self.get_profile(profile_name)
        if not profile:
            return {"success": False, "error": f"Profile '{profile_name}' not found"}
        static = self.validate_user_data_dir(profile["user_data_dir"]) 
        recs = []
        if static.get("status") == "missing":
            recs.append("Profile directory missing/incomplete. Run human login bootstrap.")
        if static.get("status") == "warn":
            recs.append("Profile present but may lack auth artifacts. Validate at runtime.")
        recs.append("Use clone_user_data_dir=False to persist sessions; True only for parallel runs.")
        return {"success": True, "profile": profile_name, "static": static, "recommendations": recs}


def create_login_profile_interactive(profile_manager: ProfileManager, profile_name: str, starting_url: str):
    """
    Helper function to create a profile with interactive login

    This allows a human to log in and save the session for future automation.

    Args:
        profile_manager: ProfileManager instance
        profile_name: Name for the new profile (or existing profile to update)
        starting_url: URL to navigate to for login
    """
    from nova_act import NovaAct

    print(f"Setting up login for profile: {profile_name}")
    print(f"You will be directed to: {starting_url}")
    print("Please log in manually. Press Enter when done...")

    # Check if profile exists, create if not
    profile = profile_manager.get_profile(profile_name)
    if not profile:
        print(f"Creating new profile: {profile_name}")
        profile = profile_manager.create_profile(
            profile_name=profile_name,
            description=f"Profile with authenticated session for {starting_url}",
            tags=["authenticated"],
            auto_login_sites=[starting_url]
        )
    else:
        print(f"Using existing profile: {profile_name}")

    # Mark profile as requiring human login
    profile_manager.mark_profile_for_login(
        profile_name=profile_name,
        requires_human=True,
        notes=f"Manual login required for {starting_url}"
    )

    # Get Nova Act config
    config = profile_manager.get_nova_act_config(profile_name, clone_for_parallel=False)

    # Open browser for manual login
    with NovaAct(
        starting_page=starting_url,
        user_data_dir=config["user_data_dir"],
        clone_user_data_dir=False,  # Don't clone to preserve session
        headless=False  # Must be visible for human login
    ) as nova:
        input("Press Enter after you've logged in...")

    print(f"✓ Profile '{profile_name}' login setup completed!")
    print(f"  User data directory: {config['user_data_dir']}")
    print(f"  Future scripts can reuse this authenticated session")

    return profile


# Example usage
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Browser Profile Manager")
    parser.add_argument("command", choices=["create", "list", "delete", "login", "update-tags"],
                       help="Command to execute")
    parser.add_argument("--profile", help="Profile name")
    parser.add_argument("--url", help="Starting URL for login")
    parser.add_argument("--description", help="Profile description")
    parser.add_argument("--tags", help="Profile tags (comma-separated for update-tags, space-separated for create)")
    parser.add_argument("--auto-login-sites", nargs="+", help="Sites where auto-login should be attempted")
    parser.add_argument("--timeout", type=int, default=24, help="Session timeout in hours (default: 24)")

    args = parser.parse_args()

    # Initialize profile manager
    manager = ProfileManager()

    if args.command == "create":
        if not args.profile:
            print("Error: --profile required")
            exit(1)

        # For create, tags can be space-separated
        tags_list = args.tags.split() if args.tags else []

        profile = manager.create_profile(
            profile_name=args.profile,
            description=args.description or "",
            tags=tags_list,
            auto_login_sites=args.auto_login_sites or []
        )
        # Set session timeout if provided
        if args.timeout:
            profile["session_timeout_hours"] = args.timeout
            manager.metadata["profiles"][args.profile] = profile
            manager._save_metadata()

        print(f"Created profile: {profile['name']}")
        print(json.dumps(profile, indent=2))

    elif args.command == "list":
        profiles = manager.list_profiles(tags=args.tags)
        # Output as JSON for easy parsing by Rust/UI
        output = {
            "profiles": profiles,
            "total_count": len(profiles)
        }
        print(json.dumps(output, indent=2))

    elif args.command == "delete":
        if not args.profile:
            print("Error: --profile required")
            exit(1)

        success = manager.delete_profile(args.profile)
        if success:
            print(f"Deleted profile: {args.profile}")
        else:
            print(f"Profile not found: {args.profile}")

    elif args.command == "login":
        if not args.profile or not args.url:
            print("Error: --profile and --url required")
            exit(1)

        create_login_profile_interactive(manager, args.profile, args.url)

    elif args.command == "update-tags":
        if not args.profile:
            print("Error: --profile required")
            exit(1)
        if not args.tags:
            print("Error: --tags required")
            exit(1)

        # For update-tags, tags are comma-separated
        tags_list = [tag.strip() for tag in args.tags.split(",") if tag.strip()]

        success = manager.update_profile_tags(args.profile, tags_list)
        if success:
            print(f"Updated tags for profile: {args.profile}")
            print(json.dumps({"tags": tags_list}, indent=2))
        else:
            print(f"Profile not found: {args.profile}", file=sys.stderr)
            exit(1)
