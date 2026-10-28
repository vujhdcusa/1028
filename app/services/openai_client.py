"""OpenAI 備援：Gemini 額度或連線暫時不可用時，讓 Agent 繼續完成工作。

只由 ``gemini_client`` 呼叫，對上層維持相同的工具呼叫格式；因此學生與導師
不需要知道目前是哪一個模型回覆。金鑰一律只讀取本機 .env。
"""

import json
import urllib.error
import urllib.request

from flask import current_app


API_URL = "https://api.openai.com/v1/chat/completions"


def ready():
    config = current_app.config
    return bool(config.get("AI_ENABLED") and config.get("OPENAI_API_KEY"))


def _request(payload, opener=urllib.request.urlopen):
    if not ready():
        # 延後 import，避免 Gemini client 與這個備援模組循環引用。
        from app.services.gemini_client import AIUnavailable
        raise AIUnavailable("目前沒有可用的備援 AI，請稍後再試或洽系統管理員。")
    request = urllib.request.Request(
        API_URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {current_app.config['OPENAI_API_KEY']}"},
        method="POST",
    )
    try:
        with opener(request, timeout=120) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        from app.services.gemini_client import AIUnavailable
        if exc.code == 429:
            raise AIUnavailable("AI 服務目前額度暫滿，請稍後再試。") from None
        if exc.code in (400, 401, 403):
            raise AIUnavailable("備援 AI 金鑰無效或沒有權限，請洽系統管理員。") from None
        raise AIUnavailable(f"備援 AI 回應錯誤（HTTP {exc.code}），請稍後再試。") from None
    except (urllib.error.URLError, TimeoutError):
        from app.services.gemini_client import AIUnavailable
        raise AIUnavailable("連不到備援 AI，請確認網路後再試一次。") from None


def _tools(declarations):
    return [{"type": "function", "function": {
        "name": item["name"], "description": item["description"],
        "parameters": item.get("parameters", {"type": "object", "properties": {}}),
    }} for item in declarations]


def _messages(contents, instruction):
    """把現有 Gemini 對話格式轉為 OpenAI 的 tool-call 格式。"""
    messages, pending = [{"role": "system", "content": instruction}], []
    call_no = 0
    for content in contents:
        role, parts = content.get("role", "user"), content.get("parts", [])
        texts = [part.get("text", "") for part in parts if part.get("text")]
        calls = [part["functionCall"] for part in parts if "functionCall" in part]
        replies = [part["functionResponse"] for part in parts if "functionResponse" in part]
        if calls:
            tool_calls = []
            for call in calls:
                call_no += 1
                call_id = f"tool_{call_no}"
                pending.append((call.get("name", ""), call_id))
                tool_calls.append({"id": call_id, "type": "function", "function": {
                    "name": call.get("name", ""), "arguments": json.dumps(call.get("args") or {}, ensure_ascii=False),
                }})
            messages.append({"role": "assistant", "content": "\n".join(texts) or None, "tool_calls": tool_calls})
        elif replies:
            for reply in replies:
                name = reply.get("name", "")
                match = next((item for item in pending if item[0] == name), None)
                if match:
                    pending.remove(match)
                    call_id = match[1]
                else:
                    call_no += 1
                    call_id = f"tool_{call_no}"
                messages.append({"role": "tool", "tool_call_id": call_id,
                                 "content": json.dumps(reply.get("response", {}).get("result", {}), ensure_ascii=False)})
        elif texts:
            messages.append({"role": "assistant" if role == "model" else "user", "content": "\n".join(texts)})
    return messages


def chat(contents, declarations, system_instruction, opener=urllib.request.urlopen):
    """回傳 Gemini 相容的 content：文字或 functionCall。"""
    payload = _request({
        "model": current_app.config.get("OPENAI_ASSISTANT_MODEL", "gpt-4.1-mini"),
        "messages": _messages(contents, system_instruction),
        "tools": _tools(declarations),
        "tool_choice": "auto",
        "temperature": 0.3,
    }, opener)
    try:
        message = payload["choices"][0]["message"]
    except (KeyError, IndexError):
        from app.services.gemini_client import AIUnavailable
        raise AIUnavailable("備援 AI 這次沒有產生回答，請換個方式再問一次。") from None
    parts = []
    if message.get("content"):
        parts.append({"text": message["content"]})
    for call in message.get("tool_calls") or []:
        try:
            args = json.loads(call["function"].get("arguments") or "{}")
        except json.JSONDecodeError:
            args = {}
        parts.append({"functionCall": {"name": call["function"].get("name", ""), "args": args}})
    return {"role": "model", "parts": parts}


def generate_json(prompt, schema, files=None, opener=urllib.request.urlopen):
    """JSON 擷取的備援；目前文字簡章可直接切換，附件檔案維持 Gemini 處理。"""
    if files:
        from app.services.gemini_client import AIUnavailable
        raise AIUnavailable("這份附件需要 Gemini 處理；Gemini 恢復後再試一次。")
    payload = _request({
        "model": current_app.config.get("OPENAI_MODEL", "gpt-4.1-mini"),
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_schema", "json_schema": {"name": "agent_result", "strict": False, "schema": schema}},
        "temperature": 0.3,
    }, opener)
    try:
        return json.loads(payload["choices"][0]["message"]["content"])
    except (KeyError, IndexError, TypeError, json.JSONDecodeError):
        from app.services.gemini_client import AIUnavailable
        raise AIUnavailable("備援 AI 回傳的格式不正確，請再試一次。") from None
