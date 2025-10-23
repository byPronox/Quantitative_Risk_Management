#!/usr/bin/env node

/**
 * Nmap Scanner Service - Test Examples
 * 
 * This script demonstrates how to use the nmap scanner service
 * with various test cases and examples.
 */

import fetch from 'node-fetch';

const NMAP_SERVICE_URL = process.env.NMAP_SERVICE_URL || 'http://localhost:8004';

// Test cases
const testCases = [
  { target: '127.0.0.1', description: 'Localhost IP' },
  { target: '192.168.1.1', description: 'Private network IP' },
  { target: '8.8.8.8', description: 'Public DNS IP' },
  { target: 'scanme.nmap.org', description: 'Nmap test hostname' }
];

/**
 * Test nmap service installation
 */
async function testNmapInstallation() {
  console.log('🔧 Testing nmap installation...');
  
  try {
    const response = await fetch(`${NMAP_SERVICE_URL}/api/v1/test`);
    const result = await response.json();
    
    if (response.ok) {
      console.log('✅ Nmap installation test:', result.data.message);
      console.log('📋 Nmap version:', result.data.version);
      return true;
    } else {
      console.log('❌ Nmap installation test failed:', result.error);
      return false;
    }
  } catch (error) {
    console.log('❌ Cannot connect to nmap service:', error.message);
    return false;
  }
}

/**
 * Validate target format
 */
async function validateTarget(target) {
  console.log(`🔍 Validating target: ${target}`);
  
  try {
    const response = await fetch(`${NMAP_SERVICE_URL}/api/v1/validate/${target}`);
    const result = await response.json();
    
    console.log(`   - Valid IP: ${result.isValidIP}`);
    console.log(`   - Valid Hostname: ${result.isValidHostname}`);
    console.log(`   - Overall Valid: ${result.isValid}`);
    
    return result.isValid;
  } catch (error) {
    console.log(`❌ Validation failed: ${error.message}`);
    return false;
  }
}

/**
 * Scan a target
 */
async function scanTarget(target) {
  console.log(`🎯 Scanning target: ${target}`);
  
  try {
    const startTime = Date.now();
    const response = await fetch(`${NMAP_SERVICE_URL}/api/v1/scan`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ ip: target })
    });
    
    const result = await response.json();
    const duration = Date.now() - startTime;
    
    if (response.ok) {
      console.log(`✅ Scan completed in ${duration}ms`);
      console.log(`📊 Results:`);
      console.log(`   - IP: ${result.data.ip}`);
      console.log(`   - OS: ${result.data.os}`);
      console.log(`   - Status: ${result.data.status}`);
      console.log(`   - Services found: ${result.data.services.length}`);
      console.log(`   - Vulnerabilities: ${result.data.vulnerabilities.length}`);
      
      if (result.data.services.length > 0) {
        console.log(`   - Sample service: ${result.data.services[0].port}/${result.data.services[0].protocol} - ${result.data.services[0].name}`);
      }
      
      console.log(`   - Timestamp: ${result.data.timestamp}`);
      return true;
    } else {
      console.log(`❌ Scan failed: ${result.error}`);
      console.log(`📝 Details: ${result.details}`);
      return false;
    }
  } catch (error) {
    console.log(`❌ Scan error: ${error.message}`);
    return false;
  }
}

/**
 * Get service status
 */
async function getServiceStatus() {
  console.log('📊 Getting service status...');
  
  try {
    const response = await fetch(`${NMAP_SERVICE_URL}/api/v1/status`);
    const result = await response.json();
    
    if (response.ok) {
      console.log('✅ Service Status:');
      console.log(`   - Service: ${result.service}`);
      console.log(`   - Version: ${result.version}`);
      console.log(`   - Status: ${result.status}`);
      console.log(`   - Scan timeout: ${result.configuration.scanTimeout}`);
      console.log(`   - Rate limit: ${result.configuration.rateLimit}`);
      console.log(`   - Nmap command: ${result.configuration.nmapCommand}`);
      return true;
    } else {
      console.log('❌ Failed to get service status:', result.error);
      return false;
    }
  } catch (error) {
    console.log('❌ Status check error:', error.message);
    return false;
  }
}

/**
 * Main test function
 */
async function runTests() {
  console.log('🧪 Starting Nmap Scanner Service Tests\n');
  console.log(`🔗 Service URL: ${NMAP_SERVICE_URL}\n`);
  
  // Test 1: Service status
  console.log('='.repeat(50));
  console.log('TEST 1: Service Status');
  console.log('='.repeat(50));
  await getServiceStatus();
  
  // Test 2: Nmap installation
  console.log('\n' + '='.repeat(50));
  console.log('TEST 2: Nmap Installation');
  console.log('='.repeat(50));
  const nmapOk = await testNmapInstallation();
  
  if (!nmapOk) {
    console.log('\n❌ Nmap is not properly installed. Please check:');
    console.log('   - nmap is installed and in PATH');
    console.log('   - nmap-scripts package is installed');
    console.log('   - Service has proper permissions');
    return;
  }
  
  // Test 3: Target validation
  console.log('\n' + '='.repeat(50));
  console.log('TEST 3: Target Validation');
  console.log('='.repeat(50));
  
  const validationTests = [
    '192.168.1.1',
    '127.0.0.1',
    '256.256.256.256',
    'invalid-ip',
    'google.com',
    'scanme.nmap.org',
    'invalid..hostname'
  ];
  
  for (const target of validationTests) {
    await validateTarget(target);
  }
  
  // Test 4: Scanning
  console.log('\n' + '='.repeat(50));
  console.log('TEST 4: Target Scanning');
  console.log('='.repeat(50));
  
  for (const testCase of testCases) {
    console.log(`\n🎯 Testing: ${testCase.description} (${testCase.target})`);
    
    // Validate first
    const isValid = await validateTarget(testCase.target);
    if (!isValid) {
      console.log('❌ Target validation failed, skipping scan');
      continue;
    }
    
    // Scan target
    await scanTarget(testCase.target);
  }
  
  console.log('\n' + '='.repeat(50));
  console.log('🏁 Test Suite Completed');
  console.log('='.repeat(50));
  console.log('\n📋 Summary:');
  console.log('- Service status checked');
  console.log('- Nmap installation verified');
  console.log('- Target validation tested');
  console.log('- Scanning functionality tested');
  console.log('\n✨ All tests completed!');
}

// Run tests if this script is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  runTests().catch(error => {
    console.error('❌ Test suite failed:', error);
    process.exit(1);
  });
}

export { testNmapInstallation, validateTarget, scanTarget, getServiceStatus };
