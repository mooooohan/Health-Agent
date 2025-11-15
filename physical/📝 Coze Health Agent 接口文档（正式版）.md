# 📝 **Coze Health Agent 接口文档（正式版）**

**Version:** 1.0
 **Author:** Miya
 **Description:**
 本接口用于客户端（前端/后端）调用自定义的 Coze Health Agent，实现多轮对话能力，以及可选的语音合成功能。

------

# 1. 基本信息

### **Base URL**

```
https://api.coze.cn
```

### **Authentication**

所有请求均需携带 API Key：

```
Authorization: Bearer <COZE_API_KEY>
```

------

# 2. Chat 接口（核心）

## **POST /open_api/v2/chat**

用于向 Coze Agent 发送用户输入，并获得模型回复。支持 **普通响应** 和 **流式响应（SSE）**。

------

## 2.1 **请求头（Headers）**

| Header        | 必填 | 说明                  |
| ------------- | ---- | --------------------- |
| Authorization | 是   | Bearer + COZE_API_KEY |
| Content-Type  | 是   | application/json      |

------

## 2.2 **请求体（Request Body）**

```
{
  "conversation_id": "string",
  "bot_id": "7559087768224432170",
  "user": "Miya",
  "query": "用户输入内容",
  "stream": true
}
```

### 字段说明

| 字段名          | 类型   | 必填 | 说明                                  |
| --------------- | ------ | ---- | ------------------------------------- |
| conversation_id | string | 是   | 每个会话固定一个 ID，用于多轮对话记忆 |
| bot_id          | string | 是   | Coze 后台的 Agent ID                  |
| user            | string | 可选 | 自定义用户名                          |
| query           | string | 是   | 用户输入                              |
| stream          | bool   | 可选 | 是否启用流式输出（SSE），默认 false   |

------

# 3. 响应规范

## 3.1 **普通模式（stream = false）**

### **响应示例**

```
{
  "messages": [
    {
      "type": "answer",
      "content": "这是完整的回复内容"
    }
  ]
}
```

### **字段说明**

| 字段路径            | 类型   | 说明             |
| ------------------- | ------ | ---------------- |
| messages[i].type    | string | 固定为 "answer"  |
| messages[i].content | string | 模型完整回复文本 |

------

## 3.2 **流式模式（stream = true）**

流式输出使用 SSE，每行格式如下：

```
data: {JSON_OBJECT}
```

示例：

```
data: {"msg_type":"answer","message":{"type":"answer","content":"你好"}}
data: {"msg_type":"answer","message":{"type":"answer","content":"，我可以为你提供帮助。"}}
data: [DONE]
```

### 字段说明

| 字段路径        | 类型   | 说明                     |
| --------------- | ------ | ------------------------ |
| msg_type        | string | 必须为 `"answer"`        |
| message.type    | string | 必须为 `"answer"`        |
| message.content | string | 当前分片文本（需要拼接） |

前端/后端应把所有 `message.content` 拼接成完整回复。

------

# 4. 返回内容处理规范

## 普通模式

```
reply = messages[0].content
```

## 流式模式

将每个 data 事件中的：

```
message.content
```

拼接为：

```
final_reply = "".join(all_chunks)
```

最终返回给前端显示。

------

# 5. 会话管理规范

- 前端或后端需生成唯一 `conversation_id`（如 UUID）
- 同一用户会话中必须 **保持 conversation_id 不变**
- 否则 Coze 将无法维持上下文

示例：

```
conversation_id = "b97a5f90-9c1d-4fbf-ac0d-3fa81d7caa4e"
```

前端可在 localStorage 或 session 中保存。

------

# 6. 语音合成（可选）

## **POST /v1/audio/speech**

生成语音的 API。

### 请求头

```
Authorization: Bearer <COZE_API_KEY>
Content-Type: application/json
```

### 请求体

```
{
  "input": "要转成语音的文本",
  "voice_id": "7468512265151692827",
  "response_format": "mp3"
}
```

### 响应

直接返回二进制音频内容（mp3）。

后端只要返回 mp3 文件给前端即可，前端可自行播放。

------

# 7. 示例代码（后端）

以下为一个可直接用的流式解析示例：

```
import requests
import json

def call_coze(query, conversation_id):
    url = "https://api.coze.cn/open_api/v2/chat"
    headers = {
        "Authorization": f"Bearer {COZE_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "conversation_id": conversation_id,
        "bot_id": "7559087768224432170",
        "user": "Miya",
        "query": query,
        "stream": True
    }

    resp = requests.post(url, headers=headers, json=payload, stream=True)

    final = ""

    for line in resp.iter_lines():
        if not line:
            continue
        if not line.startswith(b"data:"):
            continue

        data = line[len(b"data:"):].strip()
        if data == b"[DONE]":
            break

        j = json.loads(data)
        msg = j.get("message", {})
        piece = msg.get("content", "")
        final += piece

    return final
```

------

# 8. 前端接收流式响应示例（SSE）

```
const response = await fetch(url, {
  method: "POST",
  headers,
  body: JSON.stringify(payload)
});

const reader = response.body.getReader();
let result = "";

while (true) {
  const { value, done } = await reader.read();
  if (done) break;

  const text = new TextDecoder().decode(value);
  const lines = text.split("\n");

  for (const line of lines) {
    if (line.startsWith("data:")) {
      const jsonStr = line.replace("data:", "").trim();
      if (jsonStr === "[DONE]") continue;

      const data = JSON.parse(jsonStr);
      const chunk = data.message?.content || "";
      result += chunk;

      // 即时显示
      appendToUI(chunk);
    }
  }
}
```

------

# 9. 项目中真实需要你告诉后端的内容（总结）

**后端仅需关注以下 4 个字段：**

| 字段                | 说明           |
| ------------------- | -------------- |
| conversation_id     | 多轮对话上下文 |
| query               | 用户输入       |
| message.content     | 回复文本片段   |
| messages[i].content | 普通模式结果   |