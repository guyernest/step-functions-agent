#!/usr/bin/env python3
"""
Fix placement of agent properties in agent stack files.

The properties (agent_description, llm_provider, llm_model, agent_metadata)
must be set BEFORE calling super().__init__() for them to be registered properly.
"""

import os
import re

def fix_cloudwatch_agent():
    """Fix cloudwatch_agent_stack.py - move properties from after to before super().__init__"""
    file_path = "stacks/agents/cloudwatch_agent_stack.py"
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Remove properties from after super().__init__
    content = re.sub(
        r'\n        # Store env_name for registration.*?\n        self\.agent_metadata = \{[^}]+\}',
        '',
        content,
        flags=re.DOTALL
    )
    
    # Add properties before the LLM import
    properties = '''
        # Set agent-specific properties for registry
        self.agent_description = "Expert system analyst for CloudWatch monitoring, log analysis, and root cause analysis"
        self.llm_provider = "claude"
        self.llm_model = "claude-3-5-sonnet-20241022"
        self.agent_metadata = {
            "tags": ['monitoring', 'logs', 'cloudwatch', 'analysis', 'root-cause']
        }
        '''
    
    # Insert after __init__ definition
    content = re.sub(
        r'(def __init__\(self.*?\) -> None:\n)',
        r'\1' + properties,
        content
    )
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Fixed {file_path}")

def fix_google_maps_agent():
    """Fix google_maps_agent_stack.py - move properties from after to before super().__init__"""
    file_path = "stacks/agents/google_maps_agent_stack.py"
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Remove properties from after super().__init__
    content = re.sub(
        r'\n        # Store env_name for registration.*?\n        self\.agent_metadata = \{[^}]+\}',
        '',
        content,
        flags=re.DOTALL
    )
    
    # Add properties before the LLM import
    properties = '''
        # Set agent-specific properties for registry
        self.agent_description = "Location and mapping assistant with Google Maps integration"
        self.llm_provider = "gemini"
        self.llm_model = "gemini-1.5-flash"
        self.agent_metadata = {
            "tags": ['maps', 'location', 'geocoding', 'directions', 'google-maps']
        }
        '''
    
    # Insert after __init__ definition
    content = re.sub(
        r'(def __init__\(self.*?\) -> None:\n)',
        r'\1' + properties,
        content
    )
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Fixed {file_path}")

def fix_graphql_agent():
    """Fix graphql_agent_stack.py - remove duplicate properties after super().__init__"""
    file_path = "stacks/agents/graphql_agent_stack.py"
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Remove duplicate properties from after super().__init__
    content = re.sub(
        r'\n        # Set agent-specific properties for registry.*?\n        self\.agent_metadata = \{[^}]+\}\n        # Store env_name for registration\n        self\.env_name = env_name',
        '',
        content,
        flags=re.DOTALL
    )
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Fixed {file_path}")

def fix_research_agent():
    """Fix research_agent_stack.py - remove duplicate properties after super().__init__"""
    file_path = "stacks/agents/research_agent_stack.py"
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Remove duplicate properties and malformed comment from after super().__init__
    content = re.sub(
        r'\n        \n        \n        # Set agent-specific properties for registry.*?\}# Store env_name for registration\n        self\.env_name = env_name',
        '',
        content,
        flags=re.DOTALL
    )
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Fixed {file_path}")

def fix_test_automation_agent():
    """Fix test_automation_remote_agent_stack.py - move properties from after to before super().__init__"""
    file_path = "stacks/agents/test_automation_remote_agent_stack.py"
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Remove properties from after super().__init__
    content = re.sub(
        r'\n        # Store env_name for registration.*?\n        self\.agent_metadata = \{[^}]+\}',
        '',
        content,
        flags=re.DOTALL
    )
    
    # Add properties before the LLM import
    properties = '''
        # Set agent-specific properties for registry
        self.agent_description = "Test automation agent with remote execution workflow and Microsoft 365 integration capabilities"
        self.llm_provider = "claude"
        self.llm_model = "claude-3-5-sonnet-20241022"
        self.agent_metadata = {
            "tags": ['test-automation', 'remote-execution', 'approval-workflow', 'microsoft-365', 'e2b']
        }
        '''
    
    # Insert after __init__ definition
    content = re.sub(
        r'(def __init__\(self.*?\) -> None:\n)',
        r'\1' + properties,
        content
    )
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Fixed {file_path}")

def fix_sql_agent():
    """Fix sql_agent_with_base_construct.py - remove duplicate properties after super().__init__"""
    file_path = "stacks/agents/sql_agent_with_base_construct.py"
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Remove duplicate properties from after super().__init__
    content = re.sub(
        r'\n        # Set agent-specific properties for registry.*?\n        self\.agent_metadata = \{[^}]+\}',
        '',
        content,
        flags=re.DOTALL
    )
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Fixed {file_path}")

if __name__ == "__main__":
    os.chdir("/Users/guy/projects/step-functions-agent")
    
    print("Fixing agent property placement in all agent stacks...")
    print("=" * 60)
    
    fix_cloudwatch_agent()
    fix_google_maps_agent()
    fix_graphql_agent()
    fix_research_agent()
    fix_test_automation_agent()
    fix_sql_agent()
    
    print("=" * 60)
    print("✅ All agent stacks fixed!")
    print("\nAgent properties are now properly placed BEFORE super().__init__()")
    print("This ensures they are available during agent registration.")