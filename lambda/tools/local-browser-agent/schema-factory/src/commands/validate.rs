use anyhow::Result;

use crate::schema::CanonicalSchema;
use crate::validator::Validator;

pub async fn execute(
    schema_path: &str,
    agent_arn: Option<&str>,
    check_tools: bool,
    check_output_mapping: bool,
) -> Result<()> {
    // Load schema
    let schema = CanonicalSchema::from_file(schema_path)?;

    let validator = Validator::new();

    if let Some(arn) = agent_arn {
        // Validate deployed agent
        validator.validate_agent_deployment(&schema, arn, check_tools, check_output_mapping)?;
    } else {
        // Just validate schema
        validator.validate_schema(&schema)?;
    }

    Ok(())
}
