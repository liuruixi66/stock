"""
系统适配模块 - 自动识别操作系统并提供相应的适配功能
"""
import os
import sys
import platform
from typing import Optional, Dict, Any, Union
import pandas as pd

class SystemAdapter:
    """根据操作系统选择原生交易模块或兼容实现。"""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.is_windows = self.system == 'windows'
        self.is_linux = self.system == 'linux'
        self.is_macos = self.system == 'darwin'
        
        # 打印系统信息
        print(f"🖥️  检测到操作系统: {platform.system()} {platform.release()}")
        print(f"🐍 Python版本: {sys.version}")
        
    def get_trading_modules(self) -> Dict[str, Any]:
        """返回统一的交易模块字典，供调用方避免直接判断操作系统。"""
        if self.is_windows:
            return self._get_windows_modules()
        else:
            return self._get_linux_modules()
    
    def _get_windows_modules(self) -> Dict[str, Any]:
        """优先加载 Windows 原生 xtquant，缺少依赖时回退到兼容模块。"""
        try:
            # 尝试导入Windows原生模块
            import xtquant.xtdata as xtdata
            from xtquant.xtpythonclient import XTPythonClient
            
            print("✅ Windows原生交易模块加载成功")
            return {
                'xtdata': xtdata,
                'XTPythonClient': XTPythonClient,
                'platform': 'windows_native'
            }
        except ImportError:
            print("⚠️  Windows原生模块不可用，使用模拟模块")
            return self._get_linux_modules()
    
    def _get_linux_modules(self) -> Dict[str, Any]:
        """加载 Linux/macOS 上用于开发和测试的兼容交易模块。"""
        from xtdata_compatible import XTDataCompatible
        from xtclient_compatible import XTClientCompatible
        
        print("✅ Linux兼容交易模块加载成功")
        return {
            'xtdata': XTDataCompatible(),
            'XTPythonClient': XTClientCompatible,
            'platform': 'linux_compatible'
        }

# 全局系统适配器实例
system_adapter = SystemAdapter()
trading_modules = system_adapter.get_trading_modules()

def get_system_info() -> Dict[str, str]:
    """返回操作系统、机器架构和 Python 版本等诊断信息。"""
    return {
        'system': platform.system(),
        'release': platform.release(),
        'machine': platform.machine(),
        'python_version': sys.version,
        'platform_info': platform.platform()
    }

def is_windows() -> bool:
    """判断当前运行环境是否为 Windows。"""
    return system_adapter.is_windows

def is_linux() -> bool:
    """判断当前运行环境是否为 Linux。"""
    return system_adapter.is_linux

def get_compatible_path(path: str) -> str:
    """按当前系统转换路径分隔符，不负责验证路径是否存在。"""
    if system_adapter.is_windows:
        return path.replace('/', '\\')
    else:
        return path.replace('\\', '/')
