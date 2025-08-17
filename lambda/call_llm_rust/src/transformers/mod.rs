use crate::error::ServiceError;
use crate::models::{LLMInvocation, TransformedRequest, TransformedResponse};
use async_trait::async_trait;
use serde_json::Value;
use std::collections::HashMap;

mod openai;
mod anthropic;
mod gemini;
mod bedrock;
mod utils;

pub use self::openai::OpenAITransformer;
pub use self::anthropic::AnthropicTransformer;
pub use self::gemini::GeminiTransformer;
pub use self::bedrock::BedrockTransformer;

#[async_trait]
pub trait MessageTransformer: Send + Sync {
    /// Transform unified format to provider-specific request format
    fn transform_request(&self, invocation: &LLMInvocation) -> Result<TransformedRequest, ServiceError>;
    
    /// Transform provider response to unified format
    fn transform_response(&self, response: Value) -> Result<TransformedResponse, ServiceError>;
    
    /// Get provider-specific headers if needed
    fn get_headers(&self) -> HashMap<String, String> {
        HashMap::new()
    }
}

pub struct TransformerRegistry {
    transformers: HashMap<String, Box<dyn MessageTransformer>>,
}

impl TransformerRegistry {
    pub fn new() -> Self {
        let mut transformers: HashMap<String, Box<dyn MessageTransformer>> = HashMap::new();
        
        // Register OpenAI transformer (also used for XAI, DeepSeek)
        let openai = Box::new(OpenAITransformer);
        transformers.insert("openai_v1".to_string(), openai);
        
        // Register Anthropic transformer
        let anthropic = Box::new(AnthropicTransformer);
        transformers.insert("anthropic_v1".to_string(), anthropic);
        
        // Register Gemini transformer
        let gemini = Box::new(GeminiTransformer);
        transformers.insert("gemini_v1".to_string(), gemini);
        
        // Register Bedrock transformer (for Jamba, Nova, etc.)
        let bedrock = Box::new(BedrockTransformer);
        transformers.insert("bedrock_v1".to_string(), bedrock);
        
        Self { transformers }
    }
    
    pub fn get(&self, name: &str) -> Result<&dyn MessageTransformer, ServiceError> {
        self.transformers
            .get(name)
            .map(|t| t.as_ref())
            .ok_or_else(|| ServiceError::TransformerNotFound(name.to_string()))
    }
}