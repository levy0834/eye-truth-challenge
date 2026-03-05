#!/usr/bin/env python3
"""
每日早报脚本 - 使用飞书 API 直接创建 Callout 高亮块
- 生成文档内容并直接调用 OpenAPI 创建块
- 支持真正的 callout 高亮效果
"""
import subprocess
import json
import os
import requests
from datetime import datetime
import argparse
import sys

FEISHU_USER_ID = "user:ou_a413ba619c59873009e5a4d5d7b8bb5e"
WORKSPACE = "/Users/levy/.openclaw/workspace"

# 飞书应用凭证
FEISHU_APP_ID = os.getenv("FEISHU_APP_ID", "cli_a92f1eea88b8dbc8")
FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET", "wgWhrWDZEbKVRl1CcVcISb8aFO0UelA4")

def get_chinese_date():
    now = datetime.now()
    weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    return f"{now.year}年{now.month}月{now.day}日 {weekdays[now.weekday()]}"

def fetch_news_baidu(query, limit=8):
    """使用百度AI搜索技能获取新闻"""
    try:
        cmd = [
            "python3", "skills/baidu-search/scripts/search.py",
            json.dumps({
                "query": query,
                "search_recency_filter": "day",
                "resource_type_filter": [{"type": "web", "top_k": limit}]
            })
        ]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30, cwd=WORKSPACE)
        if r.returncode == 0 and r.stdout.strip():
            lines = r.stdout.strip().split('\n')
            if len(lines) >= 2:
                json_str = '\n'.join(lines[1:])
                data = json.loads(json_str)
                results = []
                for item in data[:limit]:
                    title = item.get('title', '').strip()
                    content = item.get('content', '').strip()
                    if title and content:
                        summary = content[:120].replace('\n', ' ')
                        results.append({
                            "title": title,
                            "summary": summary,
                            "url": item.get('url', '')
                        })
                    elif title:
                        results.append({
                            "title": title,
                            "summary": "",
                            "url": item.get('url', '')
                        })
                return results if results else []
    except Exception as e:
        print(f"⚠️ 搜索失败 [{query}]: {e}")
        return []

def get_feishu_tenant_token():
    """获取飞书租户访问令牌"""
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    headers = {"Content-Type": "application/json"}
    data = {
        "app_id": FEISHU_APP_ID,
        "app_secret": FEISHU_APP_SECRET
    }
    try:
        resp = requests.post(url, headers=headers, json=data, timeout=10)
        resp.raise_for_status()
        result = resp.json()
        if result.get("code") == 0:
            token = result.get("tenant_access_token")
            print(f"✅ 获取tenant_access_token成功（长度: {len(token) if token else 0}）")
            return token
        else:
            print(f"❌ 获取tenant_access_token失败: code={result.get('code')}, msg={result.get('msg')}")
    except Exception as e:
        print(f"❌ 请求tenant_access_token异常: {e}")
    return None

def create_empty_feishu_doc(title, owner_open_id=None):
    """创建空飞书文档（仅标题）"""
    token = get_feishu_tenant_token()
    if not token:
        return None
    
    url = "https://open.feishu.cn/open-apis/docx/v1/documents"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {"title": title}
    if owner_open_id:
        if owner_open_id.startswith("user:"):
            owner_open_id = owner_open_id.replace("user:", "")
        data["owner_id"] = {"id": owner_open_id, "open_id": owner_open_id}
    
    try:
        resp = requests.post(url, headers=headers, json=data, timeout=30)
        resp.raise_for_status()
        result = resp.json()
        if result.get("code") == 0:
            doc = result.get("data", {}).get("document", {})
            return doc.get("document_id")  # 用 document_id，不是 token
        else:
            print(f"❌ 创建文档失败: {result.get('msg')}")
            return None
    except Exception as e:
        print(f"❌ 创建文档异常: {e}")
        return None

def build_text_block(text, bold=False):
    """构建文本块 (block_type=2)"""
    elements = []
    # 处理文本中的链接（简单处理，实际上需要更复杂的解析）
    if "[" in text and "](" in text:
        # 这里简化处理，实际需要解析 markdown 链接
        elements.append({"text_run": {"content": text}})
    else:
        elements.append({"text_run": {"content": text}})
    
    if bold:
        elements[0]["text_run"]["style"] = {"bold": True}
    
    return {
        "block_type": 2,  # text
        "text": {"elements": elements}
    }

def build_callout_block(title, emoji_id="bulb", bg_color=2):
    """构建高亮块 (Callout, block_type=40)"""
    return {
        "block_type": 40,  # callout
        "callout": {
            "background_color": bg_color,
            "border_color": 0,
            "emoji_id": emoji_id
        },
        "children": [
            build_text_block(title, bold=True)
        ]
    }

def build_heading_block(level, text):
    """构建标题块 (block_type=3/4/5 for heading1/2/3)"""
    heading_map = {1: ("heading1", 3), 2: ("heading2", 4), 3: ("heading3", 5)}
    heading_type, block_type = heading_map.get(level, ("heading2", 4))
    return {
        "block_type": block_type,
        heading_type: {
            "elements": [{"text_run": {"content": text, "style": {"bold": True}}}]
        }
    }

def create_blocks_sequential(token, doc_token, blocks_data):
    """顺序创建块（每块独立调用）"""
    url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_token}/blocks"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    block_ids = []
    for i, block in enumerate(blocks_data, 1):
        payload = {"index": 0, **block}  # 插入到末尾
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        if resp.status_code == 200 and resp.json().get("code") == 0:
            result = resp.json()
            block_id = result.get("data", {}).get("block", {}).get("block_id")
            if block_id:
                block_ids.append(block_id)
                print(f"✅ [{i}/{len(blocks_data)}] 创建块成功: type={block.get('block_type')} → {block_id[:12]}...")
        else:
            print(f"❌ [{i}] 创建块失败 (HTTP {resp.status_code}): {resp.text[:300]}")
            # 打印请求详情以便调试
            if resp.status_code == 404:
                print(f"   请求URL: {url}")
                print(f"   请求体: {json.dumps(block, ensure_ascii=False)[:200]}...")
    
    return block_ids

def build_full_document_blocks():
    """构建完整的文档块数据结构"""
    date_str = get_chinese_date()
    ai_news = fetch_news_baidu("人工智能 AI 最新动态", 6)
    finance_news = fetch_news_baidu("财经新闻 投资 股市", 6)
    hangzhou_news = fetch_news_baidu("杭州新闻 最新动态", 6)
    
    blocks = []
    
    # 1. 标题 (H2)
    blocks.append(build_heading_block(2, f"📰 每日早报 | {date_str}"))
    
    # 2. AI 板块
    blocks.append(build_heading_block(3, "🤖 AI 前沿动态"))
    blocks.append(build_callout_block("💡 今日要点：重点关注AI领域的最新突破", emoji_id="bulb", bg_color=2))
    for i, news in enumerate(ai_news, 1):
        title = news['title']
        url = news.get('url', '')
        if url:
            blocks.append({
                "block_type": 2,
                "text": {
                    "elements": [
                        {"text_run": {"content": f"{i}. "}},
                        {"text_run": {"content": title, "style": {"bold": True, "link": {"url": url}}}}
                    ]
                }
            })
        else:
            blocks.append(build_text_block(f"{i}. {title}", bold=True))
        if news.get('summary'):
            blocks.append(build_text_block(news['summary']))
        blocks.append(build_text_block(""))  # 空行
    
    # 3. 财经板块
    blocks.append(build_heading_block(3, "📈 投资与财经"))
    blocks.append(build_callout_block("💰 市场热点：关注今日财经动态", emoji_id="warning", bg_color=3))
    for i, news in enumerate(finance_news, 1):
        title = news['title']
        url = news.get('url', '')
        if url:
            blocks.append({
                "block_type": 2,
                "text": {
                    "elements": [
                        {"text_run": {"content": f"{i}. "}},
                        {"text_run": {"content": title, "style": {"bold": True, "link": {"url": url}}}}
                    ]
                }
            })
        else:
            blocks.append(build_text_block(f"{i}. {title}", bold=True))
        if news.get('summary'):
            blocks.append(build_text_block(news['summary']))
        blocks.append(build_text_block(""))
    
    # 4. 杭州板块
    blocks.append(build_heading_block(3, "🏙️ 杭州新鲜事"))
    blocks.append(build_callout_block("🏙️ 本地资讯：杭州最新动态", emoji_id="star", bg_color=4))
    for i, news in enumerate(hangzhou_news, 1):
        title = news['title']
        url = news.get('url', '')
        if url:
            blocks.append({
                "block_type": 2,
                "text": {
                    "elements": [
                        {"text_run": {"content": f"{i}. "}},
                        {"text_run": {"content": title, "style": {"bold": True, "link": {"url": url}}}}
                    ]
                }
            })
        else:
            blocks.append(build_text_block(f"{i}. {title}", bold=True))
        if news.get('summary'):
            blocks.append(build_text_block(news['summary']))
        blocks.append(build_text_block(""))
    
    return blocks

def send_to_feishu_doc_api(dry_run=False):
    """主流程：使用飞书 API 创建文档和块"""
    title = f"📰 每日早报 | {get_chinese_date()}"
    
    if dry_run:
        print("⚠️  dry-run 模式暂不支持 API 块构建")
        return False
    
    print("🔄 开始生成每日早报 (API Callout 模式)...")
    
    # 1. 获取 token
    token = get_feishu_tenant_token()
    if not token:
        print("❌ 无法获取 token")
        return False
    
    # 2. 创建空文档
    print(f"🔧 创建文档: {title}")
    doc_token = create_empty_feishu_doc(title, owner_open_id=FEISHU_USER_ID)
    if not doc_token:
        print("❌ 创建文档失败")
        return False
    print(f"✅ 文档创建成功，token: {doc_token}")
    print(f"🔗 链接: https://feishu.cn/docx/{doc_token}")
    
    # 3. 构建所有块
    print("🔧 构建文档块...")
    blocks = build_full_document_blocks()
    print(f"📦 共构建 {len(blocks)} 个块")
    
    # 4. 顺序创建块
    print("🔧 开始创建块...")
    created_ids = create_blocks_sequential(token, doc_token, blocks)
    
    if len(created_ids) == len(blocks):
        print("✅ 所有块创建完成！")
        return True
    else:
        print(f"⚠️  部分块创建失败: {len(created_ids)}/{len(blocks)}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="每日早报生成器（API模式）")
    parser.add_argument("--dry-run", action="store_true", help="预览模式（暂不支持）")
    args = parser.parse_args()
    
    success = send_to_feishu_doc_api(dry_run=args.dry_run)
    sys.exit(0 if success else 1)
