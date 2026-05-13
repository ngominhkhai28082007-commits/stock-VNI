# VN Stock Analyst

Hệ thống phân tích kỹ thuật và AI hỗ trợ dự đoán thị trường chứng khoán Việt Nam. Dự án được thiết kế dưới dạng module chuyên nghiệp, hỗ trợ tự động lấy dữ liệu (qua vnstock), tính toán các chỉ báo kỹ thuật, và đưa ra khuyến nghị mua/bán.

## 📂 Cấu trúc dự án

```text
stock VNI/
├── main.py              # File chạy chính (Entry Point)
├── core/                # Module cốt lõi
│   └── stock_analyst.py # Engine lấy dữ liệu, tính chỉ báo, phát hiện tín hiệu
├── analysis/            # Các công cụ phân tích mở rộng
│   ├── ml_model.py      # AI dự đoán xu hướng (XGBoost / Random Forest)
│   ├── backtest.py      # Kiểm tra hiệu suất chiến lược trong quá khứ
│   └── scanner.py       # Quét tín hiệu toàn bộ danh mục (VN30, Bank...)
├── bot/                 # Bot tự động
│   └── zalo_bot.py      # Gửi cảnh báo mua/bán qua Zalo OA
├── data/                # Module dữ liệu thô
│   └── get_ohlcv.py     # Script độc lập tải dữ liệu thô ra file CSV
└── requirements.txt     # Danh sách thư viện cần thiết
```

## 🚀 Hướng dẫn cài đặt

1. Đảm bảo bạn đã cài đặt Python (3.9 trở lên).
2. Mở Terminal/Command Prompt tại thư mục dự án và chạy:
```bash
pip install vnstock pandas-ta scikit-learn xgboost python-telegram-bot schedule requests
```

## 🛠 Hướng dẫn sử dụng

Sử dụng trực tiếp qua file `main.py` ở thư mục gốc:

**1. Phân tích 1 mã cổ phiếu cụ thể:**
```bash
python main.py analyze FPT
```
*(Lệnh này sẽ tải dữ liệu FPT, tính 30 chỉ báo, xuất tín hiệu MUA/BÁN và tâm lý thị trường).*

**2. Quét toàn bộ danh mục:**
```bash
python main.py scan --group vn30
# Các nhóm có sẵn: vn30, bank, bds, tech
```

**3. Sử dụng AI để dự đoán xu hướng T+3:**
```bash
python main.py predict HPG --model xgboost
```

**4. Backtest chiến lược (Kiểm tra xem phương pháp có lãi không):**
```bash
python main.py backtest VNM
```

**5. Chạy Bot Zalo cảnh báo tự động:**
```bash
python main.py bot --run
```
*(Lưu ý: Bạn cần cấu hình `ZALO_OA_ACCESS_TOKEN` trong file `bot/zalo_bot.py` trước khi dùng).*

## ⚠️ Khuyến cáo rủi ro
Phần mềm này chỉ cung cấp các phân tích dựa trên dữ liệu lịch sử và chỉ báo kỹ thuật. Không phải là lời khuyên đầu tư tài chính. Luôn luôn kiểm tra (backtest) và quản trị rủi ro trước khi dùng tiền thật.
