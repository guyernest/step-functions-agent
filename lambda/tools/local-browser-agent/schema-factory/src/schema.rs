use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use chrono::{DateTime, Utc};

/// Canonical schema for a browser automation extraction task
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CanonicalSchema {
    pub extraction_name: String,
    pub version: String,
    pub description: String,
    pub input_schema: SchemaDefinition,
    pub output_schema: SchemaDefinition,
    pub browser_config: BrowserConfig,
    pub metadata: Metadata,
}

/// Schema definition for input or output
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SchemaDefinition {
    #[serde(rename = "type")]
    pub schema_type: String,
    pub properties: HashMap<String, PropertyDefinition>,
}

/// Property definition within a schema
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PropertyDefinition {
    #[serde(rename = "type")]
    pub property_type: String,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub required: Option<bool>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub pattern: Option<String>,

    #[serde(skip_serializing_if = "Option::is_none")]
    #[serde(rename = "enum")]
    pub enum_values: Option<Vec<String>>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub format: Option<String>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub items: Option<Box<PropertyDefinition>>,
}

/// Browser configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BrowserConfig {
    pub profile_name: String,
    pub starting_url: String,
    pub timeout: u32,

    #[serde(default)]
    pub requires_login: bool,

    #[serde(default)]
    pub clone_for_parallel: bool,
}

/// Metadata about the schema
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Metadata {
    pub author: String,
    pub created_at: String,
    pub tags: Vec<String>,
    pub use_cases: Vec<String>,
}

/// Schema registry entry
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SchemaRegistryEntry {
    pub schema_id: String,
    pub version: String,
    pub canonical_schema: CanonicalSchema,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub agent_arn: Option<String>,

    pub tool_name: String,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub browser_script_s3: Option<String>,

    pub status: SchemaStatus,
    pub created_at: DateTime<Utc>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub created_by: Option<String>,

    pub tags: Vec<String>,
    pub dependencies: SchemaDependencies,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum SchemaStatus {
    Active,
    Deprecated,
    Testing,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SchemaDependencies {
    pub profile: String,
    pub requires_login: bool,
}

impl CanonicalSchema {
    /// Load schema from JSON file
    pub fn from_file(path: &str) -> anyhow::Result<Self> {
        let content = std::fs::read_to_string(path)?;
        let schema: CanonicalSchema = serde_json::from_str(&content)?;
        Ok(schema)
    }

    /// Validate the schema structure
    pub fn validate(&self) -> anyhow::Result<()> {
        // Check extraction name is valid
        if self.extraction_name.is_empty() {
            anyhow::bail!("extraction_name cannot be empty");
        }

        // Check version format (semantic versioning)
        let version_regex = regex::Regex::new(r"^\d+\.\d+\.\d+$")?;
        if !version_regex.is_match(&self.version) {
            anyhow::bail!("version must follow semantic versioning (e.g., 1.0.0)");
        }

        // Check input schema has at least one property
        if self.input_schema.properties.is_empty() {
            anyhow::bail!("input_schema must have at least one property");
        }

        // Check output schema has at least one property
        if self.output_schema.properties.is_empty() {
            anyhow::bail!("output_schema must have at least one property");
        }

        // Validate browser config
        if self.browser_config.profile_name.is_empty() {
            anyhow::bail!("browser_config.profile_name cannot be empty");
        }

        if self.browser_config.starting_url.is_empty() {
            anyhow::bail!("browser_config.starting_url cannot be empty");
        }

        if self.browser_config.timeout == 0 {
            anyhow::bail!("browser_config.timeout must be greater than 0");
        }

        Ok(())
    }

    /// Get schema ID (extraction_name + version)
    pub fn schema_id(&self) -> String {
        format!("{}_{}", self.extraction_name, self.version.replace('.', "_"))
    }

    /// Get tool name
    pub fn tool_name(&self) -> String {
        self.extraction_name.replace('_', "-")
    }

    /// Get agent name
    pub fn agent_name(&self) -> String {
        format!("{}-structured", self.tool_name())
    }

    /// Get all required input fields
    pub fn required_input_fields(&self) -> Vec<String> {
        self.input_schema
            .properties
            .iter()
            .filter(|(_, prop)| prop.required.unwrap_or(false))
            .map(|(name, _)| name.clone())
            .collect()
    }

    /// Get all required output fields
    pub fn required_output_fields(&self) -> Vec<String> {
        self.output_schema
            .properties
            .iter()
            .filter(|(_, prop)| prop.required.unwrap_or(false))
            .map(|(name, _)| name.clone())
            .collect()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_schema_validation() {
        let mut schema = CanonicalSchema {
            extraction_name: "test_extraction".to_string(),
            version: "1.0.0".to_string(),
            description: "Test".to_string(),
            input_schema: SchemaDefinition {
                schema_type: "object".to_string(),
                properties: HashMap::new(),
            },
            output_schema: SchemaDefinition {
                schema_type: "object".to_string(),
                properties: HashMap::new(),
            },
            browser_config: BrowserConfig {
                profile_name: "test".to_string(),
                starting_url: "https://example.com".to_string(),
                timeout: 300,
                requires_login: false,
                clone_for_parallel: false,
            },
            metadata: Metadata {
                author: "test".to_string(),
                created_at: "2025-01-01".to_string(),
                tags: vec![],
                use_cases: vec![],
            },
        };

        // Should fail - no input properties
        assert!(schema.validate().is_err());

        // Add input property
        schema.input_schema.properties.insert(
            "test_field".to_string(),
            PropertyDefinition {
                property_type: "string".to_string(),
                description: None,
                required: Some(true),
                pattern: None,
                enum_values: None,
                format: None,
                items: None,
            },
        );

        // Should still fail - no output properties
        assert!(schema.validate().is_err());

        // Add output property
        schema.output_schema.properties.insert(
            "result".to_string(),
            PropertyDefinition {
                property_type: "boolean".to_string(),
                description: None,
                required: Some(true),
                pattern: None,
                enum_values: None,
                format: None,
                items: None,
            },
        );

        // Should now pass
        assert!(schema.validate().is_ok());
    }

    #[test]
    fn test_schema_id() {
        let schema = CanonicalSchema {
            extraction_name: "broadband_availability".to_string(),
            version: "1.0.0".to_string(),
            description: "Test".to_string(),
            input_schema: SchemaDefinition {
                schema_type: "object".to_string(),
                properties: HashMap::new(),
            },
            output_schema: SchemaDefinition {
                schema_type: "object".to_string(),
                properties: HashMap::new(),
            },
            browser_config: BrowserConfig {
                profile_name: "test".to_string(),
                starting_url: "https://example.com".to_string(),
                timeout: 300,
                requires_login: false,
                clone_for_parallel: false,
            },
            metadata: Metadata {
                author: "test".to_string(),
                created_at: "2025-01-01".to_string(),
                tags: vec![],
                use_cases: vec![],
            },
        };

        assert_eq!(schema.schema_id(), "broadband_availability_1_0_0");
        assert_eq!(schema.tool_name(), "broadband-availability");
        assert_eq!(schema.agent_name(), "broadband-availability-structured");
    }
}
