#!/usr/bin/env python3
"""添加 OpenClaw 每日复盘任务到 crontab（22:00）"""
import subprocess
import sys

def add_cron_job():
    # 获取当前 crontab
    try:
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        current_cron = result.stdout if result.returncode == 0 else ""
    except Exception as e:
        print(f"读取 crontab 失败: {e}")
        current_cron = ""
    
    # 要添加的任务
    new_job = "0 22 * * * /Users/levy/.openclaw/workspace/scripts/run_daily_review.sh >> /Users/levy/.openclaw/workspace/logs/daily_review.log 2>&1"
    
    # 检查是否已存在
    if new_job in current_cron:
        print("✅ 任务已存在，无需添加")
        return
    
    # 追加新任务
    updated_cron = current_cron.strip() + "\n" + new_job + "\n"
    
    # 写入临时文件
    with open('/tmp/new_crontab', 'w') as f:
        f.write(updated_cron)
    
    # 安装新 crontab
    try:
        subprocess.run(['crontab', '/tmp/new_crontab'], check=True)
        print("✅ 已添加每日复盘任务（22:00）")
        subprocess.run(['crontab', '-l'])
    except subprocess.CalledProcessError as e:
        print(f"❌ 安装 crontab 失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    add_cron_job()
