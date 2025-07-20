use lambda_runtime::{tracing, Error, LambdaEvent};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::HashMap;
use std::result;

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

// Embedding using cohere
use anyhow::Result;
use reqwest::Client;

#[derive(Deserialize)]
struct CohereResponse {
    outputs: Vec<Vec<f32>>,
}

pub async fn embed(client: &Client, text: &str, api_key: &str) -> Result<Vec<Vec<f32>>> {
    let CohereResponse { outputs } = client
        .post("https://api.cohere.ai/embed")
        .header("Authorization", &format!("Bearer {api_key}"))
        .header("Content-Type", "application/json")
        .header("Cohere-Version", "2021-11-08")
        .body(format!("{{\"text\":[\"{text}\"],\"model\":\"small\"}}"))
        .send()
        .await?
        .json()
        .await?;
    Ok(outputs)
}

// Upsert document to Qdrant
use qdrant_client::qdrant::{
    CreateCollectionBuilder, Distance, SearchResponse, VectorParamsBuilder,
};
use qdrant_client::qdrant::{PointStruct, UpsertPointsBuilder};
use qdrant_client::{Payload, Qdrant};
use serde_json::json;

use qdrant_client::qdrant::{
    Condition, CountPointsBuilder, Filter, SearchParamsBuilder, SearchPointsBuilder,
};
// Semantic Search using vector database (Qdrant) in Rust
pub async fn search(
    text: &str,
    collection_name: String,
    // client: &Client,
    // api_key: &str,
    qdrant: &Qdrant,
) -> Result<SearchResponse> {
    let points = qdrant
        .search_points(
            SearchPointsBuilder::new(collection_name, vec![0.2, 0.1, 0.9, 0.7], 3)
                // .filter(Filter::must([Condition::matches(
                //     "city",
                //     "London".to_string(),
                // )]))
                .with_payload(true)
                .params(SearchParamsBuilder::default().hnsw_ef(128).exact(false)),
        )
        .await?;

    Ok(points)
}

use aws_config::meta::region::RegionProviderChain;
use aws_sdk_secretsmanager::{config::Region, meta::PKG_VERSION};

async fn semantic_search_rust(
    search_query: String,
) -> Result<String, Box<dyn std::error::Error + Send + Sync>> {
    // Embed the search query
    // let embed_client = Client::new("http://localhost:6333");
    // let embed_api_key = "your_api_key_here";
    // let embed = embed(embed_client, search_query, embed_api_key)?;

    // Handle Secrets
    let region_provider = RegionProviderChain::default_provider().or_else("us-west-2");
    let shared_config = aws_config::defaults(aws_config::BehaviorVersion::latest())
        .region(region_provider)
        .load()
        .await;
    let secrets_client = aws_sdk_secretsmanager::Client::new(&shared_config);
    let name: &str = "/ai-agent/qdrant";
    let resp = secrets_client
        .get_secret_value()
        .secret_id(name)
        .send()
        .await?;
    let secret_json: serde_json::Value =
        serde_json::from_str(&resp.secret_string().unwrap_or_default())
            .expect("Failed to parse JSON");
    let api_key_value: String = secret_json["QDRANT_API_KEY"]
        .as_str()
        .unwrap_or("No value!")
        .to_string();
    let qdrant_url_value: &str = secret_json["QDRANT_URL"].as_str().unwrap_or("No value!");

    // Search the vector database
    // let client = Qdrant::new(qdrant_client_confit).unwrap();
    let client = Qdrant::from_url(qdrant_url_value)
        .api_key(api_key_value)
        .build()
        .unwrap();

    let collection_name = "star_charts";

    // clean_setup(collection_name).await?;
    let search_results = search(&search_query, collection_name.to_owned(), &client).await?;

    let response_body: String = search_results
        .result
        .into_iter()
        .map(|p| {
            p.payload
                .get("colony")
                .unwrap()
                .as_str()
                .unwrap()
                .to_owned()
        })
        .collect::<Vec<String>>()
        .join("\n");
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
                semantic_search_rust(payload.input["search_query"].as_str().unwrap().to_string())
                    .await?;

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
        // ignore this test if API_KEY isn't set
        let api_key = &std::env::var("API_KEY");
        // let embedding = crate::embed("What is semantic search?", api_key).unwrap()[0];
        // Cohere's `small` model has 1024 output dimensions.
        // assert_eq!(1024, embedding.len());
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