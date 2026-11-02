"""Django 服务配置：数据库、应用、中间件、跨域和静态资源等运行参数。"""

import os

# 由统一路径模块提供项目根目录，避免不同启动目录下的相对路径解析不一致。
from .paths import BASE_DIR

# 券商连接信息等敏感配置从 backend/.env 读取（参考 .env.example），不写入代码仓库。
try:
    from dotenv import load_dotenv

    load_dotenv(BASE_DIR / '.env')
except ImportError:
    pass

STOCKS_DATABASE_PATH = os.getenv(
    'STOCKS_DATABASE_PATH', r'E:\股票数据集\data\stocks.db',
)


# 以下是 Django 项目启动时使用的基础配置；部署到生产环境前必须按部署清单
# 收紧调试、密钥、允许域名和跨域策略，不能直接沿用当前开发设置。

# 安全提示：生产环境密钥必须从安全配置注入，不能使用源码中的开发占位值。
SECRET_KEY = "django-insecure-(of6q+c%x7a0ujr1vne-ml*o!cxcjwr7fyahg080ps8e&pvsd8"

# 安全提示：DEBUG 仅适用于本地开发；生产环境应关闭并配置受限的 ALLOWED_HOSTS。
DEBUG = True

ALLOWED_HOSTS = ['*'] # 开发期接受任意 Host；生产环境应替换为明确的域名白名单。


# Django 应用定义：基础管理功能、跨域支持和本项目的股票业务模型。

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",  # 为前后端分离开发提供跨域响应头。
    # "rest_framework",  # 暂未启用 Django REST framework，避免引入当前不需要的依赖。
    "stockmarket",  # 注册股票数据、账户、订单、自选列表和研究记录模型。
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",  # 在通用响应处理前添加跨域响应头。
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# 跨域设置：当前允许所有来源是开发便利配置，生产环境必须限制为受信任前端域名。
CORS_ALLOW_ALL_ORIGINS = True  # 开发环境下允许所有源
CORS_ALLOW_CREDENTIALS = True

# 跨域预检允许的方法；实际 API 仍由各视图按请求方法进行校验。
CORS_ALLOW_METHODS = [
    'GET',
    'POST',
    'PUT',
    'PATCH',
    'DELETE',
    'OPTIONS'
]

# 浏览器跨域请求可携带的请求头。
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# Django CSRF 校验认可的来源；跨域设置不会自动关闭 CSRF 防护。
CSRF_TRUSTED_ORIGINS = [
    'http://127.0.0.1:8002',
    'http://localhost:8002'
]


ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# 数据库选择：设置 DB_ENGINE=mysql 时连接 MySQL，否则使用项目目录下的 SQLite 文件。

if os.getenv('DB_ENGINE') == 'mysql':
    import pymysql

    pymysql.install_as_MySQLdb()
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.getenv('DB_NAME', 'stockdb'),
            'USER': os.getenv('DB_USER', 'root'),
            'PASSWORD': os.getenv('DB_PASSWORD', ''),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', '3306'),
            'OPTIONS': {'charset': 'utf8mb4'},
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# Django 管理用户密码校验器；当前业务 API 的账户模型不等同于 Django 登录用户。

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# 国际化和时区配置；启用时区支持后，Django 会以 UTC 保存带时区的时间戳。

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# 静态资源 URL 前缀；开发期由 Django/Vite 处理，生产部署需配置静态文件收集服务。

STATIC_URL = "static/"

# 未显式声明主键类型的 Django 模型默认使用 64 位自增主键。

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
