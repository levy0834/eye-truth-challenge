#!/bin/bash
set -e
echo "== Qwen3.5-1.5B 多源下载器 =="
mkdir -p ~/Downloads/models/qwen3.5-1.5b
cd ~/Downloads/models/qwen3.5-1.5b

# 尝试源1: hf-mirror
echo ""
echo ">>> 尝试 hf-mirror.com (aria2)..."
if aria2c -x 8 -s 8 -k 1M "https://hf-mirror.com/Qwen/Qwen3.5-1.5B-Instruct-GGUF/resolve/main/Qwen3.5-1.5B-Instruct-Q4_K_M.gguf"; then
  echo "✅ 下载成功！"
  exit 0
fi

# 尝试源2: huggingface (wget)
echo ""
echo ">>> 尝试 huggingface.co (wget)..."
if wget -c --no-check-certificate "https://huggingface.co/Qwen/Qwen3.5-1.5B-Instruct-GGUF/resolve/main/Qwen3.5-1.5B-Instruct-Q4_K_M.gguf"; then
  echo "✅ 下载成功！"
  exit 0
fi

# 尝试源3: modelscope API (aria2)
echo ""
echo ">>> 尝试 modelscope.cn (aria2)..."
if aria2c -x 8 -s 8 "https://modelscope.cn/api/v1/models/Qwen/Qwen3.5-1.5B-Instruct-GGUF/repo?Revision=master&FilePath=Qwen3.5-1.5B-Instruct-Q4_K_M.gguf"; then
  echo "✅ 下载成功！"
  exit 0
fi

echo ""
echo "❌ 所有源都失败了。"
echo "建议手动访问 https://modelscope.cn/models/Qwen/Qwen3.5-1.5B-Instruct-GGUF 下载"
