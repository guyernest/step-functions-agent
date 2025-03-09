# Lambda Runtime API Proxy * Developer Guide

There are a few ways to build Lambda extensions that we tried out. This one is built on the lessons learned from the other approaches. We need to built a proxy and not a standalone extension, as the events that are received by the extension don't include the input and output of the Lambda function. Since we want to be able eventually to manipulate the input and output of the Lambda function, we need to build a proxy.

We will do it in Rust, as it is a systems programming language that is fast and safe.

We will do it in small steps:

* Building a simple Lambda extension in python that simply logs the input event. This lambda function will use the extension as a layer that will be deployed with the function to the /opt/extensions directory.
* building the proxy first as it is without any changes, and deploy it with the above Lambda function. We can see that the logs are written and can everything is working, without any changes.
* Next we will upgrade the proxy to newer version of hyper and tokio, and make sure that it is still working.
* Then adding the ability to manipulate the input and output of the Lambda function.

## Build & Test Commands

* `cargo lambda build --extension --target x86_64-unknown-linux-musl` * Standard build of the lambda extension
* `cargo lambda build --extension --target aarch64-unknown-linux-musl` * Cross-compile for ARM64
* `cargo test` * Run tests
* `make` or `make default` * Build and deploy layer
* `make clean` * Clean build and cargo artifacts
* `make zip` * Create deployment zip file
* `make doc` * Generate documentation
* `cross build --release --target x86_64-unknown-linux-musl` * Cross-compile for x86_64
* `cross build --release --target aarch64-unknown-linux-musl` * Cross-compile for ARM64

## Code Style Guidelines

* Follow standard Rust naming conventions:
  * `snake_case` for functions/variables
  * `SCREAMING_SNAKE_CASE` for constants
* Group imports logically, with stdlib first, then external crates
* Use doc comments with `///` for items and `//!` for modules
* Use descriptive error messages in `expect()` and `unwrap_or_else()`
* Prefer strong typing over raw strings/integers
* Organize modules with clear hierarchical structure
* Use Tokio async/await consistently for async operations
* Make liberal use of Rust's type system for safety guarantees

## Architecture

This project is a Lambda Runtime API Proxy extension written in Rust, designed to intercept and process Lambda function invocations.
