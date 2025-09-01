#!/bin/bash

# 股票系统前后端启动脚本
# 使用方法: ./start_system.sh [frontend|backend|all]

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 项目路径
BACKEND_DIR="/home/liu/桌面/stock-main/backend"
FRONTEND_DIR="/home/liu/桌面/stock-main/frontend"

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

# 检查依赖
check_dependencies() {
    log_info "检查依赖..."
    
    # 检查Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 未安装"
        exit 1
    fi
    
    # 检查Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js 未安装"
        exit 1
    fi
    
    # 检查npm
    if ! command -v npm &> /dev/null; then
        log_error "npm 未安装"
        exit 1
    fi
    
    log_info "依赖检查完成"
}

# 启动后端
start_backend() {
    log_info "启动后端服务..."
    
    cd "$BACKEND_DIR"
    
    # 检查虚拟环境
    if [ ! -d "venv" ]; then
        log_info "创建Python虚拟环境..."
        python3 -m venv venv
    fi
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 安装依赖
    log_info "安装Python依赖..."
    pip install -r requirements.txt 2>/dev/null || {
        log_warn "requirements.txt 不存在，安装基础依赖..."
        pip install django django-cors-headers pymysql pandas numpy
    }
    
    # 数据库迁移
    log_info "执行数据库迁移..."
    cd myproject
    python manage.py makemigrations
    python manage.py migrate
    
    # 启动Django服务器
    log_info "启动Django服务器 (端口 8002)..."
    python manage.py runserver 0.0.0.0:8002 &
    BACKEND_PID=$!
    
    log_info "后端服务已启动 (PID: $BACKEND_PID)"
    echo $BACKEND_PID > "$BACKEND_DIR/backend.pid"
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
    npm run dev &
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
            check_dependencies
            start_backend
            show_status
            ;;
        "frontend")
            check_dependencies
            start_frontend
            show_status
            ;;
        "all")
            check_dependencies
            start_backend
            sleep 3  # 等待后端启动
            start_frontend
            sleep 2  # 等待前端启动
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
