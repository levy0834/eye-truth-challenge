#!/usr/bin/env python3
from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    # 启动浏览器（headless模式）
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    print("📸 正在访问 http://localhost:8080 ...")
    page.goto("http://localhost:8080", wait_until="networkidle", timeout=60000)
    
    # 等待关键元素出现
    print("⏳ 等待数据加载...")
    page.wait_for_selector("#total-count", timeout=15000)
    time.sleep(2)  # 额外等待图表渲染
    
    # 截图
    screenshot_path = "/Users/levy/.openclaw/workspace/quant-trading-system/dashboard/dashboard_screenshot.png"
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"✅ 截图已保存: {screenshot_path}")
    
    # 提取页面数据验证
    data = {
        "total_count": page.text_content("#total-count"),
        "stock_count": page.text_content("#stock-count"),
        "best_strategy": page.text_content("#best-strategy"),
        "best_return": page.text_content("#best-return"),
        "table_rows": len(page.query_selector_all("#table-body tr")),
        "summary_rows": len(page.query_selector_all("#summary-body tr"))
    }
    print("📊 页面数据:", data)
    
    browser.close()
    print("✅ 完成")
