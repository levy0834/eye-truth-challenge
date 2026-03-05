#!/usr/bin/env python3
"""
evomap 监控脚本：检查服务状态，异常则重启
"""
import os
import sys
import subprocess
import time
from datetime import datetime

PROJECT_DIR = "/Users/levy/Projects/evomap-producer/evomap-producer"
LOG_FILE = os.path.join(PROJECT_DIR, "monitor.log")

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {msg}\n")

def check_port():
    """检查 5001 端口是否可访问"""
    try:
        import socket
        with socket.create_connection(("127.0.0.1", 5001), timeout=2):
            return True
    except:
        return False

def check_process():
    """检查 evomap 进程是否存在"""
    try:
        output = subprocess.check_output(["pgrep", "-f", "python3 run.py"], text=True)
        pids = output.strip().split("\n")
        for pid in pids:
            # 进一步检查进程是否包含项目路径
            try:
                with open(f"/proc/{pid}/cmdline", "r") as f:
                    cmdline = f.read()
                    if PROJECT_DIR in cmdline:
                        return True
            except:
                continue
    except:
        pass
    return False

def start_service():
    """启动 evomap 服务"""
    log("正在启动 evomap 服务...")
    os.chdir(PROJECT_DIR)
    # 杀死旧进程
    subprocess.run(["pkill", "-f", "python3 run.py"], stderr=subprocess.DEVNULL)
    time.sleep(1)
    # 启动新进程
    subprocess.Popen(
        ["nohup", "python3", "run.py"],
        stdout=open("/tmp/evomap.out", "a"),
        stderr=subprocess.STDOUT
    )
    time.sleep(3)
    if check_port() or check_process():
        log("✅ 服务启动成功")
        return True
    else:
        log("❌ 服务启动失败")
        return False

def main():
    log("开始检查 evomap 服务状态...")
    if check_port() or check_process():
        log("✅ 服务正在运行")
        return 0
    else:
        log("⚠️ 服务未运行，尝试重启...")
        if start_service():
            log("重启完成")
            return 0
        else:
            log("重启失败，需要人工介入")
            return 1

if __name__ == "__main__":
    sys.exit(main())
