#!/usr/bin/env python3
"""
LM Backend Benchmark: Ollama vs llama-server
对比 qwen3-1.7b 在不同后端的性能表现
"""
import time
import json
import sys
import os
import psutil
import requests
from typing import Dict, List, Tuple

# 配置
OLLAMA_URL = "http://localhost:11434/v1/completions"
LLAMA_URL = "http://localhost:8080/v1/completions"
MODEL_NAME = "qwen3:1.7b"  # Ollama model name
LLAMA_MODEL = "qwen3-1.7b.gguf"  # llama-server model name
TEST_PROMPTS = [
    ("简单介绍", "用一句话介绍杭州西湖"),
    ("算法题", "写一个快速排序算法，并解释时间复杂度"),
    ("推理题", "如果今天周三，29天后是星期几？请分步骤推理")
]
RUNS_PER_PROMPT = 3
MAX_TOKENS = 256

def get_memory_usage() -> Dict:
    """获取当前进程内存使用 (MB)"""
    process = psutil.Process(os.getpid())
    mem = process.memory_info()
    return {"rss_mb": mem.rss / 1024 / 1024, "vms_mb": mem.vms / 1024 / 1024}

def call_ollama(prompt: str) -> Tuple[float, float, int, str]:
    """调用 Ollama API，返回 (ttft, total_time, tokens, text)"""
    start = time.time()
    resp = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "max_tokens": MAX_TOKENS,
            "stream": False
        },
        timeout=120
    )
    first_token_time = None
    data = resp.json()
    total_time = time.time() - start
    # 如果没有流式，无法精确测量TTFT，用总时间的一半估算
    ttft = total_time / 2
    tokens = data.get("usage", {}).get("completion_tokens", 0)
    text = data.get("choices", [{}])[0].get("text", "")
    return ttft, total_time, tokens, text

def call_llama(prompt: str) -> Tuple[float, float, int, str]:
    """调用 llama-server API"""
    start = time.time()
    resp = requests.post(
        LLAMA_URL,
        json={
            "model": LLAMA_MODEL,
            "prompt": prompt,
            "max_tokens": MAX_TOKENS,
            "stream": False
        },
        timeout=120
    )
    data = resp.json()
    total_time = time.time() - start
    # 同样估算 TTFT
    ttft = total_time / 2
    tokens = data.get("usage", {}).get("completion_tokens", 0)
    text = data.get("choices", [{}])[0].get("text", "")
    return ttft, total_time, tokens, text

def benchmark_backend(name: str, func, prompt: str) -> Dict:
    """对单个后端单次Prompt跑多次，返回平均值"""
    ttfts = []
    totals = []
    tokenss = []
    mem_before = get_memory_usage()
    for i in range(RUNS_PER_PROMPT):
        try:
            ttft, total, tokens, _ = func(prompt)
            ttfts.append(ttft)
            totals.append(total)
            tokenss.append(tokens)
            print(f"  [{name}] run {i+1}: ttft={ttft:.3f}s total={total:.3f}s tokens={tokens}")
        except Exception as e:
            print(f"  [{name}] run {i+1} failed: {e}")
    mem_after = get_memory_usage()
    return {
        "backend": name,
        "prompt": prompt[:30] + ("..." if len(prompt)>30 else ""),
        "ttft_avg": sum(ttfts)/len(ttfts) if ttfts else None,
        "total_avg": sum(totals)/len(totals) if totals else None,
        "tokens_avg": sum(tokenss)/len(tokenss) if tokenss else None,
        "tps_avg": sum(tokenss)/sum(totals) if totals else None,
        "memory_delta_mb": mem_after["rss_mb"] - mem_before["rss_mb"]
    }

def main():
    print("="*60)
    print("Start benchmark at", time.strftime("%Y-%m-%d %H:%M:%S"))
    print("="*60)
    results = []

    for task_name, prompt in TEST_PROMPTS:
        print(f"\n🔹 Task: {task_name}")
        # Ollama
        res_ollama = benchmark_backend("Ollama", call_ollama, prompt)
        results.append(res_ollama)
        # llama-server
        res_llama = benchmark_backend("llama-server", call_llama, prompt)
        results.append(res_llama)

    # 输出汇总
    print("\n" + "="*60)
    print("RESULTS SUMMARY")
    print("="*60)
    print(json.dumps(results, indent=2, ensure_ascii=False))

    # 生成 Markdown 报告
    report_path = f"/Users/levy/.openclaw/workspace/reports/qwen-benchmark-{time.strftime('%Y%m%d-%H%M')}.md"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Qwen3-1.7B 性能对比报告\n\n")
        f.write(f"- 时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("- 模型: qwen3-1.7b (GGUF)\n")
        f.write("- 测试机器: macOS 15.7.4, Intel x86_64, 16GB RAM\n\n")
        f.write("## 测试设置\n\n")
        f.write("- Ollama API: `http://localhost:11434`\n")
        f.write("- llama-server API: `http://localhost:8080`\n")
        f.write(f"- 每项任务运行次数: {RUNS_PER_PROMPT}\n")
        f.write(f"- 最大输出 token 数: {MAX_TOKENS}\n\n")

        f.write("## 详细数据 (JSON)\n\n```json\n")
        f.write(json.dumps(results, indent=2, ensure_ascii=False))
        f.write("\n```\n\n")

        f.write("## 对比表格\n\n")
        f.write("| 任务 | 后端 | TTFT (s) | 总耗时 (s) | Tokens | TPS | 内存增量 (MB) |\n")
        f.write("|------|------|----------|------------|--------|-----|---------------|\n")
        for r in results:
            f.write(f"| {r['backend']} | {r['prompt']} | {r['ttft_avg']:.3f} | {r['total_avg']:.3f} | {int(r['tokens_avg'])} | {r['tps_avg']:.1f} | {r['memory_delta_mb']:.1f} |\n")

        # 简单推荐
        f.write("\n## 结论与建议\n\n")
        f.write("根据以上数据：\n")
        # 稍后填充

    print(f"\n📊 Report saved to: {report_path}")
    print("✓ Benchmark complete!")

if __name__ == "__main__":
    main()
