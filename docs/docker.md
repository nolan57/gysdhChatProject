# Docker 部署和环境配置指南

## 环境说明

本项目支持以下环境：

1. 开发环境 (Development)
2. 生产环境 (Production)

## 配置文件说明

- `docker-compose.yml`: 基础配置文件，包含所有环境通用的配置
- `docker-compose.prod.yml`: 生产环境特定配置
- `docker/Dockerfile`: Docker镜像构建文件
- `docker/entrypoint.sh`: 容器启动脚本

## 环境变量配置

创建 `.env` 文件并配置以下环境变量：

```bash
# Django 配置
DJANGO_ENV=development  # 或 production
SECRET_KEY=your-secret-key
DEBUG=True  # 生产环境设为 False

# 数据库配置
DB_NAME=gysdh_chat
DB_USER=postgres
DB_PASSWORD=your-db-password
DATABASE_HOST=db
DATABASE_PORT=5432

# Redis配置
REDIS_HOST=redis
REDIS_PORT=6379

# 邮件配置
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-email-password
```

## 开发环境部署

```bash
# 构建并启动服务
docker-compose up --build

# 后台运行
docker-compose up -d

# 查看日志
docker-compose logs -f
```

## 生产环境部署

```bash
# 使用生产环境配置启动
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 查看生产环境日志
docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f
```

## 数据库备份

### 自动备份

项目包含自动备份服务，配置如下：

1. 开发环境：
   - 每天自动备份一次
   - 保留最近7天的备份

2. 生产环境：
   - 每天自动备份一次
   - 保留最近30天的备份
   - 备份文件会被压缩

备份文件存储在 `backups/` 目录下。

### 手动备份

使用提供的备份脚本：

```bash
# 执行手动备份
./scripts/backup.sh

# 指定保留天数的备份
KEEP_DAYS=14 ./scripts/backup.sh

# 同步到远程存储
REMOTE_BACKUP_PATH="user@remote:/path/to/backup" ./scripts/backup.sh
```

## 常见问题处理

1. 数据库连接失败：
```bash
# 检查数据库容器状态
docker-compose ps db
# 查看数据库日志
docker-compose logs db
```

2. Redis连接问题：
```bash
# 检查Redis容器状态
docker-compose ps redis
# 查看Redis日志
docker-compose logs redis
```

3. 静态文件不可访问：
```bash
# 重新收集静态文件
docker-compose exec web python manage.py collectstatic --no-input
```

## 性能优化建议

1. 生产环境配置：
   - 使用多个Gunicorn工作进程
   - 启用Redis持久化
   - 配置适当的Celery并发数

2. 数据库优化：
   - 启用PostgreSQL查询缓存
   - 定期执行VACUUM
   - 监控并优化慢查询

3. 缓存策略：
   - 使用Redis缓存会话
   - 缓存频繁访问的数据
   - 使用页面缓存

## 监控和维护

1. 容器监控：
```bash
# 查看容器资源使用情况
docker stats

# 查看容器日志
docker-compose logs -f [service_name]
```

2. 数据库维护：
```bash
# 进入数据库容器
docker-compose exec db psql -U $DB_USER -d $DB_NAME

# 备份数据库
docker-compose exec backup ./scripts/backup.sh
```

3. 日志管理：
```bash
# 查看特定服务的日志
docker-compose logs -f web
docker-compose logs -f celery
```
