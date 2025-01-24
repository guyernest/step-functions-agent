# lambda/call_llm/__init__.py
import os
import sys

# Add the package directory to the Python path
package_dir = os.path.dirname(os.path.abspath(__file__))
if package_dir not in sys.path:
    sys.path.insert(0, package_dir)

# Define the package name
__package__ = 'call_llm'

# Import your submodules
from . import common
from . import llms
from . import handlers

# Make the imports available at the package level
__all__ = ['common', 'llms', 'handlers']