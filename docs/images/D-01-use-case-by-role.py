"""依角色產生使用案例圖（人形＋功能橢圓），樣式參考歷屆專題報告書。

修改方式：只要改下面 ROLES 的內容，再執行
    python D-01-use-case-by-role.py
就會重新產生 D-01-use-case-<角色>.svg 與 .png。

每個功能寫成 (主標題, 括號說明, 是否為後續功能)：
- 括號說明可留空字串 ""。
- 後續功能（例如 Phase 2）會畫成虛線橢圓。
"""
import os
import subprocess
from html import escape

ROLES = [
    {
        "file": "D-01-use-case-student",
        "actor": "學生",
        "color": "#DBEAFE",
        "title": "學生",
        "items": [
            ("選擇目標校系", "查看該校系需要的備審資料與標準", False),
            ("上傳學習資料", "成績與學分、證照、活動、競賽、服務學習、幹部經歷", False),
            ("確認整理結果", "AI 輔助辨識；可修正或手動輸入", False),
            ("查看缺件清單", "對照目標校系還缺什麼", False),
            ("查看導師建議", "依建議修改後重新送出", False),
            ("產出備審資料", "下載可列印的完整備審資料", False),
            ("個人資料", "查看個人資料、修改密碼", False),
            ("登出", "", False),
        ],
    },
    {
        "file": "D-01-use-case-teacher",
        "actor": "導師",
        "color": "#DCFCE7",
        "title": "導師",
        "items": [
            ("本班學生清單", "查看資料完成度；只能看本班學生", False),
            ("學生資料檢視", "學習資料、目標校系與缺件清單", False),
            ("確認內容", "標記已確認或留下修改建議", False),
            ("班級統計", "預計申請學校、完成度與缺件；Phase 2", True),
            ("個人資料", "查看個人資料、修改密碼", False),
            ("登出", "", False),
        ],
    },
    {
        "file": "D-01-use-case-admin",
        "actor": "系統\n管理者",
        "color": "#EDE9FE",
        "title": "系統管理者（開發者）",
        "items": [
            ("帳號與權限管理", "建立、停用帳號，設定角色", False),
            ("校系備審要求維護", "學校、科系、年度、加權與資料來源", False),
            ("審核招生資料更新", "比對 Agent 擷取的新舊差異後核准發布", False),
            ("課程與證照規則維護", "年度課程規劃與證照規則", False),
            ("操作紀錄查詢", "查看重要操作與資料異動", False),
            ("登出", "", False),
        ],
    },
]

FONT = "Microsoft JhengHei, Noto Sans TC, Arial, sans-serif"
STROKE = "#374151"
W = 980
OVAL_X, OVAL_W = 440, 490
ROW_H, GAP, TOP = 70, 16, 70


def svg_for(role):
    items = role["items"]
    rows = len(items)
    content_h = rows * ROW_H + (rows - 1) * GAP
    h = TOP + content_h + 50
    cx, cy = 190, TOP + content_h / 2  # 人形中心
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" '
        f'font-family="{FONT}">',
        f'<rect width="{W}" height="{h}" fill="#FFFFFF"/>',
        '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" '
        f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{STROKE}"/></marker></defs>',
        f'<rect x="20" y="20" width="{W - 40}" height="{h - 40}" fill="none" stroke="#9CA3AF" stroke-width="1.5" rx="6"/>',
        f'<text x="40" y="52" font-size="18" fill="#374151">資管科智慧學習歷程系統－{escape(role["title"])}</text>',
    ]
    # 人形：大頭（內含角色名稱）、身體、手、腳
    head_r = 62
    hy = cy - 70
    out.append(f'<circle cx="{cx}" cy="{hy}" r="{head_r}" fill="{role["color"]}" stroke="{STROKE}" stroke-width="3"/>')
    lines = role["actor"].split("\n")
    for k, line in enumerate(lines):
        dy = (k - (len(lines) - 1) / 2) * 30
        out.append(f'<text x="{cx}" y="{hy + dy + 9}" font-size="26" font-weight="bold" text-anchor="middle" '
                   f'fill="#111827">{escape(line)}</text>')
    body_top = hy + head_r
    out.append(f'<ellipse cx="{cx}" cy="{body_top + 52}" rx="38" ry="52" fill="#FFFFFF" stroke="{STROKE}" stroke-width="3"/>')
    hand_y = body_top + 45
    out.append(f'<path d="M{cx - 36},{hand_y} L{cx - 78},{hand_y + 28}" stroke="{STROKE}" stroke-width="3" fill="none"/>')
    out.append(f'<circle cx="{cx - 84}" cy="{hand_y + 32}" r="8" fill="#FFFFFF" stroke="{STROKE}" stroke-width="3"/>')
    out.append(f'<path d="M{cx + 36},{hand_y} L{cx + 78},{hand_y + 28}" stroke="{STROKE}" stroke-width="3" fill="none"/>')
    out.append(f'<circle cx="{cx + 84}" cy="{hand_y + 32}" r="8" fill="#FFFFFF" stroke="{STROKE}" stroke-width="3"/>')
    leg_top = body_top + 100
    for sx in (-1, 1):
        x = cx + sx * 20
        out.append(f'<path d="M{x},{leg_top} L{x},{leg_top + 45} L{x + sx * 20},{leg_top + 45}" '
                   f'stroke="{STROKE}" stroke-width="3" fill="none"/>')
    # 箭頭起點：人形右手
    ax, ay = cx + 92, hand_y + 32
    for idx, (title, note, later) in enumerate(items):
        y = TOP + idx * (ROW_H + GAP)
        my = y + ROW_H / 2
        dash = ' stroke-dasharray="8 5"' if later else ""
        color = "#6B7280" if later else "#111827"
        out.append(f'<path d="M{ax},{ay} L{OVAL_X - 4},{my}" stroke="{STROKE}" stroke-width="2" fill="none" '
                   f'marker-end="url(#arrow)"{dash}/>')
        out.append(f'<rect x="{OVAL_X}" y="{y}" width="{OVAL_W}" height="{ROW_H}" rx="{ROW_H / 2}" '
                   f'fill="#FFFFFF" stroke="{STROKE}" stroke-width="2.5"{dash}/>')
        if note:
            out.append(f'<text x="{OVAL_X + OVAL_W / 2}" y="{my - 4}" font-size="20" font-weight="bold" '
                       f'text-anchor="middle" fill="{color}">{escape(title)}</text>')
            out.append(f'<text x="{OVAL_X + OVAL_W / 2}" y="{my + 22}" font-size="15" text-anchor="middle" '
                       f'fill="#4B5563">（{escape(note)}）</text>')
        else:
            out.append(f'<text x="{OVAL_X + OVAL_W / 2}" y="{my + 7}" font-size="20" font-weight="bold" '
                       f'text-anchor="middle" fill="{color}">{escape(title)}</text>')
    out.append("</svg>")
    return "\n".join(out), h


def to_png(svg_path, png_path, width, height):
    """用 Mermaid CLI 內建的 Chrome（puppeteer）把 SVG 轉成 PNG。"""
    script = os.path.join(os.path.dirname(svg_path), "_svg2png.cjs")
    with open(script, "w", encoding="utf-8") as f:
        f.write(
            "const path=require('path');\n"
            "const pp=require(path.join(process.env.APPDATA,'npm','node_modules','@mermaid-js','mermaid-cli',"
            "'node_modules','puppeteer'));\n"
            "(async()=>{const [svg,png,w,h]=process.argv.slice(2);"
            "const b=await pp.launch({headless:'new'});const p=await b.newPage();"
            "await p.setViewport({width:+w,height:+h,deviceScaleFactor:2});"
            "await p.goto('file:///'+path.resolve(svg).replace(/\\\\/g,'/'));"
            "await p.screenshot({path:png,clip:{x:0,y:0,width:+w,height:+h}});await b.close();})();\n"
        )
    try:
        subprocess.run(["node", script, svg_path, png_path, str(width), str(height)], check=True)
    finally:
        os.remove(script)


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    for role in ROLES:
        svg, h = svg_for(role)
        svg_path = os.path.join(here, role["file"] + ".svg")
        with open(svg_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(svg)
        to_png(svg_path, os.path.join(here, role["file"] + ".png"), W, h)
        print("產生", role["file"])
