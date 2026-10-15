"""啟動本機合成資料展示站：python scripts/run_local_demo.py"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.demo import create_local_demo_app


app = create_local_demo_app()

if __name__ == "__main__":
    print("本機展示站：http://127.0.0.1:5013/proposal-preview")
    print("合成帳號：student_demo / teacher_demo / staff_demo / admin_demo；密碼皆為 demo2026")
    print("資料庫為記憶體 SQLite，服務停止後資料即消失；Google Drive 不會連線。")
    app.run(host="127.0.0.1", port=5013, debug=False, threaded=False)
