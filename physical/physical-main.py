import json
import os
import platform
import subprocess
import tempfile
import uuid
from datetime import datetime
from typing import Optional

import requests

# === 1️⃣ Coze API 配置 ===
API_KEY = os.getenv("COZE_API_KEY", "pat_DyjwNAuK4thhVGMDE7WusSNFPFYwfiEEwYOs7WbOoZ9QJjNpXoQXPkNERk2Ld2aO")
BOT_ID = "7559087768224432170"  # 你的 Coze Agent ID
BASE_URL = "https://api.coze.cn/open_api/v2/chat"

# === 🔊 语音合成配置（沿用 Coze 语音 API）===
VOICE_ID = os.getenv("COZE_VOICE_ID", "7468512265151692827")
SPEECH_URL = "https://api.coze.cn/v1/audio/speech"

# === 2️⃣ 请求头 ===
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

# === 3️⃣ 生成唯一会话ID（多轮对话保持一致） ===
conversation_id = str(uuid.uuid4())  # 每次启动脚本生成新的会话ID，可改为固定值保持长期记忆

# === 🧠 新增：全局缓存用户个人信息 ===
user_profile = {
    "context": ""
}

# === 4️⃣ 语音合成相关 ===
def _auto_play_audio(file_path: str) -> bool:
    """Try to play the generated audio automatically on the current OS."""

    def try_command(command):
        try:
            subprocess.run(command, check=False)
            return True
        except FileNotFoundError:
            return False

    system = platform.system()

    if system == "Darwin":
        if try_command(["afplay", file_path]):
            print("🎵 正在自动播放音频...")
            return True
        if try_command(["open", file_path]):
            print("🎵 正在自动播放音频...")
            return True
    elif system == "Windows":
        try:
            os.startfile(file_path)
            print("🎵 正在自动播放音频...")
            return True
        except OSError:
            return False
    else:
        if try_command(["xdg-open", file_path]):
            print("🎵 正在自动播放音频...")
            return True

    print("⚠️ 自动播放失败，请手动播放该文件。")
    return False


def synthesize_speech(text: str, output_file: Optional[str] = None) -> None:
    """Call Coze speech API and auto play reply audio without persisting files."""
    clean_text = text.strip()
    if not clean_text:
        return

    headers_voice = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    body = {
        "input": clean_text,
        "voice_id": VOICE_ID,
        "response_format": "mp3"
    }

    try:
        response = requests.post(SPEECH_URL, headers=headers_voice, json=body, timeout=30)
    except requests.exceptions.RequestException as exc:
        print(f"⚠️ 语音合成网络异常：{exc}")
        return

    if response.status_code != 200:
        print(f"⚠️ 语音合成失败：{response.status_code} - {response.text}")
        return

    temp_path = None

    try:
        target_path = output_file
        if not target_path:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            temp_path = tmp.name
            tmp.close()
            target_path = temp_path

        with open(target_path, "wb") as f:
            f.write(response.content)
        if output_file:
            print(f"🎧 音频已保存：{output_file}")
        else:
            print("🎧 临时音频已生成，正在播放...")
    except OSError as exc:
        print(f"⚠️ 写入音频文件失败：{exc}")
        if temp_path:
            try:
                os.remove(temp_path)
            except OSError:
                pass
        return

    played = _auto_play_audio(target_path)

    if not output_file and temp_path:
        try:
            if played:
                os.remove(temp_path)
            else:
                print(f"ℹ️ 已保留临时音频文件：{temp_path}")
        except OSError as exc:
            print(f"⚠️ 无法删除临时音频文件：{exc}")


# === 5️⃣ 发送对话函数 ===
def call_agent(user_input, stream=True):
    global user_profile

    # === 检测是否包含用户个人信息关键词 ===
    keywords = ["year", "old", "sleep", "stress", "male", "female", "woman", "man"]
    if any(k in user_input.lower() for k in keywords):
        user_profile["context"] = user_input

    if user_profile["context"] and not any(k in user_input.lower() for k in keywords):
        full_input = user_profile["context"] + " " + user_input
    else:
        full_input = user_input

    base_payload = {
        "conversation_id": conversation_id,
        "bot_id": BOT_ID,
        "user": "Miya",
        "query": full_input,
    }

    if stream:
        ok, reply_or_error = _stream_agent_response({**base_payload, "stream": True})
        if ok:
            return reply_or_error, True
        print("⚠️ 流式输出失败，改用普通模式。\n")
        fallback = _request_agent_response({**base_payload, "stream": False})
        return fallback, False

    return _request_agent_response({**base_payload, "stream": False}), False


def _request_agent_response(payload):
    try:
        response = requests.post(BASE_URL, headers=headers, data=json.dumps(payload), timeout=60)
        if response.status_code != 200:
            return f"❌ Request failed: {response.status_code} - {response.text}"

        res = response.json()
        messages = res.get("messages", [])

        if os.getenv("DEBUG_Coze", "0") == "1":
            print("\n[DEBUG] Full response JSON:")
            print(json.dumps(res, indent=2, ensure_ascii=False))
            print("\n")

        for msg in messages:
            if msg.get("type") == "answer":
                content = msg.get("content", "").strip()
                if content:
                    return content

        return "⚠️ Agent didn’t return a message. This may happen if the model timed out or your input triggered a filter."

    except requests.exceptions.RequestException as e:
        return f"❌ Network error: {e}"
    except json.JSONDecodeError:
        return f"❌ Response JSON parse error: {response.text[:200]}"
    except Exception as e:
        return f"❌ Unexpected error: {e}"


def _stream_agent_response(payload):
    try:
        response = requests.post(
            BASE_URL,
            headers=headers,
            data=json.dumps(payload),
            stream=True,
            timeout=60,
        )
    except requests.exceptions.RequestException as e:
        return False, f"❌ Network error: {e}"

    if response.status_code != 200:
        return False, f"❌ Request failed: {response.status_code} - {response.text}"

    reply_parts = []
    print("Agent: ", end="", flush=True)

    for raw_line in response.iter_lines(decode_unicode=True):
        if not raw_line:
            continue

        line = raw_line.strip()
        if line.startswith("data:"):
            line = line[len("data:") :].strip()

        if not line or line == "[DONE]":
            continue

        text_piece = _extract_text_from_stream_payload(line)
        if not text_piece:
            continue

        reply_parts.append(text_piece)
        print(text_piece, end="", flush=True)

    print()

    combined = "".join(reply_parts).strip()
    if combined:
        return True, combined
    return False, "⚠️ Agent didn’t send stream chunks."


def _extract_text_from_stream_payload(payload_str: str) -> Optional[str]:
    try:
        payload_json = json.loads(payload_str)
    except json.JSONDecodeError:
        # 保留原文本作为兜底，避免丢失真正的内容
        return payload_str

    # Try typical Coze message schema
    msg_type = payload_json.get("msg_type")
    if msg_type and msg_type not in {"answer"}:
        return None

    message = payload_json.get("message")
    if isinstance(message, dict):
        if message.get("type") and message.get("type") != "answer":
            return None
        content = message.get("content")
        if isinstance(content, str) and content:
            return content
        if isinstance(content, list):
            pieces = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    pieces.append(block.get("text", ""))
                elif isinstance(block, str):
                    pieces.append(block)
            return "".join(pieces).strip() or None

    # Fallback to looking for generic text fields.
    for key in ("content", "text", "delta"):
        value = payload_json.get(key)
        if isinstance(value, str) and value.strip():
            return value
        if isinstance(value, dict):
            inner_text = value.get("content") or value.get("text")
            if isinstance(inner_text, str) and inner_text.strip():
                return inner_text

    if isinstance(payload_json, str):
        return payload_json

    return None

# === 6️⃣ 保存聊天记录 ===
def save_chat_log(user_input, agent_reply):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("chat_history.txt", "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}]\nYou: {user_input}\nAgent: {agent_reply}\n\n")

# === 7️⃣ 主循环 ===
if __name__ == "__main__":
    print("💬 Coze Health Agent")
    # 输入 exit 或 quit 结束会话

    while True:
        try:
            user_input = input("You: ").strip()
            if user_input.lower() in ["exit", "quit"]:
                print("👋 Session ended，Goodbye！")
                break

            if not user_input:
                print("⚠️ Please enter your message before pressing Enter.\n")
                continue

            reply, streamed = call_agent(user_input, stream=True)
            if not streamed:
                print(f"Agent: {reply}\n")
            else:
                print()

            # 朗读回复
            synthesize_speech(reply)

            # 保存聊天记录
            save_chat_log(user_input, reply)

        except KeyboardInterrupt:
            print("\n👋 Session interrupted by user")
            break
        except Exception as e:
            print(f"❌ Unexpected error in main loop:{e}")
