"""券商适配层的公共类型：所有外部券商（模拟盘/实盘）都实现 BrokerAdapter。"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal
from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from stockmarket.models import SimulationAccount, SimulationOrder


class BrokerError(RuntimeError):
    """券商 SDK 未安装、连接失败或券商拒绝请求时抛出。"""


# 订单在本系统内的统一状态；OPEN_STATUSES 中的订单仍可能被券商继续成交或撤销。
OPEN_STATUSES = ('PENDING', 'SUBMITTED', 'PARTIAL')
FINAL_STATUSES = ('FILLED', 'CANCELLED', 'REJECTED')


@dataclass
class OrderResult:
    status: str
    broker_order_id: str = ''
    filled_quantity: Decimal = Decimal('0')
    executed_price: Decimal | None = None
    commission: Decimal = Decimal('0')
    tax: Decimal = Decimal('0')
    message: str = ''


@dataclass
class AccountSnapshot:
    cash: Decimal
    market_value: Decimal
    total_assets: Decimal
    currency: str
    frozen_cash: Decimal = Decimal('0')
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class PositionSnapshot:
    symbol: str
    quantity: Decimal
    average_price: Decimal
    available_quantity: Decimal | None = None
    market_value: Decimal | None = None


def to_decimal(value: Any, default: str = '0') -> Decimal:
    """把 SDK 返回的 float/str/numpy 标量安全地转换为 Decimal。"""
    if value is None:
        return Decimal(default)
    try:
        text = str(value).strip()
        if not text or text.lower() in {'nan', 'none', 'n/a'}:
            return Decimal(default)
        return Decimal(text)
    except (ArithmeticError, ValueError):
        return Decimal(default)


def env(name: str, default: str = '') -> str:
    return os.getenv(name, default).strip()


def require_env(name: str, hint: str) -> str:
    value = env(name)
    if not value:
        raise BrokerError(f'缺少环境变量 {name}：{hint}')
    return value


def import_sdk(module: str, package: str):
    """按需导入券商 SDK，未安装时给出可执行的安装提示。"""
    try:
        return import_module(module)
    except ImportError as exc:
        raise BrokerError(f'未安装券商 SDK {package}（import {module} 失败：{exc}）。请执行 pip install {package}') from exc


def a_share_exchange(symbol: str) -> str:
    """根据 6 位 A 股代码推断交易所：SH / SZ / BJ。"""
    code = symbol.strip().upper()
    if code.startswith('92') or code.startswith(('4', '8')):
        return 'BJ'
    if code.startswith(('5', '6', '9')):
        return 'SH'
    return 'SZ'


class BrokerAdapter(ABC):
    """一个适配器实例对应一个已绑定券商账号的 SimulationAccount。"""

    code: str = ''
    label: str = ''
    markets: frozenset[str] = frozenset()
    supports_live: bool = False
    sdk_module: str | None = None
    sdk_package: str | None = None
    env_vars: tuple[str, ...] = ()
    notes: str = ''

    def __init__(self, account: 'SimulationAccount'):
        self.account = account

    @property
    def is_live(self) -> bool:
        return self.account.trading_mode == 'LIVE'

    @abstractmethod
    def place_order(self, order: 'SimulationOrder') -> OrderResult:
        """向券商报单并返回券商侧的初始状态。"""

    @abstractmethod
    def cancel_order(self, order: 'SimulationOrder') -> OrderResult:
        """撤销尚未完成的委托。"""

    @abstractmethod
    def get_order(self, order: 'SimulationOrder') -> OrderResult:
        """查询单笔委托的最新状态。"""

    @abstractmethod
    def get_account(self) -> AccountSnapshot:
        """查询资金。"""

    @abstractmethod
    def get_positions(self) -> list[PositionSnapshot]:
        """查询持仓，数量为 0 的持仓应被过滤掉。"""

    def list_accounts(self) -> list[dict[str, Any]]:
        """列出券商侧可用账号，用于首次接入时确定 broker_account_id；不支持时返回空列表。"""
        return []

    @classmethod
    def describe(cls) -> dict[str, Any]:
        from importlib.util import find_spec

        installed = True
        if cls.sdk_module:
            try:
                installed = find_spec(cls.sdk_module.split('.')[0]) is not None
            except (ImportError, ValueError):
                installed = False
        return {
            'code': cls.code,
            'label': cls.label,
            'markets': sorted(cls.markets),
            'supports_live': cls.supports_live,
            'external': True,
            'sdk_package': cls.sdk_package,
            'sdk_installed': installed,
            'env_vars': list(cls.env_vars),
            'notes': cls.notes,
        }
