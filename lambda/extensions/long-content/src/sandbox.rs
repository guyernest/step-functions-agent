//! Interact with the Lambda Runtime API, the service managing this sandbox
//!
//! Includes helpers for sending request for `next` and posting back responses.
//!

use std::sync::Arc;

use hyper::{Body, Error, HeaderMap, Request, Response};

pub async fn next(headers: &HeaderMap, path: &str) -> Result<(Arc<String>, Response<Body>), Error> {
    println!("[LRAP] Getting next event from Lambda Runtime API: {}", path);
    
    let uri = hyper::Uri::builder()
        .scheme("http")
        .authority(crate::env::sandbox_runtime_api())
        .path_and_query(path)
        .build()
        .expect("[LRAP] Error building Sandbox Lambda Runtime API endpoint URL");

    println!("[LRAP] Sending request to Lambda Runtime API: GET {}", uri);
    
    let mut req = Request::builder()
        .method("GET")
        .uri(uri.clone())
        .body(Body::empty())
        .expect("Cannot create Sandbox Lambda Runtime API request");

    *req.headers_mut() = headers.clone();

    println!("[LRAP] Sending request to Lambda Runtime API. Awaiting response...");
    let response = hyper::Client::new().request(req).await?;
    println!("[LRAP] Received response from Lambda Runtime API: {}", response.status());

    // Log all headers for debugging
    println!("[LRAP] Response headers:");
    for (name, value) in response.headers() {
        println!("[LRAP]   {}: {}", name, value.to_str().unwrap_or("(not utf8)"));
    }

    match response.headers().get("lambda-runtime-aws-request-id") {
        Some(id) => {
            let id = id.to_str().expect("Error parsing Lambda Runtime API request ID");
            println!("[LRAP] Found request ID in response: {}", id);
            Ok((Arc::new(id.to_string()), response))
        },
        // Instead of panicking, use a fallback request ID
        _ => {
            eprintln!("[LRAP] WARNING: Sandbox Lambda Runtime API response missing 'lambda-runtime-aws-request-id' header");
            println!("[LRAP] Using fallback request ID instead of panicking");
            let fallback_id = format!("fallback-{}", uuid::Uuid::new_v4().to_string());
            println!("[LRAP] Using fallback request ID: {}", fallback_id);
            Ok((Arc::new(fallback_id), response))
        }
    }
}

/// Send a request through a {hyper::Client}
pub async fn send_request(request: Request<Body>) -> Result<Response<Body>, Error> {
    hyper::Client::new().request(request).await
}

#[allow(dead_code)]
pub async fn create_invoke_result_request(id: &str, body: Body) -> Result<Request<Body>, Error> {
    let uri = hyper::Uri::builder()
        .scheme("http")
        .authority(crate::env::sandbox_runtime_api())
        .path_and_query(format!(
            "/{}/runtime/invocation/{}/response",
            crate::LAMBDA_RUNTIME_API_VERSION,
            id
        ))
        .build()
        .expect("[LRAP] Error building Sandbox Lambda Runtime API endpoint URL");

    Ok(hyper::Request::builder()
        .method("POST")
        .uri(uri)
        .body(body)
        .expect("Cannot create Sandbox Lambda Runtime API request"))
}

/// Lambda Extensions API
///
/// Interact with the Lambda sandbox as a Lambda Extension
///
#[allow(dead_code)]
pub mod extension {
    use hyper::{Body, Response};
    use once_cell::sync::OnceCell;

    /// Cannonical Lambda Extensions API version
    ///
    /// Documentation: https://docs.aws.amazon.com/lambda/latest/dg/runtimes-extensions-api.html
    ///
    const EXTENSION_API_VERSION: &str = "2020-01-01";
    static LAMBDA_EXTENSION_IDENTIFIER: OnceCell<String> = OnceCell::new();

    fn find_extension_name() -> String {
        let name = crate::EXTENSION_NAME.to_owned();
        println!("[LRAP:Extension] Using extension name: {}", name);
        name
    }

    pub(super) fn extension_id() -> &'static String {
        LAMBDA_EXTENSION_IDENTIFIER
            .get()
            .expect("[LRAP:Extension] Lambda Extension Identifier not set!")
    }

    fn make_uri(path: &str) -> hyper::Uri {
        let authority = crate::env::sandbox_runtime_api();
        let path_and_query = format!("/{}/extension{}", EXTENSION_API_VERSION, path);
        println!("[LRAP:Extension] Building URI: http://{}{}",
                authority, path_and_query);
                
        hyper::Uri::builder()
            .scheme("http")
            .authority(authority)
            .path_and_query(path_and_query)
            .build()
            .expect("[LRAP:Extension] Error building Lambda Extensions API endpoint URL")
    }

    /// Register the extension with the Lambda Extensions API
    pub async fn register() {
        println!("[LRAP:Extension] Registering extension with Lambda Extensions API");
        let uri = make_uri("/register");
        println!("[LRAP:Extension] Registration URI: {}", uri);

        let body = hyper::Body::from(r#"{"events":["INVOKE"]}"#);
        println!("[LRAP:Extension] Registration payload: {}", r#"{"events":["INVOKE"]}"#);
        
        let mut request = hyper::Request::builder()
            .method("POST")
            .uri(uri)
            .body(body)
            .expect("[LRAP:Extension] Cannot create Lambda Extensions API request");

        // Set Lambda Extension Name header
        let extension_name = find_extension_name();
        println!("[LRAP:Extension] Setting Lambda-Extension-Name header: {}", extension_name);
        request.headers_mut().append(
            "Lambda-Extension-Name",
            extension_name.try_into().unwrap(),
        );

        println!("[LRAP:Extension] Sending registration request");
        let response = super::send_request(request)
            .await
            .expect("[LRAP:Extension] Cannot send Lambda Extensions API request to register");

        println!("[LRAP:Extension] Registration response status: {}", response.status());
        println!("[LRAP:Extension] Registration response headers:");
        for (name, value) in response.headers() {
            println!("[LRAP:Extension]   {}: {}", 
                    name, value.to_str().unwrap_or("(not utf8)"));
        }

        let extension_identifier = response
            .headers()
            .get("lambda-extension-identifier")
            .expect("[LRAP:Extension] Lambda Extensions API response missing 'lambda-extension-identifier' header in Lambda Extensions API POST:register response")
            .to_str()
            .unwrap();

        println!("[LRAP:Extension] Got extension identifier: {}", extension_identifier);
        LAMBDA_EXTENSION_IDENTIFIER
            .set(extension_identifier.to_owned())
            .expect("[LRAP:Extension] Error setting Lambda Extensions API request ID");
            
        println!("[LRAP:Extension] Registration complete");
    }

    /// Get next event from the Lambda Extensions API
    ///
    pub async fn get_next() -> Result<Response<Body>, hyper::Error> {
        println!("[LRAP:Extension] Getting next extension event");
        let uri = make_uri("/event/next");
        println!("[LRAP:Extension] Next event URI: {}", uri);

        let mut request = hyper::Request::builder()
            .method("GET")
            .uri(uri)
            .body(Body::empty())
            .expect("[LRAP:Extension] Cannot create Lambda Extensions API request");

        let ext_id = extension_id();
        println!("[LRAP:Extension] Using extension identifier: {}", ext_id);
        request.headers_mut().insert(
            "Lambda-Extension-Identifier",
            ext_id.try_into().unwrap(),
        );

        println!("[LRAP:Extension] Sending next event request");
        match super::send_request(request).await {
            Ok(response) => {
                println!("[LRAP:Extension] Next event response status: {}", response.status());
                println!("[LRAP:Extension] Next event response headers:");
                for (name, value) in response.headers() {
                    println!("[LRAP:Extension]   {}: {}", 
                            name, value.to_str().unwrap_or("(not utf8)"));
                }
                
                // We return the result now to handle it in the caller
                Ok(response)
            },
            Err(e) => {
                eprintln!("[LRAP:Extension] Error getting next event: {}", e);
                Err(e)
            }
        }
    }
}
