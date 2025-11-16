# 📝 **Coze Health Agent 后端对接接口文档（正式版 · 服务端权威版本）**

**Version:** 2.0
 **Author:** Miya
 **Description:**
 本接口文档专为**后端（服务器）对接使用**，后端通过本地 Python 模块（基于 test2.py）调用 Coze Health Agent，与前端解耦。文档包含：

- 调用 Agent 的服务端函数接口
- Coze API（chat + streaming）完整规范
- 返回字段说明
- 语音合成 API
- 会话管理要求
- 后端应封装给前端的最终 API 结构

------

# 1. 基本信息

### **Base URL**

```
https://api.coze.cn
```

### **Authorization**

必须在 Header 中携带：

```
Authorization: Bearer <COZE_API_KEY>
```

------

# 2. 服务端本地调用方式（你的脚本提供的接口）

后端无需直接访问 Coze，只需要调用脚本中的唯一函数：

## ✔ `call_agent(user_input: str, stream=True) -> (reply: str, streamed: bool)`

示例：

```
from test2 import call_agent

reply, streamed = call_agent("I feel tired today")
```

返回：

| 字段         | 类型   | 说明                                                     |
| ------------ | ------ | -------------------------------------------------------- |
| **reply**    | string | Agent 的完整回复文本（自动拼接、多轮上下文、emoji 修复） |
| **streamed** | bool   | 是否成功使用流式输出（后端不用处理该字段）               |

⚠ **后端只需要使用 reply 作为最终结果返回给前端。**

------

# 3. Coze Chat API 规范（脚本内部自动调用，后端无需手写）

脚本内部会向 Coze 发起如下 API 请求：

## **POST /open_api/v2/chat**

------

## 3.1 Headers

| Header        | 必填 | 说明             |
| ------------- | ---- | ---------------- |
| Authorization | 是   | Bearer + API_KEY |
| Content-Type  | 是   | application/json |

------

## 3.2 Request Body（由你的脚本自动构造）

```
{
  "conversation_id": "22f1a13a-xxx-xxx",
  "bot_id": "7559087768224432170",
  "user": "Miya",
  "query": "用户输入内容",
  "chat_history": [...],
  "stream": true
}
```

### 字段说明

| 字段            | 类型   | 必填 | 说明                   |
| --------------- | ------ | ---- | ---------------------- |
| conversation_id | string | 是   | 会话 ID，脚本自动固定  |
| bot_id          | string | 是   | Coze Agent ID          |
| user            | string | 否   | 显示用用户名           |
| query           | string | 是   | 用户当前输入           |
| chat_history    | list   | 是   | 多轮上下文，由脚本维护 |
| stream          | bool   | 是   | true = 流式输出        |

后端无需处理这些字段。

------

# 4. Coze API 响应规范（脚本自动解析）

## **4.1 普通模式（stream = false）**

返回结构示例：

```
{
  "messages": [
    {
      "type": "answer",
      "content": "这是完整回复"
    }
  ]
}
```

解析逻辑（脚本自动实现）：

```
reply = messages[0].content
```

------

## **4.2 流式模式（stream = true）**

流式输出使用 SSE，每一行格式如下：

```
data: {JSON_OBJECT}
```

示例：

```
data: {"msg_type":"answer","message":{"type":"answer","content":"你好"}}
data: {"msg_type":"answer","message":{"type":"answer","content":"，我可以帮你改善睡眠。"}}
data: [DONE]
```

### 字段说明

| 字段路径        | 类型   | 说明             |
| --------------- | ------ | ---------------- |
| msg_type        | string | 必须是 "answer"  |
| message.type    | string | 必须是 "answer"  |
| message.content | string | 当前片段，需拼接 |

你的脚本会自动拼接并执行乱码修复：

```
final_reply = "".join(all_chunks)
```

后端只需接收最终 `reply`。

------

# 5. 会话管理规范（脚本自动完成）

### ✔ 会话 ID：

```
conversation_id = uuid.uuid4()
```

由脚本生成并在运行期间保持不变。

### ✔ chat_history：

脚本内维护形式如下：

```
{
  "role": "user" / "assistant",
  "content": "文本",
  "content_type": "text"
}
```

后端无需持久化，也无需传输 history。

------

# 6. 语音合成 API（可选功能）

## **POST /v1/audio/speech**

请求体：

```
{
  "input": "文本",
  "voice_id": "7468512265151692827",
  "response_format": "mp3"
}
```

返回：`MP3 二进制数据`

脚本中：

- 默认生成本地临时音频文件
- 自动播放（适用于 CLI）
- 不会返回给前端（除非你修改）

如需给前端播放语音，后端可修改脚本为：

```
synthesize_speech(reply, output_file="static/audio/xxx.mp3")
```

然后在 API 返回：

```
{
  "reply": "...",
  "audio_url": "/static/audio/xxx.mp3"
}
```

------

# 7. 后端应封装给前端的 API（建议）

后端只需暴露一个端点，例如：

## ✔ **POST /agent/chat**

### Request（前端 → 后端）

```
{
  "message": "I feel tired today"
}
```

### Response（后端 → 前端）

```
{
  "reply": "I'm sorry to hear that you're feeling tired..."
}
```

⚠ **前端不需要 chat_history，不需要 conversation_id，不需要流式解析，不需要语音处理。**

所有复杂逻辑在 physical-main.py 内处理完毕。

------

# 8. 后端调用示例

```
from flask import request
from test2 import call_agent

@app.post("/agent/chat")
def chat():
    user_input = request.json.get("message", "")
    reply, _ = call_agent(user_input)
    return {"reply": reply}
```

------

# 9. 错误处理规范

脚本可能返回的错误（均为字符串形式）：

| 类型       | 文本示例                             |
| ---------- | ------------------------------------ |
| 网络错误   | `"❌ Network error: ..."`             |
| 状态码错误 | `"❌ Request failed: 500 - ..."`      |
| 空内容     | `"⚠️ Agent didn’t return a message."` |

后端建议：
 直接原样返回给前端，用于 UI 提示。

------

# 10. 最终给后端的 TL;DR（可直接发给他们）

> **你们只需要调用 `call_agent(message)`，它会返回一个字符串 `reply`，这是最终 AI 回复。
> 会话管理、流式解析、历史上下文、语音、emoji 修复全部由脚本封装完成，不需要额外开发。
> 后端只需将 reply 返回给前端即可。**

