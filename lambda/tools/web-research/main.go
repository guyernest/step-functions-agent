package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"strings"

	"github.com/aws/aws-lambda-go/lambda"
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
	Name      string `json:"name"`
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
	// Set up logging based on LOG_LEVEL env var
	logLevel := os.Getenv("LOG_LEVEL")
	if logLevel == "" {
		logLevel = "INFO"
	}
	isDebug := logLevel == "DEBUG"
	
	log.Printf("[INFO] Starting handler for tool: %s (ID: %s)", event.Name, event.ID)
	if isDebug {
		eventJSON, _ := json.MarshalIndent(event, "", "  ")
		log.Printf("[DEBUG] Received event: %s", string(eventJSON))
	}
	
	response := ToolResponse{
		Type:      "tool_result",
		Name:      event.Name,
		ToolUseID: event.ID,
	}

	// Get API key using the consolidated secrets helper
	log.Printf("[INFO] Retrieving API key from consolidated secrets for tool: web-research")
	apiKey, err := GetSecretValue(ctx, "web-research", "PPLX_API_KEY", "")
	if err != nil {
		log.Printf("[ERROR] Failed to get API key: %v", err)
		return response, fmt.Errorf("error getting API key: %v", err)
	}
	
	if apiKey == "" {
		log.Printf("[ERROR] PPLX_API_KEY not configured in consolidated secrets")
		return response, fmt.Errorf("PPLX_API_KEY not configured in consolidated secrets")
	}
	
	if isDebug {
		// Log first 10 chars of API key for verification (masked)
		if len(apiKey) > 10 {
			log.Printf("[DEBUG] API key retrieved successfully (first 10 chars): %s...", apiKey[:10])
		} else {
			log.Printf("[DEBUG] API key retrieved but appears invalid (length: %d)", len(apiKey))
		}
	}

	switch event.Name {
	case "research_company":
		var input ResearchInput
		if err := json.Unmarshal(event.Input, &input); err != nil {
			log.Printf("[ERROR] Failed to parse input: %v", err)
			response.Content = fmt.Sprintf("Error parsing input: %v", err)
			return response, nil
		}
		
		log.Printf("[INFO] Processing research_company request for: %s", input.Company)
		if isDebug {
			log.Printf("[DEBUG] Research topics: %v", input.Topics)
		}

		result, err := researchCompany(ctx, apiKey, input, isDebug)
		if err != nil {
			log.Printf("[ERROR] Research failed: %v", err)
			response.Content = fmt.Sprintf("Error performing research: %v", err)
			return response, nil
		}

		resultJSON, err := json.MarshalIndent(result, "", "  ")
		if err != nil {
			log.Printf("[ERROR] Failed to format result: %v", err)
			response.Content = fmt.Sprintf("Error formatting result: %v", err)
			return response, nil
		}

		log.Printf("[INFO] Research completed successfully for company: %s", input.Company)
		response.Content = string(resultJSON)

	default:
		log.Printf("[ERROR] Unknown tool requested: %s", event.Name)
		response.Content = fmt.Sprintf("Unknown tool: %s", event.Name)
	}

	return response, nil
}

func researchCompany(ctx context.Context, apiKey string, input ResearchInput, isDebug bool) (ResearchResult, error) {
	log.Printf("[INFO] Initializing Perplexity client for company: %s", input.Company)
	client := NewPerplexityClient(apiKey)
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
		log.Printf("[INFO] Using default topics for research")
	}

	for i, topic := range input.Topics {
		prompt := fmt.Sprintf(
			"Provide a concise summary of %s's %s. Focus on the most recent and relevant information. "+
				"Keep the response factual and under 100 words.",
			input.Company, topic,
		)
		
		log.Printf("[INFO] Researching topic %d/%d: %s", i+1, len(input.Topics), topic)
		if isDebug {
			log.Printf("[DEBUG] Prompt: %s", prompt)
		}

		res, err := client.CreateCompletion(ctx, []PerplexityMessage{
			{
				Role:    "user",
				Content: prompt,
			},
		}, isDebug)

		if err != nil {
			log.Printf("[ERROR] Perplexity API error for topic '%s': %v", topic, err)
			if isDebug {
				// Log more details about the error
				log.Printf("[DEBUG] Full error details: %+v", err)
			}
			return result, fmt.Errorf("error researching %s - %s: %v", input.Company, topic, err)
		}

		if isDebug {
			log.Printf("[DEBUG] Response received for topic '%s'", topic)
		}
		
		content := strings.TrimSpace(res.GetLastContent())
		result.Information[topic] = content
		log.Printf("[INFO] Successfully researched topic: %s (response length: %d chars)", topic, len(content))
	}

	log.Printf("[INFO] Completed research for all %d topics", len(input.Topics))
	return result, nil
}

func main() {
	// Initialize logging
	log.SetFlags(log.LstdFlags | log.Lmicroseconds)
	log.Printf("[INFO] Starting web-research Lambda function")
	log.Printf("[INFO] Environment: %s", os.Getenv("ENVIRONMENT"))
	log.Printf("[INFO] Log Level: %s", os.Getenv("LOG_LEVEL"))
	
	lambda.Start(handler)
}
