package main

import (
	"context"
	"encoding/json"
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestHandler(t *testing.T) {
	// Test event for researching a company
	testEvent := ToolEvent{
		ID:   "research_company_unique_id",
		Name: "research_company",
		Input: json.RawMessage(`{
			"company": "Apple",
			"topics": ["recent financial performance"]
		}`),
		Type: "tool_use",
	}

	// Call handler
	response, err := handler(context.Background(), testEvent)
	assert.NoError(t, err)

	// Verify response structure
	assert.Equal(t, "tool_result", response.Type)
	assert.Equal(t, "research_company_unique_id", response.ToolUseID)
	assert.NotEmpty(t, response.Content)

	// Parse the content
	var result ResearchResult
	err = json.Unmarshal([]byte(response.Content), &result)
	assert.NoError(t, err)

	// Basic content verification
	assert.Equal(t, "Apple", result.Company)
	assert.Contains(t, result.Information, "recent financial performance")
	assert.NotEmpty(t, result.Information["recent financial performance"])
	assert.Contains(t, result.Information["recent financial performance"], "Apple")

	// Test with unknown tool
	unknownToolEvent := ToolEvent{
		ID:   "unknown_tool_id",
		Name: "unknown_tool",
		Input: json.RawMessage(`{
			"company": "Apple"
		}`),
		Type: "tool_use",
	}

	response, err = handler(context.Background(), unknownToolEvent)
	assert.NoError(t, err)
	assert.Equal(t, "tool_result", response.Type)
	assert.Equal(t, "unknown_tool_id", response.ToolUseID)
	assert.Contains(t, response.Content, "Unknown tool")
}

func TestToolEventParsing(t *testing.T) {
	jsonData := `{
		"id": "test-id",
		"name": "research_company",
		"input": {
			"company": "Apple",
			"topics": ["performance", "news"]
		},
		"type": "tool_use"
	}`

	var event ToolEvent
	err := json.Unmarshal([]byte(jsonData), &event)
	assert.NoError(t, err)

	var input ResearchInput
	err = json.Unmarshal(event.Input, &input)
	assert.NoError(t, err)
	assert.Equal(t, "Apple", input.Company)
	assert.Equal(t, []string{"performance", "news"}, input.Topics)
}
