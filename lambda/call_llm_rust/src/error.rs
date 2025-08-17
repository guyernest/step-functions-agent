use thiserror::Error;

#[derive(Error, Debug)]
pub enum ServiceError {
    #[error("Transformer not found: {0}")]
    TransformerNotFound(String),

    #[error("Secret not found: {0}")]
    SecretNotFound(String),

    #[error("Secret key not found: {0} in secret: {1}")]
    SecretKeyNotFound(String, String),

    #[error("AWS SDK error: {0}")]
    AwsSdkError(#[from] aws_sdk_secretsmanager::Error),

    #[error("HTTP request failed: {0}")]
    HttpError(#[from] reqwest::Error),

    #[error("JSON serialization error: {0}")]
    JsonError(#[from] serde_json::Error),

    #[error("Provider API error: {provider} returned {status}: {message}")]
    ProviderApiError {
        provider: String,
        status: u16,
        message: String,
    },

    #[error("Invalid configuration: {0}")]
    InvalidConfiguration(String),

    #[error("Transform error: {0}")]
    TransformError(String),

    #[error("Timeout after {0} seconds")]
    Timeout(u64),

    #[error("Rate limit exceeded for provider: {0}")]
    RateLimitExceeded(String),

    #[error("Lambda runtime error: {0}")]
    LambdaError(#[from] lambda_runtime::Error),

    #[error("Unknown error: {0}")]
    Unknown(String),
}

// Lambda runtime will automatically handle the error conversion
// since ServiceError implements std::error::Error