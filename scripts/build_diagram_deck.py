"""產生「流程圖彙整」簡報：每頁一張最新的流程圖，方便抓圖貼到 Canva。

沿用 build_teacher_presentation.py 的版面函式，但輸出成另一個檔案，
不會覆蓋 10-07 的指導老師討論簡報（那份保留當作當天的討論紀錄）。

執行：.venv\\Scripts\\python.exe scripts\\build_diagram_deck.py
圖檔來源：docs/images（先用 Mermaid CLI 與 D-01-use-case-by-role.py 更新圖檔再執行）。
"""
from pptx import Presentation
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches

from build_teacher_presentation import IMG, ROOT, WHITE, add_text, base_slide, diagram_slide

OUT = ROOT / "docs" / "08_簡報" / "AI_流程圖彙整_2026-10-10.pptx"

# 依 docs/04_圖表與介面/diagrams.md 的規格書圖號；圖 7（專題共同審查）2026-10-10 已移除
DIAGRAMS = [
    ("D-01-use-case-student.png", "圖 1｜學生使用案例圖"),
    ("D-01-use-case-teacher.png", "圖 2｜老師使用案例圖（導師、專任教師、指導老師）"),
    ("D-01-use-case-admin.png", "圖 3｜系統管理者使用案例圖"),
    ("D-01-use-case-staff.png", "圖 1-1｜科辦／科助使用案例圖"),
    ("D-02-login-role-routing.png", "圖 4｜登入與角色導頁流程圖"),
    ("D-10-main-line-flow.png", "圖 5｜學生主線流程圖"),
    ("D-20-form-download-flow.png", "圖 6｜科辦表單下載區流程圖"),
    ("D-13-admission-rule-update-flow.png", "圖 8｜招生資料更新流程圖"),
    ("D-16-teacher-confirm-flow.png", "圖 9｜導師確認流程圖"),
    ("D-17-admin-maintain-requirements.png", "圖 10｜系統管理者維護校系備審要求流程圖"),
    ("D-14-role-responsibility.png", "圖 11｜角色與責任圖"),
    ("D-05-system-architecture.png", "圖 12｜系統架構圖"),
    ("D-06-dfd.png", "圖 13｜DFD 資料流程圖"),
    ("D-09-erd-v2.png", "圖 14｜ERD 資料庫關聯圖"),
    ("D-15-report-overview.png", "圖 15｜報告用總體流程圖"),
    ("D-18-staff-service-record-flow.png", "圖 16｜科辦核准電子獎狀流程圖"),
    ("D-19-admission-announcement-flow.png", "圖 17｜二技招生公告與 AI 推薦校系流程圖"),
]


def make_deck():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    cover = base_slide(prs, "資管科智慧學習歷程系統", dark=True)
    add_text(cover, "流程圖彙整（2026-10-10 版）", 0.82, 1.55, 11, 0.7, 32, WHITE, True)
    add_text(cover, "依 10-10 定案的設計規格更新；圖號與 docs/04_圖表與介面/diagrams.md 一致。",
             0.86, 4.95, 11.5, 0.45, 16, WHITE)
    missing = []
    for filename, title in DIAGRAMS:
        if not (IMG / filename).exists():
            missing.append(filename)
        diagram_slide(prs, filename, title, "原圖：docs/images/" + filename)
    if missing:
        raise SystemExit(f"找不到圖檔：{missing}")
    prs.save(OUT)
    print(OUT)


if __name__ == "__main__":
    make_deck()
