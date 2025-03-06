# Web Scraper Project Guidelines

## Purpose

The purpose of this tool is to navigate the web and extract relevant information from various websites. The tool is designed to get instructions from an LLM on how to perform searches and extract data, and then execute those instructions. The tool can be used in an iterative mode, where the LLM can refine its instructions based on the results of previous searches.

## Build Commands

- `npm install` - Install dependencies
- `npm run build` - Build the TypeScript code
- `npm run clean` - Clean the dist directory
- `sam build` - Build using SAM CLI
- `sam local invoke WebScraperFunction --event tests/test-event.json` - Test locally with SAM

## Code Style Guidelines

- Use TypeScript strict mode and strong typing
- Use interfaces for input/output type definitions
- Follow camelCase for variables and functions
- Use async/await pattern for asynchronous operations
- Always include proper error handling with try/catch blocks
- Use structured logging with @aws-lambda-powertools/logger
- Lambda handler should maintain Handler<T, R> typing pattern

## Project Structure

- Source code in `src/` directory
- Tests in `tests/` directory
- Build output in `dist/` directory
- Chrome binary in Lambda layer

## Roadmap

- Get instructions from LLM
- Execute instructions
- Return results to LLM
- Iterate on instructions and results
- Refine results based on LLM feedback
