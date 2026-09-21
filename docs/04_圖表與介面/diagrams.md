# 系統流程圖與架構圖

> 這份文件使用 Mermaid。Antigravity / VS Code 通常可用 Markdown Preview 或 Mermaid 外掛預覽。
>
> AI 做得出流程圖、架構圖、ERD。開發階段建議先用 Mermaid，因為它可以直接放進 `.md`、容易用 BMAD 修改，也能轉成圖片放進報告或簡報。

## 1. 系統總架構圖

```mermaid
flowchart LR
    %% 顏色與樣式定義
    classDef frontend fill:#fff,stroke:#333;
    classDef backend fill:#E0F2FE,stroke:#333;
    classDef db fill:#F3F4F6,stroke:#333;
    classDef ai fill:#FFEDD5,stroke:#333;
    classDef external fill:#FEF9C3,stroke:#333;
    classDef student fill:#DBEAFE,stroke:#333;
    classDef teacher fill:#DCFCE7,stroke:#333;
    classDef admin fill:#EDE9FE,stroke:#333;

    U[前端介面]:::frontend
    R[Flask 後端]:::backend
    M[(MySQL 資料庫)]:::db
    AI[AI Agent 模組]:::ai
    Gemini[Gemini API]:::external
    GH[GitHub REST API]:::external
    
    Student[學生]:::student --> U
    Teacher[教師 / 導師]:::teacher --> U
    Staff[科辦 / 行政]:::admin --> U
    Admin[系統管理者]:::admin --> U
    
    U --> R
    R --> M
    R --> AI
    AI --> Gemini
    AI --> GH
```

## 2. 角色功能架構圖 (使用者案例)

```mermaid
flowchart TD
    classDef student fill:#DBEAFE,stroke:#333;
    classDef teacher fill:#DCFCE7,stroke:#333;
    classDef admin fill:#EDE9FE,stroke:#333;
    classDef ai fill:#FFEDD5,stroke:#333;
    classDef backend fill:#E0F2FE,stroke:#333;

    System[前端介面與後端]:::backend

    System --> Student[學生]:::student
    System --> Teacher[教師 / 導師]:::teacher
    System --> Staff[科辦 / 行政]:::admin
    System --> Admin[系統管理者]:::admin
    System --> Agent[AI Agent]:::ai

    Student --> S1[學習歷程管理]:::student
    Student --> S2[上傳佐證資料]:::student
    Student --> S3[任務地圖解鎖]:::student
    Student --> S4[提交備審與成績]:::student
    Student --> S5[查看 AI 檢核報告]:::student

    Teacher --> T1[查看被分派學生]:::teacher
    Teacher --> T2[提供輔導與補件建議]:::teacher
    Teacher --> T3[人工覆核 AI 提示]:::teacher
    Teacher --> T4[提供補件建議]:::teacher

    Staff --> F1[登錄共同審查結論]:::admin
    Staff --> F2[整理補正項目]:::admin

    Admin --> A1[帳號與權限管理]:::admin
    Admin --> A2[系統設定維護]:::admin
    Admin --> A3[操作與錯誤日誌]:::admin
    Admin --> A4[監控 AI 任務狀態]:::admin
    Admin --> A5[審核並發布招生規則]:::admin

    Agent --> G1[成績單文字擷取]:::ai
    Agent --> G2[備審主張證據檢核]:::ai
    Agent --> G3[分析任務地圖進度]:::ai
    Agent --> G4[擷取官方招生資料]:::ai
```

## 3. 學生學習歷程流程圖

```mermaid
flowchart TD
    classDef student fill:#DBEAFE,stroke:#333;
    classDef backend fill:#E0F2FE,stroke:#333;

    Start([開始]) --> Login[學生登入]:::student
    Login --> Profile[維護個人基本資料]:::student
    Profile --> Portfolio[新增學習歷程]:::student
    Portfolio --> Classify[填寫學年度與類型]:::student
    Classify --> Evidence[上傳佐證資料]:::student
    Evidence --> Draft{是否存草稿?}
    Draft -- 是 --> SaveDraft[儲存草稿]:::backend
    SaveDraft --> Edit[修改資料]:::student
    Edit --> Submit[正式提交]:::backend
    Draft -- 否 --> Submit
    Submit --> Milestone[更新任務地圖]:::backend
    Milestone --> End([完成])
```

## 4. 小組專題成果與共同審查流程圖

> 報告圖片來源：`images/D-03-group-project-review-flow.mmd`。專題是學習歷程中的小組共用成果，不另做評審帳號、場地或網站公告管理系統。

```mermaid
flowchart TD
    Start([專五專題開始]) --> Team[學生組成 3 至 4 人小組]
    Team --> Advisor[小組找指導老師]
    Advisor --> Record[建立小組共用專題成果]
    Record --> Template{選擇專題類型}
    Template -- 資訊軟體開發組 --> Software[套用系統成果要求]
    Template -- 商務網站經營組 --> Business[套用商務成果要求]
    Software --> Submit[繳交階段成果與個人分工]
    Business --> Submit
    Submit --> Discuss[教師共同討論成果]
    Discuss --> RecordDecision[科主任或科助登錄共同結果與評語]
    RecordDecision --> Revision{需要補正?}
    Revision -- 是 --> Fix[學生補正並附完成證據]
    Fix --> Submit
    Revision -- 否 --> Link[成果連結至每位組員學習歷程]
```

## 5. AI 備審主張－證據檢核流程圖

```mermaid
flowchart TD
    classDef student fill:#DBEAFE,stroke:#333;
    classDef teacher fill:#DCFCE7,stroke:#333;
    classDef ai fill:#FFEDD5,stroke:#333;
    classDef backend fill:#E0F2FE,stroke:#333;
    classDef alert fill:#FEE2E2,stroke:#333;

    Start([開始]) --> Upload[上傳備審資料]:::student
    Upload --> CreateTask[建立檢核任務]:::backend
    CreateTask --> Extract[擷取文字內容]:::ai
    Extract --> Claims[拆解可驗證主張]:::ai
    Claims --> SearchEvidence[搜尋佐證資料]:::ai
    SearchEvidence --> Matrix[建立主張證據矩陣]:::ai
    Matrix --> Status[標示支持程度]:::ai
    Status --> Report[產生檢核報告]:::ai
    Report --> StudentReview[學生查看並補件]:::student
    StudentReview --> TeacherReview[教師人工覆核]:::teacher
    TeacherReview --> Decision{教師決定}
    Decision -- 採納 --> Accepted[保存採納紀錄]:::backend
    Decision -- 駁回 --> Rejected[保存駁回理由]:::alert
    Decision -- 待確認 --> Pending[列入面試追問]:::alert
    Accepted --> End([完成])
    Rejected --> End
    Pending --> End
```

## 6. 成績單擷取流程圖

```mermaid
flowchart TD
    classDef student fill:#DBEAFE,stroke:#333;
    classDef ai fill:#FFEDD5,stroke:#333;
    classDef backend fill:#E0F2FE,stroke:#333;
    classDef alert fill:#FEE2E2,stroke:#333;

    Start([開始]) --> Login[學生登入]:::student
    Login --> Upload[上傳成績單圖片]:::student
    Upload --> Validate[檢查檔案格式]:::backend
    Validate --> Valid{格式正確?}
    Valid -- 否 --> Error[顯示錯誤訊息]:::alert
    Valid -- 是 --> Task[建立 Agent 任務]:::backend
    Task --> OCR[擷取影像文字]:::ai
    OCR --> AI[提取課程與成績]:::ai
    AI --> Schema[驗證結構化資料]:::ai
    Schema --> OK{結果完整?}
    OK -- 否 --> Pending[標示擷取失敗]:::alert
    OK -- 是 --> Draft[產生成績草稿]:::backend
    Draft --> Confirm[學生確認修正]:::student
    Confirm --> Save[寫入資料庫]:::backend
    Save --> End([完成])
```

## 7. 招生資料更新流程圖

```mermaid
flowchart TD
    classDef admin fill:#EDE9FE,stroke:#333;
    classDef ai fill:#FFEDD5,stroke:#333;
    classDef backend fill:#E0F2FE,stroke:#333;
    classDef alert fill:#FEE2E2,stroke:#333;

    Start([開始]) --> Source[設定官方來源]:::admin
    Source --> Check[檢查來源更新]:::ai
    Check --> Extract[擷取招生規則]:::ai
    Extract --> Compare[比對現行版本]:::ai
    Compare --> Candidate[建立候選更新]:::ai
    Candidate --> Review[管理者查看差異]:::admin
    Review --> Approve{是否核准?}
    Approve -- 否 --> Reject[駁回並紀錄]:::alert
    Approve -- 是 --> Publish[發布新規則版本]:::backend
    Publish --> Log[寫入操作紀錄]:::backend
    Reject --> Log
    Log --> End([完成])
```

## 8. 管理者維護流程圖

```mermaid
flowchart TD
    classDef admin fill:#EDE9FE,stroke:#333;
    classDef backend fill:#E0F2FE,stroke:#333;

    Admin[系統管理者登入]:::admin --> Dashboard[進入管理者維護模組]:::backend
    Dashboard --> Users[帳號與權限管理]:::admin
    Dashboard --> Settings[系統設定維護]:::admin
    Dashboard --> Logs[操作與錯誤日誌]:::admin
    Dashboard --> Tasks[監控 AI 任務狀態]:::admin
    Dashboard --> Backup[備份匯出與報表]:::admin

    Settings --> UploadLimit[設定檔案大小限制]:::backend
    Settings --> AIFlag[切換 AI 功能開關]:::backend
    Tasks --> Retry[重新執行失敗任務]:::backend
```

## 9. ERD 草圖

```mermaid
erDiagram
    USERS ||--o| STUDENT_PROFILES : "has"
    USERS ||--o{ PORTFOLIOS : "owns"
    USERS ||--o{ AGENT_TASKS : "requests"
    USERS ||--o{ HUMAN_REVIEWS : "reviews"

    PORTFOLIOS ||--o{ PORTFOLIO_EVIDENCE : "contains"
    PORTFOLIOS ||--o{ PORTFOLIO_CLAIMS : "includes"
    PORTFOLIOS ||--o{ AI_AUDIT_REPORTS : "audited_by"

    PORTFOLIO_CLAIMS ||--o{ CLAIM_EVIDENCE_LINKS : "maps"
    PORTFOLIO_EVIDENCE ||--o{ CLAIM_EVIDENCE_LINKS : "supports"

    AGENT_TASKS ||--o{ AI_AUDIT_REPORTS : "produces"
    AI_AUDIT_REPORTS ||--o{ HUMAN_REVIEWS : "reviewed_by"

    OFFICIAL_SOURCES ||--o{ ADMISSION_RULE_VERSIONS : "provides"
    ADMISSION_RULE_VERSIONS ||--o{ ADMISSION_RULE_ITEMS : "contains"
    ADMISSION_RULE_VERSIONS ||--o{ SIMULATION_RESULTS : "used_by"
    STUDENT_PROFILES ||--o{ SIMULATION_RESULTS : "calculates"

    USERS {
        int user_id PK
        string username
        string password_hash
        string role
        string status
    }

    PORTFOLIOS {
        int portfolio_id PK
        int student_id FK
        string title
        string category
        string status
    }

    AGENT_TASKS {
        int task_id PK
        string task_type
        int requested_by FK
        string status
        string error_message
    }
```

## 10. DFD 資料流程圖

```mermaid
flowchart LR
    classDef student fill:#DBEAFE,stroke:#333;
    classDef teacher fill:#DCFCE7,stroke:#333;
    classDef admin fill:#EDE9FE,stroke:#333;
    classDef ai fill:#FFEDD5,stroke:#333;
    classDef db fill:#F3F4F6,stroke:#333;

    Student[學生]:::student --> P1[學習歷程模組]
    P1 --> D1[(學習歷程資料)]:::db
    Student --> P2[佐證資料模組]
    P2 --> D2[(檔案與草稿資料)]:::db
    P2 --> P3[AI Agent 模組]:::ai
    P3 --> D3[(任務與檢核報告)]:::db
    Teacher[教師 / 導師]:::teacher --> P4[人工覆核流程]
    P4 --> D4[(評分與覆核紀錄)]:::db
    Staff[科辦 / 行政]:::admin --> P6[共同結論登錄]
    P6 --> D4
    Admin[系統管理者]:::admin --> P5[管理者維護模組]
    P5 --> D5[(帳號規則日誌)]:::db
```

## 11. AI 可以幫你做哪些圖

AI 可以做：

- 系統架構圖
- 使用者流程圖
- DFD 資料流程圖
- ERD 資料庫關聯圖
- 權限矩陣圖
- AI Agent 任務流程圖
- 管理者維護流程圖
- 報告用圖片版流程圖

建議順序：

1. 先用 Mermaid 產生 `.md` 可讀版本。
2. 確認流程正確。
3. 再轉成圖片放到報告書或簡報。
4. 最後才做美化版圖表。

## 12. 文件與開發同步流程圖

```mermaid
flowchart TD
    classDef source fill:#FEF9C3,stroke:#333;
    classDef docs fill:#E0F2FE,stroke:#333;
    classDef dev fill:#DCFCE7,stroke:#333;
    classDef check fill:#FEE2E2,stroke:#333;

    GoogleDoc[Google Docs 最終版]:::source --> ActionPlan[system-design-action-plan.md]:::docs
    Share[ChatGPT 分享對話]:::source --> ActionPlan

    ActionPlan --> Spec[系統規格設計書]:::docs
    ActionPlan --> Diagrams[diagrams.md]:::docs
    ActionPlan --> DataDict[Data Dictionary]:::docs
    ActionPlan --> API[API Specification]:::docs
    ActionPlan --> Permission[Role Permission Matrix]:::docs
    ActionPlan --> Tests[Test Case]:::docs
    ActionPlan --> UI[UI Wireframe / UI UX 規格]:::docs

    Spec --> BMAD[BMAD 任務切分]:::dev
    Diagrams --> BMAD
    DataDict --> Models[Flask / SQLAlchemy Models]:::dev
    API --> Routes[Flask Routes / API]:::dev
    Permission --> Auth[登入與權限控制]:::dev
    Tests --> Pytest[pytest 驗證]:::check
    UI --> Templates[HTML / CSS / JavaScript]:::dev

    Models --> Pytest
    Routes --> Pytest
    Auth --> Pytest
    Templates --> Pytest
```

## 13. 角色權限同步流程圖

```mermaid
flowchart TD
    classDef docs fill:#E0F2FE,stroke:#333;
    classDef db fill:#F3F4F6,stroke:#333;
    classDef dev fill:#DCFCE7,stroke:#333;
    classDef check fill:#FEE2E2,stroke:#333;

    Start([開始]) --> Roles[確認角色清單與 role 值]:::docs
    Roles --> UseCase[更新 Use Case]:::docs
    UseCase --> ERD[更新 ERD]:::docs
    ERD --> UserRole[同步 users.role 允許值]:::db
    UserRole --> Permission[更新權限矩陣]:::docs
    Permission --> API[更新 API Specification]:::docs
    API --> UI[更新各角色畫面與導頁]:::dev
    UI --> Tests[補角色測試案例]:::check
    Tests --> Decision{文件、資料庫、API、畫面是否一致?}
    Decision -- 否 --> Roles
    Decision -- 是 --> End([完成])
```

## 14. MVP 主流程圖

```mermaid
flowchart TD
    classDef student fill:#DBEAFE,stroke:#333;
    classDef teacher fill:#DCFCE7,stroke:#333;
    classDef admin fill:#EDE9FE,stroke:#333;
    classDef backend fill:#E0F2FE,stroke:#333;
    classDef db fill:#F3F4F6,stroke:#333;
    classDef alert fill:#FEE2E2,stroke:#333;

    Start([開始]) --> Login[使用者登入]:::backend
    Login --> Role{判斷角色}

    Role -- 學生 --> StudentHome[學生首頁]:::student
    StudentHome --> CreatePortfolio[建立或修改學習歷程]:::student
    CreatePortfolio --> Evidence[上傳 PDF / 圖片 / 外部連結]:::student
    Evidence --> Submit[提交學習歷程]:::backend
    Submit --> LockCheck{是否進入審查?}
    LockCheck -- 是 --> Locked[鎖定版本]:::db
    LockCheck -- 否 --> Draft[保留草稿]:::db

    Role -- 教師/導師 --> TeacherHome[教師工作區]:::teacher
    TeacherHome --> Assigned[查看被分派學生]:::teacher
    Assigned --> Review[查看歷程與佐證]:::teacher
    Review --> Advice[提供輔導與補件建議]:::teacher

    Role -- 管理者 --> AdminHome[管理者後台]:::admin
    AdminHome --> Users[帳號與權限管理]:::admin
    AdminHome --> Result[查看審查結果]:::admin
    AdminHome --> Settings[系統設定]:::admin

    Role -- 科辦/行政 --> StaffHome[行政工作區]:::admin
    StaffHome --> Committee[登錄教師共同結論]:::admin
    Committee --> Decision{是否需要補正?}
    Decision -- 是 --> Returned[記錄補正項目]:::alert
    Decision -- 否 --> Approved[保存共同結論]:::db

    Approved --> End([完成])
    Returned --> StudentHome
    Advice --> End
    Users --> End
    Result --> End
    Settings --> End
```

## 15. UI/UX 視覺概念流程圖

```mermaid
flowchart LR
    classDef concept fill:#FEF9C3,stroke:#333;
    classDef public fill:#DBEAFE,stroke:#333;
    classDef student fill:#DCFCE7,stroke:#333;
    classDef work fill:#EDE9FE,stroke:#333;
    classDef ai fill:#FFEDD5,stroke:#333;

    Concept[把五年，拼成下一站]:::concept --> Public[公開首頁]:::public
    Concept --> Student[學生首頁]:::student
    Concept --> TeacherAdmin[教師與行政工作頁]:::work
    Concept --> AI[AI 小助手入口]:::ai

    Public --> P1[散落資料]
    P1 --> P2[連接與分類]
    P2 --> P3[五年路徑]
    P3 --> P4[升學 / 實習 / 就業下一站]

    Student --> S1[個人五年路線]
    S1 --> S2[成果節點逐年增加]
    S2 --> S3[缺漏以空白拼圖或未完成節點呈現]

    TeacherAdmin --> T1[表格]
    TeacherAdmin --> T2[搜尋與篩選]
    TeacherAdmin --> T3[狀態與批次操作]

    AI --> A1[看看我的歷程還少了什麼]
    AI --> A2[幫我整理下一步]
    AI --> A3[只提供建議，不直接修改正式資料]
```
