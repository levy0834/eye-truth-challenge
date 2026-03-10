#!/bin/bash
# 一键回测脚本
set -e

cd "$(dirname "$0")/.."

echo "=========================================="
echo "🔬 运行回测"
echo "=========================================="

# 检查依赖
python3 -c "import pandas" 2>/dev/null || { echo "❌ 请先安装依赖: pip3 install -r requirements.txt"; exit 1; }

# 默认参数
SYMBOL="${1:-510300.SH}"
STRATEGY="${2:-ma_cross}"

echo "📊 标的: $SYMBOL"
echo "🎯 策略: $STRATEGY"
echo ""

python3 -m src.main backtest --symbol "$SYMBOL" --strategy "$STRATEGY"

echo ""
echo "✅ 回测完成！查看 results/$SYMBOL/ 目录"
