use lambda_runtime::{tracing, Error, LambdaEvent};
use serde::{Deserialize, Serialize};
use serde_json::Value;

#[derive(Deserialize, Debug)]
pub struct ToolUsePayload {
    pub id: String,
    pub name: String,
    pub input: Value,
}

impl Default for ToolUsePayload {
    fn default() -> Self {
        ToolUsePayload {
            id: String::from(""),
            name: String::from(""),
            input: Value::Null,
        }
    }
}

#[derive(Serialize, Debug)]
pub struct ToolUseResponse {
    pub tool_use_id: String,
    pub name: String,
    #[serde(rename = "type")]
    pub response_type: String,
    pub content: String,
}

use anyhow::{Context, Result};

// Embedding using cohere
use reqwest::Client;

#[derive(Deserialize, Debug)]
struct CohereResponse {
    embeddings: EmbeddingsResponse,
}

#[derive(Deserialize, Debug)]
struct EmbeddingsResponse {
    float: Vec<Vec<f32>>,
}
pub async fn embed(text: &str) -> Result<Vec<Vec<f32>>> {
    let client = Client::new();
    let region_provider = RegionProviderChain::default_provider().or_else("us-west-2");
    let shared_config = aws_config::defaults(aws_config::BehaviorVersion::latest())
        .region(region_provider)
        .load()
        .await;
    let secrets_client = aws_sdk_secretsmanager::Client::new(&shared_config);
    let name: &str = "/ai-agent/api-keys";
    let resp = secrets_client
        .get_secret_value()
        .secret_id(name)
        .send()
        .await
        .context(format!("Failed to retrieve secret '{name}' from AWS Secrets Manager. Please check key name and IAM permissions"))?;

    let secret_json: serde_json::Value =
        serde_json::from_str(resp.secret_string().unwrap_or_default())
            .expect("Failed to parse JSON");
    let api_key_value: &str = secret_json["CO_API_KEY"].as_str().unwrap_or("No value!");

    let response = client
        .post("https://api.cohere.com/v2/embed")
        .header("Authorization", &format!("Bearer {api_key_value}"))
        .header("Content-Type", "application/json")
        .header("accept", "application/json")
        .body(
            serde_json::json!({
                "texts": [text],
                "model": "embed-english-v3.0",
                "input_type": "search_query",
                "embedding_types": ["float"],
            })
            .to_string(),
        )
        .send()
        .await
        .context("Failed to embed text using Cohere API. Please check API key and input.")?;

    // Print the raw response body for debugging
    let response_text = response.text().await?;
    tracing::debug!("Response text from emebedding API: {}", response_text);

    // Parse the response text back to json
    let CohereResponse { embeddings } = serde_json::from_str(&response_text)?;

    Ok(embeddings.float)
}

// Upsert document to Qdrant
use qdrant_client::qdrant::SearchResponse;
use qdrant_client::Qdrant;

use qdrant_client::qdrant::{SearchParamsBuilder, SearchPointsBuilder};
// Semantic Search using vector database (Qdrant) in Rust
pub async fn search(
    text: &str,
    collection_name: String,
    // client: &Client,
    // api_key: &str,
    qdrant: &Qdrant,
) -> Result<SearchResponse> {
    let embeddings = embed(text).await?;
    let vector = embeddings[0].clone();
    println!("Vector: {:?}", vector);
    // Search for the closest vectors
    let points = qdrant
        .search_points(
            SearchPointsBuilder::new(collection_name, vector, 3)
                .with_payload(true)
                .params(SearchParamsBuilder::default().hnsw_ef(128).exact(false)),
        )
        .await?;

    Ok(points)
}

use aws_config::meta::region::RegionProviderChain;

async fn semantic_search_rust(
    search_query: String,
) -> Result<String> {
    // Handle Secrets
    let region_provider = RegionProviderChain::default_provider().or_else("us-west-2");
    let shared_config = aws_config::defaults(aws_config::BehaviorVersion::latest())
        .region(region_provider)
        .load()
        .await;
    let secrets_client = aws_sdk_secretsmanager::Client::new(&shared_config);
    let name: &str = "/ai-agent/semantic_search";
    let resp = secrets_client
        .get_secret_value()
        .secret_id(name)
        .send()
        .await        
        .context(format!("Failed to retrieve secret '{name}' from AWS Secrets Manager. Please check key name and IAM permissions"))?;
    
    let secret_json: serde_json::Value =
        serde_json::from_str(resp.secret_string().unwrap_or_default())
            .expect("Failed to parse JSON");
    let api_key_value: String = secret_json["QDRANT_API_KEY"]
        .as_str()
        .unwrap_or("No value!")
        .to_string();

    // let qdrant_url_value: &str = secret_json["QDRANT_URL"].as_str().unwrap_or("No value!");
    let ssm_client = aws_sdk_ssm::Client::new(&shared_config);

    let parameter_name: &str = "/ai-agent/qdrant/qdrant_endpoint";

    let qdrant_url_value: String = ssm_client
        .get_parameter()
        .name(parameter_name)
        .send()
        .await
        .context(format!("Failed to retrieve parameter '{parameter_name}' from AWS Parameter Store. Please check key name and IAM permissions"))
        .unwrap()
        .parameter
        .unwrap()
        .value
        .unwrap();
    

    // Search the vector database
    // let client = Qdrant::new(qdrant_client_confit).unwrap();
    let client = Qdrant::from_url(&qdrant_url_value)
        .api_key(api_key_value)
        .build()
        .unwrap();

    let collection_name = "test_collection";

    // clean_setup(collection_name).await?;
    let search_results = search(
        &search_query, 
        collection_name.to_owned(), 
        &client
    ).await
    .context(format!("Failed to retrieve documents from collection '{collection_name}'. Please check endpoint URL and API key"))?;


    let response_body: String = search_results
        .result
        .into_iter()
        .map(|p| {
            let title = p
                .payload.get("title")
                .context("Retrieved document's Payload should include title element.")
                .unwrap()
                .as_str()
                .unwrap()
                .to_owned();

            let description = p
                .payload
                .get("description")
                .context("Retrieved document's Payload should include description element.")
                .unwrap()
                .as_str()
                .unwrap()
                .to_owned();

            format!("Title:{}\n Description: {}", title, description)
        })
        .collect::<Vec<String>>()
        .join("\n");
    tracing::debug!("Search results: {}", response_body);
    println!("Search results: {}", response_body);

    // // Return the search results
    Ok(response_body)
    // Ok("".to_string())
}

pub(crate) async fn function_handler(event: LambdaEvent<Value>) -> Result<ToolUseResponse, Error> {
    let payload: ToolUsePayload = match serde_json::from_value(event.payload.clone()) {
        Ok(payload) => payload,
        Err(e) => {
            println!("Failed to parse payload: {}", e);
            ToolUsePayload::default()
        }
    };
    tracing::info!("Payload: {:?}", payload);

    let result: String;

    match payload.name.as_str() {
        "semantic_search_rust" => {
            tracing::info!("Semantic search using vector database (Qdrant) in Rust");
            // Your tool logic here

            // Call tool function
            let response_body =
                semantic_search_rust(
                    payload.input["search_query"].as_str().unwrap().to_string()
                )
                .await
                .context("Internal tool function failed to execute.")?;

            result = serde_json::to_string(&serde_json::json!({
                "docs": response_body,
            }))?;
        }
        _ => {
            tracing::error!("Unknown tool_name: {}", payload.name);
            result = serde_json::to_string(&serde_json::json!({
                "error": "Unknown tool_name",
            }))?;
        }
    }

    Ok(ToolUseResponse {
        tool_use_id: payload.id,
        name: payload.name,
        response_type: "tool_result".to_string(),
        content: result,
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use lambda_runtime::{Context, LambdaEvent};
    use serde_json::json;

    #[tokio::test]
    async fn check_embedding() {
        let embedding = embed("What is semantic search?").await.unwrap();
        // Cohere's embed model has 1024 output dimensions.
        assert_eq!(1024, embedding[0].len());
    }

    #[tokio::test]
    async fn test_event_handler() {
        let payload = json!({
            "id": "tool_use_unique_id",
            "name": "semantic_search_rust",
            "input": {
                "search_query": "How many vacation days can I take?",
            }
        });
        let event = LambdaEvent::new(payload, Context::default());
        let response = function_handler(event).await.unwrap();

        println!("Response: {:?}", serde_json::to_string(&response).unwrap());
        assert_eq!(response.tool_use_id, "tool_use_unique_id".to_string());
        assert_eq!(response.response_type, "tool_result".to_string());
        assert!(!response.content.is_empty());
    }
}
