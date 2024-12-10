#!/bin/bash

# 启动Redis
brew services start redis

# 激活虚拟环境
source venv/bin/activate

# 运行数据库迁移
python manage.py migrate

# 收集静态文件
python manage.py collectstatic --noinput

# 启动Daphne
daphne -b 0.0.0.0 -p 8000 gysdhChatProject.asgi:application
