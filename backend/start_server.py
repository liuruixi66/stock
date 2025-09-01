#!/usr/bin/env python3
"""
Django服务器启动脚本
配置Django环境并启动开发服务器
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

def setup_django_environment():
    """设置Django环境"""
    # 设置Django设置模块
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
    
    # 添加项目路径
    project_root = os.path.dirname(os.path.abspath(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    # 初始化Django
    django.setup()
    
    print("✅ Django环境配置成功")
    print(f"📁 项目路径: {project_root}")
    print(f"⚙️  设置模块: {os.environ.get('DJANGO_SETTINGS_MODULE')}")

def main():
    """主函数"""
    print("🚀 启动Django股票量化交易系统")
    print("=" * 50)
    
    try:
        # 设置Django环境
        setup_django_environment()
        
        # 检查数据库连接
        from django.db import connection
        try:
            connection.ensure_connection()
            print("✅ 数据库连接正常")
        except Exception as e:
            print(f"⚠️  数据库连接警告: {e}")
            print("💡 系统将使用内存数据库继续运行")
        
        # 显示可用的API端点
        print(f"\n📋 可用的API端点:")
        print(f"   🔬 回测API: http://localhost:8002/api/backtest/run/")
        print(f"   ⚙️  回测配置: http://localhost:8002/api/backtest/config/")
        print(f"   📊 股票数据: http://localhost:8002/api/stock-spot/")
        print(f"   📈 技术指标: http://localhost:8002/api/market/ma/")
        print(f"   🏛️  管理后台: http://localhost:8002/admin/")
        
        # 启动开发服务器
        print(f"\n🌐 启动Django开发服务器...")
        print(f"📍 服务器地址: http://localhost:8002")
        print(f"🛑 按 Ctrl+C 停止服务器\n")
        
        # 执行Django命令
        execute_from_command_line(['manage.py', 'runserver', '0.0.0.0:8002'])
        
    except KeyboardInterrupt:
        print(f"\n🛑 服务器已停止")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
