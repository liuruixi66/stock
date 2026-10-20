"""为配置、缓存读取器和命令行工具提供统一的项目目录路径。"""

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = BASE_DIR / 'cache'
