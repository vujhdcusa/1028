# AI 代理協作工作佇列

狀態：啟用中  
建立日期：2026-09-23  
適用範圍：`D:\democase\ai`

## 用途與使用方式

此文件是 Codex、IDE 內的 BMAD Agent 與人工審閱者共用的交接點，目的在於避免重複貼上長篇上下文。

1. 使用者在 IDE 的 BMB 對話中輸入：`依工作佇列執行`。
2. BMB 先讀取本文件，選擇唯一一項「待執行」工作，改為「進行中」。
3. 完成後，在本文件最下方追加代理回報，並將工作改為「待使用者確認」或「完成」。
4. Codex 可直接讀取回報進行驗收與補充下一項工作。

此佇列不會自動喚醒 IDE 的 BMAD；它減少的是上下文複製，不取代使用者啟動 Agent 的動作。

## 已確認決策基線

- 採用「先做根，再向外延伸」：先完成單一學生工作檯，再擴展首頁視覺與外部公開資料模組。
- P0 必須有可操作的 8 塊互鎖拼圖作品集；P2 僅深化校園插畫、材質與動畫，不能延後拼圖本體。
- 每次送出檔案至 Gemini 前，學生必須明確同意；只傳送本機去識別化後的最小必要文字／結構資料，不傳送原始整頁文件。
- AI 只產生草稿；本機規則解析與學生人工確認才可形成正式學習歷程資料。
- 支援系統共用 API 與學生個人 API 金鑰：測試版須同時支援單次使用即丟棄，以及學生同意後的安全保存／撤銷／替換。金鑰不可寫入前端、日誌或 Git。
- 二技招生與本校資管科公開資料納入年度更新與差異偵測；僅能在科辦覆核發布後影響學生介面。參考來源包含 `https://www.techadmi.edu.tw/` 與 `https://im.ukn.edu.tw/`。
- 現有專案為 Flask Session 架構。安全目標可採可替換實作；不得把 JWT、`.enc` 格式或 Celery 視為測試版既有能力。

## 工作規則

- 一次只認領一項工作；不得偷偷擴張為未授權的程式碼、憑證、資料庫或外部網站寫入。
- 所有新 Markdown 文件放在 `D:\democase\ai\docs`；歷史回報只追加，不覆寫。
- 保留既有未提交變更。遇到衝突、缺少測試資料或需要外部權限時，停止於「待使用者確認」並清楚記錄。
- 回報必須包含角色、日期、修改檔案、驗證方式、結果、風險／阻塞與下一步。

## 目前工作

### ROOM-02｜AI 會議室修正清單（Claude 驗收後交給 GPT）（**目前工作**）

- 狀態：待使用者確認（GPT／Codex 已完成程式修正；瀏覽器驗收受本機環境阻塞）
- 認領：GPT／Codex
- 計畫：`docs/09_AI會議室/AI_實作計畫_會議室修正清單_Claude驗收_2026-10-10.md`（7 個必修、2 件要問使用者、文件整理、系統完整性報告更正）
- 最優先：第 1 項「會議清單 API 讀錯檔案」，不修就不能重啟 8765。
- 開工時先把目前未提交的修改照原樣提交一次；不推送；這段時間 Claude 不動 `ai-meeting-room`。

### ROOM-01｜AI 會議室：版面整理、資料夾分類、編輯與歷史版本、搜尋（**目前工作**）

- 狀態：**待使用者確認**（GPT 第一版 `743e415`；Claude 接手收尾並完成瀏覽器驗收與重新下載驗收，見代理回報最後一筆）。
- 認領：GPT／Codex（約 5 小時）→ Claude Code 接手收尾
- 計畫：`docs/09_AI會議室/AI_實作計畫_會議室版面整理_資料夾_編輯歷史_搜尋_2026-10-10.md`（**全部照這份做**，包含硬性規則與時間分配）
- 範圍：只改 `D:\democase\ai-meeting-room`，以及在 `ai/docs` 寫日誌與回報；起點提交 `b603025`。
- 重點限制：不做刪除功能、不改發言內容、改動要記錄學號、路徑一律相對、不花 AI 額度、不推送、只測修改過的地方但要真的開瀏覽器操作。
- 驗收：計畫第四節的交代事項寫在本文件「代理回報」與開發日誌。

### ARCH-02｜BMAD 對最終可實作規格進行交叉審閱

- 狀態：待使用者確認 (已完成審閱)
- 建議認領：@BMB（協調）、@BMM（流程）、@WDS（拼圖 UX）、@TEA（Flask 安全邊界）、@QAS（驗收）
- 輸入：`AI_設計規格_測試版最終可實作規格_2026-09-23.md`、`AI_設計規格_單一核心流程重整提案_2026-09-23.md`
- 工作：檢查規格是否完整落實 P0 互鎖拼圖、Flask Session 相容的安全目標、每次同意與去識別化、人工確認、兩種 BYOK、公開資料覆核發布。不得修改程式碼。
- 驗收：在本文件「代理回報」新增一份具角色署名的審閱紀錄；若發現矛盾，提出具檔名與段落的修正建議。

### TEAM-01｜三人開發線與個人完整線建立

- 狀態：待使用者確認基準快照
- 輸入：`AI_產品北極星與垂直切片_2026-09-29.md`、`AI_三人開發分工與功能契約_2026-09-29.md`、`AI_雙專案與分支整合策略_2026-09-29.md`、`AI_整合驗收與失敗回收規則_2026-09-29.md`
- 工作：確認目前未提交變更的基準快照，建立團隊協作線與個人完整線；組員只能透過功能契約與驗收案例交付。
- 限制：不得使用 reset／checkout 清除既有變更；不得直接寫入共用 MySQL；不得在沒有備份的情況下執行 migration。
- 驗收：個人備份可讀、團隊線與個人線路徑明確、每位組員責任範圍與第一個驗收案例已記錄。

### PPT-01｜依 10-08 流程圖更新指導老師討論簡報

- 狀態：待使用者確認
- 建議認領：GPT／Codex
- 輸入：`docs/03_開發紀錄/development-log.md` 的 2026-10-08 第七節（圖檔清單、舊圖清單、文字重點）；規格書「2026-10-08 功能確認總表」（科辦已改為「核准電子獎狀」，以日誌第八節為準）
- 工作：更新 `docs/08_簡報/AI_指導老師討論簡報_2026-10-07.pptx`（GPT 原本產出；產生腳本 `scripts/build_teacher_presentation.py`），換上新圖、拿掉舊圖、修正科辦與競賽相關文字。需要時也可以修改流程圖。
- 修改流程圖時請一起同步：改 `docs/images/*.mmd` → 重新匯出 PNG／SVG → 把原始碼貼回 `docs/04_圖表與介面/diagrams.md` → 內容有變就更新規格書 → 在開發日誌記下改了哪張、為什麼。
- 協調：不要和 Claude Code 在同一個資料夾同時工作（10-08 上午兩邊同時匯出圖片，互相覆蓋）；開工前看 `git status`，有別人未 commit 的變更先問使用者。
- 驗收：簡報中沒有「科辦核准競賽證明」「科助任務待確認」等舊說法；圖號與規格書一致；在本文件「代理回報」追加紀錄。

## 代理回報

### 【@BMB 統籌回報】ARCH-02 最終規格交叉審閱
- **日期**：2026-09-23
- **角色**：@BMB (協同 @BMM, @WDS, @TEA, @QAS)
- **修改檔案**：僅更新工作佇列狀態與回報，無修改原始碼。
- **驗證方式與結果**：
  針對 `AI_設計規格_測試版最終可實作規格_2026-09-23.md` 進行交叉審閱：
  1. **P0 互鎖拼圖**：第2、3節已嚴格規範 8 塊實體互鎖拼圖，禁用卡片或線性節點。
  2. **Flask Session 安全目標**：第6節明確定義沿用 Flask Session 身分驗證、伺服器端所有權檢查及私有 Storage Adapter。
  3. **每次同意與去識別化**：第4.1節確實涵蓋本機遮蔽與最小傳輸原則，原始文件不傳 Gemini。
  4. **人工確認**：第3、4節確保 AI 僅產出草稿，抵免補判斷交由人工或本機規則確認。
  5. **兩種 BYOK**：第4.2節完整制定系統共用、個人單次與個人保存等金鑰安全邊界。
  6. **公開資料覆核**：第5節確實落實差異偵測、科辦審閱與發布機制。
  **結論**：規格完整且無矛盾，完全符合前期提案的設計決策與系統現況邊界。
- **待確認事項與下一步**：
  - 規格已就緒，無阻塞事項。
  - 下一步：等待使用者確認。若無異議，請下達指令進入「撰寫實作計畫 → 測試驅動開發」階段，優先實作 P0 學生主工作檯與拼圖組件。

### 【@GPT／Codex 回報】PPT-01 簡報與新版圖檔更新
- **日期**：2026-10-08
- **角色**：@GPT／Codex
- **修改檔案**：`docs/08_簡報/AI_指導老師討論簡報_2026-10-07.pptx`、`scripts/build_teacher_presentation.py`、`docs/03_開發紀錄/AI_流程圖更新紀錄_2026-10-08.md`、`docs/05_交接與專案管理/AI_正式文件草稿_給組員_2026-10-08.md`。
- **驗證方式與結果**：重新執行簡報產生腳本成功；簡報共 36 張投影片，PPTX ZIP 完整性檢查通過；腳本已移除舊版流程圖引用並改用新版角色圖與 `D-18-staff-service-record-flow.png`；PowerPoint 程序已關閉；`~$` 暫存檔未加入版本控制。
- **本次內容修正**：科辦改為核准科上服務電子獎狀；學生從學校獎懲記錄勾選申請；固定外框、內文可編輯；電子獎狀不取代正式獎懲記錄。競賽報名頁已標為「後續擴充草稿／待問科助」，不列為已確認功能。
- **風險／待確認**：競賽報名、科辦實際行政範圍與學校資料驗證方式仍需問科助；本次未修改 `app/`、`tests/`、規格書、`diagrams.md` 或 `development-log.md`。
- **下一步**：請組員與指導老師審閱 PPT 與正式文件草稿；確認競賽功能後，再決定是否建立後續開發項目。

### 【@GPT／Codex 回報】窄視窗與文件預覽實機診斷追加（2026-10-10）

- **角色**：GPT／Codex
- **修改檔案**：`ai-meeting-room/static/index.html`、`ai-meeting-room/tests/test_layout_and_preview.py`、`ai/docs/AI_開發紀錄_文件預覽與版面改版_2026-10-10.md`、`ai/docs/03_開發紀錄/development-log.md`。
- **修正內容**：窄視窗下右側欄預設收合但保留 `>` 把手，點擊可開啟浮動欄；檔案面板維持全寬浮層；收合／展開游標與入口不再消失。
- **診斷結果**：重整後內容空白是 `current` 未自動選回，重新點選會議可恢復；資料檔仍存在。舊後端程序未載入新文件抽取程式時，PPTX 仍會顯示舊版二進位提示，需重啟會議室後端。
- **驗證結果**：`py_compile` 與文件／布局靜態檢查通過；目前 Python 環境未安裝 pytest，故完整 pytest 未執行。未合併、未推送、未執行 migration。

### 【@GPT／Codex 回報】文件預覽依賴與 PDF 可核對內容追加（2026-10-10）

- **修改內容**：安裝 `pypdf`、`python-docx`、`openpyxl`、`python-pptx`、`odfpy`；PDF 面板追加原始頁面與 AI 抽取文字／來源位置雙重顯示。
- **證據**：`20261009-185407` 快照的 PPTX 抽出 36 張投影片，PDF 抽出 36 頁；`python -m pytest tests -q` 結果 **13 passed**。
- **注意**：瀏覽器目前若仍顯示「二進位檔」，代表 8765 後端尚未重啟，仍使用舊程序；重啟後才會載入文件抽取依賴與新版前端。

### 【@GPT／Codex 回報】PPTX 視覺投影片預覽追加（2026-10-10）

- **修改內容**：PPTX 不再以文字抽取作為主畫面；改用 `python-pptx` 產生投影片比例、文字方塊與圖片位置的視覺畫布，抽取文字移到可展開的 AI 查核區。PDF 維持原始頁面加文字來源雙重預覽。
- **驗證結果**：實際 36 張簡報均能產生 visual slide data；測試為 **14 passed**。未合併、未推送、未執行 migration。
- **限制**：目前環境沒有 LibreOffice，因此 PPTX 是本機安全的近似投影片渲染；複雜動畫、SmartArt、轉場與特殊圖形不一定能完全還原。

### 【@GPT／Codex 回報】文件切換閃爍、查核證據 UI 與 DOC fallback（2026-10-10）

- **修正**：移除開啟 PDF／PPTX 時自動隱藏檔案目錄的行為，避免點檔案時閃爍及誤以為左上專案被刪除；目錄改由 `🗂` 明確控制。
- **UI**：PDF／PPTX 的「AI 讀取文字與來源位置」改成醒目的 `🔎 AI 讀取證據` 可展開卡，並限制內容區高度可滾動。
- **DOC**：增加 Windows Microsoft Word／pywin32 fallback；無法轉讀時顯示明確原因並保留下載原始檔。
- **驗證**：`14 passed`、Python compile 通過；未合併、未推送、未執行 migration。

## 代理回報：Claude Code → 交接給 GPT（2026-10-09 23:25，Claude 額度將用完）

- **角色**：Claude Code（實作＋會議室主筆）
- **已完成**：小組 repo 合併並推送（`acac34e`）；資管科小助手第 1 步「確認與版本」實作在分支 `feat/assistant-confirm-versions`（`c157c25`、`f0d16f2`、`8b2f164`，**未推送、未合併回 main**）。210 tests passed。細節見開發日誌 2026-10-09（續）與 `docs/02_需求與設計/AI_實作計畫_資管科小助手_確認與版本_2026-10-09.md`。
- **進行中**：AI 會議室 `20261009-185407`「資管科小助手計畫・第 2 輪審查」#48 起為第 3 段，審查上述實作；快照已更新為實作後程式（舊快照備份在 `workspaces/20261009-185407-snapshot-1854`）。主筆已由使用者換成 GPT。另一場 `20261009-230524` 已停止，不再使用。
- **GPT 接手要做**：
  1. 等本圈審查結束，以主筆身分逐條對照程式查證（接受／駁回），整理要修的項目給使用者決定。
  2. 使用者同意後再改程式；每次修改都要寫開發日誌；改完跑全部測試：`.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp=<可寫暫存資料夾>`。
  3. 合併回 main、推送、在 MySQL 執行 migration `e6c1a3b8f215`（先備份）都要先問使用者。
- **注意**：工作目錄 `D:\democase\ai` 目前在分支 `feat/assistant-confirm-versions`；不要和其他代理同時改同一個資料夾。會議室裡的「Claude（獨立審查）」也會用到 Claude 額度，必要時可以在右側禁言。

## 代理回報：GPT／Codex → 審查結論（2026-10-09）

- **角色**：GPT／Codex（AI 會議室主筆）
- **完成事項**：讀取 `AGENTS.md`、本佇列「交接給 GPT」段落與會議 `20261009-185407` #48–#53；整理第 3 段「確認與版本」實作審查結論。
- **修改檔案**：`ai/docs/AI_審查結論_資管科小助手_確認與版本_2026-10-09.md`、本文件。
- **審查結果**：判定「要修改，暫不合併」。P0 為：送出後修改經歷需重新確認、導師確認需防舊快照競態、禁止舊自傳版本覆蓋新版本、入學學年度需可信來源或行政確認。額度 `rollback()` 列 P1；專一一般科系 AI 尚未實作，需如實標示。
- **驗證結果**：已核對會議 JSONL #48–#53；未修改程式、未合併、未推送、未執行 migration。210 tests passed 為會議既有紀錄，尚未由本次重跑。
- **待使用者確認**：入學學年度資料來源；是否接受 `taken_at`／最新 review 防競態方案；確認修正後再進入完整測試、瀏覽器驗證與合併流程。

### 【@GPT／Codex 回報】AI 會議室導覽與 Gemini 診斷（2026-10-10）

- **角色**：GPT／Codex
- **修改檔案**：`ai-meeting-room/static/index.html`、`ai-meeting-room/tests/test_topic_header.py`、`ai/docs/03_開發紀錄/development-log.md`、`ai/docs/AI_開發紀錄_會議室導覽與Gemini診斷_2026-10-10.md`。
- **完成事項**：導覽改為清楚說明多模型群組互審，加入 `ⓘ` 主題、600 秒疑似卡住、額度提醒關閉與重新整理再提醒的操作說明；補上開發與診斷紀錄。
- **Gemini 診斷**：`20261009-230524` 曾被中止；`20261009-185407` 的 Gemini 已於 00:01:36 完成 #55，耗時約 17.45 分鐘、9 次工具查詢，並由 flash fallback 完成；目前無活躍程序。
- **驗證結果**：先以失敗測試鎖定導覽缺口，補正後將執行 4 項靜態 UI 檢查與 inline JavaScript 語法檢查。
- **待確認事項與下一步**：若使用者希望改善「看起來像卡住」的體感，另立後端進度事件／工具查詢超時改善工作；本次未修改後端策略、未合併、未推送、未執行 migration。

### 【@GPT／Codex 回報】文件預覽與三欄版面改版（2026-10-10）

- **角色**：GPT／Codex
- **修改檔案**：`ai-meeting-room/document_extract.py`、`ai-meeting-room/agents.py`、`ai-meeting-room/server.py`、`ai-meeting-room/static/index.html`、`ai-meeting-room/README.md`、`ai-meeting-room/requirements-document-preview.txt`、`ai-meeting-room/tests/test_document_extract.py`、`ai-meeting-room/tests/test_agent_attachment_preview.py`、`ai-meeting-room/tests/test_server_document_preview.py`、`ai-meeting-room/tests/test_layout_and_preview.py`，以及 AI 開發紀錄文件。
- **完成事項**：文件點擊預覽、PDF 原始頁面 iframe、Office／ODF 文字抽取與來源標籤、原始檔下載／新分頁；附件文字會進入 AI prompt；左／中／右欄收合、展開把手與拖曳寬度控制；導覽與 README 已更新。
- **驗證結果**：11 項直接檢查通過；inline JavaScript 語法與 Python compile 通過。PyPI 依賴安裝因 DNS 無法解析 `pypi.org` 失敗，已保留 fallback 與明確錯誤。
- **待確認事項與下一步**：網路恢復後安裝 `requirements-document-preview.txt` 並用真實 PDF、DOCX、XLSX、PPTX、ODF 做瀏覽器目視驗收；舊式 DOC／XLS／PPT 暫以下載／另存提示處理。本次未合併、未推送、未執行 migration。
- **追加修正**：發現前端初始化曾因漏放 `#leftResize` 元素而中斷，造成內容看似消失；已補回元素並重新通過 11 項檢查、JavaScript 語法與 Python compile。會議 JSONL／raw 檔案未被刪除。
- **再追加修正**：保存的 inline 欄寬蓋掉收合 CSS，已改為收合狀態強制 `width: 0 !important`；新增回歸測試後 12 項檢查、JavaScript 語法與 Python compile 通過。

### 【@GPT／Codex 回報】會議檔案面板歷史快照優先與專案 fallback（2026-10-10）

- **角色**：GPT／Codex
- **修改檔案**：`ai-meeting-room/.gitignore`、`ai-meeting-room/server.py`、`ai-meeting-room/static/index.html`、`ai-meeting-room/tests/test_server_document_preview.py`、`ai-meeting-room/tests/test_layout_and_preview.py`、`ai-meeting-room/README.md`、`ai/docs/AI_設計規格_公開會議記憶庫與團隊同步_2026-10-10.md`、`ai/docs/03_開發紀錄/development-log.md`。
- **完成事項**：檔案面板新增 `preview_root()`，歷史 workspace 優先，缺少時使用 `meta.json.repo`；API 與 UI 顯示來源提示；raw 下載與文件預覽共用同一來源；AI live turn 仍使用隔離 workspace。
- **驗證方式與結果**：來源選擇回歸測試 **5 passed**；完整測試 **19 passed**；Python compile、inline JavaScript 語法與 `git diff --check` 通過。
- **風險／限制**：fallback 顯示的是目前專案而非會議當時版本；跨電腦需維持使用者指定的 `D:\democase` 目錄結構。`meetings/` 公開推送前仍需人工檢查 raw、附件與個資，尚未推送或合併。
- **下一步**：公開 GitHub 前仍需人工檢查 `meetings/` 的 raw、附件與個資，並由使用者另行授權推送。

### 【@GPT／Codex 回報】檔案面板顯示來源實際路徑（2026-10-10）

- **角色**：GPT／Codex
- **修改檔案**：`ai-meeting-room/server.py`、`ai-meeting-room/static/index.html`、`ai-meeting-room/tests/test_server_document_preview.py`、`ai-meeting-room/tests/test_layout_and_preview.py`、`ai/docs/03_開發紀錄/development-log.md`。
- **完成事項**：歷史快照與專案 fallback 的檔案樹／檔案預覽 API 新增 `source_path`；檔案面板以純文字顯示來源類型與實際路徑。
- **驗證方式與結果**：相關測試 **10 passed**；完整測試與 Python／JavaScript 語法檢查待收尾執行。
- **風險／限制**：顯示的是本機絕對路徑；跨電腦若目錄不同，仍需依約使用 `D:\democase` 結構或重新建立會議。

### 【@GPT／Codex 回報】外部路徑與備份素材整理（2026-10-10）

- **角色**：GPT／Codex
- **修改檔案**：`ai/scripts/transcribe_project_recordings.py`、`ai/scripts/transcribe_meeting_audio.py`、`ai-meeting-room/server.py`、`ai-meeting-room/static/index.html`、`ai-meeting-room/README.md`、`ai-meeting-room/docs/操作手冊.md`、`ai/docs/03_開發紀錄/development-log.md`；新增 `D:\democase\backup\專題素材\錄音` 與 `D:\democase\backup\環境清單\外部路徑與備份原則.txt`。
- **完成事項**：只複製外部錄音到新增 backup 分類，未刪除／移動／覆寫 `D:\democase` 原有專案；轉錄腳本改為讀取 democase backup 路徑；舊 `D:\專題\ai` 使用提示已改正。
- **驗證方式與結果**：錄音備份共 16 個檔案、約 84,299,296 bytes；外部舊路徑已從 `ai-meeting-room` 非歷史 raw 程式／文件中清除。後續需重跑兩個 repo 的完整測試與語法檢查。
- **風險／限制**：錄音可能含個資，只適合 USB／Google Drive 受控或加密備份，不應未審查就推到 GitHub；`.codex`、`.agents`、登入狀態與 Token 未複製。

### 【@GPT／Codex 回報】新對話起點交接準備（2026-10-10）

- **角色**：GPT／Codex
- **修改檔案**：新增 `ai/docs/AI_交接摘要_新對話起點_2026-10-10.md`；追加 `ai/docs/03_開發紀錄/development-log.md`。
- **內容**：整理三個 repo、AI 會議室文件預覽與 fallback、backup 素材、測試證據、GitHub 未推送狀態、敏感資料界線與新對話讀取順序。
- **驗證方式與結果**：交接文件已寫入 `D:\\democase\\ai\\docs`；未修改既有專案檔案、未刪除／移動資料、未 commit／push。

### 【@Claude 回報】小助手審查修正、合併回 main、文件歸位（2026-10-10）

- **角色**：Claude Code（主筆接手收尾）
- **會議**：`20261009-185407` GPT 收尾（#57）被中止；Claude 在 #58 補上收尾並回答主持人 #54，#59 記錄主持人決定「入學學年度由管理者匯入」。
- **修改檔案**：`app/routes/{admin,student,teacher}.py`、`app/services/` 的 `ai_quota_service.py`、`autobiography_service.py`、`review_snapshot_service.py`、`student_rules.py`、相關範本、`tests/test_assistant_confirm_versions.py`、`tests/test_main_line_routes.py`。
- **文件歸位**（不改寫其他代理的歷史回報，路徑以這裡為準）：
  - `docs/AI_交接說明_會議室GitHub同步與共同記憶_2026-10-10.md`、`AI_實作計畫_會議室文件預覽與版面改版_2026-10-10.md`、`AI_實作計畫_會議室歷史快照與專案路徑Fallback_2026-10-10.md`、`AI_設計規格_公開會議記憶庫與團隊同步_2026-10-10.md`、`AI_開發紀錄_文件預覽與版面改版_2026-10-10.md`、`AI_開發紀錄_會議室導覽與Gemini診斷_2026-10-10.md` → `docs/09_AI會議室/`
  - `docs/AI_審查結論_資管科小助手_確認與版本_2026-10-09.md` → `docs/02_需求與設計/`
  - `docs/AI_交接摘要_新對話起點_2026-10-10.md` → 併入 `docs/05_交接與專案管理/AI_交接_新對話起點_2026-10-08.md`，原檔封存到 `docs/99_封存_歷史與待確認/01_舊版交接與對話/`
  - 開發日誌 10-10 各節移到最上面（最新在上）。
- **驗證結果**：219 passed；展示資料走查全部通過；未用瀏覽器實際操作。
- **待確認事項**：學生取消目標後要不要還能看自傳版本紀錄；推送 `main`、MySQL migration、會議室 `meetings/` 公開前的個資檢查（學號 111534105）。
- **下一步**：小助手開工順序第 2 步（拿掉聊天框、導師備審摘要）。

### 【@GPT／Codex 回報】ROOM-01 會議室版面、資料夾、編輯歷史與搜尋（2026-10-10）

- **角色**：GPT／Codex
- **修改檔案**：`ai-meeting-room/server.py`、`ai-meeting-room/static/index.html`、`ai-meeting-room/meetings/folders.json`、`ai-meeting-room/tests/test_room_features.py`、`ai-meeting-room/tests/test_layout_and_preview.py`、`ai-meeting-room/tests/test_server_document_preview.py`、`ai-meeting-room/README.md`、`ai-meeting-room/docs/操作手冊.md`、`ai/docs/03_開發紀錄/development-log.md`。
- **完成事項**：ROOM-01 可提交範圍已實作：測試資料目錄由 `MEETING_ROOM_DATA` 隔離；資料夾可新增、改名、搬移但沒有刪除；資料夾變更與會議編輯歷史只追加並記錄學號、姓名、時間、前後內容；編輯使用歷史筆數防止舊頁面覆蓋；搜尋支援會議與發言、附件、`from:`、`in:`、`has:附件`、`before:`、`after:`；右側與會者明確分為主持人與 AI 兩區；檔案面板來源路徑改以相對路徑呈現。沒有修改既有發言內容，也沒有動 `ai` 專案程式碼。
- **驗證結果**：ROOM-01 相關測試、版面測試與文件預覽相對路徑測試共 **16 項通過**；Python 編譯通過；內嵌 JavaScript 語法檢查通過；本機提交為 `743e415`，未推送。
- **瀏覽器實際操作**：已嘗試用隔離測試資料與 `8766` 開啟本機瀏覽器，但本工作環境的隔離瀏覽器無法連到本機埠（連線逾時／拒絕），因此未取得瀏覽器截圖；沒有使用真的會議資料，也沒有按請 AI 發言。
- **未完成／風險**：完整測試另外有 4 項既有平行發言逾時測試失敗（未修改 `agents.py`）；完整瀏覽器逐項驗收、重新下載副本驗收、導覽逐步點驗尚未完成。8765 未重啟，因為目前無法以瀏覽器確認隔離驗收且尚未取得「沒有 AI 正在發言」的可靠程序證據。
- **待使用者確認與下一步**：請在可連到 `127.0.0.1:8766` 的本機瀏覽器完成資料夾新增／搬移／改名、搜尋跳轉、編輯版本衝突與寬窄右欄截圖；確認後再決定是否處理既有平行發言測試、重跑完整測試、重啟 `8765`。`ai` 工作區另有既有未提交的腳本變更，本次未碰也未提交。


### 【@Claude 回報】ROOM-01 接手收尾：瀏覽器驗收、未完成部分、重新下載驗收（2026-10-10）

- **角色**：Claude Code（接手 GPT 的 ROOM-01；使用者睡覺中，依使用者「睡醒前做好、要真的開網頁驗收」的要求）
- **修改檔案**：`ai-meeting-room/server.py`、`agents.py`（`speaker_name()`）、`static/index.html`、`README.md`、`docs/操作手冊.md`、`tests/test_room_features.py`、`tests/test_server_document_preview.py`；`ai/docs/03_開發紀錄/development-log.md`（續 5）、本文件。
- **完成事項**：新會議真的存相對路徑 `../ai`（GPT 版本其實仍存絕對路徑）；搜尋 3.5 秒 → 0.04 秒且不再整場會議重複列出；編輯視窗按取消也會存檔的問題；資料夾欄改成 Discord 式直排圖示（全部／未分類／拖曳搬移／改名換圖示，沒有刪除）；搬移改點選（原本要手打代號）；編輯紀錄改前改後並排（原本 `alert`）；右側兩框、說明一行；導覽新增三步（共 21 步）；找不到專案資料夾的提示。
- **驗證結果**：會議室測試 **48 個全部通過**（GPT 回報的 4 個失敗在本機重跑通過）；Playwright 瀏覽器實際操作 **32 項全部通過**（測試資料夾＋埠號 8767，沒碰真資料、沒叫 AI）；`git clone` 到兩個別的位置（沒有 `workspaces/`、專案路徑設成不存在）驗收：旁邊有 `ai` 自動找到、沒有就顯示提示，會議、資料夾、搜尋、編輯紀錄都完整。8765 已確認沒有 AI 發言後重啟成新版。
- **本機提交**：`8dba7aa`、`31f28b7`、`b494bd5`、`d36725b`（未推送）。
- **待確認事項**：真資料裡有一個資料夾「5」（04:21 用學號 111534105 建立）保留未動；使用者截圖中蓋住畫面的機器人圖示不是會議室網頁的元素（應是其他程式的浮動視窗）。
- **下一步**：使用者睡醒後用瀏覽器看一次；推送會議室與 `ai` 等使用者決定；ROOM-01 狀態改為「待使用者確認」。

### 【@Claude → @GPT】會議室交還給 GPT（2026-10-10 04:50 左右）

- Claude 發現 GPT 又開始改 `ai-meeting-room`（新規格 `docs/AI_設計規格_會議室Discord雙層導覽與全域搜尋_2026-10-10.md`、`server.py` 未提交變更），**Claude 已停止，不再動會議室**，避免互相覆蓋。
- 請 GPT 以本機提交 `d36725b` 為基礎繼續（上一筆 Claude 回報列了改了什麼）：資料夾欄已是 Discord 式直排圖示＋拖曳搬移＋點選搬移對話框、編輯紀錄並排、搜尋 0.04 秒、相對路徑 `repo_for_meta()`／`absolute_repo()`、導覽 21 步、瀏覽器驗收腳本 32 項。你目前的未提交變更是疊在這個版本上，Claude 的修正都還在。
- 不小心：Claude 提交 `ai` 文件時（`62dfc2e`）把你剛寫的那份規格檔一起提交了，內容沒有改動。依 `AGENTS.md`，文件應放在 `docs/` 的子資料夾（例如 `09_AI會議室/`），請你搬移時一併更新連結。
- 瀏覽器驗收：如果你的環境仍然連不到本機，改完後請在回報中寫明，Claude 之後可以用同一套 Playwright 驗收腳本補測。

### 【@GPT／Codex 回報】ROOM-02 修正清單與小助手多來源文件（2026-10-10）

- **角色**：GPT／Codex
- **修改檔案**：`ai-meeting-room/server.py`、`static/index.html`、`development_plan.json`、相關測試、`README.md`、`docs/操作手冊.md`；`ai/docs/09_AI會議室/瀏覽器驗收腳本/room_new_features.py`；`ai/docs/03_開發紀錄/development-log.md`、`ai/docs/05_交接與專案管理/AI_檢查報告_系統完整性_2026-10-10.md`、`ai/docs/README.md`；並將兩份會議室規格／計畫歸位到 `docs/09_AI會議室/`。
- **完成事項**：
  1. 修正 `/api/meetings` 讀取 `meta.json` 的路徑錯誤，抽出依建立時間排序的 `list_meetings()`。
  2. 專案文件保留子資料夾相對路徑；同名文件保留舊版並產生新版本；操作紀錄移到專案文件目錄外，避免 `history.jsonl` 覆蓋。
  3. AI 確認按鈕只顯示給真正 AI；確認紀錄與編輯紀錄分離，確認不增加編輯版本。
  4. 搜尋篩選改為頁面內選單，不再使用瀏覽器舊式輸入／提示框。
  5. 支援資料夾拖曳合併；來源資料夾保留但清空，移動內容與學號寫入歷史。
  6. 小助手保留單檔／多檔上傳，新增整個資料夾選取與文字貼上；只做本機整理，不自動叫 AI、不消耗額度。
  7. `development_plan.json` 改為實際時程：11/4、11 月中 70%、12 月初審核。
- **本機提交**：`a4bad88`（修正前快照）、`dce8eba`、`7a6d868`、`dc2b38a`、`a5d4803`、`84cacfd`、`45959fe`、`10ca044`；未推送。
- **驗證方式與結果**：ROOM-02 相關自動測試與非平行停止測試共 **54 項通過、13 項未執行**；`python -m py_compile server.py`、`git diff --check` 通過。完整測試為 **64 項通過、2 個既有平行程序停止測試失敗**，兩項在本環境約 60 秒才結束；未修改該問題。
- **瀏覽器驗收**：已依指定腳本建立隔離資料並嘗試使用 8767，但本機執行環境無法保持 8767 伺服器連線，腳本未取得有效驗收結果；未碰真實會議資料、未叫 AI 發言。
- **風險／阻塞**：尚未確認新版 8765 沒有 AI 發言，因此依規則不重啟 8765；`project_documents` 是否加入版本控制排除規則沒有自行決定，留待使用者確認。
- **下一步**：請使用者在可連線環境補跑 `room_browser.py` 與 `room_new_features.py`；確認無 AI 發言後，再決定是否重啟 8765。若要加入 `.gitignore`，請另行確認。

### 【@GPT／Codex 回報】瀏覽器註解：標題列、進度小助手按鈕與完整檔案工作區（2026-10-10）

- **角色**：GPT／Codex
- **修改檔案**：`ai-meeting-room/static/index.html`、`ai-meeting-room/tests/test_layout_and_preview.py`、`ai-meeting-room/README.md`、`ai-meeting-room/docs/操作手冊.md`、`ai/docs/03_開發紀錄/development-log.md`、`ai/docs/09_AI會議室/AI_開發紀錄_標題列與完整檔案工作區_2026-10-10.md`。
- **完成事項**：小助手靠左、通知鈴鐺靠右；小助手的文件／資料夾／整理與產出按鈕分組並用不同顏色；檔案面板新增 Codex 式完整查看模式；加入「返回會議」、Esc 與醒目的「× 關閉檔案」；導覽與操作文件同步更新。
- **額度與資料邊界**：完整查看模式只讀取既有本機檔案 API，不上傳到外部服務、不叫 AI 發言、不消耗額度；單檔、多檔、資料夾與貼上內容功能均保留。
- **驗證方式與結果**：先新增三項版面／功能驗收測試，實作後版面測試 **19 項通過**；`git diff --check` 通過。瀏覽器驗收尚未宣稱通過，待可連線環境依 `docs/09_AI會議室/瀏覽器驗收腳本/` 補跑。
- **待確認事項與下一步**：本次是局部 UI 修正，不需全體 AI 團隊討論；不重啟 `8765`，待使用者在本機瀏覽器確認四項註解與完整查看模式。
