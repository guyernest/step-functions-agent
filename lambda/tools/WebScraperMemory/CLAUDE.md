# CLAUDE.md - WebScraperMemory Codebase Guide

## Purpose

The WebScraperMemory Lambda function tool is part of an AI agent that learns and extracts information from websites. The Memory component is responsible for storing and retrieving data from a DynamoDB table, for the extraction scripts that are performed by the WebScraper tool. The tool read and writes two types of records:

* Site Schema - Describes the site functionality and the set of scripts that are already available to extract information from the site.
* Extraction Script - Describes a script that can be used to extract specific type of information from the site.

The WebScraperMemory tool helps the AI Agent, and its LLM model to quickly learn and adapt to new sites, and to be able to extract information from them, efficiently once a successful script is created.

## Build/Test Commands

- Build for production: `cargo lambda build --arm64 --release`
- Build for development: `cargo lambda build --arm64`
- Run tests: `cargo test`
- Run single test: `cargo test test_event_handler`
- Local invoke with SAM: `sam build && sam local invoke WebScraperMemory --event tests/test-event.json`

## Code Style Guidelines

- **Formatting**: Use standard Rust formatting (rustfmt)
- **Error Handling**: Use `anyhow::Result` for function results, with contextual error messages
- **Types**: Define custom types with proper Serde derive macros (`Serialize`, `Deserialize`)
- **Naming**:
  - Use PascalCase for types, structs, and function names
  - Use snake_case for variables and module names
  - Prefix internal functions with `pub(crate)`
- **File Structure**:
  - `main.rs`: Entry point with minimal logic
  - `event_handler.rs`: Event parsing and core logic
- **Testing**: Include unit tests in the same file as the implementation with the `#[cfg(test)]` attribute
- **Imports**: Order imports by standard library, then external crates, then local modules
- **Error Logging**: Use `tracing` crate for all logging (info, error, debug)