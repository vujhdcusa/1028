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
