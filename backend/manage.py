#!/usr/bin/env python
"""Django 管理命令入口，例如运行服务、数据库迁移和自定义交易命令。"""
import os
import sys


def main():
    """设置项目导入路径并将命令行参数交给 Django 管理命令执行。"""
    # 兼容旧版 instock 模块目录：将其加入导入路径，供依赖该目录的模块解析。
    stock_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../stock'))
    sys.path.insert(0, stock_path)
    
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
