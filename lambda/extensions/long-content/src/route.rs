//! Routing for Runtime API requests.  This builds out the services and stitches them together as
//! well as builds routing tables for HTTP methods on resources to proxy the Lambda Runtime API.
//!
//!

use std::sync::Arc;

use httprouter::Router;
use hyper::{Body, Error, Request, Response, Uri};

use crate::{env, sandbox, stats, transform};

pub fn make_route<'a>() -> Router<'a> {
    // Route `invocation/next` demonstrates hooks for filtering incoming request events
    // Users can implement a similar patern in `invocation/:id/response` to filter responses
    let router = Router::default()
        .get("/", passthru_proxy)
        .get("/:apiver/runtime/invocation/next", proxy_invocation_next)
        .post(
            "/:apiver/runtime/invocation/:reqid/response",
            proxy_invocation_response,
        )
        .post("/:apiver/runtime/invocation/:reqid/error", passthru_proxy)
        // The matchit router conflicts with similar wildcard patterns, so we'll rely on not_found for other routes
        .not_found(notfound_passthru_proxy);
    router
}

/// Pass-through the request, but log the unhandled path and method
#[allow(dead_code)]
pub async fn notfound_passthru_proxy(req: Request<Body>) -> Result<Response<Body>, Error> {
    // Log a more informative message
    println!(
        "[LRAP] Handling unmatched route: path={} method={}",
        &req.uri().path(),
        &req.method()
    );

    // EMERGENCY FALLBACK: If the Lambda Runtime is trying to connect and we're not ready yet,
    // we need to respond quickly with something valid instead of timing out
    if req.method() == hyper::Method::GET && req.uri().path().contains("/runtime/invocation/next") {
        println!("[LRAP] !!! EMERGENCY RESPONSE: Detected GET for /next but was routed to notfound handler !!!");
        // Return a valid placeholder response to buy us time
        let response = Response::builder()
            .status(200)
            .header("lambda-runtime-aws-request-id", "emergency-fallback-id")
            .body(Body::from(r#"{"source":"lrap-emergency-fallback","message":"This is a fallback response to prevent Lambda runtime timeout"}"#))
            .unwrap();
        return Ok(response);
    }

    // Check if this is a GET request for a specific invocation
    if req.method() == hyper::Method::GET
        && req.uri().path().contains("/runtime/invocation/")
        && !req.uri().path().ends_with("/next")
        && !req.uri().path().ends_with("/response")
        && !req.uri().path().ends_with("/error")
    {
        println!("[LRAP] Detected GET request for invocation details");
    }

    // Forward the request to the actual Lambda Runtime API
    passthru_proxy(req).await
}

#[allow(dead_code)]
pub async fn passthru_proxy(req: Request<Body>) -> Result<Response<Body>, Error> {
    // possible improvement: replace with resource pool or persistent connection
    let endpoint_client = hyper::Client::new();

    // Print detailed information about the request
    println!("[LRAP DEBUG] ===================== PROXY REQUEST START =====================");
    println!("[LRAP DEBUG] Method: {}", req.method());
    println!("[LRAP DEBUG] Path: {}", req.uri().path());
    println!("[LRAP DEBUG] Query: {:?}", req.uri().query());
    println!("[LRAP DEBUG] Headers:");
    for (name, value) in req.headers() {
        println!(
            "[LRAP DEBUG]   {}: {}",
            name,
            value.to_str().unwrap_or("(not utf8)")
        );
    }

    // Check if this is an event input or response
    let is_next_event = req.uri().path().contains("/invocation/next");
    let is_response =
        req.uri().path().contains("/invocation/") && req.uri().path().contains("/response");
    let is_error = req.uri().path().contains("/invocation/") && req.uri().path().contains("/error");

    println!("[LRAP DEBUG] Is next event request: {}", is_next_event);
    println!("[LRAP DEBUG] Is response: {}", is_response);
    println!("[LRAP DEBUG] Is error: {}", is_error);

    // If this is a response, we should be using our special response handler
    if is_response {
        println!("[LRAP WARN] Response detected in passthru_proxy but not handled by proxy_invocation_response!");

        // Attempt to read and log the response body for debugging
        let (parts, body) = req.into_parts();
        let body_bytes = hyper::body::to_bytes(body).await?;
        println!(
            "[LRAP DEBUG] Response body: {}",
            String::from_utf8_lossy(&body_bytes)
        );

        // Reconstruct the request
        let req = Request::from_parts(parts, Body::from(body_bytes));

        // Try calling our response handler directly
        return proxy_invocation_response(req).await;
    }

    // Build the endpoint URI for the actual Lambda Runtime API
    // Use original_runtime_api instead of sandbox_runtime_api to ensure proper proxying
    let endpoint_uri: Uri = Uri::builder()
        .scheme("http")
        .authority(env::original_runtime_api())
        .path_and_query(req.uri().path())
        .build()
        .unwrap();

    println!("[LRAP DEBUG] Forwarding to: {}", endpoint_uri);

    // Log the incoming request
    println!(
        "[LRAP] Proxying request: {} {} -> {}",
        req.method(),
        req.uri().path(),
        endpoint_uri
    );

    // remap URI
    let mut endpoint_req: Request<Body> = req.into();
    *endpoint_req.uri_mut() = endpoint_uri.clone();

    let method = endpoint_req.method().clone();

    match endpoint_client.request(endpoint_req).await {
        Ok(res) => {
            println!(
                "[LRAP] Received response from Lambda Runtime API: {} for {} {}",
                res.status(),
                method,
                endpoint_uri
            );

            // If this is a next event request, we should be using our special handler
            if is_next_event {
                println!("[LRAP WARN] Next event detected in passthru_proxy but not handled by proxy_invocation_next!");
            }

            Ok(res)
        }
        Err(e) => {
            eprintln!(
                "[LRAP] Error invoking endpoint ({} on {}): {:?}",
                method, endpoint_uri, e
            );
            Ok(Response::builder()
                .status(502)
                .body("502 - Bad Gateway: Lambda Runtime API did not process request".into())
                .unwrap())
        }
    }
}

/// Get next invocation; provide hooks for skipping bad requests (payload malicious or ill-formed)
///
/// Flow:
///
///          [App Runtime]               [LRAP]                        [Lambda Service]
///               |                         
///               +---- GET next event --->|
///                                        |
///                                 [ proxy request ]-- GET next event ------>|
///                                                                           |                             
///                                                                           |<---- [ INVOKE with payload ]
///                                        |<--------- event payload ---------|
///                                        |                                   
///                          [ if validation fails: DROP event ]                  
///                                        |                                   
///                                        |----------- GET next event ------>|
///                                                                           |<---- [ INVOKE with payload ]
///                                        |<--------- event payload ---------|
///                                        |                                   
///               |<-- event -----[ if validation succeeds: PASS event ]               
///               |   payload             
///               |                         
///           [ appp logic ]                
///               |                         
///               |--response payload ---->|
///                                        |                                   
///                              [ sanitize response ]-- response sanitized ->|
///                                                                           |----->[ synchronous response ]
///                                         
pub async fn proxy_invocation_next(req: Request<Body>) -> Result<Response<Body>, Error> {
    use std::time::Duration;

    println!("[LRAP] Proxy: received GET next invocation request from Lambda function");
    println!("[LRAP] Request URI: {}", req.uri());
    println!("[LRAP] Request Headers:");
    for (name, value) in req.headers() {
        println!(
            "[LRAP]   {}: {}",
            name,
            value.to_str().unwrap_or("(not utf8)")
        );
    }

    'getNext: loop {
        println!("[LRAP] Starting getNext loop iteration");
        // track either initialization  -or-
        // how long it took to process the event and request next
        stats::get_next_event();

        println!("[LRAP] Calling sandbox::next to get next event from Lambda Runtime API");

        let max_attempts = 5;
        let mut attempt = 0;

        loop {
            attempt += 1;
            println!(
                "[LRAP] Attempt {} of {} to get next event",
                attempt, max_attempts
            );

            match crate::sandbox::next(req.headers(), req.uri().path()).await {
                Ok(response) => {
                    println!("[LRAP] Successfully got next event with request ID");
                    let (aws_request_id, response) = response;

                    // start the counter on the new event
                    stats::event_start();
                    println!("[LRAP] Started event timing");

                    println!("[LRAP] Validating and processing event");
                    match validate_and_mangle_next_event(aws_request_id, response).await {
                        Ok(response) => {
                            println!("[LRAP] Validation succeeded, returning response to Lambda function");
                            return Ok(response);
                        }
                        Err(req) => {
                            println!("[LRAP] Validation failed, sending error response and getting next event");
                            sandbox::send_request(req).await.ok();
                            break; // Break the inner loop and continue the outer 'getNext loop
                        }
                    }
                }
                Err(e) => {
                    eprintln!(
                        "[LRAP] Error getting next invocation from Runtime API: {}",
                        e
                    );
                    eprintln!("[LRAP] uri: {}", req.uri());

                    if attempt >= max_attempts {
                        eprintln!(
                            "[LRAP] Reached maximum retry attempts ({}). Breaking retry loop.",
                            max_attempts
                        );

                        // Create a minimal, valid response that the Lambda function can process
                        // Create a unique request ID for this fallback response
                        let fallback_id = format!("fallback-{}", uuid::Uuid::new_v4());

                        println!("[LRAP] Using fallback request ID: {}", fallback_id);

                        // Create a response with proper headers and body that will be acceptable to the Lambda runtime
                        let minimal_response = Response::builder()
                            .status(200)
                            .header("lambda-runtime-aws-request-id", &fallback_id)
                            .header("lambda-runtime-deadline-ms", (std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_millis() + 3000).to_string())
                            .header("lambda-runtime-invoked-function-arn", "arn:aws:lambda:us-west-2:000000000000:function:fallback-function")
                            .header("lambda-runtime-trace-id", "Root=1-00000000-000000000000000000000000")
                            .body(Body::from(format!(r#"{{
                                "source":"lrap-proxy-fallback",
                                "requestId":"{}",
                                "isBase64Encoded":false,
                                "proxy":"here",
                                "message":"This is a fallback response created by the proxy after failing to get an event from the Lambda Runtime API"
                            }}"#, fallback_id)))
                            .unwrap();

                        println!("[LRAP] Returning fallback response to Lambda function");
                        // Return a valid response as fallback
                        return Ok(minimal_response);
                    }

                    let backoff_time = 100 * attempt; // Exponential backoff
                    println!("[LRAP] Sleeping {}ms before retrying...", backoff_time);
                    tokio::time::sleep(Duration::from_millis(backoff_time)).await;
                    continue; // Try again in the inner loop
                }
            }
        }

        continue 'getNext; // Continue the outer loop
    }
}

/// Process the next invocation event from the Lambda Runtime API
///
/// Event context, payload is in `response`
///
/// On Error, create a [`Request<Body>`] to send to the Runtime API.
///
/// This _could_ be a request to the Runtime API's /runtime/invocation/:id/response to short-cut the Application with a specific code
///

/// Process the Lambda function's response before sending it to the Lambda Runtime API
///
/// This replaces large "content" fields with DynamoDB references to avoid size limitations
pub async fn proxy_invocation_response(req: Request<Body>) -> Result<Response<Body>, Error> {
    // Extract the request ID from the URL path
    let path = req.uri().path().to_string(); // Clone the path
    println!("[LRAP] Processing Lambda response: {}", path);

    // Read the response body to modify it
    let body_bytes = hyper::body::to_bytes(req.into_body()).await?;

    // Log the original response (truncate if too large)
    let body_str = String::from_utf8_lossy(&body_bytes);
    if body_str.len() > 1000 {
        println!(
            "[LRAP] Lambda response (truncated): {}...",
            &body_str[..1000]
        );
    } else {
        println!("[LRAP] Lambda response: {}", body_str);
    }

    // Transform the response
    println!("[LRAP] Transforming the Lambda response");
    let modified_body = match transform::transform_response(&body_bytes) {
        Ok(transformed) => transformed,
        Err(e) => {
            println!("[LRAP] Error during response transformation: {}", e);
            body_bytes.to_vec()
        }
    };

    // Create the endpoint URI for forwarding to the actual Lambda Runtime API
    let endpoint_uri: Uri = Uri::builder()
        .scheme("http")
        .authority(env::original_runtime_api())
        .path_and_query(path)
        .build()
        .unwrap();

    println!("[LRAP DEBUG] Forwarding response to: {}", endpoint_uri);

    // Create a new request with the modified body and correct Content-Length
    let mut request = Request::builder().method("POST").uri(endpoint_uri);

    // Set the correct Content-Length header for our modified body
    let correct_content_length = modified_body.len().to_string();
    println!(
        "[LRAP]   Setting correct Content-Length: {}",
        correct_content_length
    );
    request = request.header(hyper::header::CONTENT_LENGTH, correct_content_length);

    // Build the request with our modified body
    let request = request.body(Body::from(modified_body)).unwrap();

    // Forward the modified request to the Lambda Runtime API
    match hyper::Client::new().request(request).await {
        Ok(res) => {
            println!("[LRAP] Successfully forwarded modified response to Lambda Runtime API");
            Ok(res)
        }
        Err(e) => {
            eprintln!("[LRAP] Error forwarding modified response: {}", e);
            Ok(Response::builder()
                .status(502)
                .body("Error forwarding modified response".into())
                .unwrap())
        }
    }
}

///
async fn validate_and_mangle_next_event(
    aws_request_id: Arc<String>,
    response: Response<Body>,
) -> Result<Response<Body>, Request<Body>> {
    // Log the request ID being processed
    println!(
        "[LRAP] Processing event with request ID: {}",
        aws_request_id
    );

    // Extract important values before consuming the response
    let status = response.status();

    // Check for successful response status
    if !status.is_success() {
        eprintln!(
            "[LRAP] Error: Received non-success status code from Lambda Runtime API: {}",
            status
        );
        return Err(sandbox::create_invoke_result_request(
            &aws_request_id,
            Body::from("Extension proxy error: non-success status from Lambda Runtime API"),
        )
        .await
        .expect("Failed to create error response"));
    }

    // Copy all headers before consuming the body
    let headers_vec: Vec<(hyper::header::HeaderName, hyper::header::HeaderValue)> = response
        .headers()
        .iter()
        .map(|(k, v)| (k.clone(), v.clone()))
        .collect();

    // Ensure we preserve the body content by cloning it
    println!("[LRAP] Converting original response body to bytes");
    let body_bytes = hyper::body::to_bytes(response.into_body())
        .await
        .expect("Failed to read original response body");

    // Log the event body for debugging (truncate if too large)
    let body_str = String::from_utf8_lossy(&body_bytes);
    if body_str.len() > 1000 {
        println!("[LRAP] Event body (truncated): {}...", &body_str[..1000]);
    } else {
        println!("[LRAP] Event body: {}", body_str);
    }

    // Transform the input event - replace DynamoDB references with actual content
    println!("[LRAP] Transforming the input event");
    let modified_body = match transform::transform_input_event(&body_bytes) {
        Ok(transformed) => transformed,
        Err(e) => {
            println!("[LRAP] Error during input transformation: {}", e);
            body_bytes.to_vec()
        }
    };

    // Build a new response with the same status, but we'll manually set correct headers
    println!("[LRAP] Creating new response with same status");
    let mut new_response = Response::builder().status(status);

    // Copy selected headers from the original response, EXCEPT Content-Length and Transfer-Encoding
    println!("[LRAP] Copying headers to new response (excluding Content-Length and Transfer-Encoding)");
    let headers = new_response.headers_mut().unwrap();
    for (name, value) in headers_vec {
        // Skip the Content-Length header - we'll set it correctly ourselves
        if name.to_string().to_lowercase() == "content-length" {
            println!(
                "[LRAP]   Skipping original Content-Length header: {}",
                value.to_str().unwrap_or("(not utf8)")
            );
            continue;
        }
        // Skip Transfer-Encoding header - it conflicts with Content-Length
        if name.to_string().to_lowercase() == "transfer-encoding" {
            println!(
                "[LRAP]   Skipping Transfer-Encoding header: {}",
                value.to_str().unwrap_or("(not utf8)")
            );
            continue;
        }
        println!(
            "[LRAP]   Adding header: {}: {}",
            name,
            value.to_str().unwrap_or("(not utf8)")
        );
        headers.insert(name, value);
    }

    // Create a new body with the modified content
    println!(
        "[LRAP] Returning modified event (length: {})",
        modified_body.len()
    );

    // Set the correct Content-Length header based on our modified body
    let correct_content_length = modified_body.len().to_string();
    println!(
        "[LRAP]   Setting correct Content-Length: {}",
        correct_content_length
    );
    headers.insert(
        hyper::header::CONTENT_LENGTH,
        hyper::header::HeaderValue::from_str(&correct_content_length).unwrap(),
    );

    let new_body = Body::from(modified_body);

    // Forward the modified response to the Lambda function
    println!("[LRAP] Returning modified response to Lambda function");
    return Ok(new_response.body(new_body).unwrap());
}
