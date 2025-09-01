#!/usr/bin/env python3
"""
数据库连接测试和数据初始化工具
"""

import os
import sys
import pymysql
import subprocess

def test_mysql_connection():
    """测试MySQL数据库连接"""
    print("🔍 测试MySQL数据库连接...")
    
    try:
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='9',
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            # 检查stockdb数据库是否存在
            cursor.execute("SHOW DATABASES LIKE 'stockdb'")
            db_exists = cursor.fetchone()
            
            if not db_exists:
                print("  📝 创建stockdb数据库...")
                cursor.execute("CREATE DATABASE stockdb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                print("  ✅ stockdb数据库创建成功")
            else:
                print("  ✅ stockdb数据库已存在")
            
            # 切换到stockdb数据库
            cursor.execute("USE stockdb")
            
            # 检查表是否存在
            cursor.execute("SHOW TABLES LIKE 'stockmarket_stockhistorydata'")
            table_exists = cursor.fetchone()
            
            if table_exists:
                cursor.execute("SELECT COUNT(*) FROM stockmarket_stockhistorydata")
                count = cursor.fetchone()[0]
                print(f"  📊 数据表存在，记录数: {count}")
            else:
                print("  ⚠️ 数据表不存在，需要运行迁移")
        
        connection.close()
        return True
        
    except Exception as e:
        print(f"  ❌ MySQL连接失败: {e}")
        return False

def run_django_migrations():
    """运行Django数据库迁移"""
    print("🔧 运行Django数据库迁移...")
    
    backend_path = "/home/liu/桌面/stock-20250730_update./backend"
    
    try:
        # 生成迁移文件
        print("  📝 生成迁移文件...")
        result = subprocess.run(
            ["python", "manage.py", "makemigrations"],
            cwd=backend_path,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("  ✅ 迁移文件生成成功")
        else:
            print(f"  ⚠️ 迁移文件生成: {result.stderr}")
        
        # 应用迁移
        print("  📝 应用数据库迁移...")
        result = subprocess.run(
            ["python", "manage.py", "migrate"],
            cwd=backend_path,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("  ✅ 数据库迁移完成")
            return True
        else:
            print(f"  ❌ 数据库迁移失败: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"  ❌ 迁移过程出错: {e}")
        return False

def check_data_initialization():
    """检查是否需要数据初始化"""
    print("🔍 检查数据初始化状态...")
    
    try:
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='9',
            database='stockdb',
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM stockmarket_stockhistorydata")
            count = cursor.fetchone()[0]
            
            if count == 0:
                print("  ⚠️ 数据表为空，需要初始化数据")
                return False
            else:
                print(f"  ✅ 数据表有 {count} 条记录")
                return True
        
        connection.close()
        
    except Exception as e:
        print(f"  ❌ 数据检查失败: {e}")
        return False

def run_data_initialization():
    """运行数据初始化脚本"""
    print("🔧 运行数据初始化...")
    
    init_script_path = "/home/liu/桌面/stock-20250730_update./init_database.py"
    
    if os.path.exists(init_script_path):
        try:
            result = subprocess.run(
                ["python", init_script_path],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("  ✅ 数据初始化完成")
                return True
            else:
                print(f"  ❌ 数据初始化失败: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"  ❌ 初始化过程出错: {e}")
            return False
    else:
        print("  ⚠️ 初始化脚本不存在")
        return False

def main():
    """主流程"""
    print("🚀 数据库完整性检查和修复")
    print("=" * 50)
    
    # 1. 测试MySQL连接
    if not test_mysql_connection():
        print("❌ MySQL连接失败，请检查数据库配置")
        return
    
    # 2. 运行Django迁移
    if not run_django_migrations():
        print("❌ 数据库迁移失败")
        return
    
    # 3. 检查数据初始化
    if not check_data_initialization():
        # 4. 运行数据初始化
        if not run_data_initialization():
            print("⚠️ 数据初始化失败，但可以继续测试API")
    
    print("\n✅ 数据库配置完成！")
    print("🔄 请重启Django服务器以应用更改")

if __name__ == "__main__":
    main()
