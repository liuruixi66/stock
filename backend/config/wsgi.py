"""Django WSGI 部署入口。

导入本模块时会根据配置创建同步服务器可调用的 `application` 对象，
供 Gunicorn、uWSGI 等 WSGI 服务器加载。
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_wsgi_application()
