#!/bin/bash
set -e
echo "== Qwen3.5-1.5B 多源下载器 =="
mkdir -p ~/Downloads/models/qwen3.5-1.5b
cd ~/Downloads/models/qwen3.5-1.5b

# 源列表（按优先级）
SOURCES=(
  "https://hf-mirror.com/Qwen/Qwen3.5-1.5B-Instruct-GGUF/resolve/main/Qwen3.5-1.5B-Instruct-Q4_K_M.gguf|aria2c -x 8 -s 8 -k 1M {}"
  "https://huggingface.co/Qwen/Qwen3.5-1.5B-Instruct-GGUF/resolve/main/Qwen3.5-1.5B-Instruct-Q4_K_M.gguf|wget -c --no-check-certificate {}"
  "https://modelscope.cn/api/v1/models/Qwen/Qwen3.5-1.5B-Instruct-GGUF/repo?Revision=master&FilePath=Qwen3.5-1.5B-Instruct-Q4_K_M.gguf|aria2c -x 8 -s 8 {}"
)

for entry in "${SOURCES[@]}"; do
  URL="${entry%%|*}"
  CMD="${entry#*|}"
  echo ""
  echo ">>> 尝试下载: $URL"
  if eval "$CMD"; then
    echo "✅ 下载成功！"
    break
  else
    echo "❌ 失败，继续下一个源..."
  fi
done

if [ -f "Qwen3.5-1.5B-Instruct-Q4_K_M.gguf" ]; then
  echo ""
  echo "文件已就绪，现在启动 llama-server？"
else
  echo ""
  echo "所有源都挂了，建议手动去 ModelScope 下载"
fi
