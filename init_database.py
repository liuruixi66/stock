#!/usr/bin/env python
"""
数据库初始化脚本
"""

import os
import sys
import django
from pathlib import Path

# 添加Django项目路径
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR / 'backend' / 'myproject'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.core.management import execute_from_command_line
from django.db import connection
import pymysql

def create_database():
    """创建数据库"""
    try:
        # 连接MySQL服务器（不指定数据库）
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='9',
            charset='utf8mb4'
        )
        cursor = conn.cursor()
        
        # 创建数据库
        cursor.execute("CREATE DATABASE IF NOT EXISTS stockdb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print("✓ 数据库 'stockdb' 创建成功")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"✗ 创建数据库失败: {e}")
        return False
    
    return True

def run_migrations():
    """执行数据库迁移"""
    try:
        print("执行数据库迁移...")
        
        # 切换到Django项目目录
        os.chdir(BASE_DIR / 'backend' / 'myproject')
        
        # 创建迁移文件
        execute_from_command_line(['manage.py', 'makemigrations'])
        print("✓ 迁移文件创建成功")
        
        # 执行迁移
        execute_from_command_line(['manage.py', 'migrate'])
        print("✓ 数据库迁移完成")
        
    except Exception as e:
        print(f"✗ 数据库迁移失败: {e}")
        return False
    
    return True

def create_superuser():
    """创建超级用户"""
    try:
        from django.contrib.auth.models import User
        
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123'
            )
            print("✓ 超级用户创建成功")
            print("  用户名: admin")
            print("  密码: admin123")
        else:
            print("✓ 超级用户已存在")
            
    except Exception as e:
        print(f"✗ 创建超级用户失败: {e}")
        return False
    
    return True

def load_sample_data():
    """加载示例数据"""
    try:
        from stockmarket.models import Stock, StockDailyData
        
        # 创建示例股票
        stocks = [
            {'code': '000001', 'name': '平安银行'},
            {'code': '000002', 'name': '万科A'},
            {'code': '000063', 'name': '中兴通讯'},
            {'code': '000568', 'name': '泸州老窖'},
        ]
        
        for stock_data in stocks:
            stock, created = Stock.objects.get_or_create(
                code=stock_data['code'],
                defaults={'name': stock_data['name']}
            )
            if created:
                print(f"✓ 创建股票: {stock.code} - {stock.name}")
        
        print(f"✓ 示例数据加载完成，共 {len(stocks)} 只股票")
        
    except Exception as e:
        print(f"✗ 加载示例数据失败: {e}")
        return False
    
    return True

def main():
    """主函数"""
    print("=" * 50)
    print("股票系统数据库初始化")
    print("=" * 50)
    
    # 1. 创建数据库
    print("\n1. 创建数据库...")
    if not create_database():
        return
    
    # 2. 执行迁移
    print("\n2. 执行数据库迁移...")
    if not run_migrations():
        return
    
    # 3. 创建超级用户
    print("\n3. 创建超级用户...")
    if not create_superuser():
        return
    
    # 4. 加载示例数据
    print("\n4. 加载示例数据...")
    if not load_sample_data():
        return
    
    print("\n" + "=" * 50)
    print("数据库初始化完成！")
    print("=" * 50)
    print("\n访问信息:")
    print("  管理后台: http://localhost:8002/admin/")
    print("  用户名: admin")
    print("  密码: admin123")
    print("  API接口: http://localhost:8002/api/")

if __name__ == '__main__':
    main()
