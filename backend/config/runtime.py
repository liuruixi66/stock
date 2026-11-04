"""研究、行情和券商工具共用的独立配置，不依赖网站框架。"""

import os
from pathlib import Path

from .paths import BASE_DIR

try:
    from dotenv import load_dotenv
except ImportError:
    pass
else:
    load_dotenv(BASE_DIR / '.env')

STOCKS_DATABASE_PATH = os.getenv(
    'STOCKS_DATABASE_PATH', r'E:\股票数据集\data\stocks.db',
)
HISTORICAL_DATA_DIR = Path(os.getenv(
    'HISTORICAL_DATA_DIR', str(BASE_DIR / 'data' / 'history' / '2024_2026'),
))
