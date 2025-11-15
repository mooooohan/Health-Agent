# Coze聊天机器人API接口文档 v1.0

## 概述

基于Coze API的心理健康聊天机器人API服务，提供同步和流式两种聊天模式，支持会话管理、上下文维护和conversation_id续传功能。

### 核心特性

- 🤖 **智能对话**: 基于Coze API的自然语言理解和生成
- 🔄 **流式输出**: 支持Server-Sent Events (SSE) 实时流式响应
- 💬 **多轮对话**: 自动维护会话上下文，支持连续对话
- 🔗 **会话续传**: 支持conversation_id续传现有会话
- 🎯 **会话绑定**: 自动管理session_id与conversation_id的映射关系
- 📊 **会话管理**: 提供会话查询、清除等管理功能
- 🛡️ **错误处理**: 完善的异常处理和日志记录
- 📖 **自动文档**: Swagger/OpenAPI自动生成接口文档

### 基础信息

- **版本**: 1.1.0
- **基础URL**: `http://localhost:6001`
- **API文档**: `http://localhost:6001/docs`
- **协议**: HTTP/1.1 + SSE
- **数据格式**: JSON

---

## 快速开始

### 1. 环境准备

确保已安装所有依赖：

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件：

```env
# Coze API配置
COZE_API_TOKEN=your_api_token_here
COZE_BOT_ID=your_bot_id_here
COZE_USER_ID=default_user
COZE_BASE_URL=https://api.coze.cn/v3

# 服务器配置
SERVER_HOST=0.0.0.0
SERVER_PORT=6001
DEBUG=false
```

### 3. 启动服务

```bash
# 启动API服务器
python api_server.py

# 或使用uvicorn直接启动
uvicorn api_server:app --host 0.0.0.0 --port 6001 --reload
```

### 4. 健康检查

```bash
curl http://localhost:6001/health   
```

---

## API接口详解

### 1. 系统状态接口

#### 1.1 健康检查

- **接口**: `GET /health`
- **描述**: 检查服务运行状态
- **响应示例**:

```json
{
    "status": "healthy",
    "timestamp": "2024-01-15T10:30:00",
    "coze_client_status": "initialized"
}
```

#### 1.2 根路径

- **接口**: `GET /`
- **描述**: 服务基本信息
- **响应示例**:

```json
{
    "message": "Coze聊天机器人API服务正在运行",
    "version": "1.0.0",
    "status": "healthy",
    "docs": "/docs"
}
```

---

### 2. 聊天功能接口

#### 2.1 同步聊天

- **接口**: `POST /chat`
- **描述**: 发送聊天消息并获取完整回复（阻塞模式）
- **请求头**:

```
Content-Type: application/json
```

- **请求体**:

```json
{
    "user_id": "user123",           // 可选，用户ID
    "message": "我最近工作压力很大",   // 必填，消息内容
    "session_id": "demo_session_1"   // 可选，会话ID
}
```

- **响应示例**:

```json
{
    "response": "我理解您的工作压力。以下是一些缓解压力的建议...",
    "session_id": "demo_session_1",
    "message_id": "msg_abc123def456",
    "timestamp": "2024-01-15T10:30:15.123456",
    "conversation_id": "conv_789xyz"
}
```

- **curl示例**:

```bash
curl -X POST "http://localhost:6001/chat" \
     -H "Content-Type: application/json" \
     -d '{
       "message": "你好，我想聊聊最近的心情",
       "session_id": "my_session"
     }'
```

#### 2.2 流式聊天

- **接口**: `POST /chat/stream`
- **描述**: 发送聊天消息并获取流式回复（实时输出）
- **请求体**: 与同步聊天相同
- **响应类型**: `text/event-stream` (SSE)

**流式响应格式**:

```text
data: {"type": "chunk", "data": {"content": "我理解您的", "chunk_index": 0, "total_chunks": 5}}
data: {"type": "chunk", "data": {"content": "感受。让我们", "chunk_index": 1, "total_chunks": 5}}
data: {"type": "chunk", "data": {"content": "一起探讨", "chunk_index": 2, "total_chunks": 5}}
data: {"type": "complete", "data": {"total_chunks": 3, "full_content": "我理解您的感受。together..."}}
```

- **curl示例**:

```bash
curl -X POST "http://localhost:6001/chat/stream" \
     -H "Content-Type: application/json" \
     -d '{"message": "能给我一些缓解压力的建议吗？"}' \
     --no-buffer
```

---

### 3. 会话管理接口

#### 3.1 获取会话信息

- **接口**: `GET /session/{session_id}/info`
- **描述**: 获取指定会话的详细信息
- **路径参数**:
  - `session_id`: 会话唯一标识符

- **响应示例**:

```json
{
    "session_id": "demo_session_1",
    "user_id": "user123",
    "conversation_id": "conv_789xyz",
    "last_activity": "2024-01-15T10:30:15.123456",
    "message_count": 5,
    "status": "active"
}
```

- **curl示例**:

```bash
curl "http://localhost:6001/session/my_session/info"
```

#### 3.2 清除会话

- **接口**: `POST /session/{session_id}/clear`
- **描述**: 清除指定会话的历史记录
- **路径参数**:
  - `session_id`: 会话唯一标识符

- **响应示例**:

```json
{
    "message": "会话已成功清除",
    "session_id": "demo_session_1",
    "cleared_at": "2024-01-15T10:35:00.123456"
}
```

- **curl示例**:

```bash
curl -X POST "http://localhost:6001/session/my_session/clear"
```

---

## Python客户端示例

### 基础聊天客户端

```python
import requests
import json

class CozeChatClient:
    def __init__(self, base_url="http://localhost:6001"):
        self.base_url = base_url
    
    def chat_sync(self, message, session_id=None):
        """同步聊天"""
        url = f"{self.base_url}/chat"
        data = {
            "message": message,
            "session_id": session_id
        }
        
        response = requests.post(url, json=data)
        response.raise_for_status()
        return response.json()
    
    def chat_stream(self, message, session_id=None):
        """流式聊天"""
        url = f"{self.base_url}/chat/stream"
        data = {
            "message": message,
            "session_id": session_id
        }
        
        response = requests.post(url, json=data, stream=True)
        response.raise_for_status()
        
        full_content = ""
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data = json.loads(line_str[6:])
                    if data['type'] == 'chunk':
                        content = data['data']['content']
                        print(content, end='', flush=True)
                        full_content += content
                    elif data['type'] == 'complete':
                        print("\n")
                        break
        return full_content

# 使用示例
client = CozeChatClient()

# 同步聊天
result = client.chat_sync("你好，我想聊聊工作压力")
print(f"回复: {result['response']}")

# 流式聊天
client.chat_stream("能给我一些缓解压力的建议吗？")
```

---

## 流式输出详细说明

### SSE事件类型

| 事件类型 | 描述 | 数据结构 |
|---------|------|----------|
| `chunk` | 数据块 | `{"type": "chunk", "data": {"content": "...", "chunk_index": 0}}` |
| `complete` | 完成 | `{"type": "complete", "data": {"total_chunks": 5, "full_content": "..."}}` |
| `error` | 错误 | `{"type": "error", "data": {"message": "错误信息"}}` |

### 前端JavaScript示例

```javascript
async function streamChat(message) {
    const response = await fetch('/chat/stream', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            message: message,
            session_id: 'web_session_1'
        })
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let fullContent = '';

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
            if (line.startsWith('data: ')) {
                try {
                    const data = JSON.parse(line.slice(6));
                    if (data.type === 'chunk') {
                        const content = data.data.content;
                        fullContent += content;
                        // 实时更新UI
                        updateChatDisplay(content, false);
                    } else if (data.type === 'complete') {
                        updateChatDisplay('', true);
                        console.log('完整回复:', fullContent);
                    }
                } catch (e) {
                    console.error('解析SSE数据失败:', e);
                }
            }
        }
    }
}
```

---

## 配置说明

### 环境变量配置

| 变量名 | 描述 | 默认值 | 必需 |
|--------|------|--------|------|
| `COZE_API_TOKEN` | Coze API访问令牌 | - | ✅ |
| `COZE_BOT_ID` | Coze机器人ID | - | ✅ |
| `COZE_USER_ID` | 用户标识 | `default_user` | ❌ |
| `COZE_BASE_URL` | API基础地址 | `https://api.coze.cn/v3` | ❌ |
| `SERVER_HOST` | 服务器监听地址 | `0.0.0.0` | ❌ |
| `SERVER_PORT` | 服务器端口 | `6001` | ❌ |
| `DEBUG` | 调试模式 | `false` | ❌ |

### 服务器配置

```python
SERVER_CONFIG = {
    'host': '0.0.0.0',           # 监听所有网卡
    'port': 6001,                # 端口号
    'debug': False,              # 调试模式
    'allowed_origins': ['*'],    # CORS允许源
    'max_request_size': 10485760 # 最大请求大小(10MB)
}
```

---

## 错误处理

### HTTP状态码

| 状态码 | 描述 | 解决方案 |
|--------|------|----------|
| 200 | 成功 | - |
| 400 | 请求参数错误 | 检查请求体格式和必需字段 |
| 500 | 服务器内部错误 | 查看服务器日志，检查Coze API配置 |
| 503 | 服务不可用 | 检查Coze API服务状态 |

### 错误响应格式

```json
{
    "detail": "错误描述信息"
}
```

### 常见错误

1. **Coze API认证失败**
   ```
   {"detail": "Coze API请求失败: 401 Unauthorized"}
   ```
   **解决方案**: 检查`COZE_API_TOKEN`是否正确

2. **Bot ID无效**
   ```
   {"detail": "Coze API请求失败: 400 Bad Request"}
   ```
   **解决方案**: 检查`COZE_BOT_ID`是否正确

3. **请求超时**
   ```
   {"detail": "同步聊天失败: timeout"}
   ```
   **解决方案**: 增加请求超时时间或检查网络连接

---

## 性能优化

### 并发处理

- 使用异步处理提高并发性能
- 支持多个同时进行的流式聊天会话
- 会话隔离，避免消息混淆

### 资源管理

- 自动管理会话映射和清理
- 流式响应减少内存占用
- 请求限流避免API调用过频

### 监控建议

1. **日志监控**: 查看`logs/api_server.log`
2. **性能指标**: 监控响应时间和并发数
3. **错误率**: 关注5xx错误出现频率
4. **资源使用**: 监控CPU和内存使用情况

---

## 最佳实践

### 1. 会话管理

```python
# 使用固定session_id维持对话上下文
session_id = "user_session_123"

# 第一轮对话
response1 = client.chat_sync("你好", session_id)
# 第二轮对话（自动使用上下文）
response2 = client.chat_sync("我刚才说了什么？", session_id)
```

### 2. 流式处理

```python
# 前端实时显示
def process_stream(response):
    for chunk in response.iter_lines():
        if chunk:
            data = json.loads(chunk.decode('utf-8')[6:])
            if data['type'] == 'chunk':
                display_chunk(data['data']['content'])
```

### 3. 错误重试

```python
import time
import random

def retry_request(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(2 ** attempt + random.uniform(0, 1))
```

### 4. 超时配置

```python
# 同步请求超时
requests.post(url, json=data, timeout=60)

# 流式请求不设超时，但要有结束条件
response = requests.post(url, json=data, stream=True, timeout=None)
```

---

## 更新日志

### v1.0.0 (2024-01-15)

- 🎉 首次发布
- ✨ 支持同步和流式聊天
- 🔧 完整的会话管理功能
- 📖 自动化API文档
- 🚀 基于FastAPI的高性能实现
- 🔄 实时SSE流式输出
- 🛡️ 完善的错误处理机制

---

## 技术支持

- **API文档**: `http://localhost:6001/docs`
- **健康检查**: `http://localhost:6001/health`
- **日志文件**: `logs/api_server.log`
- **配置示例**: `.env.example`

---

*本文档版本: v1.0.0*  
*最后更新: 2024年1月15日*