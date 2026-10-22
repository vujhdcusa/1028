"""招生時程：依招生管道列出重要日程，標出已過、進行中、下一步。

資料放在 app/content/admission_schedule.csv，每一列附官方出處；時間是台灣時間。
- 二技技優甄審（6 位數志願代碼）：全國共用技專校院招生委員會聯合會的日程。
- 日間部申請入學：各校日期不同，這一版不列，請看學校招生網站。
- 這一年的日程還沒公告時，用最近一年當參考（reference=True），畫面要標明「去年」。
"""

import csv
from datetime import datetime
from pathlib import Path

SCHEDULE_FILE = Path(__file__).resolve().parents[1] / "content" / "admission_schedule.csv"

CHANNEL_LABELS = {"skill_review": "二技技優甄審"}

# 最近一次到官網確認「下一屆日程是否公告」的日期；公告後把新日程加進 CSV
CHECKED_ON = "2026-10-22"


def _parse(text):
    text = (text or "").strip()
    return datetime.strptime(text, "%Y-%m-%d %H:%M") if text else None


def load_schedule(path=None):
    """回傳 {(管道, 學年度): [{name, start, end, note, source}]}，依開始時間排序。"""
    path = path or SCHEDULE_FILE
    if not Path(path).is_file():
        return {}
    schedule = {}
    with open(path, encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            schedule.setdefault((row["管道"].strip(), int(row["學年度"])), []).append({
                "name": row["項目"].strip(),
                "start": _parse(row["開始"]),
                "end": _parse(row["結束"]),
                "note": row["說明"].strip(),
                "source": row["出處"].strip(),
            })
    for events in schedule.values():
        events.sort(key=lambda event: event["start"].date())  # 同一天依官方表格順序（sort 是穩定排序）
    return schedule


def program_channel(program):
    return "skill_review" if program.program_code.isdigit() else None


def _state(event, now):
    # 只有一個時間點的項目（例如「報到截止 17:00」），當天都算進行中
    end = event["end"] or event["start"].replace(hour=23, minute=59)
    if now > end:
        return "past"
    return "current" if now >= event["start"] or now.date() == event["start"].date() else "upcoming"


def _build(channel, year, schedule, now, reference):
    now = now or datetime.now()
    events = [{**event, "state": _state(event, now)} for event in schedule[(channel, year)]]
    upcoming = [event for event in events if event["state"] != "past"]
    return {
        "channel": channel,
        "channel_label": CHANNEL_LABELS[channel],
        "year": year,
        "reference": reference,
        "events": events,
        "next": upcoming[0] if upcoming else None,
        "finished": not upcoming,
    }


def timeline(program, schedule=None, now=None):
    """回傳 {channel, channel_label, year, reference, events, next, finished}；沒有共用日程的管道回傳 None。"""
    channel = program_channel(program)
    if channel is None:
        return None
    schedule = load_schedule() if schedule is None else schedule
    years = sorted(year for key_channel, year in schedule if key_channel == channel and year <= program.admission_year)
    if not years:
        return None
    return _build(channel, years[-1], schedule, now, reference=years[-1] != program.admission_year)


def latest_timeline(channel="skill_review", schedule=None, now=None):
    """某個管道最新一年的日程（招生時程頁用）；沒有資料時回傳 None。"""
    schedule = load_schedule() if schedule is None else schedule
    years = sorted(year for key_channel, year in schedule if key_channel == channel)
    return _build(channel, years[-1], schedule, now, reference=False) if years else None
