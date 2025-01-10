package main

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"

	"github.com/aws/aws-lambda-go/lambda"
	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/service/secretsmanager"
	"github.com/aws/aws-sdk-go/aws"
	"github.com/sgaunet/perplexity-go"
)

// ToolEvent represents the incoming event structure
type ToolEvent struct {
	ID    string          `json:"id"`
	Name  string          `json:"name"`
	Input json.RawMessage `json:"input"`
	Type  string          `json:"type"`
}

// ToolResponse represents the response structure
type ToolResponse struct {
	Type      string `json:"type"`
	ToolUseID string `json:"tool_use_id"`
	Content   string `json:"content"`
}

// ResearchInput represents the input structure for company research
type ResearchInput struct {
	Company string   `json:"company"`
	Topics  []string `json:"topics,omitempty"`
}

// ResearchResult represents the structured research result
type ResearchResult struct {
	Company     string            `json:"company"`
	Information map[string]string `json:"information"`
}

// handler is our lambda handler invoked by the `lambda.Start` function
func handler(ctx context.Context, event ToolEvent) (ToolResponse, error) {
	response := ToolResponse{
		Type:      "tool_result",
		ToolUseID: event.ID,
	}

	// Get API key from AWS Secrets Manager
	cfg, err := config.LoadDefaultConfig(ctx)
	if err != nil {
		return response, fmt.Errorf("unable to load SDK config: %v", err)
	}

	// Create Secrets Manager client
	svc := secretsmanager.NewFromConfig(cfg)
	secret, err := svc.GetSecretValue(ctx, &secretsmanager.GetSecretValueInput{
		SecretId: aws.String("/ai-agent/PPLX_API_KEY"),
	})
	if err != nil {
		return response, fmt.Errorf("unable to get secret: %v", err)
	}

	// Parse secret JSON
	var secretData struct {
		PPLX_API_KEY string `json:"PPLX_API_KEY"`
	}
	if err := json.Unmarshal([]byte(*secret.SecretString), &secretData); err != nil {
		return response, fmt.Errorf("unable to parse secret: %v", err)
	}

	switch event.Name {
	case "research_company":
		var input ResearchInput
		if err := json.Unmarshal(event.Input, &input); err != nil {
			response.Content = fmt.Sprintf("Error parsing input: %v", err)
			return response, nil
		}

		result, err := researchCompany(ctx, secretData.PPLX_API_KEY, input)
		if err != nil {
			response.Content = fmt.Sprintf("Error performing research: %v", err)
			return response, nil
		}

		resultJSON, err := json.MarshalIndent(result, "", "  ")
		if err != nil {
			response.Content = fmt.Sprintf("Error formatting result: %v", err)
			return response, nil
		}

		response.Content = string(resultJSON)

	default:
		response.Content = fmt.Sprintf("Unknown tool: %s", event.Name)
	}

	return response, nil
}

func researchCompany(ctx context.Context, apiKey string, input ResearchInput) (ResearchResult, error) {
	client := perplexity.NewClient(apiKey)
	result := ResearchResult{
		Company:     input.Company,
		Information: make(map[string]string),
	}

	// If no specific topics provided, use default ones
	if len(input.Topics) == 0 {
		input.Topics = []string{
			"recent financial performance",
			"major products or services",
			"market position",
			"recent news",
		}
	}

	for _, topic := range input.Topics {
		prompt := fmt.Sprintf(
			"Provide a concise summary of %s's %s. Focus on the most recent and relevant information. "+
				"Keep the response factual and under 100 words.",
			input.Company, topic,
		)

		res, err := client.CreateCompletion([]perplexity.Message{
			{
				Role:    "user",
				Content: prompt,
			},
		})

		if err != nil {
			return result, fmt.Errorf("error researching %s - %s: %v", input.Company, topic, err)
		}

		result.Information[topic] = strings.TrimSpace(res.GetLastContent())
	}

	return result, nil
}

func main() {
	lambda.Start(handler)
}
