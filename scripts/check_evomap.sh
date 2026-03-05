#!/bin/bash

# evomap 项目监控脚本
# 每小时检查一次，如果服务没启动就重启

PROJECT_DIR="/Users/levy/Projects/evomap-producer/evomap-producer"
LOG_FILE="/Users/levy/Projects/evomap-producer/evomap-producer/monitor.log"
PID_FILE="/tmp/evomap.pid"

# 函数：写日志
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# 检查进程是否在运行（基于端口 5001）
check_port() {
    /usr/sbin/lsof -i :5001 | grep -q LISTEN
    return $?
}

# 检查进程是否在运行（基于项目目录 + python）
check_process() {
    pgrep -f "python3 run.py" | grep -q "$PROJECT_DIR"
    return $?
}

# 启动服务
start_service() {
    log "正在启动 evomap 服务..."
    cd "$PROJECT_DIR" || exit 1
    # 使用 nohup 后台运行，并记录 PID
    nohup python3 run.py > /tmp/evomap.out 2>&1 &
    echo $! > "$PID_FILE"
    sleep 3
    if check_port || check_process; then
        log "✅ 服务启动成功"
        return 0
    else
        log "❌ 服务启动失败"
        return 1
    fi
}

# 主逻辑
main() {
    log "开始检查 evomap 服务状态..."

    if check_port || check_process; then
        log "✅ 服务正在运行（端口 5001 存在）"
        exit 0
    else
        log "⚠️ 服务未运行，尝试重启..."
        # 如果 PID 文件存在， kill 旧进程
        if [ -f "$PID_FILE" ]; then
            old_pid=$(cat "$PID_FILE")
            if kill -0 "$old_pid" 2>/dev/null; then
                log "杀死旧进程 PID $old_pid"
                kill -9 "$old_pid" 2>/dev/null || true
            fi
        fi
        if start_service; then
            log "重启完成"
        else
            log "重启失败，请手动检查"
            # 可以加通知（如发飞书消息）
        fi
    fi
}

main
