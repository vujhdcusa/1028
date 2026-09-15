# MySQL 設定筆記

日期：2026-09-15

## 目前系統設定狀態 (已完成)

已成功完成 MySQL Server 8.0 資料庫環境設定與初始化：

- **服務連接埠**：`127.0.0.1:3307`
- **資料庫名稱**：`smart_learning_portfolio`
- **專用帳號**：`smart_learning_app`
- **驗證方式**：`mysql_native_password`
- **連線測試**：使用 `scripts/check_db.py` 通過驗證。
- **資料表建置**：已透過 `scripts/init_db.py` 建立 `users`, `student_profiles`, `portfolios`, `portfolio_evidence`, `agent_tasks`, `audit_logs` 資料表與預設管理者帳號 (`admin`)。

`.env` 設定範例：

```env
DB_HOST=127.0.0.1
DB_PORT=3307
DB_NAME=smart_learning_portfolio
DB_USER=smart_learning_app
DB_PASSWORD=change-this-password
```

---

## 新環境建立指南與初始化步驟

新環境開發生效步驟：

1. 先確認你知道 MySQL root 密碼，開啟 PowerShell：

```powershell
& "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -h 127.0.0.1 -P 3307 -u root -p
```

2. 建立專案資料庫與專用帳號：

```sql
CREATE DATABASE IF NOT EXISTS smart_learning_portfolio
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'smart_learning_app'@'localhost'
  IDENTIFIED BY 'change-this-password';

GRANT ALL PRIVILEGES ON smart_learning_portfolio.*
  TO 'smart_learning_app'@'localhost';

FLUSH PRIVILEGES;
exit;
```

3. 執行 Python 初始化腳本建立資料表及初始化預設帳號：

```powershell
python scripts/init_db.py
```

> **注意**：預設管理者帳號之密碼可於 `.env` 中設定 `ADMIN_DEFAULT_PASSWORD`，初次初始化後請務必修改密碼。

---

## 歷史紀錄與問題排查 (Troubleshooting)

### 偵測到的 MySQL 環境
```text
MySQL Server 8.0: C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe
MySQL Server 8.4: C:\Program Files\MySQL\MySQL Server 8.4\bin\mysql.exe
XAMPP MariaDB: D:\xampp\mysql\bin\mysql.exe
```

### 常見連線錯誤與判斷方式

1. **`Access denied for user 'root'@'localhost'`**
   - 代表 MySQL 服務正常，但 `root` 無密碼或密碼錯誤。建議不要讓 Flask 直接用 `root`，改用專用帳號 `smart_learning_app`。

2. **`Can't connect to MySQL server`**
   - 請檢查 MySQL 服務 (`MySQL80`) 是否執行，以及 Port 是否設定為 `3307`。

3. **`caching_sha2_password` 驗證錯誤**
   - 若連線提示缺少 `cryptography` 套件，可將專案帳號驗證方式改為 `mysql_native_password`。
