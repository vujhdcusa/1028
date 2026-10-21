"""OCR 課程名稱字形校正：只把字形相近的錯字改成課程清單上唯一的課名；學生仍要確認。"""

# OCR 常把左邊的字讀成右邊的字：(OCR 讀到的字, 課程清單上的字)。
# 來源：docs/03_開發紀錄/OCR驗收紀錄_2026-10-20.md 的成績單課程名稱錯字。
LOOK_ALIKE_PAIRS = {
    ("合", "會"), ("育", "資"), ("脊", "資"), ("貢", "資"), ("商", "育"),
    ("獲", "護"), ("域", "識"), ("滑", "濟"), ("奧", "與"), ("事", "寧"),
}
# 本科課程名稱清單，須由學校「修業科目表」的中文課名建立（來源寫在 school/public-sources/）。
# 清單是空的時候不做任何校正。
COURSE_CATALOG = ()
MAX_LOOK_ALIKE_CHARS = 2


def correct_course_name(name, catalog=COURSE_CATALOG):
    """Return (name, original). original is set only when exactly one catalog name matches."""
    if not name or name in catalog:
        return name, None
    matches = set()
    for official in catalog:
        if len(official) != len(name):
            continue
        diffs = [(read, true) for read, true in zip(name, official) if read != true]
        if 0 < len(diffs) <= MAX_LOOK_ALIKE_CHARS and all(pair in LOOK_ALIKE_PAIRS for pair in diffs):
            matches.add(official)
    if len(matches) == 1:
        return matches.pop(), name
    return name, None


def apply_name_correction(course, catalog=COURSE_CATALOG):
    corrected, original = correct_course_name(course.get("course_name"), catalog)
    if original is None:
        return course
    course["course_name"] = corrected
    course["course_name_corrected_from"] = original
    course["needs_confirmation"] = True
    course.setdefault("review_reasons", []).append(
        f"課程名稱已依課程清單校正為『{corrected}』（OCR 原文『{original}』），請對照原圖。")
    return course
