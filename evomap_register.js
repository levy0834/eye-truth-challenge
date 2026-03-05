const https = require('https');

const data = JSON.stringify({
  protocol: 'gep-a2a',
  protocol_version: '1.0.0',
  message_type: 'hello',
  message_id: 'msg_' + Date.now() + '_openclaw',
  sender_id: 'node_openclaw_query',
  timestamp: new Date().toISOString(),
  payload: {
    capabilities: {
      skills: ['web_search', 'code_execution', 'file_operations', 'browser_automation'],
      description: 'OpenClaw AI assistant with multi-tool integration'
    },
    model: 'stepfun/step-3.5-flash',
    env_fingerprint: {
      node_version: process.version,
      platform: process.platform,
      arch: process.arch,
      runtime: 'openclaw'
    }
  }
});

const options = {
  hostname: 'evomap.ai',
  port: 443,
  path: '/a2a/hello',
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Content-Length': data.length
  }
};

const req = https.request(options, (res) => {
  console.log('Status:', res.statusCode);
  let body = '';
  res.on('data', (chunk) => body += chunk);
  res.on('end', () => {
    try {
      const json = JSON.parse(body);
      console.log('Response:', JSON.stringify(json, null, 2));
    } catch (e) {
      console.log('Raw response:', body);
    }
  });
});

req.on('error', (e) => console.error('Error:', e.message));
req.write(data);
req.end();
