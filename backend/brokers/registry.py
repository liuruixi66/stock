"""券商注册表：根据账户的 broker 字段返回适配器实例，并提供给前端展示的目录。"""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

from .base import BrokerAdapter, BrokerError

if TYPE_CHECKING:
    from stockmarket.models import SimulationAccount

SIMULATED = 'SIM'

# code -> (模块, 类名)。延迟导入，避免未安装的 SDK 影响服务启动。
_ADAPTERS: dict[str, tuple[str, str]] = {
    'FUTU': ('brokers.futu_broker', 'FutuBroker'),
    'QMT': ('brokers.qmt_broker', 'QmtBroker'),
    'IB': ('brokers.ib_broker', 'IbBroker'),
}

BROKER_CHOICES = [
    (SIMULATED, '内置模拟撮合'),
    ('FUTU', '富途 OpenD'),
    ('QMT', '迅投 QMT'),
    ('IB', '盈透 IBKR'),
]


def adapter_class(code: str) -> type[BrokerAdapter]:
    try:
        module_name, class_name = _ADAPTERS[code.upper()]
    except KeyError as exc:
        raise BrokerError(f'未知券商类型: {code}') from exc
    return getattr(import_module(module_name), class_name)


def is_external(code: str) -> bool:
    return code.upper() != SIMULATED


def get_broker(account: 'SimulationAccount') -> BrokerAdapter:
    if not is_external(account.broker):
        raise BrokerError('内置模拟账户没有外部券商适配器')
    return adapter_class(account.broker)(account)


def broker_catalog() -> list[dict[str, Any]]:
    catalog: list[dict[str, Any]] = [{
        'code': SIMULATED,
        'label': '内置模拟撮合',
        'markets': ['A', 'US', 'CRYPTO'],
        'supports_live': False,
        'external': False,
        'sdk_package': None,
        'sdk_installed': True,
        'env_vars': [],
        'notes': '使用本系统行情源即时撮合，不需要任何券商账号。',
    }]
    for code in _ADAPTERS:
        catalog.append(adapter_class(code).describe())
    return catalog
