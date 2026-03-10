#!/usr/bin/env python3
"""
每日早报脚本 - 新浪新闻 API（严格24小时+智能分类）
"""
import json
import re
from datetime import datetime, timedelta
import argparse
import sys
import requests

WORKSPACE = "/Users/levy/.openclaw/workspace"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# 新浪新闻分类 lid
NEWS_LIDS = {
    'finance': '2509',  # 财经
    'china': '2516',    # 国内新闻
}

def get_chinese_date():
    now = datetime.now()
    weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    return f"{now.year}年{now.month}月{now.day}日 {weekdays[now.weekday()]}"

def fetch_sina_news(lid, max_items=20):
    """从新浪新闻 API 获取最新新闻"""
    try:
        url = f"https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid={lid}&k=&num={max_items}"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            return []
        data = resp.json()
        items = data.get('result', {}).get('data', [])
        now_dt = datetime.now()
        results = []
        
        for item in items:
            title = item.get('title', '').strip()
            link = item.get('url', '').strip()
            intro = item.get('intro', '').strip()
            ctime = item.get('ctime')
            
            if not title or len(title) < 8 or len(title) > 60:
                continue
            if not link:
                continue
            
            # 时间过滤：24小时内
            article_date = None
            if ctime:
                try:
                    article_date = datetime.fromtimestamp(int(ctime))
                except:
                    pass
            if not article_date:
                continue
            if (now_dt - article_date).total_seconds() > 24 * 3600:
                continue
            
            # 摘要处理
            summary = intro if intro else title
            summary = re.sub(r'<[^>]+>', '', summary).strip()
            if len(summary) > 150:
                summary = summary[:150] + "..."
            
            results.append({
                'title': title,
                'url': link,
                'summary': summary,
                'date': article_date.strftime("%Y-%m-%d %H:%M:%S"),
                'source': '新浪新闻'
            })
        
        return results
    except Exception as e:
        print(f"⚠️ 新浪新闻获取失败 (lid={lid}): {e}", file=sys.stderr)
        return []

def categorize_news(items):
    """将国内新闻智能分类到不同板块"""
    hangzhou_news = []
    life_news = []
    china_news = []
    
    hangzhou_keywords = ['杭州', '杭城', '西湖', '滨江', '余杭', '萧山', '临平', '钱塘', '富阳', '临安', '桐庐', '淳安', '建德']
    life_keywords = ['健康', '医保', '医疗', '医院', '教育', '学校', '双减', '消费', '价格', '物价', '菜价', '民生', '社保']
    
    for item in items:
        title_lower = item['title'].lower()
        summary_lower = item['summary'].lower()
        text = title_lower + ' ' + summary_lower
        
        # 检查是否杭州相关
        if any(kw in text for kw in hangzhou_keywords):
            hangzhou_news.append(item)
            continue
        
        # 检查是否生活服务相关
        if any(kw in text for kw in life_keywords):
            life_news.append(item)
            continue
        
        # 否则归为国内要闻
        china_news.append(item)
    
    return hangzhou_news, life_news, china_news

def generate_markdown_report():
    date_str = get_chinese_date()
    
    # 1. 获取财经新闻
    finance_items = fetch_sina_news(NEWS_LIDS['finance'], 30)
    finance_news = finance_items[:4]
    
    # 2. 获取国内新闻，然后分类
    china_items = fetch_sina_news(NEWS_LIDS['china'], 40)
    hangzhou_news, life_news, remaining_china = categorize_news(china_items)
    
    # 取各自所需数量
    hangzhou_news = hangzhou_news[:3]
    life_news = life_news[:3]
    china_news = remaining_china[:3]
    
    # 全局去重（基于URL）
    seen_urls = set()
    sections = [
        ("📈 投资与财经", finance_news),
        ("🏙️ 杭州本地", hangzhou_news),
        ("🧑‍⚕️ 生活服务", life_news),
        ("📰 国内要闻", china_news),
    ]
    
    md_lines = []
    md_lines.append(f"# 📰 每日早报 | {date_str}")
    md_lines.append("")
    
    for section_title, news_list in sections:
        section_items = []
        for item in news_list:
            if item['url'] in seen_urls:
                continue
            seen_urls.add(item['url'])
            section_items.append(item)
        
        if section_items:
            md_lines.append(f"## {section_title}")
            md_lines.append("")
            for i, item in enumerate(section_items, 1):
                title = item['title']
                url = item.get('url', '')
                title = re.sub(r'\[.*?\]|\(.*?\)', '', title).strip()
                if url:
                    md_lines.append(f"{i}. **[{title}]({url})**")
                else:
                    md_lines.append(f"{i}. **{title}**")
                summary = item.get('summary', '')
                if summary and summary != title:
                    md_lines.append(f"   {summary}")
                md_lines.append("")
    
    return "\n".join(md_lines)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="每日早报生成器（新浪新闻API）")
    parser.add_argument("--output", help="将内容写入指定文件")
    args = parser.parse_args()
    
    report = generate_markdown_report()
    
    print(report, file=sys.stderr)
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"✅ 早报内容已写入: {args.output}", file=sys.stderr)
    else:
        print(report)