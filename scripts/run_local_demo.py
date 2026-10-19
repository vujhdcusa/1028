"""啟動本機合成資料展示站：python scripts/run_local_demo.py

加上 --ocr 會改用真實的本機 RapidOCR（組員 OCR 流程＋PP-OCRv5），上傳的圖片只在本機辨識；
需先執行 python scripts/download_ocr_models.py 下載模型。
再加上 --gpu 編號 會用 Windows DirectML 顯示卡加速（需安裝 onnxruntime-directml）；
筆電的 0 多半是內建顯示，獨立顯示卡常是 1。不加 --gpu 就是 CPU。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.demo import create_local_demo_app


app = create_local_demo_app()
args = sys.argv[1:]
if "--ocr" in args:
    app.config["DOCUMENT_ANALYSIS_PROVIDER"] = "rapidocr"
if "--gpu" in args:
    position = args.index("--gpu")
    app.config["OCR_DEVICE"] = "dml"
    app.config["OCR_DML_DEVICE_ID"] = int(args[position + 1]) if position + 1 < len(args) else 0

if __name__ == "__main__":
    print("本機展示站：http://127.0.0.1:5013/proposal-preview")
    print("合成帳號：student_demo / teacher_demo / staff_demo / admin_demo；密碼皆為 demo2026")
    print("資料庫為記憶體 SQLite，服務停止後資料即消失；Google Drive 不會連線。")
    if app.config["DOCUMENT_ANALYSIS_PROVIDER"] == "rapidocr":
        device = (f"顯示卡（DirectML 編號 {app.config['OCR_DML_DEVICE_ID']}）"
                  if app.config.get("OCR_DEVICE") == "dml" else "CPU")
        print(f"OCR 模式：真實本機 RapidOCR，執行裝置：{device}")
    else:
        print("OCR 模式：模擬 OCR（合成資料）；加上 --ocr 可改用真實辨識")
    # 多執行緒：單執行緒時瀏覽器保留的連線會卡住其他請求；記憶體 SQLite 已設定 StaticPool 可跨執行緒，
    # RapidOCR 推論另有鎖保護
    app.run(host="127.0.0.1", port=5013, debug=False, threaded=True)
