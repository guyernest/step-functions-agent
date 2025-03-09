//! Lambda Runtime API Proxy Extension library

pub mod env;
pub mod route;
pub mod sandbox;
pub mod stats;
pub mod transform;

/// Name to register with the Lambda Extension API.
pub const EXTENSION_NAME: &str = "lrap";

/// Default port to listen on, overridden by LRAP_LISTENER_PORT environment variable
pub const DEFAULT_PROXY_PORT: u16 = 9009;

/// Lambda Runtime API version
pub static LAMBDA_RUNTIME_API_VERSION: &str = "2018-06-01";
