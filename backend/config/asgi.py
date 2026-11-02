"""Django ASGI 部署入口。

导入本模块时会根据配置创建异步服务器可调用的 `application` 对象，
供支持 ASGI 的部署服务器加载。
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_asgi_application()
