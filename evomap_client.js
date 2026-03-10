/**
 * EvoMap Query Client with Retry Logic
 * Node ID: node_openclaw_query
 * Retry: up to 3 attempts with exponential backoff
 */

const https = require('https');

const NODE_ID = 'node_openclaw_query';
const BASE_URL = 'https://evomap.ai/a2a';
const MAX_RETRIES = 3;

// Exponential backoff: 1s, 2s, 4s
function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function evomapRequest(endpoint, payload = {}) {
  const body = JSON.stringify(payload);

  const options = {
    hostname: 'evomap.ai',
    port: 443,
    path: endpoint,
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Content-Length': body.length
    }
  };

  for (let attempt = 1; attempt <= MAX_RETRIES; attempt++) {
    try {
      console.log(`[Attempt ${attempt}/${MAX_RETRIES}] POST ${endpoint}`);

      const result = await new Promise((resolve, reject) => {
        const req = https.request(options, (res) => {
          let data = '';
          res.on('data', chunk => data += chunk);
          res.on('end', () => {
            try {
              const json = JSON.parse(data);
              resolve({ status: res.statusCode, data: json });
            } catch (e) {
              resolve({ status: res.statusCode, data: data });
            }
          });
        });

        req.on('error', (err) => reject(err));
        req.on('timeout', () => {
          req.destroy();
          reject(new Error('Request timeout'));
        });
        req.write(body);
        req.end();
      });

      if (result.status === 200) {
        console.log(`✓ Success`);
        return result.data;
      } else {
        console.warn(`⚠️  HTTP ${result.status}:`, result.data?.error || 'Unknown error');
        if (attempt < MAX_RETRIES) {
          const backoff = Math.pow(2, attempt) * 1000;
          console.log(`   Retrying in ${backoff}ms...`);
          await delay(backoff);
        } else {
          throw new Error(`Failed after ${MAX_RETRIES} attempts: HTTP ${result.status}`);
        }
      }
    } catch (err) {
      console.error(`✗ Attempt ${attempt} failed:`, err.message);
      if (attempt < MAX_RETRIES) {
        const backoff = Math.pow(2, attempt) * 1000;
        console.log(`   Retrying in ${backoff}ms...`);
        await delay(backoff);
      } else {
        throw err;
      }
    }
  }
}

// Send heartbeat
async function heartbeat() {
  return evomapRequest('/a2a/heartbeat', {
    node_id: NODE_ID
  });
}

// Search assets by signals (REST endpoint, faster than A2A fetch)
async function searchAssets(signals, limit = 10) {
  const query = new URLSearchParams({
    signals: Array.isArray(signals) ? signals.join(',') : signals,
    limit: limit
  });

  const options = {
    hostname: 'evomap.ai',
    port: 443,
    path: `/a2a/assets/search?${query}`,
    method: 'GET'
  };

  // GET 不需要重试逻辑这么复杂，直接 fetch
  return new Promise((resolve, reject) => {
    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const json = JSON.parse(data);
          resolve(json);
        } catch (e) {
          resolve(data);
        }
      });
    });

    req.on('error', reject);
    req.on('timeout', () => {
      req.destroy();
      reject(new Error('Request timeout'));
    });
    req.end();
  });
}

// Get ranked assets (top quality)
async function getRanked(limit = 10) {
  return new Promise((resolve, reject) => {
    https.get({
      hostname: 'evomap.ai',
      port: 443,
      path: `/a2a/assets/ranked?limit=${limit}`
    }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          resolve(JSON.parse(data));
        } catch (e) {
          resolve(data);
        }
      });
    }).on('error', reject).on('timeout', () => {
      req.destroy();
      reject(new Error('Timeout'));
    });
  });
}

// Get recommended tasks (GET endpoint)
async function getTasks(minBounty = 0, limit = 20) {
  const query = new URLSearchParams({
    min_bounty: minBounty,
    limit: limit
  });

  return new Promise((resolve, reject) => {
    https.get({
      hostname: 'evomap.ai',
      port: 443,
      path: `/a2a/task/list?${query}`
    }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          resolve(JSON.parse(data));
        } catch (e) {
          resolve(data);
        }
      });
    }).on('error', reject).on('timeout', () => {
      req.destroy();
      reject(new Error('Timeout'));
    });
  });
}

// Check node status
async function checkStatus() {
  const response = await evomapRequest('/a2a/nodes/' + NODE_ID);
  return response;
}

// Main interactive mode
async function main() {
  if (process.argv.length < 3) {
    console.log(`
EvoMap Query Client (node: ${NODE_ID})

Usage:
  node evomap_client.js heartbeat          # Send heartbeat
  node evomap_client.js search <signals>  # Search assets by signals (comma-separated)
  node evomap_client.js ranked [limit]    # Get top-ranked assets (default 10)
  node evomap_client.js tasks [minBounty] # List bounty tasks (default minBounty=0)
  node evomap_client.js status            # Check node status

Examples:
  node evomap_client.js search "retry,exponential_backoff,python"
  node evomap_client.js ranked 5
  node evomap_client.js tasks 100         # Only tasks with bounty >= 100
`);
    process.exit(1);
  }

  const command = process.argv[2];

  try {
    switch (command) {
      case 'heartbeat':
        const hb = await heartbeat();
        console.log('Heartbeat response:', JSON.stringify(hb, null, 2));
        break;

      case 'search':
        if (!process.argv[3]) {
          console.error('Error: signals required');
          process.exit(1);
        }
        const signals = process.argv[3].split(',').map(s => s.trim());
        const limit = parseInt(process.argv[4]) || 10;
        console.log(`Searching assets with signals: ${signals.join(', ')} (limit=${limit})`);
        const assets = await searchAssets(signals, limit);
        console.log('Search results:', JSON.stringify(assets, null, 2));
        break;

      case 'ranked':
        const rankLimit = parseInt(process.argv[3]) || 10;
        console.log(`Fetching top ${rankLimit} ranked assets`);
        const ranked = await getRanked(rankLimit);
        console.log('Ranked assets:', JSON.stringify(ranked, null, 2));
        break;

      case 'tasks':
        const minBounty = parseInt(process.argv[3]) || 0;
        console.log(`Fetching tasks with min_bounty >= ${minBounty}`);
        const tasks = await getTasks(minBounty);
        console.log('Tasks:', JSON.stringify(tasks, null, 2));
        break;

      case 'status':
        console.log('Checking node status...');
        const status = await checkStatus();
        console.log('Status:', JSON.stringify(status, null, 2));
        break;

      default:
        console.error(`Unknown command: ${command}`);
        process.exit(1);
    }
  } catch (err) {
    console.error('Fatal error:', err.message);
    process.exit(1);
  }
}

// Export for programmatic use
module.exports = {
  heartbeat,
  searchAssets,
  getRanked,
  getTasks,
  checkStatus,
  evomapRequest
};

// Run if called directly
if (require.main === module) {
  main();
}
