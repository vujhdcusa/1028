"""啟動本機合成資料展示站：python scripts/run_local_demo.py

加上 --ocr 會改用真實的本機 RapidOCR（組員 OCR 流程＋PP-OCRv5），上傳的圖片只在本機辨識；
需先執行 python scripts/download_ocr_models.py 下載模型。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.demo import create_local_demo_app


app = create_local_demo_app()
if "--ocr" in sys.argv[1:]:
    app.config["DOCUMENT_ANALYSIS_PROVIDER"] = "rapidocr"

if __name__ == "__main__":
    print("本機展示站：http://127.0.0.1:5013/proposal-preview")
    print("合成帳號：student_demo / teacher_demo / staff_demo / admin_demo；密碼皆為 demo2026")
    print("資料庫為記憶體 SQLite，服務停止後資料即消失；Google Drive 不會連線。")
    print("OCR 模式：" + ("真實本機 RapidOCR（一頁約 10 秒）" if app.config["DOCUMENT_ANALYSIS_PROVIDER"] == "rapidocr"
                         else "模擬 OCR（合成資料）；加上 --ocr 可改用真實辨識"))
    # 多執行緒：單執行緒時瀏覽器保留的連線會卡住其他請求；記憶體 SQLite 已設定 StaticPool 可跨執行緒，
    # RapidOCR 推論另有鎖保護
    app.run(host="127.0.0.1", port=5013, debug=False, threaded=True)
