#!/usr/bin/env node
/**
 * Test Groq API Connectivity
 * Models: llama-3.1-70b-versatile, llama-3.1-8b, gemma2-9b-it
 */

const https = require('https');

const API_KEY = 'gsk_...'; // 需要真实的 API key
const MODELS = [
  'llama-3.1-70b-versatile',
  'llama-3.1-8b-instant',
  'gemma2-9b-it'
];

function testGroq(model) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify({
      model: model,
      messages: [{ role: 'user', content: 'Hello, are you working? Reply in one word.' }],
      max_tokens: 10
    });

    const options = {
      hostname: 'api.groq.com',
      port: 443,
      path: '/openai/v1/chat/completions',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${API_KEY}`,
        'Content-Length': data.length
      },
      timeout: 10000
    };

    const startTime = Date.now();
    const req = https.request(options, (res) => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => {
        const duration = Date.now() - startTime;
        try {
          const json = JSON.parse(body);
          if (json.error) {
            resolve({ model, success: false, error: json.error.message || json.error, duration });
          } else {
            resolve({ model, success: true, content: json.choices[0].message.content.trim(), duration });
          }
        } catch (e) {
          resolve({ model, success: false, error: 'Parse error: ' + e.message, duration, raw: body });
        }
      });
    });

    req.on('error', (err) => {
      resolve({ model, success: false, error: err.message, duration: Date.now() - startTime });
    });

    req.on('timeout', () => {
      req.destroy();
      resolve({ model, success: false, error: 'Timeout (10s)', duration: Date.now() - startTime });
    });

    req.write(data);
    req.end();
  });
}

async function main() {
  console.log('=== Groq API Connectivity Test ===\n');
  
  for (const model of MODELS) {
    console.log(`Testing: ${model}...`);
    const result = await testGroq(model);
    
    if (result.success) {
      console.log(`  ✅ Success (${result.duration}ms)`);
      console.log(`  Response: "${result.content}"\n`);
    } else {
      console.log(`  ❌ Failed (${result.duration}ms)`);
      console.log(`  Error: ${result.error}\n`);
    }
    
    // 避免限流，间隔 1 秒
    await new Promise(r => setTimeout(r, 1000));
  }
}

main().catch(console.error);
