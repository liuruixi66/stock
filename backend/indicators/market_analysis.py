"""
市场和板块分析模块
包含上证、深证市场识别和板块指数分析功能
"""
import pandas as pd
import numpy as np
import re


class MarketAnalyzer:
    """市场分析器"""
    
    # 上证股票代码规则
    SHANGHAI_PATTERNS = [
        r'^60[0-9]{4}$',    # 主板 600xxx, 601xxx, 603xxx, 605xxx等
        r'^68[0-9]{4}$',    # 科创板 688xxx
        r'^900[0-9]{3}$',   # B股 900xxx
    ]
    
    # 深证股票代码规则  
    SHENZHEN_PATTERNS = [
        r'^000[0-9]{3}$',   # 主板 000xxx
        r'^001[0-9]{3}$',   # 主板 001xxx
        r'^002[0-9]{3}$',   # 中小板 002xxx  
        r'^003[0-9]{3}$',   # 主板 003xxx
        r'^300[0-9]{3}$',   # 创业板 300xxx
        r'^301[0-9]{3}$',   # 创业板 301xxx
        r'^200[0-9]{3}$',   # B股 200xxx
    ]
    
    # 主要指数代码
    INDEX_CODES = {
        'shanghai': {
            '000001': '上证综指',
            '000002': '上证A指',
            '000003': '上证B指',
            '000016': '上证50',
            '000300': '沪深300',
            '000688': '科创50',
            '000905': '中证500',
            '000852': '中证1000'
        },
        'shenzhen': {
            '399001': '深证成指',
            '399002': '深成指R',
            '399003': '成份B指',
            '399004': '深证100R',
            '399005': '中小板指',
            '399006': '创业板指',
            '399007': '深证300',
            '399008': '中小300'
        }
    }
    
    # 行业板块分类
    SECTOR_MAPPING = {
        '房地产': ['000002', '000006', '000014', '000031'],
        '银行': ['000001', '002142', '002807', '600000'],
        '保险': ['601318', '601336', '601601', '601628'],
        '证券': ['000166', '000776', '000783', '002736'],
        '煤炭': ['600123', '600188', '600508', '600714'],
        '钢铁': ['000709', '000717', '000761', '000825'],
        '有色金属': ['000831', '000878', '002460', '600111'],
        '石油石化': ['000554', '000656', '000703', '600028'],
        '电力': ['000027', '000539', '000543', '000600'],
        '公用事业': ['000035', '000040', '000826', '600008'],
        '交通运输': ['000039', '000089', '000099', '600026'],
        '电子': ['000021', '000050', '000725', '002415'],
        '计算机': ['000158', '000555', '000938', '002230'],
        '通信': ['000063', '000055', '000997', '600050'],
        '医药生物': ['000028', '000423', '000513', '000538'],
        '食品饮料': ['000568', '000596', '000799', '000858'],
        '纺织服装': ['000902', '002029', '600177', '600630'],
        '轻工制造': ['000911', '002041', '002271', '600337'],
        '商业贸易': ['000417', '000501', '000759', '600694'],
        '休闲服务': ['000069', '000430', '000721', '600138'],
        '汽车': ['000625', '000800', '000957', '600104'],
        '家用电器': ['000333', '000651', '000921', '600690'],
        '建筑材料': ['000401', '000619', '000786', '600585'],
        '建筑装饰': ['000090', '000065', '000632', '600491'],
        '机械设备': ['000157', '000528', '000680', '600031'],
        '国防军工': ['000519', '000547', '000625', '600184'],
        '化工': ['000059', '000510', '000822', '600028'],
        '农林牧渔': ['000061', '000713', '000735', '600108']
    }

    @staticmethod
    def identify_market(stock_code):
        """
        识别股票所属市场
        
        Args:
            stock_code: 股票代码
        
        Returns:
            str: 'shanghai' 或 'shenzhen' 或 'unknown'
        """
        # 移除可能的后缀（如.SH, .SZ）
        clean_code = stock_code.split('.')[0]
        
        # 检查上证
        for pattern in MarketAnalyzer.SHANGHAI_PATTERNS:
            if re.match(pattern, clean_code):
                return 'shanghai'
        
        # 检查深证
        for pattern in MarketAnalyzer.SHENZHEN_PATTERNS:
            if re.match(pattern, clean_code):
                return 'shenzhen'
        
        return 'unknown'

    @staticmethod
    def filter_stocks_by_market(stock_codes, target_market):
        """
        根据市场筛选股票
        
        Args:
            stock_codes: 股票代码列表
            target_market: 目标市场 'shanghai' 或 'shenzhen'
        
        Returns:
            list: 筛选后的股票代码列表
        """
        filtered_codes = []
        
        for code in stock_codes:
            market = MarketAnalyzer.identify_market(code)
            if market == target_market:
                filtered_codes.append(code)
        
        return filtered_codes

    @staticmethod
    def get_market_index_codes(market):
        """
        获取指定市场的指数代码
        
        Args:
            market: 'shanghai' 或 'shenzhen'
        
        Returns:
            dict: 指数代码和名称的映射
        """
        return MarketAnalyzer.INDEX_CODES.get(market, {})

    @staticmethod
    def get_sector_stocks(sector_name):
        """
        获取指定板块的股票代码
        
        Args:
            sector_name: 板块名称
        
        Returns:
            list: 该板块的股票代码列表
        """
        return MarketAnalyzer.SECTOR_MAPPING.get(sector_name, [])

    @staticmethod
    def identify_sector(stock_code):
        """
        识别股票所属板块
        
        Args:
            stock_code: 股票代码
        
        Returns:
            str: 板块名称，如果未找到返回'其他'
        """
        clean_code = stock_code.split('.')[0]
        
        for sector, codes in MarketAnalyzer.SECTOR_MAPPING.items():
            if clean_code in codes:
                return sector
        
        return '其他'

    @staticmethod
    def analyze_market_distribution(stock_codes):
        """
        分析股票列表的市场分布
        
        Args:
            stock_codes: 股票代码列表
        
        Returns:
            dict: 市场分布统计
        """
        distribution = {
            'shanghai': 0,
            'shenzhen': 0,
            'unknown': 0,
            'total': len(stock_codes)
        }
        
        market_details = {
            'shanghai': [],
            'shenzhen': [],
            'unknown': []
        }
        
        for code in stock_codes:
            market = MarketAnalyzer.identify_market(code)
            distribution[market] += 1
            market_details[market].append(code)
        
        return {
            'distribution': distribution,
            'details': market_details,
            'percentage': {
                'shanghai': (distribution['shanghai'] / distribution['total'] * 100) if distribution['total'] > 0 else 0,
                'shenzhen': (distribution['shenzhen'] / distribution['total'] * 100) if distribution['total'] > 0 else 0,
                'unknown': (distribution['unknown'] / distribution['total'] * 100) if distribution['total'] > 0 else 0
            }
        }

    @staticmethod
    def analyze_sector_distribution(stock_codes):
        """
        分析股票列表的板块分布
        
        Args:
            stock_codes: 股票代码列表
        
        Returns:
            dict: 板块分布统计
        """
        sector_count = {}
        sector_details = {}
        
        for code in stock_codes:
            sector = MarketAnalyzer.identify_sector(code)
            
            if sector not in sector_count:
                sector_count[sector] = 0
                sector_details[sector] = []
            
            sector_count[sector] += 1
            sector_details[sector].append(code)
        
        total = len(stock_codes)
        sector_percentage = {
            sector: (count / total * 100) if total > 0 else 0 
            for sector, count in sector_count.items()
        }
        
        return {
            'sector_count': sector_count,
            'sector_details': sector_details,
            'sector_percentage': sector_percentage,
            'total_sectors': len(sector_count),
            'total_stocks': total
        }


def get_market_analysis_summary(stock_codes, target_market=None):
    """
    获取市场分析摘要
    
    Args:
        stock_codes: 股票代码列表
        target_market: 目标市场筛选
    
    Returns:
        dict: 完整的市场分析报告
    """
    # 如果指定了目标市场，先进行筛选
    if target_market:
        filtered_codes = MarketAnalyzer.filter_stocks_by_market(stock_codes, target_market)
    else:
        filtered_codes = stock_codes
    
    market_dist = MarketAnalyzer.analyze_market_distribution(filtered_codes)
    sector_dist = MarketAnalyzer.analyze_sector_distribution(filtered_codes)
    
    return {
        'original_count': len(stock_codes),
        'filtered_count': len(filtered_codes),
        'target_market': target_market,
        'market_analysis': market_dist,
        'sector_analysis': sector_dist,
        'filtered_codes': filtered_codes[:50],  # 限制返回数量避免过大
        'index_codes': MarketAnalyzer.get_market_index_codes(target_market) if target_market else {}
    }
