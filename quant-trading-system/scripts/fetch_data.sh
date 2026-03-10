#!/bin/bash
# 一键数据抓取脚本
set -e

cd "$(dirname "$0")/.."

echo "=========================================="
echo "📥 抓取历史数据"
echo "=========================================="

# 检查依赖（至少需要yfinance或akshare）
python3 -c "import yfinance" 2>/dev/null || echo "⚠️  yfinance 未安装"
python3 -c "import akshare" 2>/dev/null || echo "⚠️  akshare 未安装"

# 默认抓取所有配置的标的
python3 -m src.main fetch "$@"

echo ""
echo "✅ 数据抓取完成！文件保存在 data/raw/ 目录"
