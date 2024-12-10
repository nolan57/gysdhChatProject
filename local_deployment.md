# 在个人电脑上部署GYSDH Chat（内网穿透方案）

## 方案一：使用 ngrok（推荐新手使用）

### 1. 安装 ngrok
```bash
# macOS（使用Homebrew）
brew install ngrok

# 或直接从官网下载：https://ngrok.com/download
```

### 2. 注册 ngrok
1. 访问 https://ngrok.com 注册账号
2. 获取 authtoken
3. 配置 authtoken：
```bash
ngrok config add-authtoken your-token-here
```

### 3. 启动Django项目
```bash
# 激活虚拟环境
source venv/bin/activate

# 确保Redis服务已启动
brew services start redis

# 运行Django项目
python manage.py runserver 8000
```

### 4. 启动ngrok
```bash
ngrok http 8000
```

ngrok会提供一个公网域名，比如：https://xxxx.ngrok.io
将这个域名添加到Django的ALLOWED_HOSTS中：

修改 .env 文件：
```
ALLOWED_HOSTS=localhost,127.0.0.1,xxxx.ngrok.io
```

## 方案二：使用 frp（更稳定，适合长期使用）

### 1. 准备工作
- 一个有公网IP的服务器（作为frp服务端）
- 下载frp客户端和服务端：https://github.com/fatedier/frp/releases

### 2. 服务端配置（在公网服务器上）
创建 frps.ini：
```ini
[common]
bind_port = 7000
dashboard_port = 7500
token = your-token-here
dashboard_user = admin
dashboard_pwd = admin
```

启动服务端：
```bash
./frps -c frps.ini
```

### 3. 客户端配置（在你的电脑上）
创建 frpc.ini：
```ini
[common]
server_addr = your-server-ip
server_port = 7000
token = your-token-here

[web]
type = tcp
local_ip = 127.0.0.1
local_port = 8000
remote_port = 8080
```

启动客户端：
```bash
./frpc -c frpc.ini
```

### 4. 配置Django
修改 .env 文件：
```
ALLOWED_HOSTS=localhost,127.0.0.1,your-server-ip
```

## 注意事项

### 1. 安全性考虑
- 使用HTTPS（ngrok默认提供）
- 设置强密码
- 定期更新系统和依赖包
- 注意个人电脑的防火墙设置

### 2. 性能考虑
- 个人电脑需要保持开机和网络连接
- 注意内存和CPU使用情况
- 建议限制最大用户数
- 文件上传可能受上传带宽限制

### 3. 稳定性考虑
- 确保电脑不会进入睡眠状态
- 保持网络连接稳定
- 建议使用有线网络连接
- 定期检查服务状态

### 4. 使用建议
- 仅用于测试或小规模使用
- 不建议用于生产环境
- 定期备份数据
- 监控系统资源使用情况

## 快速启动脚本

创建 `start_chat.sh`：
```bash
#!/bin/bash

# 启动Redis
brew services start redis

# 激活虚拟环境
source venv/bin/activate

# 运行数据库迁移
python manage.py migrate

# 启动Django
python manage.py runserver 8000 &

# 等待Django启动
sleep 5

# 启动ngrok（如果使用ngrok）
ngrok http 8000
```

使用方法：
```bash
chmod +x start_chat.sh
./start_chat.sh
```

## 故障排除

### 1. 连接问题
- 检查Django服务是否正常运行
- 确认内网穿透服务是否正常
- 检查ALLOWED_HOSTS设置
- 验证防火墙设置

### 2. 性能问题
- 检查系统资源使用情况
- 考虑减少最大连接数
- 优化文件上传大小限制
- 清理不必要的日志和数据

### 3. 常见错误
- DisallowedHost：检查ALLOWED_HOSTS设置
- 连接超时：检查网络和内网穿透服务
- 数据库错误：确保Redis正常运行
- 文件权限：检查上传目录权限

如需更多帮助，请参考项目文档或提交Issue。
