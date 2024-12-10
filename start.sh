#!/bin/bash

# 确保脚本在错误时停止
set -e

# 检查 .env 文件是否存在
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    # 生成随机的 SECRET_KEY
    SECRET_KEY=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
    # 生成随机的 ENCRYPTION_KEY
    ENCRYPTION_KEY=$(python -c 'import base64; import os; print(base64.urlsafe_b64encode(os.urandom(32)).decode())')
    # 更新 .env 文件
    sed -i.bak "s|your-secret-key-here|${SECRET_KEY}|g" .env
    sed -i.bak "s|your-encryption-key-here|${ENCRYPTION_KEY}|g" .env
    rm -f .env.bak
fi

# 检查操作系统
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    echo "Detected macOS system"
    # 检查 Docker Desktop 是否运行
    if ! pgrep -f Docker > /dev/null; then
        echo "Please start Docker Desktop first"
        exit 1
    fi
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    echo "Detected Windows system"
    # 检查 Docker Desktop 是否运行
    if ! tasklist | grep -q "Docker Desktop"; then
        echo "Please start Docker Desktop first"
        exit 1
    fi
fi

# 停止并删除所有现有容器
echo "Stopping any existing containers..."
docker-compose down -v

# 构建并启动容器
echo "Building and starting containers..."
docker-compose up --build -d

# 等待服务就绪
echo "Waiting for services to be ready..."
sleep 10

# 显示容器状态
echo "Container status:"
docker-compose ps

# 显示访问信息
echo "
==============================================
🚀 Application is now running!

📱 Access the application:
   - Web Interface: http://localhost:8000
   - Admin Panel: http://localhost:8000/admin
   
🔑 Default admin credentials:
   Username: admin
   Password: admin

📝 Logs can be viewed with:
   docker-compose logs -f

⚠️ To stop the application:
   docker-compose down

==============================================
"
