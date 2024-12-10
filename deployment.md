# GYSDH Chat 部署指南

## 1. 系统要求
- Python 3.12+
- Redis 6+
- PostgreSQL 12+
- Nginx
- 域名和SSL证书

## 2. 安装步骤

### 2.1 安装系统依赖
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3-pip python3-dev libpq-dev postgresql postgresql-contrib nginx redis-server

# CentOS/RHEL
sudo yum install python3-pip python3-devel postgresql-server postgresql-devel nginx redis
```

### 2.2 创建虚拟环境
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2.3 配置环境变量
1. 复制环境变量模板：
```bash
cp .env.prod .env
```

2. 修改 `.env` 文件：
- 生成新的 SECRET_KEY
- 设置你的域名到 ALLOWED_HOSTS
- 配置数据库连接
- 设置 Redis 连接信息
- 生成新的 ENCRYPTION_KEY

### 2.4 配置 Nginx
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # 重定向到HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location /static/ {
        alias /path/to/your/static/;
    }

    location /media/ {
        alias /path/to/your/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 2.5 配置 Gunicorn
创建 `gunicorn.conf.py`:
```python
bind = "127.0.0.1:8000"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
```

### 2.6 配置 Systemd 服务
创建 `/etc/systemd/system/gysdhchat.service`:
```ini
[Unit]
Description=GYSDH Chat Service
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/gysdhChatProject
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/gunicorn -c gunicorn.conf.py gysdhChatProject.asgi:application

[Install]
WantedBy=multi-user.target
```

### 2.7 启动服务
```bash
# 收集静态文件
python manage.py collectstatic

# 运行数据库迁移
python manage.py migrate

# 创建超级用户
python manage.py createsuperuser

# 启动服务
sudo systemctl start gysdhchat
sudo systemctl enable gysdhchat
sudo systemctl start nginx
sudo systemctl enable nginx
```

## 3. 安全注意事项
1. 确保生产环境中 DEBUG=False
2. 使用强密码和密钥
3. 定期更新系统和依赖包
4. 配置防火墙只开放必要端口
5. 使用SSL证书加密通信
6. 定期备份数据

## 4. 性能优化建议
1. 使用 Redis 缓存
2. 配置适当的 Gunicorn 工作进程数
3. 启用 Nginx 缓存
4. 使用 CDN 加速静态资源
5. 定期清理旧的聊天记录和文件

## 5. 监控和维护
1. 设置日志轮转
2. 配置系统监控
3. 定期检查系统资源使用情况
4. 监控应用性能和错误日志

## 6. 故障排除
1. 检查日志文件：
   ```bash
   sudo journalctl -u gysdhchat.service
   sudo tail -f /var/log/nginx/error.log
   ```

2. 检查服务状态：
   ```bash
   sudo systemctl status gysdhchat
   sudo systemctl status nginx
   sudo systemctl status redis
   ```

如需更多帮助，请参考项目文档或联系技术支持。
