use anyhow::Result;

fn main() -> Result<()> {
    // Call the main function from the library
    // We don't need #[tokio::main] here because the library function already has it
    local_sfn_agent::main()
}