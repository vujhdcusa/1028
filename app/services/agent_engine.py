"""升學 Agent 共用引擎：一個引擎、多組工具（規格 AI_設計規格_Agent分工規劃_2026-10-22.md 第〇節）。

流程：決定下一步 → 後端執行工具 → 把結果交回 → 再決定，最多 max_steps 次。
- 決定下一步的有兩種：AiDecider（Gemini 依工具說明自己選）與固定流程（每個工作自己寫的 fallback）。
- AI 沒設定、額度用完或連不上時，自動改走固定流程，結果仍然能用（「AI 失敗要能回到手動流程」）。
- 工具只能讀資料或產生「候選／草稿」；正式資料一律由人確認。
- 每次執行記一筆 agent_tasks：用了哪些工具、每步摘要、最後總結；不記學生的姓名、學號。

工具回傳 dict：summary（給人看的一句話）、error（失敗原因）、link（{label, endpoint, params}，畫面上的連結），
其他欄位會交回給 AI 判斷下一步。
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Callable

from app.extensions import db
from app.models import AgentTask
from app.services import gemini_client
from app.services.gemini_client import AIUnavailable


TAIPEI = timezone(timedelta(hours=8))


def taipei_time(value, pattern="%Y-%m-%d %H:%M"):
    """資料庫存的是 UTC（沒有時區資訊），畫面上改顯示台灣時間。"""
    if value is None:
        return ""
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(TAIPEI).strftime(pattern)


class ToolError(Exception):
    """工具拒絕這次呼叫（參數錯、沒有權限）。訊息是給人看的中文。"""


@dataclass
class Tool:
    name: str
    label: str
    description: str
    run: Callable[..., dict]
    params: dict = field(default_factory=dict)

    def declaration(self):
        declaration = {"name": self.name, "description": self.description}
        if self.params:
            declaration["parameters"] = {
                "type": "OBJECT",
                "properties": {key: {"type": "STRING", "description": text} for key, text in self.params.items()},
                "required": list(self.params),
            }
        return declaration


class AiDecider:
    """請 Gemini 決定下一步：回傳 {"tool", "args"} 或 {"finish": 總結}。chat 可換成假的（測試用）。"""

    def __init__(self, instruction, chat=None):
        self.instruction = instruction
        self.chat = chat

    def __call__(self, goal, steps, tools):
        contents = [{"role": "user", "parts": [{"text": goal}]}]
        for step in steps:
            contents.append({"role": "model", "parts": [{"functionCall": {"name": step["tool"], "args": step["args"]}}]})
            contents.append({"role": "user", "parts": [
                {"functionResponse": {"name": step["tool"], "response": {"result": step["result"]}}}]})
        chat = self.chat or gemini_client.chat
        content = chat(contents, [tool.declaration() for tool in tools], self.instruction)
        parts = content.get("parts", [])
        calls = [part["functionCall"] for part in parts if "functionCall" in part]
        if calls:  # 一次只執行第一個工具，結果交回後再讓 AI 決定
            return {"tool": calls[0].get("name"), "args": calls[0].get("args") or {}}
        text = "".join(part.get("text", "") for part in parts).strip()
        if not text:
            raise AIUnavailable("AI 沒有給出下一步。")
        return {"finish": text}


def _execute(tools, name, args):
    tool = tools.get(name)
    if tool is None:
        return {"error": "沒有這個工具。"}
    clean = {key: str(value) for key, value in (args or {}).items() if key in tool.params}
    try:
        return tool.run(**clean)
    except ToolError as exc:
        return {"error": str(exc)}
    except TypeError:
        return {"error": "工具參數不正確。"}


def run(*, task_type, goal, tools, requester, decide, fallback, max_steps=6, target_type=None, target_id=None):
    """執行一次 Agent。decide 是 AI（None 表示直接走固定流程）；fallback 是固定流程。

    回傳 {task_id, mode, steps, summary, links}；steps 每步含 tool、label、args、result、summary。
    """
    task = AgentTask(task_type=task_type, requester_id=requester.id, target_type=target_type, target_id=target_id,
                     status="running", started_at=datetime.now(timezone.utc))
    db.session.add(task)
    db.session.commit()  # 先存起來；工具失敗時會 rollback，不能把這筆紀錄一起退掉

    registry = {tool.name: tool for tool in tools}
    mode, fallback_reason = ("ai" if decide else "rule"), None
    steps, summary = [], None
    for _ in range(max_steps):
        try:
            decision = (decide if mode == "ai" else fallback)(goal, steps, tools)
        except AIUnavailable as exc:
            mode, fallback_reason = "rule", str(exc)
            decision = fallback(goal, steps, tools)
        if "finish" in decision:
            summary = decision["finish"]
            break
        result = _execute(registry, decision.get("tool"), decision.get("args"))
        steps.append({
            "tool": decision.get("tool"),
            "label": registry[decision["tool"]].label if decision.get("tool") in registry else decision.get("tool"),
            "args": decision.get("args") or {},
            "result": result,
            "summary": result.get("error") or result.get("summary", ""),
        })

    links = []
    for step in steps:
        link = step["result"].get("link")
        if link and link not in links:
            links.append(link)
    task = db.session.get(AgentTask, task.id)
    task.status = "succeeded" if summary else "stopped"
    task.result_json = {
        "mode": mode,
        "fallback_reason": fallback_reason,
        "steps": [{"tool": s["tool"], "label": s["label"], "summary": s["summary"]} for s in steps],
        "summary": summary or f"執行了 {len(steps)} 步還沒有結論，已停止；請稍後再試或改用手動流程。",
        "links": links,
    }
    task.finished_at = datetime.now(timezone.utc)
    db.session.commit()
    return {"task_id": task.id, "mode": mode, "steps": steps, "summary": task.result_json["summary"], "links": links}
