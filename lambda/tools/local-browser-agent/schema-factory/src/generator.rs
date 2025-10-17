use anyhow::Result;
use std::fs;
use colored::Colorize;

use crate::schema::CanonicalSchema;
use crate::templates::TemplateGenerator;

pub struct Generator {
    template_generator: TemplateGenerator,
}

impl Generator {
    pub fn new() -> Self {
        Self {
            template_generator: TemplateGenerator::new(),
        }
    }

    pub fn generate_all(&self, schema: &CanonicalSchema, output_dir: &str) -> Result<()> {
        println!("\n{}", "📦 Generating artifacts...".bright_cyan());

        // Create output directory structure
        self.create_directory_structure(output_dir)?;

        // Generate CDK stack
        println!("  {} Generating CDK stack...", "→".bright_blue());
        let cdk_stack = self.template_generator.generate_cdk_stack(schema)?;
        fs::write(
            format!("{}/stack.py", output_dir),
            cdk_stack,
        )?;
        println!("    {} stack.py", "✓".bright_green());

        // Generate browser script template
        println!("  {} Generating browser script template...", "→".bright_blue());
        let browser_script = self.template_generator.generate_browser_script(schema)?;
        fs::write(
            format!("{}/browser_script_template.json", output_dir),
            browser_script,
        )?;
        println!("    {} browser_script_template.json", "✓".bright_green());

        // Generate tool specification
        println!("  {} Generating tool specification...", "→".bright_blue());
        let tool_spec = self.template_generator.generate_tool_spec(schema)?;
        fs::write(
            format!("{}/tool_spec.json", output_dir),
            tool_spec,
        )?;
        println!("    {} tool_spec.json", "✓".bright_green());

        // Generate output tool specification
        println!("  {} Generating output tool specification...", "→".bright_blue());
        let output_tool_spec = self.template_generator.generate_output_tool_spec(schema)?;
        fs::write(
            format!("{}/output_tool_spec.json", output_dir),
            output_tool_spec,
        )?;
        println!("    {} output_tool_spec.json", "✓".bright_green());

        // Generate batch mapping
        println!("  {} Generating batch processor mapping...", "→".bright_blue());
        let batch_mapping = self.template_generator.generate_batch_mapping(schema)?;
        fs::write(
            format!("{}/batch_mapping.json", output_dir),
            batch_mapping,
        )?;
        println!("    {} batch_mapping.json", "✓".bright_green());

        // Generate validator
        println!("  {} Generating validator...", "→".bright_blue());
        let validator = self.template_generator.generate_validator(schema)?;
        fs::write(
            format!("{}/validator.py", output_dir),
            validator,
        )?;
        println!("    {} validator.py", "✓".bright_green());

        // Copy canonical schema
        println!("  {} Copying canonical schema...", "→".bright_blue());
        let schema_json = serde_json::to_string_pretty(schema)?;
        fs::write(
            format!("{}/canonical_schema.json", output_dir),
            schema_json,
        )?;
        println!("    {} canonical_schema.json", "✓".bright_green());

        // Generate README
        self.generate_readme(schema, output_dir)?;
        println!("    {} README.md", "✓".bright_green());

        println!("\n{}", "✓ All artifacts generated successfully!".bright_green().bold());

        Ok(())
    }

    fn create_directory_structure(&self, output_dir: &str) -> Result<()> {
        fs::create_dir_all(output_dir)?;
        fs::create_dir_all(format!("{}/tests", output_dir))?;
        Ok(())
    }

    fn generate_readme(&self, schema: &CanonicalSchema, output_dir: &str) -> Result<()> {
        let readme = format!(
            r#"# {} Agent

Auto-generated extraction agent from canonical schema.

## Schema Information

- **Extraction Name**: {}
- **Version**: {}
- **Description**: {}
- **Tool Name**: {}
- **Agent Name**: {}

## Input Schema

```json
{}
```

## Output Schema

```json
{}
```

## Browser Configuration

- **Profile**: {}
- **Starting URL**: {}
- **Timeout**: {} seconds
- **Requires Login**: {}

## Generated Artifacts

- `stack.py` - CDK stack definition
- `browser_script_template.json` - Browser automation script template
- `tool_spec.json` - Tool specification for agent
- `output_tool_spec.json` - Output tool (print_output) specification
- `batch_mapping.json` - Batch processor mapping configuration
- `validator.py` - Schema validator
- `canonical_schema.json` - Original canonical schema

## Usage

### Deploy the Agent

```bash
cd {}
cdk deploy
```

### Test Locally

```bash
python validator.py --input test_input.json --output test_output.json
```

### Use in Batch Processing

Configure the batch processor with `batch_mapping.json`:

```bash
aws stepfunctions start-execution \
  --state-machine-arn <batch-processor-arn> \
  --input file://batch_input.json
```

## Metadata

- **Author**: {}
- **Created**: {}
- **Tags**: {}
- **Use Cases**: {}
"#,
            schema.extraction_name,
            schema.extraction_name,
            schema.version,
            schema.description,
            schema.tool_name(),
            schema.agent_name(),
            serde_json::to_string_pretty(&schema.input_schema)?,
            serde_json::to_string_pretty(&schema.output_schema)?,
            schema.browser_config.profile_name,
            schema.browser_config.starting_url,
            schema.browser_config.timeout,
            schema.browser_config.requires_login,
            output_dir,
            schema.metadata.author,
            schema.metadata.created_at,
            schema.metadata.tags.join(", "),
            schema.metadata.use_cases.join(", "),
        );

        fs::write(format!("{}/README.md", output_dir), readme)?;

        Ok(())
    }
}

impl Default for Generator {
    fn default() -> Self {
        Self::new()
    }
}
