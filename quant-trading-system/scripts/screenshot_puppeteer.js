#!/usr/bin/env node
const puppeteer = require('puppeteer-core');

(async () => {
  // Chrome路径（Mac）
  const chromePath = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
  
  const browser = await puppeteer.launch({
    executablePath: chromePath,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const page = await browser.newPage();
  console.log('📸 正在访问 http://localhost:8080 ...');
  
  try {
    await page.goto('http://localhost:8080', { 
      waitUntil: 'networkidle2', 
      timeout: 30000 
    });
  } catch (e) {
    console.log('⚠️  页面加载超时，尝试截图 anyway...');
  }
  
  // 等待数据加载
  await page.waitForSelector('#total-count', { timeout: 15000 }).catch(() => console.log('Selector not found'));
  await new Promise(r => setTimeout(r, 2000));
  
  const screenshotPath = './dashboard/dashboard_screenshot.png';
  await page.screenshot({ path: screenshotPath, fullPage: true });
  console.log('✅ 截图已保存:', screenshotPath);
  
  // 验证数据
  const data = await page.evaluate(() => {
    return {
      total: document.getElementById('total-count')?.textContent,
      stocks: document.getElementById('stock-count')?.textContent,
      best: document.getElementById('best-strategy')?.textContent,
      return: document.getElementById('best-return')?.textContent,
      tableRows: document.querySelectorAll('#table-body tr').length,
      summaryRows: document.querySelectorAll('#summary-body tr').length
    };
  });
  console.log('📊 数据验证:', JSON.stringify(data, null, 2));
  
  await browser.close();
  console.log('✅ 完成');
})().catch(err => {
  console.error('❌ 失败:', err.message);
  process.exit(1);
});
