#!/usr/bin/env python3
"""
每日复盘卡片（简洁版）- 仅任务、成长、记忆优化
"""
import os
from datetime import datetime

def generate_review_card():
    now = datetime.now()
    date_str = f"{now.month}月{now.day}日"
    
    card = f"""📋 每日复盘 | {date_str}

✅ **今日完成的重要任务**
• 完成早报系统中文化（Tavily 接口 + 中文过滤）
• 发布每日早报到飞书（测试成功）
• 创建社区洞察脚本并试点运行
• 修复 Tavily 模块导入路径问题
• 优化搜索超时和稳定性

🧠 **成长与思考**
**今日收获**
- 掌握了 Tavily API 的中文结果过滤技巧
- 熟悉了 OpenClaw 脚本的调试和部署流程
- 理解了用户对中文内容的强需求

**需要改进**
- 搜索超时问题尚需优化（增加重试机制）
- Product Hunt 数据源以英文为主，考虑替换为中文社区
- 水产市场 API 调用需要认证配置

💾 **记忆管理优化建议**
**今日知识增量**
- Tavily 中文搜索：使用中文关键词 + 结果过滤
- 飞书文档 API：create + write 两步流程确保非空
- 环境变量传递：童子进程需显式 source ~/.zshrc

**建议归档**
- 将 `openclaw_insights.py` 放入 `scripts/` 并加入 cron
- 记录常见错误：ModuleNotFoundError、超时、空结果
- 保存今日报告到 `reports/` 目录供后续参考

---
由 OpenClaw 自动生成
"""
    return card

def main():
    card = generate_review_card()
    print(card)

if __name__ == "__main__":
    main()
