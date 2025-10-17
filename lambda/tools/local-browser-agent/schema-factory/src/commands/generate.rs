use anyhow::Result;
use colored::Colorize;

use crate::schema::CanonicalSchema;
use crate::generator::Generator;
use crate::validator::Validator;

pub async fn execute(schema_path: &str, output_dir: &str, deploy: bool, env: &str) -> Result<()> {
    // Load and validate schema
    println!("\n{}", "📖 Loading canonical schema...".bright_cyan());
    let schema = CanonicalSchema::from_file(schema_path)?;
    println!("  {} Loaded schema: {} v{}", "✓".bright_green(), schema.extraction_name, schema.version);

    // Validate schema
    let validator = Validator::new();
    validator.validate_schema(&schema)?;

    // Generate all artifacts
    let generator = Generator::new();
    generator.generate_all(&schema, output_dir)?;

    // Optionally deploy
    if deploy {
        println!("\n{}", "🚀 Deploying to AWS...".bright_cyan());
        super::deploy::execute(schema_path, env, false).await?;
    }

    Ok(())
}
