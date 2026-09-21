# 康寧大學公開來源快照

> 用途：保存已公開瀏覽並下載的官方頁面／附件，供規格核對與後續 AI Agent 建立來源索引。
>
> 抓取日期：2026-09-17
>
> 限制：這些檔案是來源快照，不等於目前生效的全部校規。正式採用前仍需確認適用學年度、公告版本與科辦／教務單位說明。

## 已下載來源

| 本機檔案 | 公開來源 | 目前可確認內容 |
| --- | --- | --- |
| `ukn-homepage.html` | <https://www.ukn.edu.tw/index.php> | 康寧大學官方首頁、招生／校務／學術單位等入口 |
| `ukn-class-schedule.html` | <https://ec.ukn.edu.tw/Schedule/ClassSchedule.aspx> | 課表查詢的學期、科系、年級、班別欄位 |
| `ukn-transfer-credit-login.html` | <https://ec.ukn.edu.tw/CT_web/login.aspx> | 抵免系統公開登入頁與操作手冊／辦法連結；未登入 |
| `ukn-transfer-department-notice.html` | <https://www.ukn.edu.tw/p/406-1000-41802,r257.php?Lang=zh-tw> | 114 學年度第 2 學期專科班校內轉科公告與附件 |
| `1142-校內轉科公告附件.doc` | 轉科公告下載附件 | 轉科名額、審查標準、申請表等附件來源 |
| `im-curriculum-planning.html` | <https://im.ukn.edu.tw/p/405-1028-609,c82-1.php> | 資管科修業科目表頁面 |
| `im-special-project-forms.html` | <https://im.ukn.edu.tw/p/412-1028-1194.php?Lang=zh-tw> | 資管科專題指導、初審、審查及意見回覆表格入口 |
| `im-news-list.html` | <https://im.ukn.edu.tw/p/403-1028-16-1.php?Lang=zh-tw> | 資管科最新活動與公告入口 |
| `im-project-submission-notice.html` | <https://im.ukn.edu.tw/p/406-1028-42684,r16.php?Lang=zh-tw> | 114 學年度畢業專題書面資料繳交公告 |
| `附件一_專題著作授權書.doc`／`.odt`／`.pdf` | 上述專題繳交公告附件 | 專題著作授權書的三種公開附件格式 |
| `附件二_專題成果報告封面及書背格式.doc`／`.odt`／`.pdf` | 上述專題繳交公告附件 | 專題成果報告封面及書背格式的三種公開附件格式 |
| `ukn-course-plan-5345609.html` | <https://ec.ukn.edu.tw/Schedule/TPlanContent.aspx?smtr=1151&cosid=5345609&cosclass=A> | 1151 學期、五專資訊管理科五年級 A 班教學計畫頁 |
| `ukn-course-schema-5345609.html` | <https://ec.ukn.edu.tw/cschemaNew/CSBrowse.aspx?CSID=5345609&Annual=115> | 實務專題課程、1 學分、專題課與課程摘要／大綱 |

## 初步可用的規格線索

- 學校課務資料可作為科別、年級、班別與課程來源，但不能直接視為登入驗證服務。
- 資管科專題公告內容具有學年度版本，不能與其他年度規則混用。
- 專題表格入口、公告與附件適合納入 `official_sources`；AI Agent 只能產生候選摘要與版本差異，需人工確認後發布。
- 抵免系統只能保存公開入口與人工處理狀態；本專案不登入、不保存抵免帳密，也不抓取登入後內容。

## 尚未完成的核對

- 各附件的正式檔名、適用年度與內容欄位。
- 資管科不同專題類型的正式繳交清單。
- 學校主資料庫／SSO／LDAP 是否提供本專案可用的授權介接方式。
- 111 級實務專題規定是否仍適用於目前或下一屆學生。
- `https://drive.google.com/drive/folders/1lc-05tMIOKmqWnkebDraxmMUjj9I7dMi?usp=sharing` 資料夾內的文件是否公開及可作為正式來源。
