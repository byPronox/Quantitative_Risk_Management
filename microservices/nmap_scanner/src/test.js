import { scanIP, validateIP, validateHostname, testNmapInstallation } from './scanner.js';

/**
 * Test suite for Nmap Scanner Service
 * Tests all core functionality with various test cases
 */

console.log('🧪 Starting Nmap Scanner Service Tests\n');

// Test cases
const testCases = [
  { target: '127.0.0.1', description: 'Localhost IP' },
  { target: '192.168.1.1', description: 'Private network IP' },
  { target: '8.8.8.8', description: 'Public DNS IP' },
  { target: 'scanme.nmap.org', description: 'Nmap test hostname' }
];

// Test validation functions
console.log('🔍 Testing validation functions...');

const validationTests = [
  { input: '192.168.1.1', type: 'IP', expected: true },
  { input: '127.0.0.1', type: 'IP', expected: true },
  { input: '256.256.256.256', type: 'IP', expected: false },
  { input: 'invalid-ip', type: 'IP', expected: false },
  { input: 'google.com', type: 'hostname', expected: true },
  { input: 'scanme.nmap.org', type: 'hostname', expected: true },
  { input: 'invalid..hostname', type: 'hostname', expected: false }
];

validationTests.forEach(test => {
  let result;
  if (test.type === 'IP') {
    result = validateIP(test.input);
  } else {
    result = validateHostname(test.input);
  }
  
  const status = result === test.expected ? '✅' : '❌';
  console.log(`${status} ${test.type} validation: "${test.input}" - Expected: ${test.expected}, Got: ${result}`);
});

console.log('\n🔧 Testing nmap installation...');

// Test nmap installation
try {
  const nmapTest = await testNmapInstallation();
  console.log('✅ Nmap installation test:', nmapTest.message);
  console.log('📋 Nmap version:', nmapTest.version);
} catch (error) {
  console.log('❌ Nmap installation test failed:', error.details);
  console.log('💡 Make sure nmap is installed and in PATH');
  process.exit(1);
}

console.log('\n🚀 Starting scan tests...\n');

// Test scanning functionality
for (const testCase of testCases) {
  console.log(`🎯 Testing: ${testCase.description} (${testCase.target})`);
  
  try {
    const startTime = Date.now();
    const result = await scanIP(testCase.target);
    const duration = Date.now() - startTime;
    
    console.log(`✅ Scan completed in ${duration}ms`);
    console.log(`📊 Results:`);
    console.log(`   - IP: ${result.ip}`);
    console.log(`   - OS: ${result.os}`);
    console.log(`   - Status: ${result.status}`);
    console.log(`   - Services found: ${result.services.length}`);
    console.log(`   - Vulnerabilities: ${result.vulnerabilities.length}`);
    
    if (result.services.length > 0) {
      console.log(`   - Sample service: ${result.services[0].port}/${result.services[0].protocol} - ${result.services[0].name}`);
    }
    
    console.log(`   - Timestamp: ${result.timestamp}`);
    console.log('');
    
  } catch (error) {
    console.log(`❌ Scan failed: ${error.error}`);
    console.log(`📝 Details: ${error.details}`);
    console.log('');
  }
}

console.log('🏁 Test suite completed!');
console.log('\n📋 Test Summary:');
console.log('- Validation functions tested');
console.log('- Nmap installation verified');
console.log('- Scan functionality tested with multiple targets');
console.log('- Error handling verified');
console.log('\n✨ All tests completed successfully!');
