#!/usr/bin/env python3
"""
对外开放服务与RCE风险扫描
检测：端口监听、服务暴露、危险配置、异常进程
"""
import subprocess
import json
import re
from datetime import datetime

RECIPIENT = "user:ou_a413ba619c59873009e5a4d5d7b8bb5e"

def run_cmd(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return result.stdout.strip()
    except:
        return ""

def check_openclaw_gateway():
    """检查OpenClaw Gateway配置"""
    alerts = []
    
    # 获取gateway配置
    port = run_cmd("openclaw config get gateway.port 2>/dev/null || echo 'unknown'")
    bind = run_cmd("openclaw config get gateway.bind 2>/dev/null || echo 'unknown'")
    auth = run_cmd("openclaw config get gateway.auth 2>/dev/null || echo 'unknown'")
    
    alerts.append(f"🔧 OpenClaw Gateway: port={port}, bind={bind}, auth={auth}")
    
    # 检查网关进程是否运行在公网接口
    if bind == "loopback" or bind == "127.0.0.1" or bind == "localhost":
        alerts.append("✅ Gateway仅本地监听，无外网暴露风险")
    else:
        alerts.append(f"⚠️ 警告：Gateway绑定到 {bind}，可能对外暴露！")
    
    # 检查认证
    if auth == "none":
        alerts.append("⚠️ 警告：Gateway认证模式为none，无需认证即可连接！")
    elif auth == "token" or auth == "password":
        alerts.append(f"✅ Gateway认证：{auth}模式")
    else:
        alerts.append(f"ℹ️ Gateway认证：{auth}")
    
    return alerts

def check_listening_ports():
    """检查监听端口（尝试多种方式）"""
    alerts = []
    
    # 方式1：使用lsof如果可用
    lsof = run_cmd("which lsof")
    if lsof:
        output = run_cmd("lsof -i -P -n 2>/dev/null | grep LISTEN | grep -v '127.0.0.1\|::1\|localhost' | head -10")
        if output:
            alerts.append("🔌 发现外网监听端口：")
            for line in output.split('\n')[:5]:
                alerts.append(f"  {line[:120]}")
        else:
            alerts.append("🔌 无外网监听端口（仅本地监听）")
    else:
        alerts.append("⚠️ lsof不可用，无法检查端口监听情况")
    
    return alerts

def check_open_ports_alternative():
    """替代方法：检查常见服务端口"""
    alerts = []
    
    # 检查常见开发服务器端口（可能暴露）
    common_ports = {
        "3000": "Node.js/React",
        "5000": "Python Flask",
        "8000": "Python Django",
        "8080": "Java/Proxy",
        "8888": "Jupyter/JupyterLab",
        "9000": "Web服务器",
        "18789": "OpenClaw Gateway"
    }
    
    listening = run_cmd("netstat -an 2>/dev/null | grep LISTEN | awk '{print $4}' | cut -d: -f2 | sort -u")
    exposed_ports = []
    
    if listening:
        for line in listening.split('\n'):
            port = line.strip()
            if port in common_ports:
                exposed_ports.append(f"{port} ({common_ports[port]})")
    
    if exposed_ports:
        alerts.append(f"📡 检测到开放端口: {', '.join(exposed_ports[:5])}")
    else:
        alerts.append("✅ 未发现常见开发端口对外暴露")
    
    return alerts

def check_dangerous_scripts():
    """检查脚本中是否有RCE风险"""
    alerts = []
    
    workspace = "/Users/levy/.openclaw/workspace"
    scripts = [
        "scripts/daily_briefing.py",
        "scripts/security_monitor.py",
        "scripts/check_evomap.py"
    ]
    
    danger_patterns = [
        r"eval\(",
        r"exec\(",
        r"os\.system\(",
        r"subprocess\.call.*shell=True",
        r"__import__\(",
        r"pickle\.loads?",
        r"compile\(",
        r"input\(",
        r"raw_input\("
    ]
    
    for script in scripts:
        script_path = f"{workspace}/{script}"
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()
                for pattern in danger_patterns:
                    if re.search(pattern, content):
                        alerts.append(f"⚠️ {script} 包含危险函数: {pattern}")
                        break
        except:
            pass
    
    if not any(a.startswith("⚠️") for a in alerts):
        alerts.append("✅ 检查脚本未发现明显RCE风险函数")
    
    return alerts

def check_rce_surface():
    """检查RCE攻击面"""
    alerts = []
    
    # 检查运行的Python/Node服务
    processes = run_cmd("ps aux | grep -E 'python3|node' | grep -v grep | wc -l")
    try:
        count = int(processes) if processes.isdigit() else 0
        if count > 5:
            alerts.append(f"⚠️ 运行中Python/Node进程较多({count}个)，建议检查是否有异常")
        else:
            alerts.append(f"✅ Python/Node进程数: {count}，在正常范围")
    except:
        alerts.append("ℹ️ 无法统计进程数")
    
    # 检查是否有调试模式运行
    debug = run_cmd("ps aux | grep -E '--debug|-debug|DEBUG=1' | grep -v grep | head -3")
    if debug:
        alerts.append("⚠️ 发现调试模式运行的进程，可能泄露信息")
    else:
        alerts.append("✅ 未发现调试模式进程")
    
    return alerts

def generate_report(sections):
    """生成安全报告"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    report_lines = [
        "🛡️ 对外开放服务与RCE风险扫描",
        f"检查时间: {now}",
        "=" * 50,
        ""
    ]
    
    for section in sections:
        report_lines.extend(section)
        report_lines.append("")
    
    report_lines.extend([
        "=" * 50,
        "📋 建议：",
        "• 确保Gateway绑定loopback或使用防火墙限制",
        "• 启用认证（token/password）",
        "• 定期检查日志异常",
        "• 避免在公网暴露调试接口"
    ])
    
    return "\n".join(report_lines)

def send_to_feishu(text):
    try:
        cmd = ["openclaw", "message", "send", "--target", RECIPIENT, "--message", text]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.returncode == 0
    except:
        return False

def main():
    print("🔍 开始扫描对外开放服务与RCE风险...")
    
    all_sections = []
    
    # 1. Gateway检查
    all_sections.append(["🔧 OpenClaw Gateway配置"])
    all_sections.append(check_openclaw_gateway())
    
    # 2. 端口监听检查
    all_sections.append(["🔌 监听端口状态"])
    all_sections.append(check_listening_ports())
    all_sections.append(check_open_ports_alternative())
    
    # 3. RCE风险检查
    all_sections.append(["⚠️ RCE风险扫描"])
    all_sections.append(check_dangerous_scripts())
    all_sections.append(check_rce_surface())
    
    # 生成报告
    report = generate_report(all_sections)
    
    print("\n" + "=" * 60)
    print("安全扫描报告：")
    print("=" * 60)
    print(report)
    print("=" * 60)
    
    if send_to_feishu(report):
        print("\n✅ 报告已发送到飞书")
        return True
    else:
        print("\n❌ 发送失败")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
