# 系統流程圖與架構圖

> 本文件的 Mermaid 原始碼是正式圖表來源。所有圖採白底、細灰框、深灰箭頭與繁中易讀字型；角色與系統節點只以低飽和淡色區分。
> AI 初檢目前只呈現 GitHub／README／佐證的缺漏與不一致候選問題；AI 不直接形成通過、退件、分數或其他正式結論。

## 1. 圖表閱讀方式

- **P0 根流程**：學生從上傳資料到取得可使用文件的完整流程。
- **檢核與補件**：學生、教師／導師、科辦／行政各自負責的確認工作。
- **P1／P2／Future**：延伸功能，不能取代 P0 根流程。

## 2. 角色與責任圖

```mermaid
%%{init: {'theme':'base','themeVariables': {'fontFamily':'Microsoft JhengHei, Noto Sans TC, Arial, sans-serif','primaryColor':'#F3F4F6','primaryTextColor':'#111827','primaryBorderColor':'#9CA3AF','lineColor':'#6B7280','edgeLabelBackground':'#FFFFFF'}}}%%
flowchart TD
    classDef student fill:#DBEAFE,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef teacher fill:#DCFCE7,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef staff fill:#EDE9FE,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef system fill:#F3F4F6,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef ai fill:#FEF3C7,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef ai fill:#FEF3C7,stroke:#9CA3AF,color:#111827,stroke-width:1px;

    Student[學生]:::student --> S1[上傳、校正與確認本人資料]:::student
    Student --> S2[查看 AI 初檢問題並補正]:::student
    Student --> S3[編輯文件草稿與下載 Word]:::student
    Teacher[教師／導師]:::teacher --> T1[檢視被指派學生資料]:::teacher
    Teacher --> T2[查看 AI 初檢報告]:::teacher
    Teacher --> T3[提供輔導與補件建議]:::teacher
    Staff[科辦／行政]:::staff --> F1[維護年度課程與證照規則]:::staff
    Staff --> F2[確認需人工判定的結論]:::staff
    Admin[系統管理者]:::staff --> A1[管理帳號、權限與系統設定]:::staff
    Admin --> A2[維護操作紀錄與服務狀態]:::staff
    System[系統]:::system --> P0[P0：整理、分類與產出]:::system
    AI[分析服務]:::ai --> G1[AI 初檢 GitHub 與佐證問題]:::ai
    G1 --> G2[產生缺漏／不一致候選提示]:::ai
    G2 -.學生與教師人工確認；不直接定案.-> F2
```

## 3. 學生學習歷程、目標與送審流程

```mermaid
%%{init: {'theme':'base','themeVariables': {'fontFamily':'Microsoft JhengHei, Noto Sans TC, Arial, sans-serif','primaryColor':'#F3F4F6','primaryTextColor':'#111827','primaryBorderColor':'#9CA3AF','lineColor':'#6B7280','edgeLabelBackground':'#FFFFFF'}}}%%
flowchart TD
    classDef student fill:#DBEAFE,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef system fill:#F3F4F6,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef teacher fill:#DCFCE7,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef staff fill:#EDE9FE,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef alert fill:#FEE2E2,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef ai fill:#FEF3C7,stroke:#9CA3AF,color:#111827,stroke-width:1px;

    Start([開始]) --> Login[學生登入]:::student
    Login --> Goal{是否已設定目標？}
    Goal -- 否 --> Choose[選擇升學、就業或實習目標]:::student
    Choose --> Map[建立個人五年學習地圖]:::system
    Goal -- 是 --> Upload
    Map --> Upload[上傳成績單、證照、作品與其他資料]:::student
    Upload --> Extract[系統擷取可辨識欄位]:::system
    Extract --> Draft[建立可校正資料草稿]:::system
    Draft --> Confirm[學生校正、補充與確認]:::student
    Confirm --> Complete{資料是否完整？}
    Complete -- 否 --> Missing[顯示待補資料]:::alert
    Missing --> Upload
    Complete -- 是 --> Rules[套用適用年度課程與證照規則]:::system
    Rules --> Review{是否需要人工確認？}
    Review -- 是 --> Teacher[教師／導師提供回饋]:::teacher
    Teacher --> Staff[科辦／行政確認規則或結論]:::staff
    Staff --> Fix{需要補件或修正？}
    Fix -- 是 --> Confirm
    Fix -- 否 --> Results[產生摘要、分類、待補清單與下一步]:::system
    Review -- 否 --> Results
    Results --> Gap[對照目標顯示差距與下一步]:::system
    Gap --> Portfolio[累積個人作品集與五年地圖]:::system
    Portfolio --> Document[產生自傳與學習／入學計畫草稿]:::system
    Document --> Edit[學生編輯、下載 Word 或送入審查專案]:::student
    Edit --> Submit[建立送審快照]:::student
    Submit --> Consent{是否同意 AI 初檢？}
    Consent -- 否 --> TeacherReview[教師／導師檢視學生資料]:::teacher
    Consent -- 是 --> AICheck[AI 初檢 GitHub、README 與佐證]:::ai
    AICheck --> AIReport[產生候選問題與補強提示]:::ai
    AIReport --> StudentCheck[學生查看問題並補充／修正]:::student
    StudentCheck --> TeacherReview
    TeacherReview --> TeacherAdvice[教師提供回饋，不直接改正式結論]:::teacher
    TeacherAdvice --> StaffReview[科辦／行政登錄正式結論]:::staff
    StaffReview --> End([完成])
```

## 4. 教師回饋、審查與補件流程

```mermaid
%%{init: {'theme':'base','themeVariables': {'fontFamily':'Microsoft JhengHei, Noto Sans TC, Arial, sans-serif','primaryColor':'#F3F4F6','primaryTextColor':'#111827','primaryBorderColor':'#9CA3AF','lineColor':'#6B7280','edgeLabelBackground':'#FFFFFF'}}}%%
flowchart TD
    classDef student fill:#DBEAFE,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef teacher fill:#DCFCE7,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef staff fill:#EDE9FE,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef system fill:#F3F4F6,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef ai fill:#FEF3C7,stroke:#9CA3AF,color:#111827,stroke-width:1px;

    Start([學生送入審查專案]) --> Snapshot[建立送審快照]:::system
    Snapshot --> Consent{學生是否同意 AI 初檢？}
    Consent -- 是 --> AICheck[AI 初檢 GitHub、README 與佐證]:::ai
    AICheck --> AIReport[產生候選缺漏／不一致提示]:::ai
    Consent -- 否 --> TeacherView
    AIReport --> TeacherView[教師／導師查看資料與 AI 報告]:::teacher
    TeacherView --> Advice[教師留下輔導或補件建議]:::teacher
    Advice --> RuleCheck{是否涉及正式規則判定？}
    RuleCheck -- 是 --> StaffCheck[科辦／行政確認規則與結論]:::staff
    RuleCheck -- 否 --> NeedFix{需要補件？}
    StaffCheck --> NeedFix
    NeedFix -- 是 --> StudentFix[學生補充資料或修正內容]:::student
    StudentFix --> StudentConfirm[學生再次確認]:::student
    StudentConfirm --> TeacherView
    NeedFix -- 否 --> Record[保存 AI 報告、教師回饋與檢核紀錄]:::system
    Record --> StaffResult[科辦／行政確認正式結論]:::staff
    StaffResult --> Result[學生查看結果並更新五年地圖]:::system
    Result --> End([完成])
```

## 5. 科辦審查專案與成果管理流程

```mermaid
%%{init: {'theme':'base','themeVariables': {'fontFamily':'Microsoft JhengHei, Noto Sans TC, Arial, sans-serif','primaryColor':'#F3F4F6','primaryTextColor':'#111827','primaryBorderColor':'#9CA3AF','lineColor':'#6B7280','edgeLabelBackground':'#FFFFFF'}}}%%
flowchart TD
    classDef staff fill:#EDE9FE,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef teacher fill:#DCFCE7,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef system fill:#F3F4F6,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef ai fill:#FEF3C7,stroke:#9CA3AF,color:#111827,stroke-width:1px;

    Start([科辦／行政登入]) --> Dashboard[進入科辦行政控制台]:::staff
    Dashboard --> Track[全局總覽與進度追蹤]:::staff
    Track --> Export[匯出獎學金公文或名單]:::system
    Dashboard --> Project[建立與管理審查專案]:::staff
    Project --> Assign[將學生名單批次分派給教師／委員]:::staff
    Assign --> Notify[系統通知並追蹤回覆]:::system
    Notify --> Snapshot[系統建立送審快照]:::system
    Snapshot --> Consent{學生是否同意 AI 初檢？}
    Consent -- 是 --> AICheck[AI 初檢 GitHub 與佐證]:::ai
    Consent -- 否 --> Review
    AICheck --> AIReport[候選問題與補強提示]:::ai
    AIReport --> Review[教師／委員查看 AI 報告並提供回饋]:::teacher
    Review --> Result[科辦輸入共同結論、分數與評語]:::staff
    Result --> Lock[鎖定成果並歸檔]:::system
```

## 6. 小組專題成果流程

```mermaid
%%{init: {'theme':'base','themeVariables': {'fontFamily':'Microsoft JhengHei, Noto Sans TC, Arial, sans-serif','primaryColor':'#F3F4F6','primaryTextColor':'#111827','primaryBorderColor':'#9CA3AF','lineColor':'#6B7280','edgeLabelBackground':'#FFFFFF'}}}%%
flowchart TD
    classDef student fill:#DBEAFE,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef teacher fill:#DCFCE7,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef staff fill:#EDE9FE,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef system fill:#F3F4F6,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef ai fill:#FEF3C7,stroke:#9CA3AF,color:#111827,stroke-width:1px;

    Start([專五專題開始]) --> Team[學生建立小組與個人分工]:::student
    Team --> Template[系統套用年度成果要求]:::system
    Template --> Submit[學生繳交成果與佐證]:::student
    Submit --> Consent{學生是否同意 AI 初檢？}:::student
    Consent -- 是 --> AICheck[AI 初檢 GitHub、README 與佐證]:::ai
    Consent -- 否 --> Teacher[教師／導師提供回饋]:::teacher
    AICheck --> AIReport[候選問題與補強提示]:::ai
    AIReport --> Teacher
    Teacher --> Staff[科辦／行政登錄共同結論]:::staff
    Staff --> Fix{需要補正？}
    Fix -- 是 --> Submit
    Fix -- 否 --> Link[連結至每位組員已確認的學習歷程]:::system
    Link --> End([完成])
```

## 7. 延伸功能位置

```mermaid
%%{init: {'theme':'base','themeVariables': {'fontFamily':'Microsoft JhengHei, Noto Sans TC, Arial, sans-serif','primaryColor':'#F3F4F6','primaryTextColor':'#111827','primaryBorderColor':'#9CA3AF','lineColor':'#6B7280','edgeLabelBackground':'#FFFFFF'}}}%%
flowchart LR
    classDef p0 fill:#F3F4F6,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef p2 fill:#DBEAFE,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef future fill:#FEF3C7,stroke:#9CA3AF,color:#111827,stroke-width:1px;

    Core[學生資料、目標、規則分類與文件產出]:::p0 --> Experience[五年地圖、互鎖拼圖與公開首頁]:::p2
    Core -.資料成熟後.-> Future[招生資料更新、進階推薦與完整 PDF]:::future
```

## 7. 系統架構圖

```mermaid
%%{init: {'theme':'base','themeVariables': {'fontFamily':'Microsoft JhengHei, Noto Sans TC, Arial, sans-serif','primaryColor':'#F3F4F6','primaryTextColor':'#111827','primaryBorderColor':'#9CA3AF','lineColor':'#6B7280','edgeLabelBackground':'#FFFFFF'}}}%%
flowchart LR
    classDef user fill:#DBEAFE,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef backend fill:#F3F4F6,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef db fill:#FFFFFF,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef ai fill:#FEF3C7,stroke:#9CA3AF,color:#111827,stroke-width:1px;

    Users[學生／教師／科辦／管理者]:::user --> UI[前端介面]:::backend
    UI --> App[Flask 後端]:::backend
    App --> Data[(學生資料、規則與檢核紀錄)]:::db
    App --> Analysis[可替換分析服務]:::ai
    Analysis --> Draft[AI 初檢 GitHub／佐證並產生候選提示]:::ai
    Draft --> App
    App --> Word[Word 文件產出]:::backend
```

## 8. DFD 資料流程圖

```mermaid
%%{init: {'theme':'base','themeVariables': {'fontFamily':'Microsoft JhengHei, Noto Sans TC, Arial, sans-serif','primaryColor':'#F3F4F6','primaryTextColor':'#111827','primaryBorderColor':'#9CA3AF','lineColor':'#6B7280','edgeLabelBackground':'#FFFFFF'}}}%%
flowchart LR
    classDef user fill:#DBEAFE,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef teacher fill:#DCFCE7,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef staff fill:#EDE9FE,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef process fill:#F3F4F6,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef store fill:#FFFFFF,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef ai fill:#FEF3C7,stroke:#9CA3AF,color:#111827,stroke-width:1px;

    Student[學生]:::user --> Upload[上傳與確認]:::process
    Upload --> Files[(原始檔與可校正草稿)]:::store
    Upload --> Classify[規則分類與結果產出]:::process
    Rules[(年度課程與證照規則)]:::store --> Classify
    Classify --> Result[(摘要、待補項目與文件草稿)]:::store
    Student[學生]:::user --> Snapshot[建立送審快照與 AI 同意紀錄]:::process
    Snapshot --> GitHub[GitHub／README／佐證連結]:::store
    GitHub --> AI[AI 初檢：缺漏與不一致候選提示]:::ai
    AI --> AIReport[(AI 分析紀錄；非正式結論)]:::store
    Teacher[教師／導師]:::teacher --> Feedback[查看 AI 報告並提供回饋]:::process
    Feedback --> Result
    Staff[科辦／行政]:::staff --> Confirm[規則與結論確認]:::process
    Confirm --> Rules
    Confirm --> Result
```

## 9. 文件與開發同步流程

```mermaid
%%{init: {'theme':'base','themeVariables': {'fontFamily':'Microsoft JhengHei, Noto Sans TC, Arial, sans-serif','primaryColor':'#F3F4F6','primaryTextColor':'#111827','primaryBorderColor':'#9CA3AF','lineColor':'#6B7280','edgeLabelBackground':'#FFFFFF'}}}%%
flowchart TD
    classDef doc fill:#F3F4F6,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef dev fill:#DBEAFE,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef check fill:#DCFCE7,stroke:#9CA3AF,color:#111827,stroke-width:1px;

    Requirement[需求基準與正式規格]:::doc --> Diagram[流程圖與權限說明]:::doc
    Diagram --> Build[程式與資料模型實作]:::dev
    Build --> Verify[測試與手動驗收]:::check
    Verify --> Log[開發日誌與規格回寫]:::doc
    Log --> Requirement
```
