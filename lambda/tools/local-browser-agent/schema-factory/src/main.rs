use anyhow::Result;
use clap::{Parser, Subcommand};
use colored::Colorize;

mod schema;
mod generator;
mod validator;
mod templates;
mod commands;

use commands::{generate, validate, deploy, list, test};

#[derive(Parser)]
#[command(name = "schema-factory")]
#[command(author, version, about, long_about = None)]
#[command(about = "Generate browser automation extraction agents from canonical schemas")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Generate all artifacts from a canonical schema
    Generate {
        /// Path to canonical schema JSON file
        #[arg(short, long)]
        schema: String,

        /// Output directory for generated artifacts
        #[arg(short, long)]
        output_dir: String,

        /// Deploy after generation
        #[arg(short, long, default_value = "false")]
        deploy: bool,

        /// AWS environment (dev, prod)
        #[arg(short, long, default_value = "dev")]
        env: String,
    },

    /// Validate existing agent against schema
    Validate {
        /// Path to canonical schema JSON file
        #[arg(short, long)]
        schema: String,

        /// Agent ARN to validate
        #[arg(short, long)]
        agent_arn: Option<String>,

        /// Check tool specifications
        #[arg(long, default_value = "false")]
        check_tools: bool,

        /// Check output mapping
        #[arg(long, default_value = "false")]
        check_output_mapping: bool,
    },

    /// Deploy generated agent to AWS
    Deploy {
        /// Path to canonical schema JSON file
        #[arg(short, long)]
        schema: String,

        /// AWS environment
        #[arg(short, long, default_value = "dev")]
        env: String,

        /// Keep previous version
        #[arg(long, default_value = "false")]
        keep_previous_version: bool,
    },

    /// List all registered schemas
    List {
        /// Show detailed information
        #[arg(short, long, default_value = "false")]
        verbose: bool,

        /// Filter by tag
        #[arg(short, long)]
        tag: Option<String>,
    },

    /// Test schema locally before deployment
    Test {
        /// Path to canonical schema JSON file
        #[arg(short, long)]
        schema: String,

        /// Path to test data JSON file
        #[arg(short = 'd', long)]
        test_data: String,

        /// Run browser automation test
        #[arg(long, default_value = "false")]
        run_browser: bool,
    },

    /// Migrate from one schema version to another
    Migrate {
        /// Path to source schema
        #[arg(short, long)]
        from: String,

        /// Path to target schema
        #[arg(short, long)]
        to: String,

        /// Migration strategy (in-place, blue-green)
        #[arg(short, long, default_value = "blue-green")]
        strategy: String,
    },
}

#[tokio::main]
async fn main() -> Result<()> {
    let cli = Cli::parse();

    match cli.command {
        Commands::Generate { schema, output_dir, deploy: should_deploy, env } => {
            println!("{}", "🏭 Schema Factory - Generate".bright_blue().bold());
            println!("Schema: {}", schema.bright_yellow());
            println!("Output: {}", output_dir.bright_yellow());

            generate::execute(&schema, &output_dir, should_deploy, &env).await?;

            println!("\n{}", "✓ Generation complete!".bright_green().bold());
        }

        Commands::Validate { schema, agent_arn, check_tools, check_output_mapping } => {
            println!("{}", "🔍 Schema Factory - Validate".bright_blue().bold());
            println!("Schema: {}", schema.bright_yellow());

            validate::execute(&schema, agent_arn.as_deref(), check_tools, check_output_mapping).await?;
        }

        Commands::Deploy { schema, env, keep_previous_version } => {
            println!("{}", "🚀 Schema Factory - Deploy".bright_blue().bold());
            println!("Schema: {}", schema.bright_yellow());
            println!("Environment: {}", env.bright_yellow());

            deploy::execute(&schema, &env, keep_previous_version).await?;

            println!("\n{}", "✓ Deployment complete!".bright_green().bold());
        }

        Commands::List { verbose, tag } => {
            println!("{}", "📋 Schema Factory - List Schemas".bright_blue().bold());

            list::execute(verbose, tag.as_deref()).await?;
        }

        Commands::Test { schema, test_data, run_browser } => {
            println!("{}", "🧪 Schema Factory - Test".bright_blue().bold());
            println!("Schema: {}", schema.bright_yellow());
            println!("Test Data: {}", test_data.bright_yellow());

            test::execute(&schema, &test_data, run_browser).await?;
        }

        Commands::Migrate { from, to, strategy } => {
            println!("{}", "🔄 Schema Factory - Migrate".bright_blue().bold());
            println!("From: {}", from.bright_yellow());
            println!("To: {}", to.bright_yellow());
            println!("Strategy: {}", strategy.bright_yellow());

            commands::migrate::execute(&from, &to, &strategy).await?;
        }
    }

    Ok(())
}
