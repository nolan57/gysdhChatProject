#!/bin/bash

# 设置变量
BACKUP_DIR="/app/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$TIMESTAMP.sql.gz"
KEEP_DAYS=7  # 默认保留7天的备份

# 确保备份目录存在
mkdir -p $BACKUP_DIR

# 执行数据库备份
echo "开始备份数据库..."
pg_dump -h ${DATABASE_HOST} -U ${DATABASE_USER} ${DATABASE_NAME} | gzip > $BACKUP_FILE

# 检查备份是否成功
if [ $? -eq 0 ]; then
    echo "数据库备份成功: $BACKUP_FILE"
    
    # 删除旧备份
    echo "清理旧备份文件..."
    find $BACKUP_DIR -type f -name "backup_*.sql.gz" -mtime +$KEEP_DAYS -delete
    
    # 计算备份文件大小
    BACKUP_SIZE=$(du -h $BACKUP_FILE | cut -f1)
    echo "备份文件大小: $BACKUP_SIZE"
    
    # 列出当前所有备份
    echo "当前备份文件列表:"
    ls -lh $BACKUP_DIR
else
    echo "数据库备份失败!"
    exit 1
fi

# 可选：将备份同步到远程存储
if [ ! -z "$REMOTE_BACKUP_PATH" ]; then
    echo "同步备份到远程存储..."
    rsync -avz $BACKUP_FILE $REMOTE_BACKUP_PATH
    if [ $? -eq 0 ]; then
        echo "远程备份同步成功"
    else
        echo "远程备份同步失败!"
    fi
fi
