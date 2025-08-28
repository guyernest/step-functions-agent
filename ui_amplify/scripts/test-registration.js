#!/usr/bin/env node
/**
 * Test script for MCP Server Registration
 * 
 * This script tests the registration functionality without actually
 * writing to DynamoDB. Useful for validating the registration logic.
 */

const {
  readAmplifyOutputs,
  extractMCPServerInfo,
  createServerRegistrationData
} = require('./register-mcp-server');

function validateServerData(serverData) {
  const requiredFields = [
    'server_id',
    'version', 
    'server_name',
    'endpoint_url',
    'protocol_type',
    'authentication_type',
    'available_tools',
    'status'
  ];

  const missingFields = requiredFields.filter(field => !serverData[field]);
  
  if (missingFields.length > 0) {
    throw new Error(`Missing required fields: ${missingFields.join(', ')}`);
  }

  // Validate available_tools is valid JSON
  try {
    const tools = JSON.parse(serverData.available_tools);
    if (!Array.isArray(tools) || tools.length === 0) {
      throw new Error('available_tools must be a non-empty array');
    }
  } catch (error) {
    throw new Error(`Invalid available_tools JSON: ${error.message}`);
  }

  // Validate configuration is valid JSON
  try {
    JSON.parse(serverData.configuration);
  } catch (error) {
    throw new Error(`Invalid configuration JSON: ${error.message}`);
  }

  // Validate metadata is valid JSON
  try {
    JSON.parse(serverData.metadata);
  } catch (error) {
    throw new Error(`Invalid metadata JSON: ${error.message}`);
  }

  return true;
}

function testRegistration() {
  console.log('🧪 Testing MCP Server Registration Logic...');
  console.log('');

  try {
    // Test reading amplify outputs
    console.log('1️⃣  Testing amplify_outputs.json reading...');
    const amplifyOutputs = readAmplifyOutputs();
    console.log('   ✅ Successfully read amplify_outputs.json');

    // Test extracting MCP info
    console.log('2️⃣  Testing MCP info extraction...');
    const mcpInfo = extractMCPServerInfo(amplifyOutputs);
    console.log('   ✅ Successfully extracted MCP info:');
    console.log(`      Environment: ${mcpInfo.environment}`);
    console.log(`      Endpoint: ${mcpInfo.endpoint}`);
    console.log(`      Region: ${mcpInfo.region}`);

    // Test creating registration data
    console.log('3️⃣  Testing registration data creation...');
    const serverData = createServerRegistrationData(mcpInfo);
    console.log('   ✅ Successfully created registration data');

    // Validate server data
    console.log('4️⃣  Validating server data...');
    validateServerData(serverData);
    console.log('   ✅ Server data validation passed');

    // Display summary
    console.log('');
    console.log('📋 Registration Data Summary:');
    console.log(`   Server ID: ${serverData.server_id}`);
    console.log(`   Version: ${serverData.version}`);
    console.log(`   Name: ${serverData.server_name}`);
    console.log(`   Endpoint: ${serverData.endpoint_url}`);
    console.log(`   Protocol: ${serverData.protocol_type}`);
    console.log(`   Auth Type: ${serverData.authentication_type}`);
    console.log(`   Status: ${serverData.status}`);

    const tools = JSON.parse(serverData.available_tools);
    console.log(`   Tools: ${tools.length} available`);
    tools.forEach((tool, index) => {
      console.log(`      ${index + 1}. ${tool.name} - ${tool.description}`);
    });

    console.log('');
    console.log('✅ All tests passed! Registration logic is working correctly.');

  } catch (error) {
    console.error('❌ Test failed:', error.message);
    process.exit(1);
  }
}

// Run tests if called directly
if (require.main === module) {
  testRegistration();
}

module.exports = { testRegistration, validateServerData };