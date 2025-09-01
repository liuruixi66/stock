"""
系统适配模块 - 自动识别操作系统并提供相应的适配功能
"""
import os
import sys
import platform
from typing import Optional, Dict, Any, Union
import pandas as pd

class SystemAdapter:
    """系统适配器 - 自动识别并适配不同操作系统"""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.is_windows = self.system == 'windows'
        self.is_linux = self.system == 'linux'
        self.is_macos = self.system == 'darwin'
        
        # 打印系统信息
        print(f"🖥️  检测到操作系统: {platform.system()} {platform.release()}")
        print(f"🐍 Python版本: {sys.version}")
        
    def get_trading_modules(self) -> Dict[str, Any]:
        """根据系统返回相应的交易模块"""
        if self.is_windows:
            return self._get_windows_modules()
        else:
            return self._get_linux_modules()
    
    def _get_windows_modules(self) -> Dict[str, Any]:
        """Windows系统的交易模块"""
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
        """Linux系统的模拟交易模块"""
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
    """获取系统信息"""
    return {
        'system': platform.system(),
        'release': platform.release(),
        'machine': platform.machine(),
        'python_version': sys.version,
        'platform_info': platform.platform()
    }

def is_windows() -> bool:
    """判断是否为Windows系统"""
    return system_adapter.is_windows

def is_linux() -> bool:
    """判断是否为Linux系统"""
    return system_adapter.is_linux

def get_compatible_path(path: str) -> str:
    """获取兼容的文件路径"""
    if system_adapter.is_windows:
        return path.replace('/', '\\')
    else:
        return path.replace('\\', '/')
