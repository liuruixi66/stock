#!/bin/bash

# 股票系统前后端启动脚本
# 使用方法: ./start_system.sh [frontend|backend|all]

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 项目路径：根据脚本位置自动定位，适用于 macOS/Linux
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
PYTHON_BIN="${PYTHON_BIN:-python}"
BACKEND_URL="http://127.0.0.1:8002/admin/login/"

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 启动后端
start_backend() {
    log_info "启动后端服务..."
    
    cd "$BACKEND_DIR"
    
    # 数据库迁移
    log_info "执行数据库迁移..."
    cd "$BACKEND_DIR"
    "$PYTHON_BIN" manage.py migrate
    
    # 启动Django服务器
    log_info "启动Django服务器 (端口 8002)..."
    "$PYTHON_BIN" manage.py runserver 0.0.0.0:8002 &
    BACKEND_PID=$!
    
    log_info "后端服务已启动 (PID: $BACKEND_PID)"
    echo $BACKEND_PID > "$BACKEND_DIR/backend.pid"
}

wait_for_backend() {
    log_info "等待后端服务就绪..."
    for _ in {1..30}; do
        if curl -fsS "$BACKEND_URL" >/dev/null 2>&1; then
            log_info "后端服务已就绪"
            return 0
        fi
        sleep 1
    done
    log_error "后端服务未能在30秒内就绪"
    return 1
}

# 启动前端
start_frontend() {
    log_info "启动前端服务..."
    
    cd "$FRONTEND_DIR"
    
    # 安装依赖
    if [ ! -d "node_modules" ]; then
        log_info "安装前端依赖..."
        npm install
    fi
    
    # 启动Vite开发服务器
    log_info "启动前端开发服务器 (端口 3000)..."
    npm run dev -- --host 0.0.0.0 &
    FRONTEND_PID=$!
    
    log_info "前端服务已启动 (PID: $FRONTEND_PID)"
    echo $FRONTEND_PID > "$FRONTEND_DIR/frontend.pid"
}

# 停止服务
stop_services() {
    log_info "停止服务..."
    
    # 停止后端
    if [ -f "$BACKEND_DIR/backend.pid" ]; then
        BACKEND_PID=$(cat "$BACKEND_DIR/backend.pid")
        if ps -p $BACKEND_PID > /dev/null; then
            kill $BACKEND_PID
            log_info "后端服务已停止"
        fi
        rm -f "$BACKEND_DIR/backend.pid"
    fi
    
    # 停止前端
    if [ -f "$FRONTEND_DIR/frontend.pid" ]; then
        FRONTEND_PID=$(cat "$FRONTEND_DIR/frontend.pid")
        if ps -p $FRONTEND_PID > /dev/null; then
            kill $FRONTEND_PID
            log_info "前端服务已停止"
        fi
        rm -f "$FRONTEND_DIR/frontend.pid"
    fi
    
    # 清理其他可能的进程
    pkill -f "manage.py runserver" 2>/dev/null || true
    pkill -f "vite" 2>/dev/null || true
}

# 显示状态
show_status() {
    log_info "服务状态:"
    
    # 检查后端
    if [ -f "$BACKEND_DIR/backend.pid" ]; then
        BACKEND_PID=$(cat "$BACKEND_DIR/backend.pid")
        if ps -p $BACKEND_PID > /dev/null; then
            echo -e "  后端: ${GREEN}运行中${NC} (PID: $BACKEND_PID, 端口: 8002)"
        else
            echo -e "  后端: ${RED}已停止${NC}"
            rm -f "$BACKEND_DIR/backend.pid"
        fi
    else
        echo -e "  后端: ${RED}未启动${NC}"
    fi
    
    # 检查前端
    if [ -f "$FRONTEND_DIR/frontend.pid" ]; then
        FRONTEND_PID=$(cat "$FRONTEND_DIR/frontend.pid")
        if ps -p $FRONTEND_PID > /dev/null; then
            echo -e "  前端: ${GREEN}运行中${NC} (PID: $FRONTEND_PID, 端口: 3000)"
        else
            echo -e "  前端: ${RED}已停止${NC}"
            rm -f "$FRONTEND_DIR/frontend.pid"
        fi
    else
        echo -e "  前端: ${RED}未启动${NC}"
    fi
    
    echo ""
    echo "访问地址:"
    echo "  前端: http://localhost:3000"
    echo "  后端API: http://localhost:8002/api/"
    echo "  后端管理: http://localhost:8002/admin/"
}

# 主函数
main() {
    case "${1:-all}" in
        "backend")
            start_backend
            show_status
            ;;
        "frontend")
            start_frontend
            show_status
            ;;
        "all")
            start_backend
            wait_for_backend
            start_frontend
            show_status
            ;;
        "stop")
            stop_services
            ;;
        "status")
            show_status
            ;;
        "restart")
            stop_services
            sleep 2
            main "all"
            ;;
        *)
            echo "用法: $0 [frontend|backend|all|stop|status|restart]"
            echo ""
            echo "命令说明:"
            echo "  frontend  - 仅启动前端服务"
            echo "  backend   - 仅启动后端服务"
            echo "  all       - 启动前后端服务 (默认)"
            echo "  stop      - 停止所有服务"
            echo "  status    - 显示服务状态"
            echo "  restart   - 重启所有服务"
            exit 1
            ;;
    esac
}

# 捕获退出信号
trap 'log_warn "接收到退出信号，正在停止服务..."; stop_services; exit 0' SIGINT SIGTERM

# 执行主函数
main "$@"

# 如果是启动服务，保持脚本运行
if [[ "${1:-all}" =~ ^(frontend|backend|all)$ ]]; then
    log_info "服务已启动，按 Ctrl+C 停止服务"
    wait
fi
