#!/usr/bin/env python3
"""修复看板：支持训练/测试集资金曲线切换"""
import re

file_path = "/Users/levy/.openclaw/workspace/quant-trading-system/dashboard/index_fixed.html"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. 修改 loadAllData：不再固定加载 equity_curves_train.json
old_load = '''        async function loadAllData() {
            setStatus('加载中...', true);
            try {
                // 并行加载
                const [trainRes, testRes, equityRes] = await Promise.all([
                    fetch('details_train.csv'),
                    fetch('details_test.csv'),
                    fetch('equity_curves_train.json')
                ]);

                if (!trainRes.ok) throw new Error('训练集数据缺失');

                const [trainTxt, testTxt, equityTxt] = await Promise.all([
                    trainRes.text(),
                    testRes.text(),
                    equityRes.ok ? equityRes.text() : Promise.resolve('{}')
                ]);

                trainData = parseCSV(trainTxt);
                testData = testRes.ok ? parseCSV(testTxt) : [];
                equityData = equityTxt ? JSON.parse(equityTxt) : {};'''

new_load = '''        async function loadAllData() {
            setStatus('加载中...', true);
            try {
                // 并行加载
                const [trainRes, testRes] = await Promise.all([
                    fetch('details_train.csv'),
                    fetch('details_test.csv')
                ]);

                if (!trainRes.ok) throw new Error('训练集数据缺失');

                const [trainTxt, testTxt] = await Promise.all([
                    trainRes.text(),
                    testRes.text()
                ]);

                trainData = parseCSV(trainTxt);
                testData = testRes.ok ? parseCSV(testTxt) : [];
                equityData = {};  // 延迟加载'''

content = content.replace(old_load, new_load)

# 2. 在 switchTab 函数中添加 loadEquityData 调用
# 找到 switchTab 函数体末尾的 updateEquityChart(); 并在之前添加
old_switch_end = '''            updateBadge();
            updateKPI();
            renderSummary();
            applyFilter();
            renderTop10();
            updateEquityChart();
        }'''

new_switch_end = '''            updateBadge();
            updateKPI();
            renderSummary();
            applyFilter();
            renderTop10();
            // 加载对应数据集的资金曲线
            loadEquityData(tab).then(() => {
                updateEquityChart();
            });
        }'''

content = content.replace(old_switch_end, new_switch_end)

# 3. 添加 loadEquityData 函数定义（在 switchTab 之后）
load_equity_func = '''
        async function loadEquityData(dataset) {
            try {
                const res = await fetch(`equity_curves_${dataset}.json`);
                if (res.ok) {
                    equityData = await res.json();
                    console.log(`✅ 资金曲线加载 (${dataset}): ${Object.keys(equityData).length} 策略`);
                } else {
                    console.warn(`equity_curves_${dataset}.json 不存在`);
                    equityData = {};
                }
            } catch (e) {
                console.warn('加载资金曲线失败:', e);
                equityData = {};
            }
        }
'''

# 插入到 switchTab 函数之后（在 "function updateBadge" 之前）
insert_marker = "        function updateBadge() {"
if insert_marker in content:
    content = content.replace(insert_marker, load_equity_func + "\n" + insert_marker)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ 看板已修复：支持训练/测试集资金曲线切换")
print("📊 请刷新: http://localhost:8081/analysis.html")
