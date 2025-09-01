from django.core.management.base import BaseCommand
import pymysql
from django.conf import settings
from stockmarket.models import (
    StockSpot, StockFundFlow, StockBonus, StockTop, StockBlocktrade,
    StockFundFlowIndustry, StockFundFlowConcept, EtfSpot,
    StockChipRaceOpen, StockChipRaceEnd, StockLimitupReason
)

class Command(BaseCommand):
    help = '从现有MySQL数据库导入数据'

    def handle(self, *args, **options):
        # 连接源数据库
        source_db = pymysql.connect(
            host='localhost',
            user='root',
            password='123456',
            database='stock_old',  # 修改为你的源数据库名
            charset='utf8mb4'
        )

        try:
            with source_db.cursor() as cursor:
                # 导入每日股票数据
                self.stdout.write('正在导入每日股票数据...')
                cursor.execute('SELECT * FROM cn_stock_spot')
                rows = cursor.fetchall()
                for row in rows:
                    StockSpot.objects.create(
                        date=row[0],
                        code=row[1],
                        name=row[2],
                        # ... 根据实际列映射添加其他字段
                    )

                # 导入资金流向数据
                self.stdout.write('正在导入资金流向数据...')
                cursor.execute('SELECT * FROM cn_stock_fund_flow')
                rows = cursor.fetchall()
                for row in rows:
                    StockFundFlow.objects.create(
                        date=row[0],
                        code=row[1],
                        name=row[2],
                        # ... 根据实际列映射添加其他字段
                    )

                # 导入分红数据
                self.stdout.write('正在导入分红数据...')
                cursor.execute('SELECT * FROM cn_stock_bonus')
                rows = cursor.fetchall()
                for row in rows:
                    StockBonus.objects.create(
                        date=row[0],
                        code=row[1],
                        name=row[2],
                        # ... 根据实际列映射添加其他字段
                    )

                # 可以继续添加其他表的导入...

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'导入出错: {str(e)}'))
        finally:
            source_db.close()

        self.stdout.write(self.style.SUCCESS('数据导入完成')) 