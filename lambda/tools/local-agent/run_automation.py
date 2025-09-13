#!/usr/bin/env python
"""
Wrapper script for running automation with uv/uvx.

Usage:
    # With uv run
    uv run run_automation.py examples/test.json
    
    # With uvx  
    uvx --from . local-agent examples/test.json
    
    # Direct Python
    python run_automation.py examples/test.json
"""

import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from script_executor import main

if __name__ == "__main__":
    main()