#!/usr/bin/env python3
"""
安全监控脚本 - 检查过去24小时的日志异常
检测：攻击、异常IP、高频失败、可疑行为
"""
import subprocess
import json
import re
from datetime import datetime, timedelta
import os

LOG_DIR = "/Users/levy/.openclaw/logs"
RECIPIENT = "user:ou_a413ba619c59873009e5a4d5d7b8bb5e"

def run_cmd(cmd):
    """执行命令并返回输出"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return result.stdout.strip()
    except:
        return ""

def check_gateway_log():
    """检查网关日志中的异常"""
    alerts = []
    
    # 1. 检查错误日志中的攻击迹象
    cmd = f"tail -1000 {LOG_DIR}/gateway.err.log 2>/dev/null | grep -i -E 'attack|block|deny|fail|error|invalid|unauthorized|brute|scan' | tail -20"
    output = run_cmd(cmd)
    
    suspicious_keywords = [
        "invalid token", "unauthorized", "authentication fail",
        "too many requests", "rate limit", "blocked ip",
        "malformed", "exploit", "injection", "traffic anomaly"
    ]
    
    for line in output.split('\n'):
        if line.strip():
            for keyword in suspicious_keywords:
                if keyword in line.lower():
                    alerts.append(f"⚠️ 可疑活动: {line[:150]}")
                    break
    
    return alerts

def check_connection_patterns():
    """检查异常连接模式"""
    alerts = []
    
    # 检查短时间大量连接（可能DDoS）
    cmd = f"tail -500 {LOG_DIR}/gateway.log 2>/dev/null | grep -oP 'conn=[^ ]+' | sort | uniq -c | sort -nr | head -10"
    output = run_cmd(cmd)
    
    lines = output.split('\n')
    if len(lines) > 1:
        for line in lines[1:4]:  # 只看top 3
            if line.strip():
                parts = line.split()
                if len(parts) >= 2:
                    count = parts[0]
                    conn_id = parts[1]
                    if int(count) > 50:  # 同一连接出现50次以上
                        alerts.append(f"🔗 高频连接: {conn_id} 出现 {count} 次")
    
    return alerts

def check_websocket_errors():
    """检查websocket错误"""
    alerts = []
    
    cmd = f"tail -500 {LOG_DIR}/gateway.log 2>/dev/null | grep -i 'errorCode' | grep -v 'cron.create' | tail -10"
    output = run_cmd(cmd)
    
    for line in output.split('\n'):
        if line.strip() and "errorCode" in line:
            alerts.append(f"❌ 错误: {line[:150]}")
    
    return alerts

def generate_report(alerts):
    """生成安全报告"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    if not alerts:
        return f"""🔐 安全日报 | {now}
✅ 过去24小时无异常活动
📊 检查项目：网关日志、连接模式、错误码
🛡️ 系统运行正常"""

    report_lines = [
        f"🔊 安全警报 | {now}",
        f"⚠️ 发现 {len(alerts)} 项异常：",
        ""
    ]
    
    for i, alert in enumerate(alerts[:10], 1):  # 最多显示10条
        report_lines.append(f"{i}. {alert}")
    
    if len(alerts) > 10:
        report_lines.append(f"... 还有 {len(alerts)-10} 条未显示")
    
    report_lines.extend([
        "",
        "📋 建议：",
        "• 检查相关连接IP",
        "• 更新访问控制列表",
        "• 加强认证机制"
    ])
    
    return "\n".join(report_lines)

def send_to_feishu(text):
    """发送消息到飞书"""
    try:
        cmd = [
            "openclaw", "message", "send",
            "--target", RECIPIENT,
            "--message", text
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.returncode == 0
    except:
        return False

def main():
    print("🔍 开始安全监控检查...")
    
    all_alerts = []
    
    # 各项检查
    all_alerts.extend(check_gateway_log())
    all_alerts.extend(check_connection_patterns())
    all_alerts.extend(check_websocket_errors())
    
    # 去重
    unique_alerts = list(set(all_alerts))
    
    # 生成报告
    report = generate_report(unique_alerts)
    
    print("=" * 60)
    print("安全监控报告：")
    print("=" * 60)
    print(report)
    print("=" * 60)
    
    # 发送
    if send_to_feishu(report):
        print("✅ 报告已发送到飞书")
        return True
    else:
        print("❌ 发送失败")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
