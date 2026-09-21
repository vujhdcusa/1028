# 開發日誌

## 使用方式

每次開發都新增一筆紀錄。重點不是寫很多，而是讓老師看到你有規劃、有測試、有修正。

## 日誌格式

```text
日期：
開發者：
今日目標：
修改檔案：
完成內容：
遇到問題：
解決方式：
測試結果：
下一步：
```

## 2026-09-15

日期：2026-09-15
開發者：田心于
今日目標：建立 BMAD 開發文件、Flask 專案骨架與環境設定。
修改檔案：

- docs/project-brief.md
- docs/prd.md
- docs/architecture.md
- docs/database-design.md
- docs/development-plan.md
- docs/development-log.md
完成內容：
- 建立專案需求與架構文件草案。
- 規劃大型系統開發流程。
- 加入系統管理者維護功能需求。
遇到問題：
- 尚未正式開始撰寫功能程式。
解決方式：
- 先完成規格、架構、資料庫與開發流程。
測試結果：
- 文件已建立，後續可交給 BMAD 產生 stories。
下一步：
- 建立 Flask 最小可啟動程式。

## 2026-09-15 MySQL 環境設定

日期：2026-09-15
開發者：liu
今日目標：設定 MySQL 開發資料庫，讓 Flask 專案可以連線。
修改檔案：
- .env
- .env.example
- docs/mysql-setup.md
- docs/database-setup.sql
- scripts/check_db.py
完成內容：
- 確認 MySQL Server 8.0 正在執行。
- 確認 MySQL 實際 port 為 3307。
- 建立 smart_learning_portfolio 資料庫。
- 建立 smart_learning_app 專案帳號。
- Flask 使用 .env 成功連線 MySQL。
- 建立並推動專案遠端儲存庫備份：
  - GitHub Repository: `https://github.com/LanyuLiu951127/smart-learning-portfolio.git` (`origin/main`)
  - GitLab Repository: `https://gitlab.com/LanyuLiu951127/smart-learning-portfolio.git` (`gitlab/main`)
- 驗證兩端儲存庫內容同步完成，具備雙備份與組員協作能力。
遇到問題：
- mysql 指令不在 PATH。
- root 不可空密碼登入。
- PyMySQL 連線時遇到 MySQL 8 預設驗證方式需要 cryptography 套件。
解決方式：
- 使用 mysql.exe 完整路徑操作。
- 使用 root 密碼建立專案帳號。
- 將 smart_learning_app 帳號驗證方式調整為 mysql_native_password。
測試結果：
- scripts/check_db.py 顯示 MySQL connected: 8.0.39。
下一步：
- 建立資料表 schema 或導入 Flask-SQLAlchemy migration。

## 2026-09-15 第一批資料表與 Model

日期：2026-09-15
開發者：liu
今日目標：建立第一批 Flask-SQLAlchemy models，並在 MySQL 建立資料表。
修改檔案：
- app/__init__.py
- app/extensions.py
- app/models/__init__.py
- app/models/user.py
- app/models/portfolio.py
- app/models/agent_task.py
- app/models/audit_log.py
- scripts/init_db.py
- tests/test_models.py
- pytest.ini
- docs/database-design.md
完成內容：
- 加入 SQLAlchemy 擴充初始化。
- 建立 users、student_profiles、portfolios、portfolio_evidence、agent_tasks、audit_logs。
- 建立 init_db.py，可初始化資料表與管理者測試帳號。
- 建立 admin 測試帳號。
- 新增 model 測試。
遇到問題：
- 第一次測試時測試資料誤寫入真實 MySQL。
- 刪除測試 user 時被 portfolios 外鍵保護擋住。
解決方式：
- 調整 create_app 支援 config_overrides，讓測試使用 sqlite:///:memory:。
- 先刪除測試 portfolio，再刪除測試 user。
測試結果：
- pytest 通過：3 passed。
- MySQL 目前資料表：agent_tasks、audit_logs、portfolio_evidence、portfolios、student_profiles、users。
- users 目前保留 admin 管理者帳號。
下一步：
- 實作登入頁與管理者登入流程。

## 2026-09-15 BMAD 規格書圖表與目錄整合

日期：2026-09-15
開發者：田心于
今日目標：整合 BMAD 圖表清單至規格設計書，並標明對應目錄與分工權責。
修改檔案：
- docs/資管科智慧學習歷程系統-系統規格設計書-開發閱讀版.md
- docs/development-log.md
完成內容：
- 檢查 `docs/diagrams.md` 中收錄的 Mermaid 圖表（系統架構圖、案例圖、流程圖、DFD、ERD、權限矩陣、管理者維護流程圖等）。
- 在 `資管科智慧學習歷程系統-系統規格設計書-開發閱讀版.md` 目錄及內文中補充視覺化圖表位置指引與備註。
- 完善工作分配章節，明確標示成員專題權責與單人獨立全端開發運作模式。
遇到問題：
- 規格書中部分圖表原本留空或預留於附錄，導致閱讀與導覽不便。
解決方式：
- 在目錄明確標註圖示位置（附錄五與各章小節），並完成對應章節的文字與圖示結構整合。
測試結果：
- 規格書目錄、工作分配與圖表導引已同步完成，內容結構完整。
下一步：
- 進入 Sprint 1：實作登入驗證、SESSION 管理與角色權限控制。

## 2026-09-15 BMAD 團隊協同完成內文圖表融合

日期：2026-09-15
開發者：田心于
今日目標：呼叫 BMAD 團隊（Analyst、PM、Architect、Dev、Reviewer、QA）將視覺化 Mermaid 圖表直接融合至規格書對應章節內文。
修改檔案：
- docs/資管科智慧學習歷程系統-系統規格設計書-開發閱讀版.md
- docs/development-log.md
完成內容：
- **Analyst (Mary)**：確認使用者案例（UC01-UC14）與流程細節。
- **PM (John)**：補強功能性與非功能性需求層級。
- **Architect (Winston)**：將系統架構圖、DFD、AI Agent 任務流程圖與 ERD 圖直接嵌至第 4、5 章對應小節。
- **Dev (Amelia)**：重構 Markdown，清理尾端重複之附錄區塊。
- **Reviewer & QA**：驗證文件格式、Mermaid 語法正確性與章節對應關係。
遇到問題：
- 附錄五預留區塊與內文圖表有重複，且圖表原本分散在附錄。
解決方式：
- 將圖表全面提升融入第 3 章、第 4 章、第 5 章與第 7 章正文中，並移除冗餘尾端附錄。
測試結果：
- Markdown 手冊預覽正常，所有 Mermaid 流程圖、案例圖、架構圖、DFD 與 ERD 均能在對應章節直接閱讀。
下一步：
- 開始 Sprint 1 功能實作（登入 / 登出及認證路由）。

## 2026-09-15 規格書高解析度實體流程圖與架構圖嵌入

日期：2026-09-15
開發者：田心于
今日目標：產出符合專題報告規範之高解析度實體流程圖、案例圖、架構圖與 ERD 圖，並直接嵌入規格設計書。
修改檔案：
- docs/資管科智慧學習歷程系統-系統規格設計書-開發閱讀版.md
- docs/images/portfolio_login_flowchart.jpg
- docs/images/portfolio_usecase_diagram.jpg
- docs/images/portfolio_system_architecture.jpg
- docs/images/portfolio_erd_diagram.jpg
- docs/development-log.md
完成內容：
- 生成並嵌入「系統首頁與使用者登入流程圖」（含訪客、學生、教師、管理者權限分流與判斷條件）。
- 生成並嵌入「使用者案例圖 (Use Case Diagram)」。
- 生成並嵌入「系統總架構圖 (System Architecture Diagram)」4 層分層圖。
- 生成並嵌入「實體關聯圖 (ERD Diagram)」6 大核心資料表實體關聯圖。
- 更新規格書目錄與章節圖檔連結。
遇到問題：
- 原文字版 Mermaid 流程圖在報告書排版中缺乏視覺化實體質感。
解決方式：
- 採用高解析度教育報告風格圖檔渲染，並統一集中保存在 `docs/images/`，直接以標準 Markdown 圖檔語法引用。
測試結果：
- 規格書中所有圖表均呈現標準圖檔，格式清爽，可直接複製至專題報告書或簡報。
下一步：
- 進入 Sprint 1：撰寫登入視圖、驗證機制與 Session 角色路由。

## 2026-09-15 Mermaid 圖表與規格書完整目錄重整

日期：2026-09-15
開發者：田心于
今日目標：依 `docs/diagram-style-guide.md` 重整 Mermaid 圖表、匯出圖片，並補全規格設計書之詳細目錄與子章節。
修改檔案：
- docs/diagrams.md
- docs/資管科智慧學習歷程系統-系統規格設計書-開發閱讀版.md
- generate_images.py
- docs/images/
- docs/development-log.md
完成內容：
- 依規範優化所有 Mermaid 圖表（加入系統邊界、適當 node 樣式與清晰節點命名）。
- 使用 Python 腳本整合 Kroki API，將 10 張 Mermaid 圖表完整渲染並匯出至 `docs/images/` 目錄。
- 重構規格設計書（`資管科智慧學習歷程系統-系統規格設計書-開發閱讀版.md`）之目錄（TOC），全面包含母節（H2）、子節（H3）及孫節（H4）之完整目錄與超連結導覽。
遇到問題：
- 原始規格書目錄僅列至母節與第一層子節，未能反映完整章節架構與流程小節。
- 直接對 Kroki 發送 GET 請求時若缺少 User-Agent 會回傳 HTTP 403。
解決方式：
- 自行解析全文 Markdown 標題階層，重構具備完整縮排與錨點連結的 Markdown 目錄。
- 在 Python 匯出腳本中加上標準 User-Agent header 與 Base64+Zlib 壓縮處理。
測試結果：
- 規格書目錄點擊跳轉正常，完整展現包含需求分析、AI Agent 限制、資料字典及附錄規範等所有小節。
- `docs/images/` 內 10 張 PNG 圖檔全數產生且無遺漏。
下一步：
- 展開 Sprint 1 前端與後端登入驗證實作。


## 2026-09-15 專案檔案結構整理與冗餘清理

日期：2026-09-15
開發者：田心于 / DMS
今日目標：清理專案中重複的舊版草案文件、備份腳本與測試圖檔，維持目錄乾淨清晰。
修改檔案：
- 刪除：`docs/prd.md`
- 刪除：`docs/architecture.md`
- 刪除：`docs/database-design.md`
- 刪除：`docs/project-brief.md`
- 刪除：`docs/development-plan.md`
- 刪除：`docs/admin-maintenance.md`
- 刪除：`scripts/generate_diagram_png.js`
- 刪除：`docs/images/demo_flowchart.png`
- 刪除：`docs/images/demo_flowchart_hd.jpg`
- 搬移：`docs/generate_images.py` -> `scripts/generate_images.py`
完成內容：
- 清理已無作用的舊草案檔（內容已全面併入主規格書）。
- 將腳本統一歸納至 `scripts/` 資料夾，使 `docs/` 資料夾專注於存放文件與圖檔。
- 清除未使用的圖片測試檔。
測試結果：
- `docs/` 及 `scripts/` 結構清爽有序，主要規格書及圖片引用均保持正常。
下一步：
- 展開 Sprint 1 前端與後端登入驗證實作。

## 2026-09-15 專案設定與程式碼細節修正

日期：2026-09-15
開發者：田心于 / GDS / DMS
今日目標：修復 README 舊文件引用、.env.example 設定、MySQL 指南狀態、Admin 密碼讀取及 Flask 安全性與上傳限制設定。
修改檔案：
- `README.md`
- `.env.example`
- `docs/mysql-setup.md`
- `scripts/init_db.py`
- `run.py`
- `app/config.py`
- `docs/development-log.md`
完成內容：
1. **README.md**：修正「文件位置」列表，移除已被清理的 6 個舊檔案，替換為現有的 5 個核心文件與圖表檔。
2. **.env.example**：將 `DB_USER` 預設值修正為專案帳號 `smart_learning_app`，並新增 `ADMIN_DEFAULT_PASSWORD`。
3. **docs/mysql-setup.md**：重構為「已完成設定狀態」、「新環境初始化步驟」與「歷史檢測與除錯紀錄」，消除前後不一致問題。
4. **scripts/init_db.py**：支援從 `.env` 讀取 `ADMIN_DEFAULT_PASSWORD`，並於印出訊息時提供警示提醒。
5. **run.py**：改由 `FLASK_DEBUG` 環境變數動態控制 `debug` 模式。
6. **app/config.py**：新增 Production 環境無 `SECRET_KEY` 時拋出錯誤機制；讀取 `MAX_CONTENT_LENGTH_MB` 並自動轉換為 Flask `MAX_CONTENT_LENGTH`（Byte）。
測試結果：
- 執行 `.\.venv\Scripts\python.exe -m pytest -q` 順利通過 (3 passed)。
下一步：
- 展開 Sprint 1 前端與後端登入驗證實作。

## 2026-09-16 系統設計文件同步與 UI/UX 規格補強

日期：2026-09-16
開發者：田心于 / Codex
今日目標：依 Google Docs 最終版與 ChatGPT 分享對話內容，將新版系統設計、角色同步、MVP 切分與 UI/UX 方向整合回本地開發文件。
修改檔案：
- `docs/system-design-action-plan.md`
- `docs/diagrams.md`
- `docs/資管科智慧學習歷程系統-系統規格設計書-開發閱讀版.md`
- `docs/development-log.md`
完成內容：
- 新增 `docs/system-design-action-plan.md`，整理系統設計更新行動計畫。
- 補上角色同步檢查，統一 `student`, `teacher`, `reviewer`, `staff`, `admin` 等角色方向。
- 補上 MVP / Phase 2 / Future 功能切割，避免開發範圍失控。
- 在 `docs/diagrams.md` 新增文件與開發同步流程圖、角色權限同步流程圖、MVP 主流程圖與 UI/UX 視覺概念流程圖。
- 在主規格書新增「第零節 系統設計版本同步原則」。
- 在主規格書補上科辦／行政角色、批次分派與通知 Use Case、權限矩陣、`Users.role` 允許值。
- 新增「附錄五、網頁視覺與使用體驗設計原則」，正式寫入「把五年，拼成下一站」與 Interactive Editorial Learning Journey 設計方向。
遇到問題：
- 一開始未同步更新 `development-log.md`，造成文件更新紀錄缺漏。
- 舊的 `environment-check.md` 與後續 `mysql-setup.md` / `development-log.md` 狀態不一致，需要以實測結果為準。
解決方式：
- 補寫本次同步紀錄。
- 將後續開發流程調整為：每次修改文件或程式後，必須同步補 `docs/development-log.md`。
測試結果：
- 執行 `.\.venv\Scripts\pytest.exe -q` 通過，結果為 `3 passed`。
下一步：
- 開始 Sprint 1 前，先整理 Git 狀態與 `.gitignore`，再實作登入、Session 與角色權限控制。

## 2026-09-16 開發前總檢查

日期：2026-09-16
開發者：田心于 / Codex
今日目標：檢視整份專案大綱、文件、環境、資料庫與測試狀態，判斷是否可以開始正式開發系統。
檢查檔案與項目：
- `README.md`
- `docs/environment-check.md`
- `docs/mysql-setup.md`
- `docs/system-design-action-plan.md`
- `docs/diagrams.md`
- `docs/資管科智慧學習歷程系統-系統規格設計書-開發閱讀版.md`
- `app/`
- `tests/`
- `scripts/check_db.py`
- Git 狀態
完成內容：
- 確認 Flask app 可載入。
- 確認目前測試通過。
- 確認 MySQL 可連線，版本為 `8.0.39`。
- 確認目前資料庫已存在第一批資料表：`users`, `student_profiles`, `portfolios`, `portfolio_evidence`, `agent_tasks`, `audit_logs`。
- 確認主規格書已具備角色、流程、ERD、DFD、MVP 切分、AI 限制與 UI/UX 附錄。
目前仍需處理：
- 專案沒有 `.gitignore`，且 Git 狀態中出現 `__pycache__` 與 `.pyc` 快取檔被加入追蹤/暫存。
- 登入、登出、Session 與角色權限尚未實作。
- 規格書列出的完整核心資料表尚未全部實作，目前僅完成 MVP 第一批模型。
- API Specification 仍未獨立整理成完整端點清單。
- Data Dictionary 目前仍是摘要，尚未列出所有欄位型別、必填、預設值與狀態允許值。
- UI Wireframe 尚未正式建立。
測試結果：
- `.\.venv\Scripts\pytest.exe -q` 通過，結果為 `3 passed`。
- `.\.venv\Scripts\python.exe scripts\check_db.py` 通過，顯示 `MySQL connected: 8.0.39`。
結論：
- 目前專案已可進入 Sprint 1 開發，但不能視為整個系統 100% 完成或完全沒有重大風險。
- 建議先完成 Git 清理、`.gitignore`、登入驗證、Session、角色導頁與基礎權限測試，再進入學生歷程 CRUD。
下一步：
- 建立 `.gitignore`。
- 移除不應追蹤的 `__pycache__` / `.pyc` 快取檔。
- 實作 Sprint 1：登入驗證、Session 管理、角色權限控制。

## 2026-09-17 期中核心第一階段開發與完整軌跡

日期：2026-09-17
開發者：Codex
今日目標：依正式規格書與 `期中開發補充.md` 開始期中核心開發，先完成登入、Session 與角色權限基礎，並建立可持續追加的完整開發軌跡。
修改檔案：
- `app/routes/main.py`
- `app/templates/login.html`
- `app/templates/dashboard.html`
- `tests/test_auth.py`
- `docs/期中開發補充.md`
- `docs/midterm-development-log.md`
- `docs/development-log.md`
完成內容：
- 新增共用登入與登出流程。
- 新增學生、教師／評審、管理員的角色導頁與後端 RBAC 保護。
- 新增學生／教師第一版工作區頁面。
- 依 TDD 先建立 4 項登入與權限測試；功能不存在時先得到 `4 failed`，完成最小實作後得到 `4 passed`。
- 建立完整期中開發軌跡，區分已完成、進行中、未開始與不可宣稱完成項目。
遇到問題：
- 原本只有首頁與管理員佔位頁，沒有登入、Session 或權限保護，無法開始期中端到端流程。
解決方式：
- 先完成核心流程所需的最小認證基礎，並把後續成果提交、AI 初檢、教師覆核與 V2 版本拆成獨立階段。
測試結果：
- `pytest -q tests/test_auth.py`：4 passed。
- 尚未宣稱完整期中核心流程完成；成果提交、快照、AI、教師覆核與版本管理仍待開發。
下一步：
- 依 M-01 至 M-10 順序建立學習目標、提交版本、目標快照與學生提交測試。

## 2026-09-21 目前系統進度重新評估

日期：2026-09-21
開發者：Codex
今日目標：依最新程式、測試、規格與公開來源快照，重新區分規劃成熟度與實際程式完成度。
完成內容：
- 重新執行專案測試，於 `D:\democase\ai` 執行 `pytest -q`，結果為 `7 passed`。
- 確認目前已實作登入、登出、Session、角色導頁與後端 RBAC。
- 確認目前只有第一批六類資料表，尚未建立專題類型、成果要求模板、學生套用、目標快照、教師覆核與 AI 分析資料表。
- 將規格成熟度與實際程式完成度分開記錄，避免用文件規劃百分比代表功能已完成。
目前評估：
- 正式規格書約 85%。
- 學校需求整合約 70%。
- 教師端規劃約 75%。
- 學生端規劃約 82%。
- 管理端規劃約 78%。
- 期中核心實際程式約 20% 左右，尚未形成完整端到端流程。
下一步：
- 先依 114 學年度「專題審查學習目標與評量對照表」建立資訊軟體開發組與商務網站經營組的成果要求範本。
- 建立 `project_types`、`requirement_templates`、`requirement_items`、`student_project_assignments`。
- 以 `admin` 建立安全的專題類型與成果要求維護頁。
- 再進入學生提交與目標快照，之後才做公開來源 AI Agent。

## 2026-09-21 需求規則修正：專題時程與證照／競賽抵免

完成內容：
- 修正學生歷程階段規劃：三年級以累積作品、證照與競賽為主，專題方向、分組與指導教師改為五年級專題正式啟動前。
- 修正抵免規則：抵免來源為學校及各科系認證的證照與競賽／比賽成果，合計至多 6 學分；不再把實習本身列為此項抵免來源。
- 將認證清單、適用年度、證明文件與審核結果列為需版本化管理的資料。
測試結果：
- 本次為規格文件修正，未修改程式碼。
- 修正內容已寫入 `需求資料蒐集與規則補充表.md` 與 `midterm-development-log.md`。
下一步：
- 依修正後的抵免規則設計證照／競賽資料模型與管理員維護欄位。

## 2026-09-17 正式規格書與期中核心範圍對照

日期：2026-09-17
開發者：Codex
今日目標：以正式專題規格設計書為基準，整理完整系統願景與期中核心開發範圍的關係。
修改檔案：
- `docs/資管科智慧學習歷程系統-系統規格設計書-開發閱讀版.md`
- `docs/期中開發補充.md`
- `docs/development-log.md`
完成內容：
- 保留五專一年級至五年級學習、證照、專題、實習、升學／就業整合的完整產品定位。
- 在正式規格書加入「正式規格與期中核心」閱讀指引，並連結期中對照文件。
- 建立期中核心範圍對照表，整理系統分層、章節對應、M-01 至 M-10 驗收項目及科方交付要求。
- 明確區分長期願景、期中核心、期中支援、期末擴充與 Future，避免把規劃功能誤認為已完成。
遇到問題：
- 正式規格書同時包含完整產品願景與多階段功能，若沒有另外標示，容易與期中交件範圍混淆。
解決方式：
- 不取代或刪除正式規格書，新增獨立的 `期中開發補充.md` 作為開發與交付管理文件。
測試結果：
- 已檢查正式規格書新增閱讀指引、對照文件連結與期中驗收表內容。
- 未修改程式碼或資料庫，尚未宣稱任何期中功能已完成。
下一步：
- 依對照文件補齊 API Specification、Data Dictionary 與期中測試案例，再開始核心流程實作。

## 2026-09-17 公開校方來源瀏覽與本機快照

日期：2026-09-17
開發者：Codex
今日目標：重新瀏覽需求補充表提供的公開校方網址，下載可公開取得的頁面與附件，供規格核對與後續 AI Agent 來源管理使用。
修改檔案：
- `school/public-sources/README.md`
- `school/public-sources/*.html`
- `school/public-sources/*.doc`
- `school/public-sources/*.odt`
- `school/public-sources/*.pdf`
- `docs/development-log.md`
完成內容：
- 保存康寧大學官網首頁、課表查詢、抵免系統公開登入頁、校內轉科公告及資管科公開頁面。
- 保存資管科專題書面繳交公告及附件：著作授權書、成果報告封面／書背格式的 Word、ODT、PDF 版本。
- 保存 1151 學期五專資訊管理科五年級 A 班教學計畫與實務專題課程綱要頁面。
- 建立 `school/public-sources/README.md`，記錄來源網址、抓取日期、初步可用線索與尚待確認項目。
- 未登入抵免系統、未讀取私人資料，也未下載 Google Drive 未確認公開權限的內容。
核對結果：
- 公開教學計畫頁顯示五專資訊管理科五年級 A 班的 1151 學期課程資料。
- 公開課程綱要頁顯示「實務專題」為 1 學分、專題課，並描述分組實作與專題流程。
- 114 學年度專題繳交公告包含每組三本紙本、每本附光碟、PDF 上傳與光碟電子檔要求；這些規則仍需依適用年度確認。
限制：
- 部分資管科頁面無法由瀏覽工具直接解析，但已用公開 HTTP 頁面下載保存。
- 111 級實務專題規定、114 學年度公告與 115 學期課程資料不可直接視為同一年度規則。
下一步：
- 將已核對來源轉成正式規格的年度化規則與成果要求模板；後續由 `admin` 管理假帳號與專題資料，不另設 `Administrator` 網站使用者。

## 2026-09-21 專題成果評量範本與角色收斂

日期：2026-09-21
開發者：Codex
今日目標：依去年度專題審查學習目標與評量對照表，將專題功能收斂為學習歷程中的小組成果，不另做專題行政系統。
修改檔案：
- `docs/資管科智慧學習歷程系統-系統規格設計書-開發閱讀版.md`
- `docs/需求資料蒐集與規則補充表.md`
- `docs/midterm-development-log.md`
- `docs/專題成果評量範本-第一版.md`
完成內容：
- 確認專題由小組共用成果、個人分工與答詢紀錄組成；不延伸為場地、委員會或網站公告系統。
- 移除正式規格中的獨立 `reviewer` 登入角色設計；教師共同討論，科主任或科助登錄共同結論。
- 建立資訊軟體開發組、商務網站經營組，以及期中／兩次複評的第一版成果要求範本。
- 將 111 級實施計畫與 114 學年度評量對照表標示為年度化參考，不視為永久固定規則。
限制：
- 本次只更新規格與開發軌跡，未修改 Python 程式、資料庫或期中核心實作完成度。
下一步：
- 以成果要求範本為依據，設計並測試 `project_types`、`requirement_templates`、`requirement_items`、`student_project_assignments`。

## 2026-09-21 核心流程第一版實作

日期：2026-09-21
開發者：Codex
今日目標：依 AI 交接摘要完成角色、模板、學生提交、審查版本與 AI 初檢第一版。
修改檔案：
- `app/models/project.py`
- `app/models/submission.py`
- `app/models/review.py`
- `app/services/portfolio_service.py`
- `app/services/review_service.py`
- `app/services/ai_service.py`
- `app/routes/student.py`、`app/routes/review.py`、`app/routes/staff.py`
- `app/security.py`、`app/config.py`
- `tests/` 新增角色、模型、提交、審查、AI 與安全測試
完成內容：
- 統一正式角色為 `student`、`teacher`、`staff`、`admin`，拒絕 `reviewer` 登入導頁。
- 新增專題類型、年度模板、成果要求、小組、成員與學生模板分派模型。
- 完成學生作品新增／編輯、提交版本、要求快照與私有證據下載／上傳。
- 完成教師分派、staff／admin 共同結論、補件版本與 V1 歷程保留。
- 完成規則式 AI 證據初檢；AI 只能保存候選結果，不會修改正式審查結論。
- 加入 CSRF token 基礎檢查、上傳檔名／副檔名檢查及管理者密碼不輸出的初始化行為。
測試結果：
- `pytest -q`：22 passed。
已知限制：
- 尚未接外部 LLM、病毒掃描、學校主資料庫或正式 migration 管理。
- 管理端模板 CRUD 與完整 UI 仍是最小可驗收頁面，需下一階段補齊。
下一步：
- 補齊 staff 模板／小組管理表單、檔案掃描策略與 Alembic migration。

## 2026-09-21 Agent 工具與產物目錄整理

日期：2026-09-21
開發者：Codex
今日目標：整理 BMAD、Codex 與 AI 工具設定，降低專案檔案瀏覽的混亂程度，同時保留工具相容性。
修改檔案／目錄：
- `agent/README.md`
- `.vscode/settings.json`
- `agent/codex/`：由 `ai/codex/` 搬移
- `agent/bmad/`：由 `ai/_bmad/` 搬移
- `ai/_bmad/`：建立指向 `agent/bmad/` 的 Windows Junction
- `agent/codex` 內報告腳本的舊路徑
完成內容：
- Codex 報告、工作腳本與歷史產物集中至 `D:\democase\agent\codex`。
- BMAD 實體資料集中至 `D:\democase\agent\bmad`，保留 `ai/_bmad` 相容路徑，避免 BMAD 專案根目錄解析失效。
- VS Code 以 `files.exclude` 與 `search.exclude` 隱藏 AI 工具設定、虛擬環境、快取、執行資料與相容 Junction；未刪除這些資料。
- 後續 AI 產生的 Markdown 仍統一放在 `D:\democase\ai\docs`。
驗證結果：
- Flask 測試：`22 passed`。
- BMAD 新位置與相容路徑均可讀取。
- Codex 內沒有殘留 `D:\democase\ai\codex` 舊路徑。
恢復方式：
- 編輯 `.vscode/settings.json`，刪除或將對應 `files.exclude`／`search.exclude` 項目設為 `false`，即可在 VS Code 顯示。
- 這些設定只影響 VS Code 顯示與搜尋，不會刪除檔案；PowerShell 使用 `Get-ChildItem -Force` 仍可查看。

## 2026-09-21 UI/UX 設計與動畫規格收斂

日期：2026-09-21
開發者：Codex
今日目標：依參考圖片、既有 UI/UX 對話稿與使用者回饋，定稿首頁與學生端的版面、文案與動畫方向。
修改檔案：
- `docs/UI_UX_設計與動畫規格_2026-09-21.md`
- `docs/system-design-action-plan.md`
- `docs/資管科智慧學習歷程系統-系統規格設計書-開發閱讀版.md`
- `docs/AI_交接摘要_2026-09-21.md`
完成內容：
- 將 UI 定位為「資訊豐富的編輯式學習歷程介面」，不再以大量空白作為主要風格。
- 定義 `Experience Layer` 與 `Work Layer`，分離展示感與工作效率。
- 定義文字密度、受控不對稱、台灣口語文案、色彩、字體、版面、元件、響應式與動畫 token。
- 規劃首頁與學生端的資料漂浮、Scroll 路徑、節點亮起、拼圖填入、成果卡進場與目標分岔動畫。
- 加入 `prefers-reduced-motion`、動畫時間上限與表單／審查頁低動畫規則。
驗證結果：
- 已讀取並對照 UI/UX 對話稿中的 20 張參考圖與既有設計討論。
- 已確認完整規格文件可在 `D:\democase\ai\docs` 找到。
下一步：
- 建立 `base.html`、共用 CSS design tokens、`JourneyPath`、`PieceCard`、`StatusChip`、`AdviceCard` 與 `DataTable`，再實作公開首頁與學生首頁動畫。

## 2026-09-21 UI 共用骨架與學生端第一版完成

日期：2026-09-21  
開發者：Codex  
今日目標：將已定稿的 UI/UX 規格落成可操作的公開首頁、學生首頁與成果管理流程。

修改檔案：

- `app/templates/base.html`
- `app/static/css/design-system.css`
- `app/static/js/motion.js`
- `app/templates/index.html`
- `app/templates/dashboard.html`
- `app/templates/login.html`
- `app/templates/student_portfolio.html`
- `app/templates/student_portfolio_form.html`
- `app/routes/main.py`
- `tests/test_ui_shell.py`

完成內容：

- 建立共用 `base.html`，統一語系、RWD viewport、設計系統 CSS、動畫腳本與鍵盤使用者的跳到主要內容連結。
- 公開首頁改為「把五年，拼成下一站」的資訊豐富敘事版面，包含浮動成果卡、五年路徑、未來分岔與台灣常見網路服務語氣的文案。
- 學生首頁改為個人化學習路徑，會顯示實際已建立的成果數量、五段路徑、可補上的拼圖與下一步提醒。
- 學生的成果清單、成果編輯與登入頁接入同一套視覺語言，避免操作流程在不同頁面出現斷裂感。
- 使用 CSS 動畫與 `IntersectionObserver` 實作卡片漂浮、捲動進場與路徑亮起；並支援 `prefers-reduced-motion`，使用者選擇減少動態時不會被強制播放動畫。
- 先新增 UI 行為測試，再完成模板與路由實作，涵蓋公開首頁、學生首頁與成果清單是否使用共用 UI 外殼。

驗證結果：

- `pytest -q tests/test_ui_shell.py`：3 passed。
- `pytest -q`：25 passed。
- `git diff --check`：無空白與 patch 格式錯誤。

下一步：

- 以相同的 Work Layer 規則，整理教師、科辦與系統管理者的待辦清單、篩選列與資料表格畫面。

## 2026-09-21 Work Layer 後台工作介面第一版完成

日期：2026-09-21  
開發者：Codex  
今日目標：把教師、科辦／行政與系統管理者從通用提示頁，改為可讀取既有資料的低動畫工作介面。

修改檔案：

- `app/routes/main.py`
- `app/routes/review.py`
- `app/templates/dashboard.html`
- `app/templates/review_queue.html`
- `app/templates/admin_dashboard.html`
- `app/static/css/design-system.css`
- `tests/test_work_layer.py`

完成內容：

- 教師工作台顯示實際被指派的審查數、最近指派項目與「我的審查」入口；教師只能閱讀與提供意見，共同結論仍由科辦登錄。
- 科辦／行政工作台顯示資料庫中狀態為 `submitted` 的送件，並直接使用既有路由登錄核可、需要補正或退件的共同結論。
- 系統管理總覽顯示啟用學生、教師、科辦帳號、送件總數、待處理送件與最近送件動態。
- 審查清單改用共用版型，讓教師從工作台進入清單時維持一致的導覽與資料層級。
- Work Layer 保持資訊密度與操作優先，僅使用必要的按鈕互動，不加入學生端的漂浮或捲動敘事動畫。
- 新增資料驅動的端到端測試，確認三種角色會收到對應的工作畫面與既有功能入口。

驗證結果：

- `pytest -q tests/test_work_layer.py`：3 passed。
- 完整回歸與程式編譯檢查會在本次收尾後重新執行。

下一步：

- 補上教師可提交建議、科辦可查看既有審查意見與管理者帳號／規則維護頁面，再完成工作流程的細節串接。

## 2026-09-21 教師意見與共同結論流程完成

日期：2026-09-21  
開發者：Codex  
今日目標：讓教師意見能安全地交給科辦參考，再由科辦登錄共同審查結論。

修改檔案：

- `app/models/review.py`
- `app/models/__init__.py`
- `app/services/review_service.py`
- `app/routes/main.py`
- `app/routes/review.py`
- `app/templates/dashboard.html`
- `app/templates/review_queue.html`
- `app/static/css/design-system.css`
- `tests/test_teacher_feedback_flow.py`

完成內容：

- 新增 `TeacherReviewFeedback`，把教師的個別意見與科辦的共同結論分開保存，避免角色責任混在同一筆資料中。
- 教師只能對自己被指派的送件提交非空白意見；未被指派的教師會收到 `403`。
- 教師工作台與「我的審查」清單都可送出意見，且會保留已送出的內容。
- 科辦工作台會在每一筆已送審成果中顯示教師意見，再使用既有的核可／補正／退件功能登錄共同結論。
- 科辦登錄結論後，送件狀態會由既有服務更新；教師無法直接改變共同結論。

驗證結果：

- `tests/test_teacher_feedback_flow.py`：4 passed，涵蓋教師提交、未指派拒絕、空白意見拒絕，以及科辦登錄後狀態更新。
- `pytest -q`：32 passed。

下一步：

- 建立資料庫 migration，讓新的教師意見資料表可安全套用到既有 MySQL 開發資料庫；再補上管理者的帳號與規則維護功能。

## 2026-09-21 教師意見資料表 Migration 完成

日期：2026-09-21  
開發者：Codex  
今日目標：讓教師意見資料表可安全、可追蹤地套用至既有 MySQL 開發資料庫。

修改檔案：

- `app/extensions.py`
- `app/__init__.py`
- `migrations/`
- `migrations/versions/52b9ba9ea108_add_teacher_review_feedback.py`
- `tests/test_migration_setup.py`
- `docs/03_開發紀錄/mysql-setup.md`

完成內容：

- 啟用已列在相依套件中的 Flask-Migrate，Flask CLI 現可使用 `db` migration 指令。
- 建立第一份增量 migration，僅新增 `teacher_review_feedback`、送件索引與教師索引，不會改動既有送件內容。
- 提供 `downgrade()`，可在確認不需保留教師意見時移除這份 migration 所建立的資料表。
- 更新 MySQL 文件，列出套用前檢查、`db current`、`db upgrade` 與回復操作的安全提醒。

驗證結果：

- Flask `db` 指令註冊測試通過。
- SQLite 實際執行 `db upgrade` 後，已驗證資料表與五個必要欄位存在。
- SQLite 實際執行 `db downgrade base` 後，已驗證資料表被移除。

下一步：

- 由使用者在確認的 MySQL 開發資料庫執行 `db upgrade`；接著建立管理者帳號與規則維護功能。

## 2026-09-21 管理者帳號與年度規則維護第一版完成

日期：2026-09-21  
開發者：Codex  
今日目標：提供系統管理者安全的帳號狀態控制，以及專題類型、成果模板與要求項目的年度化設定介面。

修改檔案：

- `app/routes/admin.py`
- `app/__init__.py`
- `app/templates/admin_dashboard.html`
- `app/templates/admin_accounts.html`
- `app/templates/admin_rules.html`
- `app/static/css/design-system.css`
- `tests/test_admin_management.py`

完成內容：

- 新增只限 `admin` 使用的帳號管理頁；可啟用／停用其他帳號，但不可停用目前登入的管理者，也不提供刪除帳號。
- 新增年度規則管理頁，可依序建立專題類型、成果模板與要求項目，並可啟用／停用類型與模板。
- 要求項目可設定階段、排序、說明，以及必填或選填；預設為必填，避免漏填規則被意外放寬。
- 管理頁不提供刪除已使用規則，也不自行填入未經學校確認的正式規定。
- 補齊桌面與行動版表單排列，維持 Work Layer 的資料優先與低動畫原則。

驗證結果：

- `tests/test_admin_management.py`：3 passed，涵蓋帳號停用保護、規則階層建立、必填／選填與非管理者拒絕存取。
- `pytest -q`：38 passed。

下一步：

- 在確認的 MySQL 開發資料庫執行 migration；之後可補上管理者帳號建立／密碼重設，以及已使用規則的版本化編輯流程。

## 2026-09-21 完整對話與開發交接文件建立

日期：2026-09-21  
開發者：Codex  
今日目標：讓使用者可開啟新的 AI 對話，同時保留本次合作的需求、決策、程式狀態與待辦。

修改檔案：

- `docs/05_交接與專案管理/AI_完整對話與開發交接_2026-09-21.md`
- `docs/README.md`
- `docs/03_開發紀錄/development-log.md`

完成內容：

- 整理使用者的資料夾、文件、UI／UX、角色流程、migration 與管理端需求。
- 記錄已完成功能、重要檔案地圖、測試命令、MySQL 寫入限制與目前進度。
- 提供可直接貼到新 AI 對話的接手指令。

下一步：

- 使用者可將此文件附加或貼到新對話；新 AI 應先依文件完成 MySQL migration 前檢查與展示驗收規劃。
