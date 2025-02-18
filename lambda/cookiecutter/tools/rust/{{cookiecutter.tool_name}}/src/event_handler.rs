use aws_config::{BehaviorVersion, SdkConfig};
use lambda_runtime::{tracing, Error, LambdaEvent};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::HashMap;

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

async fn {{cookiecutter.tool_name}}(
    {{cookiecutter.input_param_name}}: Type,
) -> Result<Vec<Type>, Box<dyn std::error::Error + Send + Sync>> {
    Ok(vec![Type::default()])
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
        "{{cookiecutter.tool_name}}" => {
            tracing::info!("{{cookiecutter.tool_description}}");
            // Your tool logic here

            // Call tool function
            let result_part_1 = {{cookiecutter.tool_name}}(
                payload.input["{{cookiecutter.input_param_name}}"].as_str().unwrap().to_string()
            ).await?;


            result = serde_json::to_string(&serde_json::json!({
                "result_part_1": result_part_1,
                // "result_part_2": result_part_2,
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
    async fn test_event_handler() {
        let payload = json!({
            "id": "tool_use_unique_id",
            "name": "{{cookiecutter.tool_name}}",
            "input": {
                "{{cookiecutter.input_param_name}}": "{{cookiecutter.input_test_value}}",
            }
        });
        let event = LambdaEvent::new(payload, Context::default());
        let response = function_handler(event).await.unwrap();

        println!("Response: {:?}", serde_json::to_string(&response).unwrap());
        assert_eq!(
            response.tool_use_id,
            "tool_use_unique_id".to_string()
        );
        assert_eq!(response.response_type, "tool_result".to_string());
        assert!(!response.content.is_empty());
    }
}
