# 系統流程圖與架構圖

> 版本：2026-10-08（依 10-07 錄音討論更新角色與主線）
> 每張圖的原始碼存放在 `docs/images/` 的 `.mmd` 檔，本文件內容與 `.mmd` 檔一致；PNG／SVG 由 Mermaid CLI 匯出，正式規格書引用 PNG。
> 流程以正式規格書為準；登入導頁與資料表以目前程式（`app/routes/main.py`、`app/models/`）為準，尚未實作的部分在圖中標示「待新增」或以虛線框表示。

## 圖表閱讀方式

| 顏色 | 代表 |
| --- | --- |
| 淺藍 | 學生 |
| 淺綠 | 導師 |
| 淺紫 | 系統管理者（開發者）、科主任或科助 |
| 淺灰藍 | 系統自動處理 |
| 淺橘 | AI 輔助（選用，失敗時可人工處理） |
| 淺紅 | 錯誤或缺件提示 |
| 虛線框 | 待確認、後續擴充或補充說明 |

## 圖表清單

| 規格書圖號 | 圖表 | 原始碼與圖檔 |
| --- | --- | --- |
| 參考 | 使用者案例總覽（所有角色合併；規格書改用圖 1～3） | `images/D-01-use-case-v2.mmd`／`.png`／`.svg` |
| 圖 4 | 登入與角色導頁流程圖 | `images/D-02-login-role-routing.mmd`／`.png`／`.svg` |
| 圖 5 | 學生主線流程圖 | `images/D-10-main-line-flow.mmd`／`.png`／`.svg` |
| 圖 6 | 行政表單數位化與申請追蹤流程圖（後續擴充） | `images/D-11-admin-forms-flow.mmd`／`.png`／`.svg` |
| 圖 7 | 專題共同審查流程圖（後續擴充） | `images/D-03-group-project-review-flow.mmd`／`.png`／`.svg` |
| 圖 8 | 招生資料更新流程圖 | `images/D-13-admission-rule-update-flow.mmd`／`.png`／`.svg` |
| 圖 9 | 導師確認流程圖 | `images/D-16-teacher-confirm-flow.mmd`／`.png`／`.svg` |
| 圖 10 | 系統管理者維護校系備審要求流程圖 | `images/D-17-admin-maintain-requirements.mmd`／`.png`／`.svg` |
| 圖 11 | 角色與責任圖 | `images/D-14-role-responsibility.mmd`／`.png`／`.svg` |
| 圖 12 | 系統架構圖 | `images/D-05-system-architecture.mmd`／`.png`／`.svg` |
| 圖 13 | DFD 資料流程圖 | `images/D-06-dfd.mmd`／`.png`／`.svg` |
| 圖 14 | ERD 資料庫關聯圖 | `images/D-09-erd-v2.mmd`／`.png`／`.svg` |
| 圖 15 | 報告用總體流程圖 | `images/D-15-report-overview.mmd`／`.png`／`.svg` |
| 圖 16 | 科辦上傳紀錄流程圖 | `images/D-18-staff-service-record-flow.mmd`／`.png`／`.svg` |

## 圖 1～3：依角色的使用案例圖

規格書的圖 1～3 依角色分開畫（人形＋功能橢圓），樣式參考歷屆專題報告書。這三張不是 Mermaid 圖，而是由 `images/D-01-use-case-by-role.py` 產生：

| 規格書圖號 | 角色 | 圖檔 |
| --- | --- | --- |
| 圖 1 | 學生 | `images/D-01-use-case-student.png`／`.svg` |
| 圖 2 | 導師 | `images/D-01-use-case-teacher.png`／`.svg` |
| 圖 3 | 系統管理者（開發者） | `images/D-01-use-case-admin.png`／`.svg` |
| 圖 1-1 | 科辦／科助 | `images/D-01-use-case-staff.png`／`.svg` |

修改方式：打開 `D-01-use-case-by-role.py`，修改最上方 `ROLES` 裡的功能清單，再到 `docs/images` 資料夾執行 `python D-01-use-case-by-role.py`，四張圖（含科辦）會一起更新。

### 2026-10-08 錄音討論後的流程圖基準

依 [10-07 會議紀錄](../06_會議錄音與逐字稿/AI_會議紀錄_科助使用者端與小助手_2026-10-07.md) 與 10-08 使用者決定：

| 項目 | 決定 |
| --- | --- |
| 選校系 | AI Agent 依學生條件推薦，學生自己選，可選多個 |
| 上傳後 | AI 辨識並判斷格式；辨識失敗時說明可能原因與修正方式；確認前 AI 標出可疑處，一定要學生本人確認 |
| 成績單、證照、競賽證明 | 不經導師審核；證照與競賽證明由 AI 判斷。競賽證明由主辦方（例如 AREC）開立，學生自行上傳 |
| 科辦／科助 | 用固定 Excel 範本上傳服務（例如帶高中機器人社團）、公假、嘉獎紀錄，依學號列入學生資料並可產出電子證明；不逐筆審核、**不審備審資料** |
| 自傳與備審 | AI 可引用學生資料與科辦紀錄撰寫，標示依據 |
| 備審資料 | 只由導師確認 |

待確認（不畫進主線）：學生發現漏列時可否線上請科辦補登；電子證明版面；科辦是否在系統開放競賽報名、處理公假與嘉獎申請（後續擴充，性質同行政表單）。

## 參考：使用者案例總覽（所有角色合併；規格書改用圖 1～3）

```mermaid
%%{init: {'theme':'base','themeVariables': {'fontFamily':'Microsoft JhengHei, Noto Sans TC, Arial, sans-serif','primaryColor':'#F3F4F6','primaryTextColor':'#111827','primaryBorderColor':'#9CA3AF','lineColor':'#6B7280','edgeLabelBackground':'#FFFFFF'},'flowchart':{'wrappingWidth':400}}}%%
flowchart LR
    classDef student fill:#DBEAFE,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef teacher fill:#DCFCE7,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef admin fill:#EDE9FE,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef ai fill:#FFEDD5,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef usecase fill:#FFFFFF,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef staff fill:#EDE9FE,stroke:#9CA3AF,color:#111827,stroke-width:1px;

    Student[學生]:::student
    Teacher[導師]:::teacher

    subgraph SYS[資管科智慧學習歷程系統]
        direction TB
        UC1([選擇目標校系]):::usecase
        UC2([上傳六類學習資料]):::usecase
        UC3([確認與修正整理結果]):::usecase
        UC4([查看還缺什麼]):::usecase
        UC5([產出完整備審資料]):::usecase
        UC6([查看本班學生資料]):::usecase
        UC7([確認內容或留下修改建議]):::usecase
        UC8([辨識上傳文件]):::usecase
        UC11([AI 判斷證照真偽]):::usecase
        UC12([AI 推薦校系並回答問題]):::usecase
        UC13([上傳服務、公假、嘉獎紀錄並產出電子證明]):::usecase
        UC9([維護校系備審要求]):::usecase
        UC10([維護帳號與權限]):::usecase
    end

    Admin[系統管理者（開發者）]:::admin
    AI[AI 輔助服務]:::ai
    Staff[科辦／科助<br/>不審備審資料]:::staff

    Student --- UC1
    Student --- UC2
    Student --- UC3
    Student --- UC4
    Student --- UC5
    UC1 -. 包含 .-> UC12
    UC2 -. 包含 .-> UC11
    UC13 -. 自傳與備審引用 .-> UC5
    Teacher --- UC6
    Teacher --- UC7
    UC2 -. 包含 .-> UC8
    UC8 --- AI
    UC11 --- AI
    UC12 --- AI
    Staff --- UC13
    UC9 --- Admin
    UC10 --- Admin
    SYS ~~~ Staff
```

## 圖 4：登入與角色導頁流程圖

依目前程式：帳號不存在、已停用或密碼錯誤時顯示同一個錯誤訊息；帳號沒有可用角色時拒絕登入；登入後每個頁面再用 `role_required` 檢查角色。

```mermaid
%%{init: {'theme':'base','themeVariables': {'fontFamily':'Microsoft JhengHei, Noto Sans TC, Arial, sans-serif','primaryColor':'#F3F4F6','primaryTextColor':'#111827','primaryBorderColor':'#9CA3AF','lineColor':'#6B7280','edgeLabelBackground':'#FFFFFF'},'flowchart':{'wrappingWidth':400}}}%%
flowchart TD
    classDef system fill:#E0F2FE,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef student fill:#DBEAFE,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef teacher fill:#DCFCE7,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef admin fill:#EDE9FE,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef staff fill:#EDE9FE,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef alert fill:#FEE2E2,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef pending fill:#FFFFFF,stroke:#9CA3AF,color:#6B7280,stroke-width:1px,stroke-dasharray:5 3;

    Start([開啟共用登入頁]) --> Input[輸入帳號與密碼]
    Input --> Auth{帳號存在、已啟用<br/>且密碼正確？}
    Auth -- 否 --> Err[顯示「帳號或密碼錯誤」]:::alert
    Err --> Input
    Auth -- 是 --> Session[清除舊登入狀態<br/>記錄目前使用者]:::system
    Session --> Role{依帳號角色導頁}
    Role -- student --> S[學生首頁<br/>選校系、上傳資料、查看缺件]:::student
    Role -- teacher --> T[導師工作台<br/>本班學生資料與確認]:::teacher
    Role -- admin --> A[管理工作區<br/>帳號、權限與校系備審要求]:::admin
    Role -- staff --> F[科辦工作區<br/>上傳服務、公假、嘉獎紀錄]:::staff
    Role -- 未設定角色 --> NoRole[顯示「此帳號尚未設定可用角色」<br/>並清除登入狀態]:::alert
    S --> Guard{每次開啟頁面或操作時<br/>再次檢查角色權限}
    T --> Guard
    A --> Guard
    F --> Guard
    Guard -- 符合 --> Allow[執行操作]:::system
    Guard -- 不符合 --> Deny[拒絕存取（403）]:::alert
```

## 圖 5：學生主線流程圖

```mermaid
%%{init: {'theme':'base','themeVariables': {'fontFamily':'Microsoft JhengHei, Noto Sans TC, Arial, sans-serif','primaryColor':'#F3F4F6','primaryTextColor':'#111827','primaryBorderColor':'#9CA3AF','lineColor':'#6B7280','edgeLabelBackground':'#FFFFFF'},'flowchart':{'wrappingWidth':400}}}%%
flowchart TD
    classDef student fill:#DBEAFE,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef system fill:#E0F2FE,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef teacher fill:#DCFCE7,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef staff fill:#EDE9FE,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef ai fill:#FFEDD5,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef alert fill:#FEE2E2,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef note fill:#FFFFFF,stroke:#9CA3AF,color:#6B7280,stroke-width:1px,stroke-dasharray:5 3;

    Start([學生登入]) --> HasTarget{已選擇目標校系？}
    HasTarget -- 否 --> Recommend[AI Agent 依學生條件<br/>推薦適合的二技校系]:::ai
    Recommend --> Choose[學生選擇想申請的校系<br/>可重選、可選多個]:::student
    Choose --> Req
    HasTarget -- 是 --> Req[系統列出該校系需要的<br/>備審資料項目與標準]:::system
    Req --> Download[學生自行登入學校系統<br/>下載成績單等資料]:::student
    Download -.- Note1[本系統不使用學生帳號登入或爬取學校系統<br/>期中修畢課程以列印版成績單為準<br/>微學分另上傳證明（處理方式待確認）]:::note
    Download --> Upload[上傳資料並選擇類別<br/>成績與學分、證照、活動、<br/>競賽、服務學習、幹部經歷]:::student
    Upload --> FileOK{檔案格式與大小正確？}
    FileOK -- 否 --> FileErr[顯示錯誤原因，請重新上傳]:::alert
    FileErr --> Upload
    FileOK -- 是 --> Extract[AI 辨識文件並判斷格式<br/>證照另判斷真偽]:::ai
    Extract --> Recognized{辨識成功？}
    Recognized -- 否 --> Explain[AI 說明可能哪裡有問題<br/>與建議怎麼修正]:::alert
    Explain --> Retry{重新上傳？}
    Retry -- 是 --> Upload
    Retry -- 否 --> Manual[學生手動輸入]:::student
    Recognized -- 是 --> Confirm[學生確認與修正<br/>AI 在旁標出可疑或不合理之處]:::student
    Manual --> Confirm
    Confirm -.- Note2[一定要學生本人確認後才存入<br/>成績單、證照與競賽證明不經導師審核<br/>競賽證明由主辦方開立，學生自行上傳]:::note
    Confirm --> Compare[系統比對校系要求]:::system
    StaffRec[科辦上傳的服務、公假、嘉獎紀錄<br/>依學號自動列入（見圖 16）]:::staff --> Compare
    Compare --> Enough{資料符合要求？}
    Enough -- 否 --> Missing[列出還缺什麼]:::alert
    Missing --> Upload
    Enough -- 是 --> Teacher[導師查看本班學生的備審內容]:::teacher
    Teacher --> Reasonable{內容合理？}
    Reasonable -- 否 --> Advice[導師留下修改建議]:::teacher
    Advice --> Confirm
    Reasonable -- 是 --> Output[導師確認後產出完整備審資料<br/>自傳可由 AI 依學生資料與科辦紀錄協助撰寫]:::system
    Output --> Print([學生下載列印])
```

## 圖 6：行政表單數位化與申請追蹤流程圖（後續擴充）

主線完成前不實作；保留供日後評估。

```mermaid
%%{init: {'theme':'base','themeVariables': {'fontFamily':'Microsoft JhengHei, Noto Sans TC, Arial, sans-serif','primaryColor':'#F3F4F6','primaryTextColor':'#111827','primaryBorderColor':'#9CA3AF','lineColor':'#6B7280','edgeLabelBackground':'#FFFFFF'},'flowchart':{'wrappingWidth':400}}}%%
flowchart TD
    classDef student fill:#DBEAFE,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef teacher fill:#DCFCE7,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef admin fill:#EDE9FE,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef system fill:#E0F2FE,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef store fill:#F3F4F6,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef ai fill:#FFEDD5,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef alert fill:#FEE2E2,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef pending fill:#FFFFFF,stroke:#9CA3AF,color:#6B7280,stroke-width:1px,stroke-dasharray:5 3;

    Start([教師登入]) --> Publish[上傳已核准空白表單<br/>設定年度、版本、對象、截止日與附件]:::teacher
    Publish --> Download[學生下載指定版本並離線填寫]:::student
    Download --> Submit[回傳填妥表單與佐證]:::student
    Submit --> RuleCheck[系統檢查格式、版本與必備附件]:::system
    RuleCheck --> TeacherView[教師初檢]:::teacher
    RuleCheck -. 選用：缺件／空白提示 .-> AI[AI 候選提示，不直接定案]:::ai
    AI -.-> TeacherView
    TeacherView --> NeedFix{需要補件？}
    NeedFix -- 是 --> StudentFix[學生補件；保留舊版本]:::student
    StudentFix --> RuleCheck
    NeedFix -- 否 --> StaffResult[科辦登錄正式行政狀態]:::pending
    StaffResult --> End([學生查看結果])
```

## 圖 7：專題共同審查流程圖（後續擴充）

狀態值與 [專題成果評量範本](../01_正式規格/專題成果評量範本-第一版.md) 及目前程式一致。

```mermaid
%%{init: {'theme':'base','themeVariables': {'fontFamily':'Microsoft JhengHei, Noto Sans TC, Arial, sans-serif','primaryColor':'#F3F4F6','primaryTextColor':'#111827','primaryBorderColor':'#9CA3AF','lineColor':'#6B7280','edgeLabelBackground':'#FFFFFF'},'flowchart':{'wrappingWidth':400}}}%%
flowchart TD
    classDef student fill:#DBEAFE,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef teacher fill:#DCFCE7,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef staff fill:#EDE9FE,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef system fill:#E0F2FE,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef alert fill:#FEE2E2,stroke:#9CA3AF,color:#111827,stroke-width:1px;

    Start([專五專題開始（後續擴充）]) --> Team[學生建立小組與個人分工]:::student
    Team --> Submit[學生繳交成果與佐證<br/>狀態：submitted]:::student
    Submit --> Discuss[教師共同討論<br/>不在系統內個別評分]:::teacher
    Discuss --> Record[科主任或科助登錄共同結論]:::staff
    Record --> Result{共同結論}
    Result -- approved 核可 --> Link[連結至每位組員的學習歷程]:::system
    Result -- needs_revision 需要補正 --> NewVersion[建立新版本<br/>版本號加 1，保留前一版]:::system
    NewVersion --> Submit
    Result -- rejected 退件 --> Reject[記錄退件原因]:::alert
    Link --> End([完成])
    Reject --> End
```

## 圖 8：招生資料更新流程圖

```mermaid
%%{init: {'theme':'base','themeVariables': {'fontFamily':'Microsoft JhengHei, Noto Sans TC, Arial, sans-serif','primaryColor':'#F3F4F6','primaryTextColor':'#111827','primaryBorderColor':'#9CA3AF','lineColor':'#6B7280','edgeLabelBackground':'#FFFFFF'},'flowchart':{'wrappingWidth':400}}}%%
flowchart TD
    classDef admin fill:#EDE9FE,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef ai fill:#FFEDD5,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef system fill:#E0F2FE,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef store fill:#F3F4F6,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef student fill:#DBEAFE,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef alert fill:#FEE2E2,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef note fill:#FFFFFF,stroke:#9CA3AF,color:#6B7280,stroke-width:1px,stroke-dasharray:5 3;

    subgraph Stage1[第一階段：手動建立]
        Manual[系統管理者依簡章或整理資料<br/>輸入校系與加權項目]:::admin
    end
    subgraph Stage23[第二、三階段：Agent 每年更新（亮點）]
        Source[管理者設定官方來源<br/>技專校院招生委員會、各校分則]:::admin
        Schedule[排程：每年簡章公告期間定期檢查]:::system
        Detect[Agent 抓取來源並比對內容雜湊]:::ai
        Changed{來源有更新？}
        Notify[通知管理者：新年度簡章已公告]:::system
        Extract[Agent 擷取校系、招生類別、<br/>原始項目名稱與加權百分比]:::ai
        Validate{格式檢查：<br/>各校系加權合計 100%？}
        Fail[擷取失敗：保留原始檔，<br/>改由管理者手動輸入]:::alert
        Source --> Schedule --> Detect --> Changed
        Changed -- 否 --> Schedule
        Changed -- 是 --> Notify --> Extract --> Validate
        Validate -- 否 --> Fail
    end
    Manual --> Candidate[(候選版本 status=candidate<br/>校系與年度、校系備審要求)]:::store
    Validate -- 是 --> Candidate
    Fail --> Manual
    Candidate --> Diff[管理者比對新舊差異<br/>並確認對應的資料類別]:::admin
    Diff --> Approve{核准？}
    Approve -- 否 --> Reject[駁回並記錄原因]:::alert
    Approve -- 是 --> Publish[(正式版本 status=published)]:::store
    Publish --> Student[學生選校系與缺件比對<br/>只讀取正式版本]:::student
    Reject --> Log[寫入操作紀錄]:::system
    Publish --> Log
    Rule[AI 不得直接發布；舊年度資料保留不覆蓋]:::note -.- Approve
```

## 圖 9：導師確認流程圖

```mermaid
%%{init: {'theme':'base','themeVariables': {'fontFamily':'Microsoft JhengHei, Noto Sans TC, Arial, sans-serif','primaryColor':'#F3F4F6','primaryTextColor':'#111827','primaryBorderColor':'#9CA3AF','lineColor':'#6B7280','edgeLabelBackground':'#FFFFFF'},'flowchart':{'wrappingWidth':400}}}%%
flowchart TD
    classDef student fill:#DBEAFE,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef teacher fill:#DCFCE7,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef admin fill:#EDE9FE,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef system fill:#E0F2FE,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef store fill:#F3F4F6,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef ai fill:#FFEDD5,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef alert fill:#FEE2E2,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef pending fill:#FFFFFF,stroke:#9CA3AF,color:#6B7280,stroke-width:1px,stroke-dasharray:5 3;

    Start([導師登入]) --> List[查看本班學生清單<br/>與資料完成度]:::teacher
    List -.- Scope[導師只能查看本班學生<br/>其他班級一律拒絕存取]:::pending
    Start -.- NoCert[成績單、證照與競賽證明不經導師審核（由 AI 判斷）<br/>服務、公假、嘉獎紀錄由科辦提供<br/>導師只確認最後整理好的備審內容]:::pending
    List --> Pick[選擇一位學生]:::teacher
    Pick --> View[查看學生資料、目標校系與缺件清單]:::teacher
    View --> Original[可查看成績單、證照、佐證照片與自傳原始檔]:::teacher
    Original --> Reasonable{備審內容合理？}
    Reasonable -- 是 --> Confirm[導師標記為已確認]:::teacher
    Confirm --> Ready[學生可產出完整備審資料]:::system
    Reasonable -- 否 --> Advice[導師留下修改建議]:::teacher
    Advice --> Fix[學生修正後重新送出]:::student
    Fix --> View
```

## 圖 10：系統管理者維護校系備審要求流程圖

```mermaid
%%{init: {'theme':'base','themeVariables': {'fontFamily':'Microsoft JhengHei, Noto Sans TC, Arial, sans-serif','primaryColor':'#F3F4F6','primaryTextColor':'#111827','primaryBorderColor':'#9CA3AF','lineColor':'#6B7280','edgeLabelBackground':'#FFFFFF'},'flowchart':{'wrappingWidth':400}}}%%
flowchart TD
    classDef student fill:#DBEAFE,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef teacher fill:#DCFCE7,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef admin fill:#EDE9FE,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef system fill:#E0F2FE,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef store fill:#F3F4F6,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef ai fill:#FFEDD5,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef alert fill:#FEE2E2,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef pending fill:#FFFFFF,stroke:#9CA3AF,color:#6B7280,stroke-width:1px,stroke-dasharray:5 3;

    Start([系統管理者登入]) --> Survey[調查目標校系的招生簡章]:::admin
    Survey --> Program[建立校系與年度<br/>學校、科系、招生年度、資料來源、最後確認日期]:::admin
    Program --> Items[設定備審資料項目與標準<br/>對應六類學習資料]:::admin
    Items --> Correct{資料正確？}
    Correct -- 否 --> Program
    Correct -- 是 --> Publish[啟用，學生端可選擇此校系]:::system
    Publish --> Log[寫入操作紀錄]:::system
    Log --> End([完成])
```

## 圖 11：角色與責任圖

```mermaid
%%{init: {'theme':'base','themeVariables': {'fontFamily':'Microsoft JhengHei, Noto Sans TC, Arial, sans-serif','primaryColor':'#F3F4F6','primaryTextColor':'#111827','primaryBorderColor':'#9CA3AF','lineColor':'#6B7280','edgeLabelBackground':'#FFFFFF'},'flowchart':{'wrappingWidth':400}}}%%
flowchart TD
    classDef student fill:#DBEAFE,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef teacher fill:#DCFCE7,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef staff fill:#EDE9FE,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef ai fill:#FEF3C7,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef alert fill:#FEE2E2,stroke:#9CA3AF,color:#111827,stroke-width:1px;

    Student[學生]:::student --> S1[上傳、校正與確認本人資料]:::student
    Student --> S2[產出並下載完整備審資料]:::student
    Teacher[導師]:::teacher --> T1[查看本班學生資料]:::teacher
    Teacher --> T2[確認備審內容並提供修改建議]:::teacher
    Staff[科辦／科助]:::staff --> F1[上傳科上的官方紀錄<br/>服務（如帶高中機器人社團）、公假、嘉獎]:::staff
    Staff --> F2[系統依學號列入學生資料<br/>並可產出電子證明]:::staff
    Staff -.不審備審資料.-> T2
    Admin[系統管理者（開發者）]:::staff --> A1[管理帳號、權限、系統設定與校系備審要求]:::staff
    Agent[AI Agent]:::ai --> G1[推薦校系、辨識文件並說明錯誤、<br/>判斷證照真偽、標出可疑處、<br/>依學生與科辦紀錄協助寫自傳、小助手回答]:::ai
    G1 -.不直接定案.-> Block[必須經學生或人工確認]:::alert
```

## 圖 12：系統架構圖

```mermaid
%%{init: {'theme':'base','themeVariables': {'fontFamily':'Microsoft JhengHei, Noto Sans TC, Arial, sans-serif','primaryColor':'#F3F4F6','primaryTextColor':'#111827','primaryBorderColor':'#9CA3AF','lineColor':'#6B7280','edgeLabelBackground':'#FFFFFF'},'flowchart':{'wrappingWidth':400}}}%%
flowchart LR
    classDef student fill:#DBEAFE,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef teacher fill:#DCFCE7,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef admin fill:#EDE9FE,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef backend fill:#E0F2FE,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef db fill:#F3F4F6,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef ai fill:#FFEDD5,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef external fill:#FFFFFF,stroke:#9CA3AF,color:#6B7280,stroke-width:1px,stroke-dasharray:5 3;

    School[學校成績系統<br/>（本系統不連線）]:::external
    Student[學生]:::student
    Teacher[導師]:::teacher
    Staff[科辦／科助]:::admin
    Admin[系統管理者（開發者）]:::admin

    School -. 學生自行下載成績單 .-> Student
    Student --> UI
    Teacher --> UI
    Staff --> UI
    Admin --> UI

    UI[瀏覽器前端<br/>HTML／CSS／少量原生 JavaScript]:::backend
    UI --> App[Flask 後端<br/>登入與權限、檔案上傳、資料整理、<br/>缺件比對、備審資料產出]:::backend
    App --> DB[(MySQL 8.0<br/>帳號、學習資料、校系備審要求)]:::db
    App --> Files[(上傳檔案儲存區)]:::db
    App -. 推薦校系、文件辨識與證照真偽、<br/>自傳小幫手、小助手、招生資料 Agent .-> Gemini[Google Gemini API]:::ai
    App --> Doc[Word 備審資料<br/>（可列印）]:::backend
```

## 圖 13：DFD 資料流程圖

```mermaid
%%{init: {'theme':'base','themeVariables': {'fontFamily':'Microsoft JhengHei, Noto Sans TC, Arial, sans-serif','primaryColor':'#F3F4F6','primaryTextColor':'#111827','primaryBorderColor':'#9CA3AF','lineColor':'#6B7280','edgeLabelBackground':'#FFFFFF'},'flowchart':{'wrappingWidth':400}}}%%
flowchart TD
    classDef student fill:#DBEAFE,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef teacher fill:#DCFCE7,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef admin fill:#EDE9FE,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef system fill:#E0F2FE,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef store fill:#F3F4F6,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef ai fill:#FFEDD5,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef alert fill:#FEE2E2,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef pending fill:#FFFFFF,stroke:#9CA3AF,color:#6B7280,stroke-width:1px,stroke-dasharray:5 3;

    Admin[系統管理者]:::admin --> P6[6.0 維護校系備審要求]:::system
    P6 --> D1[(D1 校系備審要求)]:::store
    D1 --> P1[1.0 選擇目標校系]:::system
    Student[學生]:::student --> P1
    P1 --> D2[(D2 學生目標校系)]:::store
    Student --> P2[2.0 上傳與確認學習資料]:::system
    P2 <-. 辨識、真偽判斷與可疑處提示 .-> AI[AI 輔助服務]:::ai
    P1 <-. 推薦校系 .-> AI
    P2 --> D3[(D3 原始檔與辨識結果)]:::store
    P2 --> D4[(D4 成績、證照、活動等學習紀錄)]:::store
    D2 --> P3[3.0 缺件比對]:::system
    D4 --> P3
    D1 -.-> P3
    P3 --> Gap[缺件清單回饋給學生]:::alert
    D4 --> P4[4.0 導師確認]:::system
    Teacher[導師]:::teacher --> P4
    P4 --> D5[(D5 導師確認紀錄)]:::store
    D5 --> P5[5.0 產出備審資料]:::system
    D4 --> P5
    P5 --> D6[(D6 備審資料檔)]:::store
    D6 --> Download[學生下載列印]:::student
    Staff[科辦]:::admin --> P7[7.0 匯入科辦紀錄]:::system
    P7 --> D7[(D7 科辦紀錄與電子證明)]:::store
    D7 --> P3
    D7 --> P5
```

## 圖 14：ERD 資料庫關聯圖

標示「待新增」的資料表是主線需要、但目前程式還沒有的資料表；其餘資料表已存在於 `app/models/`。

```mermaid
%%{init: {'theme':'base','themeVariables': {'fontFamily':'Arial, Microsoft JhengHei, sans-serif','fontSize':'14px','primaryColor':'#F3F4F6','primaryTextColor':'#111827','primaryBorderColor':'#9CA3AF','lineColor':'#6B7280'},'er':{'minEntityWidth':160,'entityPadding':20}}}%%
erDiagram
    USERS ||--o| STUDENT_PROFILES : "學生基本資料"
    USERS ||--o{ CLASS_ADVISORS : "擔任導師"
    USERS ||--o{ SOURCE_DOCUMENTS : "上傳"
    SOURCE_DOCUMENTS ||--o| DOCUMENT_EXTRACTIONS : "辨識結果"
    USERS ||--o{ LEARNING_COURSE_RECORDS : "成績與學分"
    SOURCE_DOCUMENTS |o--o{ LEARNING_COURSE_RECORDS : "來源檔"
    USERS ||--o{ CREDENTIAL_RECORDS : "證照"
    SOURCE_DOCUMENTS |o--o{ CREDENTIAL_RECORDS : "來源檔"
    USERS ||--o{ PORTFOLIOS : "活動競賽服務幹部"
    PORTFOLIOS ||--o{ PORTFOLIO_EVIDENCE : "佐證"
    ADMISSION_RULE_VERSIONS ||--o{ ADMISSION_RULE_ITEMS : "備審要求"
    USERS ||--o{ STUDENT_TARGETS : "選擇校系"
    ADMISSION_RULE_VERSIONS ||--o{ STUDENT_TARGETS : "被選擇"
    USERS ||--o{ LEARNING_PROFILE_OUTPUTS : "產出備審資料"
    LEARNING_PROFILE_OUTPUTS ||--o{ PACKAGE_REVIEWS : "導師確認"
    USERS ||--o{ PACKAGE_REVIEWS : "確認者"

    USERS["USERS 使用者　　　"] {
        int id PK
        string username "學號或帳號"
        string role "student teacher staff admin"
        bool is_active
    }
    STUDENT_PROFILES["STUDENT_PROFILES 學生資料　　　"] {
        int id PK
        int user_id FK
        string student_no
        string class_name "班級"
    }
    CLASS_ADVISORS["CLASS_ADVISORS 導師班級　　　"] {
        int id PK "待新增"
        int teacher_id FK
        string class_name
        int school_year
    }
    SOURCE_DOCUMENTS["SOURCE_DOCUMENTS 上傳原始檔　　　"] {
        int id PK
        int owner_id FK
        string document_type "成績單 證照等"
        string file_path
        string status
    }
    DOCUMENT_EXTRACTIONS["DOCUMENT_EXTRACTIONS 辨識結果　　　"] {
        int id PK
        int source_document_id FK
        string status "辨識狀態"
        datetime confirmed_at "學生確認時間"
    }
    LEARNING_COURSE_RECORDS["LEARNING_COURSE_RECORDS 成績與學分　　　"] {
        int id PK
        int student_id FK
        int source_document_id FK
        string course_name
        int credits
        int score
    }
    CREDENTIAL_RECORDS["CREDENTIAL_RECORDS 證照　　　"] {
        int id PK
        int student_id FK
        int source_document_id FK
        string credential_name
        string level
    }
    PORTFOLIOS["PORTFOLIOS 活動競賽服務幹部　　　"] {
        int id PK
        int student_id FK
        string category "活動 競賽 服務學習 幹部經歷"
        string title
        string status
    }
    PORTFOLIO_EVIDENCE["PORTFOLIO_EVIDENCE 佐證檔案　　　"] {
        int id PK
        int portfolio_id FK
        string file_path
        string external_url
    }
    ADMISSION_RULE_VERSIONS["ADMISSION_RULE_VERSIONS 校系與年度　　　"] {
        int id PK "待新增"
        string program_code "志願代碼"
        string school_name "學校"
        string department_name "科系"
        string admission_category "招生類別"
        int admission_year "學年度"
        string source_url "資料來源"
        string status "candidate published"
        string data_origin "manual agent"
        date checked_at "最後確認日期"
    }
    ADMISSION_RULE_ITEMS["ADMISSION_RULE_ITEMS 校系備審要求　　　"] {
        int id PK "待新增"
        int rule_version_id FK
        string source_item_name "簡章原始項目名稱"
        int weight_percent "加權百分比"
        string mapped_categories "對應資料類別"
        string mapping_status "確定 待確認"
        string requirement "需要的資料與標準"
        bool is_required
    }
    STUDENT_TARGETS["STUDENT_TARGETS 學生目標校系　　　"] {
        int id PK "待新增"
        int student_id FK
        int rule_version_id FK
        datetime selected_at
    }
    LEARNING_PROFILE_OUTPUTS["LEARNING_PROFILE_OUTPUTS 備審資料產出　　　"] {
        int id PK
        int student_id FK
        string output_type "備審資料"
        datetime created_at
    }
    PACKAGE_REVIEWS["PACKAGE_REVIEWS 導師確認紀錄　　　"] {
        int id PK "待新增"
        int output_id FK
        int teacher_id FK
        string result "confirmed needs_revision"
        string comment "修改建議"
    }
```

## 圖 15：報告用總體流程圖

```mermaid
%%{init: {'theme':'base','themeVariables': {'fontFamily':'Microsoft JhengHei, Noto Sans TC, Arial, sans-serif','primaryColor':'#F3F4F6','primaryTextColor':'#111827','primaryBorderColor':'#9CA3AF','lineColor':'#6B7280','edgeLabelBackground':'#FFFFFF'},'flowchart':{'wrappingWidth':400}}}%%
flowchart LR
    classDef student fill:#DBEAFE,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef system fill:#F3F4F6,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef teacher fill:#DCFCE7,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef staff fill:#EDE9FE,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef ai fill:#FFEDD5,stroke:#9CA3AF,color:#111827,stroke-width:1px;

    Recommend[AI 推薦校系]:::ai --> Target[學生選擇目標校系]:::student
    Target --> Upload[上傳六類學習資料]:::student
    Upload --> Check[AI 辨識、說明錯誤<br/>判斷證照真偽]:::ai
    Check --> Confirm[學生確認並補齊資料]:::student
    Staff[科辦上傳服務、<br/>公假、嘉獎紀錄]:::staff -.-> Core
    Confirm --> Core[系統比對缺件]:::system
    Core --> Teacher
    Teacher[導師確認備審內容]:::teacher
    Teacher --> Output[產出完整備審資料]:::system
```

## 圖 16：科辦上傳紀錄流程圖

依 2026-10-07 錄音討論與 2026-10-08 使用者決定：科辦是「科上官方紀錄」的資料來源，用固定 Excel 範本一次上傳服務、公假、嘉獎名單，不逐筆審核、不審備審資料。

```mermaid
%%{init: {'theme':'base','themeVariables': {'fontFamily':'Microsoft JhengHei, Noto Sans TC, Arial, sans-serif','primaryColor':'#F3F4F6','primaryTextColor':'#111827','primaryBorderColor':'#9CA3AF','lineColor':'#6B7280','edgeLabelBackground':'#FFFFFF'},'flowchart':{'wrappingWidth':400}}}%%
flowchart TD
    classDef student fill:#DBEAFE,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef staff fill:#EDE9FE,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef system fill:#E0F2FE,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef ai fill:#FFEDD5,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef alert fill:#FEE2E2,stroke:#9CA3AF,color:#111827,stroke-width:1px;
    classDef note fill:#FFFFFF,stroke:#9CA3AF,color:#6B7280,stroke-width:1px,stroke-dasharray:5 3;

    Start([科辦登入]):::staff --> Template[下載固定 Excel 範本<br/>學號、項目類別、名稱、日期、說明]:::staff
    Template --> Upload[填好名單後上傳<br/>例如帶高中機器人社團、公假、嘉獎]:::staff
    Upload --> Check{系統檢查格式<br/>學號存在、日期正確？}
    Check -- 否 --> Err[列出第幾列有問題與原因]:::alert
    Err --> Upload
    Check -- 是 --> Preview[預覽：每位學生會新增哪些紀錄]:::system
    Preview --> Publish[科辦按「確認匯入」]:::staff
    Publish --> Record[依學號列入學生學習資料<br/>標示「科辦提供」，學生不能修改]:::system
    Record --> Cert[系統可依紀錄產出電子證明<br/>（類似電子獎狀）]:::system
    Record --> Student[學生在「活動與經歷」看到紀錄]:::student
    Record --> AI[自傳小幫手與備審資料引用<br/>標示「依據：科辦紀錄」]:::ai
    Note1[取代過去「做備審時才一次匯整給科助、<br/>在電子證書平台開證明」的做法]:::note -.- Upload
    Note2[科辦是官方資料來源，不逐筆審核、<br/>不審備審資料（備審由導師確認）]:::note -.- Publish
    Note3[待確認：學生發現漏列時可否線上請科辦補登；<br/>電子證明的版面]:::note -.- Cert
```

## 修改圖表的步驟

1. 修改 `docs/images/` 裡對應的 `.mmd` 檔。
2. 匯出圖片（需先安裝 Mermaid CLI）：

   ```bash
   mmdc -i D-10-main-line-flow.mmd -o D-10-main-line-flow.png -b white -s 2
   mmdc -i D-10-main-line-flow.mmd -o D-10-main-line-flow.svg -b white
   ```

3. 重新產生本文件，或把 `.mmd` 內容貼回對應章節，確保兩邊一致。
