use aws_config::{BehaviorVersion, SdkConfig};
use aws_sdk_s3::Client;
use hdbscan::{DistanceMetric, Hdbscan, HdbscanHyperParams, NnAlgorithm};
use lambda_runtime::{tracing, Error, LambdaEvent};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::HashMap;

struct S3Config {
    bucket: String,
    key: String,
}

// Structure to hold a named vector
#[derive(Debug, Clone)]
struct NamedVector {
    name: String,
    vector: Vec<f32>, // Note: Changed to f32 to match hdbscan expectations
}

fn parse_csv(data: &str) -> Result<Vec<NamedVector>, Box<dyn std::error::Error + Send + Sync>> {
    data.lines()
        .filter(|line| !line.trim().is_empty())
        .map(|line| {
            let mut parts = line.split(',');
            let name = parts
                .next()
                .ok_or("Missing name column")?
                .trim()
                .to_string();

            // Parse rest of columns as f32 instead of f64
            let vector = parts
                .map(|num| num.trim().parse::<f32>())
                .collect::<Result<Vec<f32>, _>>()?;

            Ok(NamedVector { name, vector })
        })
        .collect()
}

async fn read_vectors_from_s3(
    config: S3Config,
) -> Result<Vec<NamedVector>, Box<dyn std::error::Error + Send + Sync>> {
    let aws_config: SdkConfig = aws_config::load_defaults(BehaviorVersion::latest()).await;
    let client = Client::new(&aws_config);

    let resp = client
        .get_object()
        .bucket(config.bucket)
        .key(config.key)
        .send()
        .await?;

    let data = resp.body.collect().await?;
    let data_str = String::from_utf8(data.to_vec())?;
    parse_csv(&data_str)
}

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
    #[serde(rename = "type")]
    pub response_type: String,
    pub content: String,
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
        "calculate_hdbscan_clusters" => {
            tracing::info!("Calculating clusters using HDBSCAN");
            let config = S3Config {
                bucket: payload.input["bucket"].as_str().unwrap().to_string(),
                key: payload.input["key"].as_str().unwrap().to_string(),
            };

            // Read vectors from S3
            let named_vectors = read_vectors_from_s3(config).await?;

            // Prepare data for HDBSCAN
            let data: Vec<Vec<f32>> = named_vectors.iter().map(|nv| nv.vector.clone()).collect();

            let hyper_params = HdbscanHyperParams::builder()
                .min_cluster_size(2)
                .min_samples(2)
                .dist_metric(DistanceMetric::Manhattan)
                .nn_algorithm(NnAlgorithm::BruteForce)
                .build();

            // Create and run HDBSCAN clusterer
            let clusterer = Hdbscan::new(&data, hyper_params);
            let labels = clusterer.cluster()?;

            // Create mappings for results
            let mut clusters_map: HashMap<i32, Vec<String>> = HashMap::new();
            let mut noise_points: Vec<String> = Vec::new();

            // Process clustering results
            for (idx, &label) in labels.iter().enumerate() {
                if label == -1 {
                    noise_points.push(named_vectors[idx].name.clone());
                } else {
                    clusters_map
                        .entry(label)
                        .or_default()
                        .push(named_vectors[idx].name.clone());
                }
            }

            // Print cluster information
            println!("\nClustering Results:");
            println!("------------------");
            for (cluster_id, members) in &clusters_map {
                println!("\nCluster {}: {} members", cluster_id, members.len());
                println!("Members:");
                for name in members {
                    println!("  - {}", name);
                }
            }

            if !noise_points.is_empty() {
                println!("\nNoise Points: {} members", noise_points.len());
                for name in &noise_points {
                    println!("  - {}", name);
                }
            }

            result = serde_json::to_string(&serde_json::json!({
                "cluster_map": clusters_map,
                "noise_points": noise_points,
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
    async fn test_event_handler() {
        let payload = json!({
            "id": "calculate_hdbscan_clusters_unique_id",
            "name": "calculate_hdbscan_clusters",
            "input": {
                "bucket": "yfinance-data-672915487120-us-west-2",
                "key": "stock_vectors/stock_data_20250107_214201.csv"
            }
        });
        let event = LambdaEvent::new(payload, Context::default());
        let response = function_handler(event).await.unwrap();

        println!("Response: {:?}", serde_json::to_string(&response).unwrap());
        assert_eq!(
            response.tool_use_id,
            "calculate_hdbscan_clusters_unique_id".to_string()
        );
        assert_eq!(response.response_type, "tool_result".to_string());
        assert!(!response.content.is_empty());
    }
}
