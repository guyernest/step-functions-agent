#!/usr/bin/env python3
"""
Project Cleanup Script

Removes temporary files, caches, and unused code from the project.
Run with --dry-run to see what would be deleted without actually deleting.
"""

import os
import shutil
import argparse
from pathlib import Path
from typing import List, Set

# Patterns for files to clean
TEMP_FILE_PATTERNS = {
    # OS-specific files
    ".DS_Store",
    "Thumbs.db",
    "desktop.ini",
    
    # Editor temporary files
    "*.swp",
    "*.swo",
    "*~",
    "*.bak",
    "*.tmp",
    ".*.un~",
    
    # Python cache
    "*.pyc",
    "*.pyo",
    "__pycache__",
    ".pytest_cache",
    "*.egg-info",
    ".eggs",
    
    # Build artifacts
    "dist",
    "build",
    ".aws-sam",
    "cdk.out",
    
    # Node artifacts (but keep node_modules in Lambda functions)
    ".npm",
    ".yarn",
    
    # Test coverage
    ".coverage",
    "htmlcov",
    ".tox",
    ".mypy_cache",
    
    # Log files
    "*.log",
    "logs",
}

# Directories to skip entirely
SKIP_DIRS = {
    ".git",
    ".github",
    "node_modules",  # Keep these as they're needed for Lambda
    ".venv",
    "venv",
    "env",
}

# Files to keep even if they match patterns
KEEP_FILES = {
    "requirements.txt",
    "package.json",
    "package-lock.json",
    "yarn.lock",
    "go.mod",
    "go.sum",
}

# Unused tool directories (not in our active system)
UNUSED_TOOL_DIRS = [
    "lambda/tools/books-recommender",
    "lambda/tools/cloudwatch-queries",
    "lambda/tools/code-interpreter",  # We use execute-code instead
    "lambda/tools/EarthQuakeQuery",
    "lambda/tools/EarthQuakeQueryTS",
    "lambda/tools/graphql-interface",
    "lambda/tools/image-analysis",
    "lambda/tools/local-agent",
    "lambda/tools/MicrosoftGraphAPI",
    "lambda/tools/rust-clustering",
    "lambda/tools/SemanticSearchRust",
    "lambda/tools/stock-analyzer",  # We use yfinance instead
    "lambda/tools/web-scraper",     # Different from web-research
    "lambda/tools/WebScraperMemory",
]

# Temporary documentation files that can be removed
TEMP_DOCS = [
    "TOOL_NAMING_AUDIT.md",  # This was for debugging
    "REFACTORING_DESIGN.md", # This was the initial design
]


def should_delete(path: Path, patterns: Set[str], skip_dirs: Set[str], keep_files: Set[str]) -> bool:
    """Determine if a path should be deleted based on patterns"""
    
    # Skip certain directories
    for parent in path.parents:
        if parent.name in skip_dirs:
            return False
    
    # Keep specific files
    if path.name in keep_files:
        return False
    
    # Check patterns
    for pattern in patterns:
        if pattern.startswith("*"):
            if path.name.endswith(pattern[1:]):
                return True
        elif pattern.endswith("*"):
            if path.name.startswith(pattern[:-1]):
                return True
        elif path.name == pattern:
            return True
    
    return False


def find_files_to_delete(root_dir: Path) -> List[Path]:
    """Find all files and directories to delete"""
    to_delete = []
    
    # Find temporary files
    for root, dirs, files in os.walk(root_dir):
        root_path = Path(root)
        
        # Skip certain directories
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        
        # Check directories
        for dir_name in dirs:
            dir_path = root_path / dir_name
            if should_delete(dir_path, TEMP_FILE_PATTERNS, SKIP_DIRS, KEEP_FILES):
                to_delete.append(dir_path)
        
        # Check files
        for file_name in files:
            file_path = root_path / file_name
            if should_delete(file_path, TEMP_FILE_PATTERNS, SKIP_DIRS, KEEP_FILES):
                to_delete.append(file_path)
    
    # Add unused tool directories
    for tool_dir in UNUSED_TOOL_DIRS:
        tool_path = root_dir / tool_dir
        if tool_path.exists():
            to_delete.append(tool_path)
    
    # Add temporary documentation
    for doc in TEMP_DOCS:
        doc_path = root_dir / doc
        if doc_path.exists():
            to_delete.append(doc_path)
    
    return sorted(set(to_delete))


def calculate_size(paths: List[Path]) -> int:
    """Calculate total size of files to be deleted"""
    total_size = 0
    for path in paths:
        try:
            if path.is_file():
                total_size += path.stat().st_size
            elif path.is_dir():
                for root, dirs, files in os.walk(path):
                    for file in files:
                        file_path = Path(root) / file
                        if file_path.exists():
                            total_size += file_path.stat().st_size
        except (OSError, PermissionError):
            pass
    return total_size


def delete_files(paths: List[Path], dry_run: bool = True) -> None:
    """Delete files and directories"""
    for path in paths:
        try:
            if dry_run:
                print(f"Would delete: {path}")
            else:
                if path.is_file():
                    path.unlink()
                    print(f"Deleted file: {path}")
                elif path.is_dir():
                    shutil.rmtree(path)
                    print(f"Deleted directory: {path}")
        except Exception as e:
            print(f"Error deleting {path}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Clean up temporary files and unused code")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted without deleting")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt")
    parser.add_argument("--path", default=".", help="Root path to clean (default: current directory)")
    args = parser.parse_args()
    
    root_dir = Path(args.path).resolve()
    print(f"Cleaning project at: {root_dir}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'ACTUAL DELETE'}")
    print("-" * 60)
    
    # Find files to delete
    to_delete = find_files_to_delete(root_dir)
    
    if not to_delete:
        print("No files to clean up!")
        return
    
    # Calculate size
    total_size = calculate_size(to_delete)
    size_mb = total_size / (1024 * 1024)
    
    print(f"Found {len(to_delete)} items to delete ({size_mb:.2f} MB)")
    print("-" * 60)
    
    # Group by type
    temp_files = [p for p in to_delete if not any(str(p).startswith(d) for d in UNUSED_TOOL_DIRS + TEMP_DOCS)]
    unused_tools = [p for p in to_delete if any(str(p).startswith(d) for d in UNUSED_TOOL_DIRS)]
    temp_docs = [p for p in to_delete if p.name in TEMP_DOCS]
    
    if temp_files:
        print(f"\nTemporary files ({len(temp_files)} items):")
        for path in temp_files[:10]:  # Show first 10
            print(f"  - {path}")
        if len(temp_files) > 10:
            print(f"  ... and {len(temp_files) - 10} more")
    
    if unused_tools:
        print(f"\nUnused tool directories ({len(unused_tools)} items):")
        for path in unused_tools:
            if path.is_dir() and path.parent.name == "tools":
                print(f"  - {path}")
    
    if temp_docs:
        print(f"\nTemporary documentation ({len(temp_docs)} items):")
        for path in temp_docs:
            print(f"  - {path}")
    
    if not args.dry_run and not args.yes:
        print("\n" + "=" * 60)
        response = input("Proceed with deletion? (y/N): ").strip().lower()
        if response != 'y':
            print("Cleanup cancelled.")
            return
    
    # Delete files
    delete_files(to_delete, args.dry_run)
    
    if not args.dry_run:
        print(f"\nCleanup complete! Freed {size_mb:.2f} MB")
    else:
        print(f"\nDry run complete. Would free {size_mb:.2f} MB")
        print("Run without --dry-run to actually delete files")


if __name__ == "__main__":
    main()