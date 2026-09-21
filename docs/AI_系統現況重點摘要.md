# 資管科智慧學習歷程系統 - 現況重點摘要

> **文件資訊**  
> 建立日期：2026-09-21  
> 檔案位置：`d:\democase\ai\docs\AI_系統現況重點摘要.md`

---

## 一、資料庫常用指令 (MySQL / MariaDB)

```sql
USE smart_learning_portfolio;
SHOW TABLES;
SELECT * FROM users;
SELECT * FROM portfolios;
SELECT * FROM portfolio_submissions;
```

---

## 二、系統各角色功能現況

### 1. 學生端 (`/student/portfolio`)
| 功能名稱 | 完成狀態 |
| :--- | :--- |
| 查看自己的學習成果 | ✅ 已有 |
| 新增學習成果 | ✅ 已有 |
| 修改學習成果 | ✅ 已有 |
| 上傳成果檔案 | ✅ 已有 |
| 送出成果審查 | ✅ 已有 |
| 刪除學習成果 | ❌ 尚未提供 |
| 刪除上傳檔案 | ❌ 尚未提供 |

---

### 2. 教師端 (`/teacher/reviews`)
- ✅ 查看受指派的審查送件
- ✅ 針對送件留下評語與回饋

---

### 3. 科辦／行政端 (`/staff/dashboard`)
- ✅ 查看待處理送件
- ✅ 登錄審查結果：
  - **核可**
  - **需要補正**
  - **退件**
  - **補充說明**

---

### 4. 管理員端 (`/admin/dashboard`)
- ✅ 查看全系統統計資料
- ❌ 網頁版帳號新增、修改、刪除 (CRUD) 尚未完成

---

## 三、總結與後續待開發事項

- **目前進度**：已具備完整的核心流程（新增 $\rightarrow$ 查看 $\rightarrow$ 修改 $\rightarrow$ 送審 $\rightarrow$ 教師/行政回饋）。
- **待補強功能**：
  1. 學生端成果與檔案刪除機制。
  2. 管理員網頁端完整的帳號與權限 CRUD 管理功能。
