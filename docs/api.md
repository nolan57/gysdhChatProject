# GYSDH Chat API 文档

## 概述

GYSDH Chat 是一个基于Django的聊天应用系统，提供实时聊天、公告发布、用户管理等功能。

## 认证

所有API请求需要进行身份认证。认证通过用户的登录凭证进行。

## API 端点

### 用户管理

#### 用户登录
- **URL**: `/api/login/`
- **方法**: POST
- **参数**:
  - `number`: 用户编号
  - `password`: 用户密码
- **返回**: 
  ```json
  {
    "token": "认证令牌",
    "user": {
      "id": "用户ID",
      "name": "用户名称",
      "number": "用户编号"
    }
  }
  ```

### 消息

#### 发送消息
- **URL**: `/api/messages/send/`
- **方法**: POST
- **认证**: 必需
- **参数**:
  - `content`: 消息内容
  - `is_private`: 是否为私信
  - `recipient`: 接收者ID（私信时必需）
  - `file`: 附件（可选）
- **返回**:
  ```json
  {
    "id": "消息ID",
    "content": "消息内容",
    "timestamp": "发送时间",
    "sender": {
      "id": "发送者ID",
      "name": "发送者名称"
    }
  }
  ```

### 公告

#### 发布公告
- **URL**: `/api/announcements/publish/`
- **方法**: POST
- **认证**: 必需
- **权限**: 需要公告发布权限
- **参数**:
  - `content`: 公告内容
  - `priority`: 优先级(1-4)
  - `expires_at`: 过期时间（可选）
  - `is_sticky`: 是否置顶
  - `file`: 附件（可选）
- **返回**:
  ```json
  {
    "id": "公告ID",
    "content": "公告内容",
    "priority": "优先级",
    "timestamp": "发布时间"
  }
  ```

## 错误处理

所有API错误响应都遵循以下格式：

```json
{
  "error": {
    "code": "错误代码",
    "message": "错误描述"
  }
}
```

常见错误代码：
- 400: 请求参数错误
- 401: 未认证
- 403: 权限不足
- 404: 资源不存在
- 500: 服务器内部错误

## WebSocket API

### 实时消息

#### 连接
- **URL**: `ws://[domain]/ws/chat/`
- **认证**: 需要在URL中包含token参数

#### 消息格式

发送消息：
```json
{
  "type": "message",
  "content": "消息内容",
  "recipient": "接收者ID（可选）"
}
```

接收消息：
```json
{
  "type": "message",
  "sender": {
    "id": "发送者ID",
    "name": "发送者名称"
  },
  "content": "消息内容",
  "timestamp": "发送时间"
}
```
