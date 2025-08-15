package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"strings"
	"sync"

	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/service/secretsmanager"
	"github.com/aws/aws-sdk-go/aws"
)

// Global variables for caching
var (
	cachedSecrets map[string]map[string]string
	cacheMutex    sync.RWMutex
	cacheOnce     sync.Once
)

// getConsolidatedSecretName returns the consolidated secret name from environment or default
func getConsolidatedSecretName() string {
	envName := os.Getenv("ENVIRONMENT")
	if envName == "" {
		envName = "prod"
	}
	
	secretName := os.Getenv("CONSOLIDATED_SECRET_NAME")
	if secretName == "" {
		secretName = fmt.Sprintf("/ai-agent/tool-secrets/%s", envName)
	}
	
	return secretName
}

// GetAllSecrets retrieves all secrets from the consolidated secret
// Results are cached for the Lambda execution context
func GetAllSecrets(ctx context.Context) (map[string]map[string]string, error) {
	// Return cached value if available
	cacheMutex.RLock()
	if cachedSecrets != nil {
		defer cacheMutex.RUnlock()
		return cachedSecrets, nil
	}
	cacheMutex.RUnlock()

	// Load secrets once
	var loadErr error
	cacheOnce.Do(func() {
		secretName := getConsolidatedSecretName()
		log.Printf("[INFO] Loading consolidated secrets from: %s", secretName)
		
		// Load AWS config
		cfg, err := config.LoadDefaultConfig(ctx)
		if err != nil {
			loadErr = fmt.Errorf("unable to load SDK config: %v", err)
			log.Printf("[ERROR] Failed to load AWS SDK config: %v", err)
			return
		}
		
		// Create Secrets Manager client
		svc := secretsmanager.NewFromConfig(cfg)
		secret, err := svc.GetSecretValue(ctx, &secretsmanager.GetSecretValueInput{
			SecretId: aws.String(secretName),
		})
		if err != nil {
			loadErr = fmt.Errorf("unable to get secret: %v", err)
			log.Printf("[ERROR] Failed to retrieve secret %s: %v", secretName, err)
			return
		}
		
		log.Printf("[DEBUG] Secret retrieved, parsing JSON...")
		
		// Parse secret JSON
		var secrets map[string]map[string]string
		if err := json.Unmarshal([]byte(*secret.SecretString), &secrets); err != nil {
			loadErr = fmt.Errorf("unable to parse secret: %v", err)
			log.Printf("[ERROR] Failed to parse secret JSON: %v", err)
			return
		}
		
		log.Printf("[INFO] Successfully loaded secrets for %d tools", len(secrets))
		for toolName := range secrets {
			log.Printf("[DEBUG] Tool in secrets: %s", toolName)
		}
		
		cacheMutex.Lock()
		cachedSecrets = secrets
		cacheMutex.Unlock()
	})
	
	if loadErr != nil {
		return nil, loadErr
	}
	
	cacheMutex.RLock()
	defer cacheMutex.RUnlock()
	return cachedSecrets, nil
}

// GetToolSecrets retrieves secrets for a specific tool from the consolidated secret
func GetToolSecrets(ctx context.Context, toolName string) (map[string]string, error) {
	allSecrets, err := GetAllSecrets(ctx)
	if err != nil {
		return nil, err
	}
	
	toolSecrets, ok := allSecrets[toolName]
	if !ok {
		return make(map[string]string), nil
	}
	
	return toolSecrets, nil
}

// GetSecretValue retrieves a specific secret value for a tool
func GetSecretValue(ctx context.Context, toolName, secretKey string, defaultValue string) (string, error) {
	log.Printf("[INFO] Getting secret value for tool: %s, key: %s", toolName, secretKey)
	
	toolSecrets, err := GetToolSecrets(ctx, toolName)
	if err != nil {
		log.Printf("[ERROR] Failed to get tool secrets for %s: %v", toolName, err)
		return defaultValue, err
	}
	
	log.Printf("[DEBUG] Retrieved %d secrets for tool %s", len(toolSecrets), toolName)
	
	value, ok := toolSecrets[secretKey]
	if !ok {
		log.Printf("[WARNING] Secret key %s not found for tool %s, using default value", secretKey, toolName)
		return defaultValue, nil
	}
	
	// Check if it's a placeholder
	if strings.HasPrefix(value, "PLACEHOLDER_") {
		log.Printf("[WARNING] Using placeholder value for %s/%s", toolName, secretKey)
		return defaultValue, nil
	}
	
	log.Printf("[INFO] Successfully retrieved secret for %s/%s", toolName, secretKey)
	return value, nil
}

// GetLegacySecret retrieves secrets from a legacy individual secret path
// This function provides backward compatibility for tools that haven't been migrated yet
func GetLegacySecret(ctx context.Context, secretPath string) (map[string]string, error) {
	// Load AWS config
	cfg, err := config.LoadDefaultConfig(ctx)
	if err != nil {
		return nil, fmt.Errorf("unable to load SDK config: %v", err)
	}
	
	// Create Secrets Manager client
	svc := secretsmanager.NewFromConfig(cfg)
	
	// First try the legacy path
	secret, err := svc.GetSecretValue(ctx, &secretsmanager.GetSecretValueInput{
		SecretId: aws.String(secretPath),
	})
	
	if err != nil {
		// Check if it's a not found error
		if strings.Contains(err.Error(), "ResourceNotFoundException") {
			// Fall back to consolidated secret
			// Extract tool name from path
			parts := strings.Split(secretPath, "/")
			for i, part := range parts {
				if part == "tools" && i+1 < len(parts) {
					toolName := parts[i+1]
					return GetToolSecrets(ctx, toolName)
				}
			}
		}
		return nil, fmt.Errorf("error retrieving legacy secret from %s: %v", secretPath, err)
	}
	
	// Parse secret JSON
	var secrets map[string]string
	if err := json.Unmarshal([]byte(*secret.SecretString), &secrets); err != nil {
		return nil, fmt.Errorf("unable to parse secret: %v", err)
	}
	
	return secrets, nil
}

// LoadSecretsToEnv loads tool secrets into environment variables
// Useful for tools that expect secrets in env vars
func LoadSecretsToEnv(ctx context.Context, toolName string) error {
	secrets, err := GetToolSecrets(ctx, toolName)
	if err != nil {
		return err
	}
	
	for key, value := range secrets {
		if !strings.HasPrefix(value, "PLACEHOLDER_") {
			os.Setenv(key, value)
		}
	}
	
	return nil
}

// ClearCache clears the cached secrets (useful for testing)
func ClearCache() {
	cacheMutex.Lock()
	defer cacheMutex.Unlock()
	cachedSecrets = nil
	cacheOnce = sync.Once{}
}