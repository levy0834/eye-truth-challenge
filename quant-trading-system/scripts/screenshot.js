#!/usr/bin/env node
const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const page = await browser.newPage();
  
  console.log('📸 访问 http://localhost:8080 ...');
  await page.goto('http://localhost:8080', { waitUntil: 'networkidle2', timeout: 30000 });
  
  // 等待数据加载
  console.log('⏳ 等待数据渲染...');
  await page.waitForSelector('#total-count', { timeout: 10000 });
  await new Promise(r => setTimeout(r, 2000)); // 额外等2秒确保图表渲染
  
  const screenshotPath = '/Users/levy/.openclaw/workspace/quant-trading-system/dashboard/dashboard_screenshot.png';
  await page.screenshot({ path: screenshotPath, fullPage: true });
  console.log('✅ 截图保存:', screenshotPath);
  
  // 提取页面关键数据
  const data = await page.evaluate(() => {
    return {
      totalCount: document.getElementById('total-count')?.textContent,
      stockCount: document.getElementById('stock-count')?.textContent,
      bestStrategy: document.getElementById('best-strategy')?.textContent,
      bestReturn: document.getElementById('best-return')?.textContent,
      tableRows: document.querySelectorAll('#table-body tr').length,
      summaryRows: document.querySelectorAll('#summary-body tr').length,
      chartExists: !!document.getElementById('dist-chart')
    };
  });
  
  console.log('📊 页面数据:', JSON.stringify(data, null, 2));
  
  await browser.close();
  console.log('✅ 完成');
})().catch(err => {
  console.error('❌ 截图失败:', err.message);
  process.exit(1);
});
