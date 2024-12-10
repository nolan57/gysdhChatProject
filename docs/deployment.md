# GYSDH Chat 部署文档

## 系统要求

- Python 3.8+
- Django 4.0+
- Redis 6.0+
- PostgreSQL 12+
- Node.js 14+ (用于前端资源构建)

## 环境准备

1. 创建并激活Python虚拟环境：
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 配置数据库：
```bash
# 在PostgreSQL中创建数据库
createdb gysdh_chat

# 执行数据库迁移
python manage.py migrate
```

4. 创建.env文件：
```bash
# 复制示例配置文件
cp .env.example .env

# 编辑.env文件，设置以下必要配置：
# - SECRET_KEY: Django密钥
# - ENCRYPTION_KEY: 用于加密的密钥
# - DATABASE_URL: 数据库连接URL
# - REDIS_URL: Redis连接URL
# - EMAIL_*: 邮件服务器配置
```

## 开发环境部署

1. 运行开发服务器：
```bash
python manage.py runserver
```

2. 启动Redis服务器（用于WebSocket）：
```bash
redis-server
```

3. 运行Celery Worker（用于异步任务）：
```bash
celery -A gysdhChatProject worker -l info
```

## 生产环境部署

### 使用Docker部署

1. 构建Docker镜像：
```bash
docker build -t gysdh-chat .
```

2. 使用docker-compose启动服务：
```bash
docker-compose up -d
```

### 手动部署

1. 配置Nginx：
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /ws/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location /static/ {
        alias /path/to/your/static/files/;
    }

    location /media/ {
        alias /path/to/your/media/files/;
    }
}
```

2. 配置Gunicorn：
```bash
gunicorn gysdhChatProject.wsgi:application --bind 127.0.0.1:8000 --workers 4
```

3. 配置Daphne（WebSocket服务器）：
```bash
daphne -b 127.0.0.1 -p 8001 gysdhChatProject.asgi:application
```

4. 配置Supervisor管理进程：
```ini
[program:gysdh-chat]
command=/path/to/venv/bin/gunicorn gysdhChatProject.wsgi:application --bind 127.0.0.1:8000 --workers 4
directory=/path/to/project
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/gysdh-chat/gunicorn.log

[program:gysdh-chat-websocket]
command=/path/to/venv/bin/daphne -b 127.0.0.1 -p 8001 gysdhChatProject.asgi:application
directory=/path/to/project
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/gysdh-chat/daphne.log

[program:gysdh-chat-celery]
command=/path/to/venv/bin/celery -A gysdhChatProject worker -l info
directory=/path/to/project
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/gysdh-chat/celery.log
```

## 安全配置

1. 设置环境变量：
- 确保所有敏感配置都通过环境变量或.env文件设置
- 生产环境中设置 `DEBUG=False`
- 设置适当的 `ALLOWED_HOSTS`

2. 配置SSL证书：
- 使用Let's Encrypt获取免费SSL证书
- 配置Nginx启用HTTPS

3. 设置防火墙：
```bash
# 只开放必要端口
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

## 监控和维护

1. 日志管理：
- 配置日志轮转
- 设置适当的日志级别
- 定期检查错误日志

2. 备份策略：
- 配置数据库定期备份
- 备份媒体文件
- 设置备份文件的保留策略

3. 性能监控：
- 使用Prometheus + Grafana监控系统性能
- 配置告警机制
- 定期检查系统资源使用情况

## 故障排除

常见问题及解决方案：

1. WebSocket连接失败：
- 检查Daphne服务是否正常运行
- 确认Nginx配置是否正确
- 检查防火墙设置

2. 静态文件404：
- 运行 `python manage.py collectstatic`
- 检查Nginx静态文件配置
- 确认文件权限设置

3. 数据库连接错误：
- 检查数据库服务是否运行
- 验证数据库连接配置
- 确认数据库用户权限
