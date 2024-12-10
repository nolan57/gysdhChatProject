#!/bin/bash

set -e

# 等待数据库准备就绪
if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for PostgreSQL..."

    while ! nc -z $DATABASE_HOST $DATABASE_PORT; do
        echo "PostgreSQL is unavailable - sleeping"
        sleep 1
    done

    echo "PostgreSQL started"
fi

# 等待Redis准备就绪
echo "Waiting for Redis..."
while ! nc -z redis 6379; do
    echo "Redis is unavailable - sleeping"
    sleep 1
done
echo "Redis started"

# 创建必要的目录
mkdir -p /app/static /app/media /app/logs

# 运行数据库迁移
echo "Running database migrations..."
python manage.py migrate --noinput

# 收集静态文件
echo "Collecting static files..."
python manage.py collectstatic --noinput

# 创建超级用户（如果不存在）
echo "Creating superuser if not exists..."
python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin')
END

# 设置正确的文件权限
find /app -type d -exec chmod 755 {} \;
find /app -type f -exec chmod 644 {} \;

echo "Initialization completed!"

exec "$@"
