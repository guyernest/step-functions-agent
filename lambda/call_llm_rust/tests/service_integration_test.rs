/// Integration tests for the Unified LLM Service
/// These tests exercise the full service pipeline including:
/// - Message transformation to provider format
/// - API calls through the service
/// - Response transformation back to unified format
/// - Tool calling flow

use serde_json::json;
use std::env;
use unified_llm_service::models::{
    LLMInvocation, ProviderConfig, UnifiedMessage, MessageContent, ContentBlock, UnifiedTool,
};
use unified_llm_service::service::UnifiedLLMService;

/// Helper to load API key from environment or .env file
fn setup_test_env() -> Result<(), String> {
    // Try loading .env file (ignore if it doesn't exist)
    let _ = dotenv::dotenv();
    Ok(())
}

/// Create a weather tool definition (unified format)
fn create_weather_tool() -> UnifiedTool {
    UnifiedTool {
        name: "get_weather".to_string(),
        description: "Get the current weather in a given location".to_string(),
        input_schema: json!({
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The city and country, e.g. Tokyo, Japan"
                }
            },
            "required": ["location"]
        }),
    }
}

/// Helper function for OpenAI testing
async fn test_openai_service_tool_calling_impl() -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    setup_test_env()?;
    
    println!("\n=== Testing OpenAI through UnifiedLLMService ===");
    
    // Check for API key
    if env::var("OPENAI_API_KEY").is_err() {
        eprintln!("Skipping test: OPENAI_API_KEY not set");
        return Ok(());
    }
    
    // Initialize the service (this would normally be done in Lambda handler)
    let service = UnifiedLLMService::new().await?;
    
    // Create provider config (this would come from Step Functions)
    let provider_config = ProviderConfig {
        provider_id: "openai".to_string(),
        model_id: "gpt-4o-mini".to_string(),
        endpoint: "https://api.openai.com/v1/chat/completions".to_string(),
        auth_header_name: "Authorization".to_string(),
        auth_header_prefix: Some("Bearer ".to_string()),
        secret_path: "/ai-agent/llm-secrets/prod".to_string(),
        secret_key_name: "OPENAI_API_KEY".to_string(),
        request_transformer: "openai_v1".to_string(),
        response_transformer: "openai_v1".to_string(),
        timeout: 30,
        custom_headers: None,
    };
    
    // Step 1: Initial request with tool (unified format)
    println!("Step 1: Sending request with weather tool...");
    let mut invocation = LLMInvocation {
        provider_config: provider_config.clone(),
        messages: vec![
            UnifiedMessage {
                role: "user".to_string(),
                content: MessageContent::Text {
                    content: "What's the weather like in Tokyo?".to_string(),
                },
            },
        ],
        tools: Some(vec![create_weather_tool()]),
        temperature: Some(0.7),
        max_tokens: Some(1000),
        top_p: None,
        stream: Some(false),
    };
    
    // Process through our service (this transforms to OpenAI format and back)
    let response1 = service.process(invocation.clone()).await?;
    
    println!("Response metadata: {:?}", response1.metadata);
    
    // Verify we got a tool call in the unified format
    assert!(response1.function_calls.is_some(), "Expected function calls");
    let function_calls = response1.function_calls.as_ref().unwrap();
    assert!(!function_calls.is_empty(), "Expected at least one function call");
    
    let weather_call = &function_calls[0];
    assert_eq!(weather_call.name, "get_weather");
    
    // Extract location
    let location = weather_call.input.get("location")
        .and_then(|v| v.as_str())
        .unwrap_or("unknown");
    println!("Tool called with location: {}", location);
    assert!(location.to_lowercase().contains("tokyo"), "Expected Tokyo in location");
    
    // Step 2: Add tool result and get final response
    println!("\nStep 2: Sending tool result back...");
    
    // Convert AssistantMessage to UnifiedMessage
    let assistant_msg = UnifiedMessage {
        role: "assistant".to_string(),
        content: MessageContent::Blocks { content: response1.message.content },
    };
    invocation.messages.push(assistant_msg);
    
    // Add tool result (unified format)
    invocation.messages.push(UnifiedMessage {
        role: "user".to_string(),
        content: MessageContent::Blocks {
            content: vec![ContentBlock::ToolResult {
                tool_use_id: weather_call.id.clone(),
                content: "The weather in Tokyo is sunny with a temperature of 22°C (72°F). Clear skies expected all day.".to_string(),
            }],
        },
    });
    
    // Remove tools for second request
    invocation.tools = None;
    
    // Process again (transforms tool result to OpenAI format and back)
    let response2 = service.process(invocation).await?;
    
    println!("Final response metadata: {:?}", response2.metadata);
    
    // Verify final response contains weather info
    let final_content = match &response2.message.content[0] {
        ContentBlock::Text { text } => text,
        _ => panic!("Expected text response"),
    };
    
    println!("Final response: {}", final_content);
    assert!(
        final_content.to_lowercase().contains("sunny") ||
        final_content.to_lowercase().contains("22") ||
        final_content.to_lowercase().contains("clear"),
        "Expected weather information in final response"
    );
    
    // Verify token usage is tracked
    assert!(response2.metadata.tokens_used.is_some(), "Expected token usage");
    let tokens = response2.metadata.tokens_used.unwrap();
    assert!(tokens.input_tokens > 0, "Expected input tokens");
    assert!(tokens.output_tokens > 0, "Expected output tokens");
    
    println!("✅ OpenAI service test passed!");
    Ok(())
}

/// Test OpenAI through service
#[tokio::test]
#[ignore]
async fn test_openai_service_tool_calling() -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    test_openai_service_tool_calling_impl().await
}

/// Helper function for Anthropic testing
async fn test_anthropic_service_tool_calling_impl() -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    setup_test_env()?;
    
    println!("\n=== Testing Anthropic through UnifiedLLMService ===");
    
    // Check for API key
    if env::var("ANTHROPIC_API_KEY").is_err() {
        eprintln!("Skipping test: ANTHROPIC_API_KEY not set");
        return Ok(());
    }
    
    // Initialize the service
    let service = UnifiedLLMService::new().await?;
    
    // Create provider config for Anthropic
    let provider_config = ProviderConfig {
        provider_id: "anthropic".to_string(),
        model_id: "claude-3-5-sonnet-20241022".to_string(),
        endpoint: "https://api.anthropic.com/v1/messages".to_string(),
        auth_header_name: "x-api-key".to_string(),
        auth_header_prefix: None,
        secret_path: "/ai-agent/llm-secrets/prod".to_string(),
        secret_key_name: "ANTHROPIC_API_KEY".to_string(),
        request_transformer: "anthropic_v1".to_string(),
        response_transformer: "anthropic_v1".to_string(),
        timeout: 30,
        custom_headers: None,
    };
    
    // Step 1: Initial request with tool
    println!("Step 1: Sending request with weather tool...");
    let mut invocation = LLMInvocation {
        provider_config: provider_config.clone(),
        messages: vec![
            UnifiedMessage {
                role: "user".to_string(),
                content: MessageContent::Text {
                    content: "What's the weather like in Tokyo?".to_string(),
                },
            },
        ],
        tools: Some(vec![create_weather_tool()]),
        temperature: Some(0.7),
        max_tokens: Some(1000),
        top_p: None,
        stream: Some(false),
    };
    
    // Process through our service (transforms to Anthropic format and back)
    let response1 = service.process(invocation.clone()).await?;
    
    println!("Response metadata: {:?}", response1.metadata);
    
    // Verify tool call
    assert!(response1.function_calls.is_some(), "Expected function calls");
    let function_calls = response1.function_calls.as_ref().unwrap();
    assert!(!function_calls.is_empty(), "Expected at least one function call");
    
    let weather_call = &function_calls[0];
    assert_eq!(weather_call.name, "get_weather");
    
    let location = weather_call.input.get("location")
        .and_then(|v| v.as_str())
        .unwrap_or("unknown");
    println!("Tool called with location: {}", location);
    assert!(location.to_lowercase().contains("tokyo"), "Expected Tokyo in location");
    
    // Step 2: Send tool result
    println!("\nStep 2: Sending tool result back...");
    
    // Convert AssistantMessage to UnifiedMessage
    let assistant_msg = UnifiedMessage {
        role: "assistant".to_string(),
        content: MessageContent::Blocks { content: response1.message.content },
    };
    invocation.messages.push(assistant_msg);
    
    // Add tool result
    invocation.messages.push(UnifiedMessage {
        role: "user".to_string(),
        content: MessageContent::Blocks {
            content: vec![ContentBlock::ToolResult {
                tool_use_id: weather_call.id.clone(),
                content: "The weather in Tokyo is sunny with a temperature of 22°C (72°F). Clear skies expected all day.".to_string(),
            }],
        },
    });
    
    invocation.tools = None;
    
    // Process again
    let response2 = service.process(invocation).await?;
    
    println!("Final response metadata: {:?}", response2.metadata);
    
    // Verify final response
    let final_content = match &response2.message.content[0] {
        ContentBlock::Text { text } => text,
        _ => panic!("Expected text response"),
    };
    
    println!("Final response: {}", final_content);
    assert!(
        final_content.to_lowercase().contains("sunny") ||
        final_content.to_lowercase().contains("22") ||
        final_content.to_lowercase().contains("clear"),
        "Expected weather information in final response"
    );
    
    println!("✅ Anthropic service test passed!");
    Ok(())
}

/// Test Anthropic through service
#[tokio::test]
#[ignore]
async fn test_anthropic_service_tool_calling() -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    test_anthropic_service_tool_calling_impl().await
}

/// Helper function for Gemini testing
async fn test_gemini_service_tool_calling_impl() -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    setup_test_env()?;
    
    println!("\n=== Testing Gemini through UnifiedLLMService ===");
    
    // Check for API key
    if env::var("GEMINI_API_KEY").is_err() {
        eprintln!("Skipping test: GEMINI_API_KEY not set");
        return Ok(());
    }
    
    // Initialize the service
    let service = UnifiedLLMService::new().await?;
    
    // Create provider config for Gemini
    let provider_config = ProviderConfig {
        provider_id: "gemini".to_string(),
        model_id: "gemini-1.5-flash".to_string(),
        endpoint: "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent".to_string(),
        auth_header_name: "x-goog-api-key".to_string(),
        auth_header_prefix: None,
        secret_path: "/ai-agent/llm-secrets/prod".to_string(),
        secret_key_name: "GEMINI_API_KEY".to_string(),
        request_transformer: "gemini_v1".to_string(),
        response_transformer: "gemini_v1".to_string(),
        timeout: 30,
        custom_headers: None,
    };
    
    // Step 1: Initial request with tool
    println!("Step 1: Sending request with weather tool...");
    let mut invocation = LLMInvocation {
        provider_config: provider_config.clone(),
        messages: vec![
            UnifiedMessage {
                role: "user".to_string(),
                content: MessageContent::Text {
                    content: "What's the weather like in Tokyo?".to_string(),
                },
            },
        ],
        tools: Some(vec![create_weather_tool()]),
        temperature: Some(0.7),
        max_tokens: Some(1000),
        top_p: None,
        stream: Some(false),
    };
    
    // Process through our service (transforms to Gemini format and back)
    let response1 = service.process(invocation.clone()).await?;
    
    println!("Response metadata: {:?}", response1.metadata);
    
    // Verify tool call
    assert!(response1.function_calls.is_some(), "Expected function calls");
    let function_calls = response1.function_calls.as_ref().unwrap();
    assert!(!function_calls.is_empty(), "Expected at least one function call");
    
    let weather_call = &function_calls[0];
    assert_eq!(weather_call.name, "get_weather");
    
    let location = weather_call.input.get("location")
        .and_then(|v| v.as_str())
        .unwrap_or("unknown");
    println!("Tool called with location: {}", location);
    assert!(location.to_lowercase().contains("tokyo"), "Expected Tokyo in location");
    
    // Step 2: Send tool result
    println!("\nStep 2: Sending tool result back...");
    
    // Add assistant's response (with tool call)
    let assistant_msg = UnifiedMessage {
        role: "assistant".to_string(),
        content: MessageContent::Blocks { content: response1.message.content },
    };
    invocation.messages.push(assistant_msg);
    
    // Add tool result
    invocation.messages.push(UnifiedMessage {
        role: "user".to_string(),
        content: MessageContent::Blocks {
            content: vec![ContentBlock::ToolResult {
                tool_use_id: weather_call.id.clone(),
                content: "The weather in Tokyo is sunny with a temperature of 22°C (72°F). Clear skies expected all day.".to_string(),
            }],
        },
    });
    
    invocation.tools = None;
    
    // Process again
    let response2 = service.process(invocation).await?;
    
    println!("Final response metadata: {:?}", response2.metadata);
    
    // Verify final response
    let final_content = match &response2.message.content[0] {
        ContentBlock::Text { text } => text,
        _ => panic!("Expected text response"),
    };
    
    println!("Final response: {}", final_content);
    assert!(
        final_content.to_lowercase().contains("sunny") ||
        final_content.to_lowercase().contains("22") ||
        final_content.to_lowercase().contains("clear"),
        "Expected weather information in final response"
    );
    
    println!("✅ Gemini service test passed!");
    Ok(())
}

/// Test Gemini through service
#[tokio::test]
#[ignore]
async fn test_gemini_service_tool_calling() -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    test_gemini_service_tool_calling_impl().await
}

/// Test that transformers correctly convert between formats
#[tokio::test]
#[ignore]
async fn test_all_providers_through_service() {
    println!("\n🚀 Testing All Providers through UnifiedLLMService\n");
    
    let mut results = Vec::new();
    
    // Test OpenAI
    print!("Testing OpenAI transformer... ");
    let openai_result = tokio::spawn(async {
        test_openai_service_tool_calling_impl().await
    }).await.unwrap();
    
    match openai_result {
        Ok(_) => {
            println!("✅");
            results.push(("OpenAI", true, String::new()));
        }
        Err(e) => {
            println!("❌");
            results.push(("OpenAI", false, e.to_string()));
        }
    }
    
    // Test Anthropic
    print!("Testing Anthropic transformer... ");
    let anthropic_result = tokio::spawn(async {
        test_anthropic_service_tool_calling_impl().await
    }).await.unwrap();
    
    match anthropic_result {
        Ok(_) => {
            println!("✅");
            results.push(("Anthropic", true, String::new()));
        }
        Err(e) => {
            println!("❌");
            results.push(("Anthropic", false, e.to_string()));
        }
    }
    
    // Test Gemini
    print!("Testing Gemini transformer... ");
    let gemini_result = tokio::spawn(async {
        test_gemini_service_tool_calling_impl().await
    }).await.unwrap();
    
    match gemini_result {
        Ok(_) => {
            println!("✅");
            results.push(("Gemini", true, String::new()));
        }
        Err(e) => {
            println!("❌");
            results.push(("Gemini", false, e.to_string()));
        }
    }
    
    // Print summary
    println!("\n=== Test Summary ===");
    for (provider, passed, error) in &results {
        if *passed {
            println!("✅ {}: PASSED", provider);
        } else {
            println!("❌ {}: FAILED - {}", provider, error);
        }
    }
    
    let total = results.len();
    let passed = results.iter().filter(|(_, p, _)| *p).count();
    println!("\nTotal: {}/{} tests passed", passed, total);
    
    if passed < total {
        panic!("Some tests failed!");
    }
}