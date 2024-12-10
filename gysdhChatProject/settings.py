"""
Django settings for gysdhChatProject project.

Generated by 'django-admin startproject' using Django 5.1.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

from pathlib import Path
import os
from django.core.exceptions import ImproperlyConfigured
import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# 初始化环境变量
env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ['localhost', '127.0.0.1']),
)

# 读取环境变量文件
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# Encryption key for password storage
ENCRYPTION_KEY = env('ENCRYPTION_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "channels",
    "gysdhChatApp",
    "conferenceApp",
    "crispy_forms",
    "crispy_tailwind",
]

CRISPY_ALLOWED_TEMPLATE_PACKS = "tailwind"
CRISPY_TEMPLATE_PACK = "tailwind"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    'gysdhChatApp.middleware.UserActivityMiddleware',  # 添加用户活动中间件
    'gysdhChatProject.middleware.SSLMiddleware',  # SSL中间件
]

ROOT_URLCONF = "gysdhChatProject.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / 'templates']
        ,
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "gysdhChatApp.context_processors.system_settings",
            ],
        },
    },
]

WSGI_APPLICATION = "gysdhChatProject.wsgi.application"

# Channels配置
ASGI_APPLICATION = "gysdhChatProject.asgi.application"
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(env('REDIS_HOST'), env.int('REDIS_PORT'))],
            "capacity": 5000,  # 每个通道的最大消息数
            "expiry": 60,  # 消息过期时间（秒）
            "group_expiry": 86400,  # 组过期时间（秒）
            "symmetric_encryption_keys": [SECRET_KEY],  # 使用相同的密钥进行加密
        },
    },
}

# Redis缓存配置
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake",
    }
}

# Celery配置
CELERY_BROKER_URL = f"redis://{env('REDIS_HOST')}:{env.int('REDIS_PORT')}/2"
CELERY_RESULT_BACKEND = f"redis://{env('REDIS_HOST')}:{env.int('REDIS_PORT')}/2"
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Shanghai'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30分钟
CELERY_WORKER_PREFETCH_MULTIPLIER = 4  # 预取任务数
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000  # 每个worker处理的最大任务数

# Security Settings
SECURE_BROWSER_XSS_FILTER = True  # 启用XSS筛选器
SECURE_CONTENT_TYPE_NOSNIFF = True  # 防止MIME类型嗅探
SECURE_HSTS_SECONDS = 31536000  # 启用HSTS（一年）
SECURE_HSTS_INCLUDE_SUBDOMAINS = True  # HSTS对所有子域都有效
SECURE_HSTS_PRELOAD = True  # 允许预加载HSTS
X_FRAME_OPTIONS = 'DENY'  # 防止在frame中显示页面

# SSL Certificate settings
SECURE_SSL_CERTIFICATE = os.path.join(BASE_DIR, 'ssl/certificate.crt')
SECURE_SSL_PRIVATE_KEY = os.path.join(BASE_DIR, 'ssl/private.key')

# 只在非调试模式下启用SSL
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
else:
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False

# 认证设置
LOGIN_URL = '/'  # 设置登录页面的URL
LOGIN_REDIRECT_URL = '/'  # 登录成功后的重定向URL
LOGOUT_REDIRECT_URL = '/'  # 登出后的重定向URL

# 文件上传设置
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.pdf', '.doc', '.docx', '.xls', '.xlsx'}

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME', default='gysdh_chat'),
        'USER': env('DB_USER', default='gysdh_user'),
        'PASSWORD': env('DB_PASSWORD', default='your_secure_password'),
        'HOST': env('DB_HOST', default='localhost'),
        'PORT': env('DB_PORT', default='5432'),
        'CONN_MAX_AGE': 60,  # 持久连接超时时间（秒）
        'OPTIONS': {
            'connect_timeout': 5,
            'client_encoding': 'UTF8',
        },
        'ATOMIC_REQUESTS': True,  # 自动将HTTP请求包装在事务中
        'AUTOCOMMIT': True,
        'TEST': {
            'NAME': 'test_gysdh_chat',  # 测试数据库名称
        },
    }
}

# 配置数据库连接池
if not DEBUG:
    DATABASES['default']['CONN_MAX_AGE'] = 600  # 生产环境使用更长的连接时间
    DATABASES['default']['OPTIONS']['keepalives'] = 1  # 启用keepalive
    DATABASES['default']['OPTIONS']['keepalives_idle'] = 30  # 空闲超时（秒）
    DATABASES['default']['OPTIONS']['keepalives_interval'] = 10  # 探测间隔（秒）
    DATABASES['default']['OPTIONS']['keepalives_count'] = 5  # 探测次数

# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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

# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = "static/"
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'gysdhChatApp/static'),
]

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = 'gysdhChatApp.User'

AUTHENTICATION_BACKENDS = [
    #'gysdhChatApp.backends.NumberBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.qq.com'
EMAIL_PORT = 465
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')  # QQ邮箱授权码
EMAIL_USE_SSL = True  # QQ邮箱需要使用SSL
EMAIL_USE_TLS = False
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# 缓存加密密钥
ENCRYPTION_KEY = 'YOUR-SECRET-KEY-MUST-BE-32-BYTES-LONG!'  # 请更改为安全的密钥

# 缓存时间设置（秒）
CACHE_TTL = {
    'message': 300,  # 消息缓存5分钟
    'user': 600,    # 用户信息缓存10分钟
    'announcement': 1800,  # 公告缓存30分钟
}

# 日志配置
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'gysdhChatApp': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# 敏感词配置
SENSITIVE_WORDS = [
    'spam', 'ad', '广告', '测试', 
    # 添加其他敏感词...
]

# 速率限制配置
RATE_LIMIT = {
    'WINDOW': 60,  # 时间窗口（秒）
    'MAX_REQUESTS': 30,  # 最大请求数
}