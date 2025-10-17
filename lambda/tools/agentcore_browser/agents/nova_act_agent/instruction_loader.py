"""Load and manage Nova Act instructions."""

import json
import yaml
from pathlib import Path
from typing import Any


class InstructionLoader:
    """Load Nova Act instructions from configuration files."""

    def __init__(self, instructions_dir: str = "instructions"):
        self.instructions_dir = Path(instructions_dir)

    def load(self, instruction_name: str) -> dict[str, Any]:
        """Load instruction by name.

        Args:
            instruction_name: Name like 'browse/search_google' or 'broadband/bt_checker'

        Returns:
            Instruction configuration dictionary
        """
        # Try YAML first, then JSON
        yaml_path = self.instructions_dir / f"{instruction_name}.yaml"
        json_path = self.instructions_dir / f"{instruction_name}.json"

        if yaml_path.exists():
            with open(yaml_path, "r") as f:
                return yaml.safe_load(f)
        elif json_path.exists():
            with open(json_path, "r") as f:
                return json.load(f)
        else:
            raise FileNotFoundError(f"Instruction not found: {instruction_name}")

    def format_instructions(self, config: dict[str, Any], parameters: dict[str, Any]) -> str:
        """Format instructions with parameters.

        Args:
            config: Instruction configuration
            parameters: Parameters to substitute

        Returns:
            Formatted instruction string
        """
        instructions = config["instructions"]

        # Validate required parameters
        if "parameters" in config:
            for param_name, param_config in config["parameters"].items():
                if param_config.get("required", False) and param_name not in parameters:
                    raise ValueError(f"Required parameter missing: {param_name}")

        # Format instructions
        for key, value in parameters.items():
            instructions = instructions.replace(f"{{{key}}}", str(value))

        return instructions

    def list_available(self) -> list[str]:
        """List all available instruction files.

        Returns:
            List of instruction names
        """
        instructions = []
        
        # Recursively find all YAML and JSON files
        for path in self.instructions_dir.rglob("*.yaml"):
            relative_path = path.relative_to(self.instructions_dir)
            name = str(relative_path.with_suffix(""))
            instructions.append(name)
            
        for path in self.instructions_dir.rglob("*.json"):
            relative_path = path.relative_to(self.instructions_dir)
            name = str(relative_path.with_suffix(""))
            if name not in instructions:  # Avoid duplicates
                instructions.append(name)
        
        return sorted(instructions)

    def validate(self, instruction_name: str) -> tuple[bool, list[str]]:
        """Validate an instruction configuration.

        Args:
            instruction_name: Name of instruction to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        try:
            config = self.load(instruction_name)
        except FileNotFoundError as e:
            return False, [str(e)]
        
        # Check required fields
        required_fields = ["name", "instructions"]
        for field in required_fields:
            if field not in config:
                errors.append(f"Missing required field: {field}")
        
        # Check instruction formatting
        if "instructions" in config and "parameters" in config:
            instructions = config["instructions"]
            for param_name in config["parameters"]:
                if f"{{{param_name}}}" not in instructions:
                    errors.append(f"Parameter '{param_name}' not used in instructions")
        
        return len(errors) == 0, errors