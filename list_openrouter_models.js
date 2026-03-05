#!/usr/bin/env node
/**
 * 查询 OpenRouter 可用的 StepFun 模型
 * 需要 OPENROUTER_API_KEY
 */

const https = require('https');

const API_KEY = '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';

function getModels() {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: 'openrouter.ai',
      port: 443,
      path: '/api/v1/models',
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${API_KEY}`,
        'Content-Type': 'application/json'
      },
      timeout: 10000
    };

    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const json = JSON.parse(data);
          resolve(json);
        } catch (e) {
          reject(new Error('Parse error: ' + e.message));
        }
      });
    });

    req.on('error', reject);
    req.on('timeout', () => {
      req.destroy();
      reject(new Error('Timeout'));
    });

    req.end();
  });
}

getModels()
  .then(models => {
    console.log('=== OpenRouter Models ===\n');
    
    // 过滤 StepFun 相关模型
    const stepfunModels = models.data.filter(m => 
      m.id.includes('step') || 
      m.id.includes(' StepFun') ||
      (m.provider && m.provider.includes('step'))
    );
    
    if (stepfunModels.length > 0) {
      console.log(`Found ${stepfunModels.length} StepFun models:\n`);
      stepfunModels.forEach(m => {
        console.log(`ID: ${m.id}`);
        console.log(`  Name: ${m.name || 'N/A'}`);
        console.log(`  Provider: ${m.provider || 'N/A'}`);
        console.log(`  Context: ${m.context_length || 'N/A'}`);
        console.log(`  Pricing: ${m.pricing ? JSON.stringify(m.pricing) : 'N/A'}`);
        console.log('');
      });
    } else {
      console.log('No StepFun models found. All models:\n');
      models.data.forEach(m => {
        console.log(`${m.id} - ${m.name || 'N/A'} (${m.provider || 'unknown'})`);
      });
    }
  })
  .catch(err => {
    console.error('Error:', err.message);
  });
