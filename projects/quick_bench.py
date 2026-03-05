#!/usr/bin/env python3
"""Quick benchmark: 每后端测一次，取关键指标"""
import time, json, requests

OLLAMA_URL = "http://localhost:11434/v1/completions"
LLAMA_URL = "http://localhost:8080/v1/completions"
MODEL_OLLAMA = "qwen3:1.7b"
MODEL_LLAMA = "qwen3-1.7b.gguf"
PROMPT = "用一句话介绍杭州西湖"
MAX_TOKENS = 64

def test_backend(url, model):
    start = time.time()
    r = requests.post(url, json={"model": model, "prompt": PROMPT, "max_tokens": MAX_TOKENS, "stream": False}, timeout=120)
    total = time.time() - start
    data = r.json()
    tokens = data.get("usage", {}).get("completion_tokens", 0)
    tps = tokens / total if total>0 else 0
    text = data.get("choices", [{}])[0].get("text", "")
    return {"total_s": total, "tokens": tokens, "tps": tps, "text_len": len(text or "")}

print("Testing Ollama...")
ollama_res = test_backend(OLLAMA_URL, MODEL_OLLAMA)
print(f"  total={ollama_res['total_s']:.2f}s, tokens={ollama_res['tokens']}, tps={ollama_res['tps']:.1f}")

print("Testing llama-server...")
llama_res = test_backend(LLAMA_URL, MODEL_LLAMA)
print(f"  total={llama_res['total_s']:.2f}s, tokens={llama_res['tokens']}, tps={llama_res['tps']:.1f}")

report = {
    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    "prompt": PROMPT,
    "ollama": ollama_res,
    "llama_server": llama_res
}
print("\n=== RESULT JSON ===")
print(json.dumps(report, indent=2, ensure_ascii=False))

# Save
path = f"/Users/levy/.openclaw/workspace/reports/qwen-quick-{time.strftime('%Y%m%d-%H%M')}.json"
with open(path, "w") as f:
    json.dump(report, f, indent=2, ensure_ascii=False)
print(f"\nSaved to: {path}")
