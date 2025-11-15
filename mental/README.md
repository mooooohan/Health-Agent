# 心理聊天机器人项目

基于Coze API的心理健康聊天机器人，具备情绪识别、专业建议、长期记忆等功能。

## 🌟 功能特性

### 核心功能
- **智能对话**: 基于Coze API的自然语言理解和生成
- **情绪识别**: 实时分析用户情绪状态
- **专业建议**: 提供基于心理学原理的建议
- **表情回复**: 根据情绪生成合适的表情符号
- **语音回复**: 生成带情绪的语音回复
- **数据存储**: 存储对话和情绪数据到数据库
- **长期记忆**: 总结上下文信息，提供个性化服务
- **多轮对话**: 支持连续的多轮对话
- **流式响应**: 支持流式API调用

### 技术特性
- **异步处理**: 基于asyncio的高性能异步处理
- **Web API**: RESTful API和WebSocket接口
- **数据持久化**: SQLite数据库存储对话数据
- **长期记忆**: 智能记忆管理和检索
- **可扩展性**: 模块化设计，易于扩展

## 🚀 快速开始

### 环境要求
- Python 3.8+
- SQLite3
- 网络连接（用于Coze API）

### 安装依赖
```bash
pip install -r requirements.txt
```

### 配置环境变量
1. 复制环境变量模板：
```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，填入你的Coze API配置（推荐使用SDK令牌）：
```env
# Coze API配置
COZE_BOT_ID=your_bot_id_here
COZE_USER_ID=your_user_id_here
COZE_API_KEY=your_api_key_here
COZE_API_SECRET=your_api_secret_here
COZE_API_TOKEN=your_token_here  # 使用TokenAuth启用SDK流式
```

说明：
- 当设置 `COZE_API_TOKEN` 时，系统优先使用官方 `cozepy` SDK 的 TokenAuth 并走 CN 域名流式接口；未设置时回退到HTTP签名方式（可能受限且不保证稳定）。
  
CN域名与端点：
- `BASE_URL_HTTP`: `https://api.coze.cn/open_api/v2`（HTTP接口）
- `BASE_URL_SDK`: `https://api.coze.cn`（SDK基址）

### 运行服务
```bash
# 启动API服务器
python api_server.py

# 或使用uvicorn直接启动
uvicorn api_server:app --host 0.0.0.0 --port 6001 --reload
```

服务启动后，访问 http://localhost:6001/docs 查看API文档。

## 📋 API使用指南

### 基础聊天接口

#### 同步模式
```python
import requests

# 发送聊天消息
response = requests.post(
    "http://localhost:6001/chat",
    json={
        "user_id": "user123",
        "message": "我今天感觉很焦虑",
        "session_id": "session123"  # 可选
    }
)

result = response.json()
print(f"回复: {result['response']}")
print(f"情绪分析: {result['emotion_analysis']}")
print(f"专业建议: {result['professional_advice']}")
```

#### 流式模式
```python
import requests
import json

# 流式响应
response = requests.post(
    "http://localhost:6001/chat/stream",
    json={
        "user_id": "user123",
        "message": "我今天感觉很焦虑",
        "session_id": "session123"
    },
    stream=True
)

for line in response.iter_lines():
    if line:
        data = json.loads(line.decode('utf-8').replace('data: ', ''))
        if data['type'] == 'response_chunk':
            print(data['data']['content'], end='', flush=True)
        elif data['type'] == 'additional_info':
            print(f"\n额外信息: {data['data']}")
```

#### 使用官方SDK进行流式（CN域名）
```python
from cozepy import Coze, TokenAuth, COZE_CN_BASE_URL, Message, ChatEventType

coze = Coze(auth=TokenAuth(token="<YOUR_TOKEN>"), base_url=COZE_CN_BASE_URL)

for event in coze.chat.stream(
    bot_id="<YOUR_BOT_ID>",
    user_id="<YOUR_USER_ID>",
    additional_messages=[Message.build_user_question_text("Tell a 500-word story.")],
):
    if event.event == ChatEventType.CONVERSATION_MESSAGE_DELTA:
        print(event.message.content, end="", flush=True)
```

### WebSocket接口
```python
import websocket
import json

def on_message(ws, message):
    data = json.loads(message)
    if data['type'] == 'response_chunk':
        print(data['data']['content'], end='', flush=True)
    elif data['type'] == 'additional_info':
        print(f"\n额外信息: {data['data']}")

def on_open(ws):
    # 发送消息
    message = {
        "user_id": "user123",
        "message": "我今天感觉很焦虑",
        "session_id": "session123"
    }
    ws.send(json.dumps(message))

ws = websocket.WebSocketApp(
    "ws://localhost:6001/ws/chat",
    on_message=on_message,
    on_open=on_open
)
ws.run_forever()
```

### 会话管理
```python
# 获取会话信息
response = requests.get("http://localhost:6001/session/session123")
session_info = response.json()
print(f"会话状态: {session_info}")

# 关闭会话
response = requests.post("http://localhost:6001/session/session123/close")
print(f"关闭结果: {response.json()}")
```

### 用户统计
```python
# 获取用户统计
response = requests.get("http://localhost:6001/user/user123/stats")
user_stats = response.json()
print(f"用户统计: {user_stats}")

# 获取记忆统计
response = requests.get("http://localhost:6001/user/user123/memories")
memory_stats = response.json()
print(f"记忆统计: {memory_stats}")
```

## 📁 项目结构

```
psychology-chatbot/
├── api_server.py              # Web API服务器
├── chatbot_agent.py           # 聊天机器人Agent
├── coze_client.py             # Coze API客户端
├── emotion_analyzer.py        # 情绪分析器
├── database_manager.py        # 数据库管理器
├── long_term_memory.py        # 长期记忆管理器
├── config.py                  # 配置文件
├── requirements.txt           # 依赖包
├── .env.example               # 环境变量模板
├── README.md                  # 项目文档
├── data/                      # 数据目录
│   ├── conversations.db       # 对话数据库
│   └── long_term_memory.db    # 长期记忆数据库
├── logs/                      # 日志目录
├── audio/                     # 语音文件目录
└── temp/                      # 临时文件目录
```

## ⚙️ 配置说明

### Coze API配置
在 `config.py` 中配置Coze API参数：
```python
COZE_CONFIG = {
    "bot_id": os.getenv("COZE_BOT_ID"),
    "user_id": os.getenv("COZE_USER_ID"),
    "api_key": os.getenv("COZE_API_KEY"),
    "api_secret": os.getenv("COZE_API_SECRET"),
    "API_TOKEN": os.getenv("COZE_API_TOKEN", ""),
    "BASE_URL_HTTP": "https://api.coze.cn/open_api/v2",
    "BASE_URL_SDK": "https://api.coze.cn"
}
```

### 集成指南（摘要）
- 调用REST接口：参考上文 `/chat` 与 `/chat/stream` 示例。
- 使用SDK直连：设置 `COZE_API_TOKEN` 并参考“使用官方SDK进行流式”。
- 直接模块集成：可导入 `chatbot_agent.py` 与 `coze_client.py` 在你的项目中使用。

更多集成示例与高级模式已合并到本README，原《心理Agent集成指南.md》和《项目结构说明.md》内容已并入并保持简洁。

### 数据库配置
```python
DATABASE_CONFIG = {
    "conversations_db": "data/conversations.db",
    "long_term_memory_db": "data/long_term_memory.db"
}
```

### 服务器配置
```python
SERVER_CONFIG = {
    "host": "0.0.0.0",
    "port": 6001,
    "debug": False,
    "allowed_origins": ["*"]
}
```

## 🔧 高级功能

### 自定义情绪分析
```python
from emotion_analyzer import EmotionAnalyzer

analyzer = EmotionAnalyzer(coze_client)
emotion = analyzer.analyze_emotion("我今天很开心", use_coze=True)
print(f"情绪: {emotion.emotion}, 强度: {emotion.intensity}")
```

### 长期记忆管理
```python
from long_term_memory import LongTermMemoryManager

memory_manager = LongTermMemoryManager()

# 保存记忆
memory_manager.save_memory(memory_item)

# 获取相关记忆
memories = memory_manager.get_relevant_memories("user123", "工作焦虑")

# 生成上下文摘要
summary = memory_manager.generate_context_summary(
    user_id="user123",
    session_id="session123",
    conversation_history=[...],
    emotion_history=[...]
)
```

### 数据库操作
```python
from database_manager import DatabaseManager

db_manager = DatabaseManager()

# 保存对话记录
db_manager.save_conversation(conversation_record)

# 获取用户对话历史
conversations = db_manager.get_user_conversations("user123", limit=10)

# 获取情绪数据
emotions = db_manager.get_user_emotions("user123", limit=10)
```

## 🐳 Docker部署

### 构建镜像
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 6001

CMD ["python", "api_server.py"]
```

### 运行容器
```bash
# 构建镜像
docker build -t psychology-chatbot .

# 运行容器
docker run -d \
  --name psychology-chatbot \
  -p 6001:6001 \
  -e COZE_BOT_ID=your_bot_id \
  -e COZE_USER_ID=your_user_id \
  -e COZE_API_KEY=your_api_key \
  -e COZE_API_SECRET=your_api_secret \
  psychology-chatbot
```

## 📊 监控和日志

### 日志配置
日志文件保存在 `logs/` 目录下：
- `api_server.log` - API服务器日志
- `chatbot_agent.log` - 聊天机器人日志
- `coze_client.log` - Coze API客户端日志

### 健康检查
```bash
# 检查服务健康状态
curl http://localhost:6001/health
```

### 性能监控
可以通过日志分析工具监控API响应时间、错误率等指标。

## 🔒 安全注意事项

1. **API密钥保护**: 妥善保管Coze API密钥，不要提交到代码仓库
2. **用户数据保护**: 对话数据包含敏感信息，需要适当的访问控制
3. **输入验证**: API接口有输入验证，防止恶意输入
4. **错误处理**: 完善的错误处理机制，避免泄露敏感信息

## 🆘 故障排除

### 常见问题

#### Coze API调用失败
- 检查API密钥是否正确
- 检查网络连接
- 查看日志文件获取详细错误信息

#### 数据库连接失败
- 确保 `data/` 目录有写入权限
- 检查磁盘空间

#### 语音生成失败
- 检查音频文件目录权限
- 确保Coze API支持语音生成功能

### 调试模式
启动服务时添加 `--debug` 参数启用调试模式：
```bash
python api_server.py --debug
```

## 📞 支持

如有问题，请：
1. 查看日志文件获取错误信息
2. 检查配置文件是否正确
3. 确保所有依赖已正确安装

## 📄 许可证

MIT License
## 🙏 致谢

- Coze API提供强大的AI能力
- 开源社区提供的优秀库和工具
