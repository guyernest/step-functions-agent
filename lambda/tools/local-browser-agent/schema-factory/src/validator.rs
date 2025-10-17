use anyhow::Result;
use colored::Colorize;

use crate::schema::CanonicalSchema;

pub struct Validator;

impl Validator {
    pub fn new() -> Self {
        Self
    }

    pub fn validate_schema(&self, schema: &CanonicalSchema) -> Result<()> {
        println!("\n{}", "🔍 Validating schema...".bright_cyan());

        // Validate schema structure
        schema.validate()?;
        println!("  {} Schema structure is valid", "✓".bright_green());

        // Validate input schema
        self.validate_input_schema(schema)?;
        println!("  {} Input schema is valid", "✓".bright_green());

        // Validate output schema
        self.validate_output_schema(schema)?;
        println!("  {} Output schema is valid", "✓".bright_green());

        // Validate browser config
        self.validate_browser_config(schema)?;
        println!("  {} Browser configuration is valid", "✓".bright_green());

        println!("\n{}", "✓ Schema validation passed!".bright_green().bold());

        Ok(())
    }

    fn validate_input_schema(&self, schema: &CanonicalSchema) -> Result<()> {
        // Check that all required fields have valid types
        for (field_name, property) in &schema.input_schema.properties {
            if !Self::is_valid_type(&property.property_type) {
                anyhow::bail!(
                    "Invalid type '{}' for input field '{}'",
                    property.property_type,
                    field_name
                );
            }
        }

        Ok(())
    }

    fn validate_output_schema(&self, schema: &CanonicalSchema) -> Result<()> {
        // Check that all required fields have valid types
        for (field_name, property) in &schema.output_schema.properties {
            if !Self::is_valid_type(&property.property_type) {
                anyhow::bail!(
                    "Invalid type '{}' for output field '{}'",
                    property.property_type,
                    field_name
                );
            }
        }

        // Ensure at least one required output field
        if schema.required_output_fields().is_empty() {
            anyhow::bail!("Output schema must have at least one required field");
        }

        Ok(())
    }

    fn validate_browser_config(&self, schema: &CanonicalSchema) -> Result<()> {
        // Validate URL format
        if !schema.browser_config.starting_url.starts_with("http://")
            && !schema.browser_config.starting_url.starts_with("https://")
        {
            anyhow::bail!("starting_url must be a valid HTTP(S) URL");
        }

        // Validate timeout is reasonable
        if schema.browser_config.timeout > 3600 {
            anyhow::bail!("timeout should not exceed 3600 seconds (1 hour)");
        }

        Ok(())
    }

    fn is_valid_type(type_name: &str) -> bool {
        matches!(
            type_name,
            "string" | "number" | "integer" | "boolean" | "array" | "object"
        )
    }

    pub fn validate_agent_deployment(
        &self,
        schema: &CanonicalSchema,
        agent_arn: &str,
        check_tools: bool,
        check_output_mapping: bool,
    ) -> Result<()> {
        println!("\n{}", "🔍 Validating agent deployment...".bright_cyan());
        println!("  Agent ARN: {}", agent_arn.bright_yellow());

        // Validate schema first
        self.validate_schema(schema)?;

        if check_tools {
            println!("\n  {} Checking tool specifications...", "→".bright_blue());
            // TODO: Implement tool validation
            println!("    {} Tool validation not yet implemented", "⚠".bright_yellow());
        }

        if check_output_mapping {
            println!("\n  {} Checking output mapping...", "→".bright_blue());
            // TODO: Implement output mapping validation
            println!("    {} Output mapping validation not yet implemented", "⚠".bright_yellow());
        }

        Ok(())
    }
}

impl Default for Validator {
    fn default() -> Self {
        Self::new()
    }
}
