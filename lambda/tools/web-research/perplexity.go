package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"time"
)

// PerplexityRequest represents the request structure for Perplexity API
type PerplexityRequest struct {
	Model    string              `json:"model"`
	Messages []PerplexityMessage `json:"messages"`
}

// PerplexityMessage represents a message in the Perplexity API
type PerplexityMessage struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

// PerplexityResponse represents the response from Perplexity API
type PerplexityResponse struct {
	ID      string                   `json:"id"`
	Model   string                   `json:"model"`
	Object  string                   `json:"object"`
	Created int64                    `json:"created"`
	Choices []PerplexityChoice       `json:"choices"`
	Usage   PerplexityUsage          `json:"usage"`
	Error   *PerplexityError         `json:"error,omitempty"`
}

// PerplexityChoice represents a choice in the response
type PerplexityChoice struct {
	Index        int               `json:"index"`
	Message      PerplexityMessage `json:"message"`
	FinishReason string            `json:"finish_reason"`
}

// PerplexityUsage represents token usage information
type PerplexityUsage struct {
	PromptTokens     int `json:"prompt_tokens"`
	CompletionTokens int `json:"completion_tokens"`
	TotalTokens      int `json:"total_tokens"`
}

// PerplexityError represents an error from the API
type PerplexityError struct {
	Message string `json:"message"`
	Type    string `json:"type"`
	Code    string `json:"code"`
}

// PerplexityClient represents a client for the Perplexity API
type PerplexityClient struct {
	apiKey     string
	httpClient *http.Client
	baseURL    string
}

// NewPerplexityClient creates a new Perplexity API client
func NewPerplexityClient(apiKey string) *PerplexityClient {
	return &PerplexityClient{
		apiKey: apiKey,
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
		},
		baseURL: "https://api.perplexity.ai",
	}
}

// CreateCompletion sends a request to the Perplexity API
func (c *PerplexityClient) CreateCompletion(ctx context.Context, messages []PerplexityMessage, isDebug bool) (*PerplexityResponse, error) {
	// Use sonar model for web search capabilities
	request := PerplexityRequest{
		Model:    "sonar",
		Messages: messages,
	}

	jsonData, err := json.Marshal(request)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	if isDebug {
		log.Printf("[DEBUG] Sending request to Perplexity API: %s", string(jsonData))
	}

	req, err := http.NewRequestWithContext(ctx, "POST", c.baseURL+"/chat/completions", bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Authorization", "Bearer "+c.apiKey)
	req.Header.Set("Content-Type", "application/json")

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response body: %w", err)
	}

	if isDebug {
		log.Printf("[DEBUG] Response status: %d", resp.StatusCode)
		log.Printf("[DEBUG] Response body: %s", string(body))
	}

	if resp.StatusCode != http.StatusOK {
		// Try to parse error response
		var errorResp struct {
			Error PerplexityError `json:"error"`
		}
		if err := json.Unmarshal(body, &errorResp); err == nil && errorResp.Error.Message != "" {
			return nil, fmt.Errorf("API error (status %d): %s", resp.StatusCode, errorResp.Error.Message)
		}
		return nil, fmt.Errorf("unexpected status code: %d, body: %s", resp.StatusCode, string(body))
	}

	var response PerplexityResponse
	if err := json.Unmarshal(body, &response); err != nil {
		return nil, fmt.Errorf("failed to parse response: %w", err)
	}

	if response.Error != nil {
		return nil, fmt.Errorf("API error: %s", response.Error.Message)
	}

	return &response, nil
}

// GetLastContent extracts the content from the last message in the response
func (r *PerplexityResponse) GetLastContent() string {
	if len(r.Choices) > 0 {
		return r.Choices[0].Message.Content
	}
	return ""
}