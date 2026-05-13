# Zalo OA Bot - Huong dan chi tiet

## Tong quan
Bot canh bao tin hieu mua/ban co phieu qua Zalo Official Account.
Chay moi 10 phut trong gio giao dich (9:00-11:30, 13:00-15:00).

## Thiet lap

### Buoc 1: Tao Zalo Official Account
1. Truy cap: https://oa.zalo.me
2. Dang ky tai khoan OA (mien phi)
3. Chon loai OA phu hop

### Buoc 2: Lay Access Token
1. Vao trang quan ly OA
2. Tim muc "API" hoac "Developers"
3. Tao Access Token
4. **Luu y**: Token het han sau 90 ngay, can lam moi

### Buoc 3: Lay User ID nguoi nhan
1. Nguoi nhan phai **follow OA** cua ban tren Zalo
2. Lay User ID tu trang quan ly OA → Followers

### Buoc 4: Cau hinh bot
Mo file `zalo_bot.py` va cap nhat:
```python
ZALO_OA_ACCESS_TOKEN = "your_token_here"
ZALO_USER_IDS = ["user_id_1", "user_id_2"]
WATCHLIST = ["FPT", "HPG", "VNM"]
```

## Cach chay

### Che do test (khong gui Zalo)
```bash
python zalo_bot.py --test
```

### Chay bot lien tuc
```bash
python zalo_bot.py --run
```

## Format tin nhan mau
```
🔔 🟢 MUA: FPT
💰 Gia: 120,000 VND
🎯 Target: 128,400 (+7%)
🛑 Stoploss: 114,000
📝 Gia cat len MA20 + RSI=45.2
─────────────────
⏰ 10:30 13/05/2026
⚠️ Chi la tin hieu tham khao, khong phai khuyen nghi dau tu.
```

## Kien truc
```
Script Python (chay moi 10 phut trong gio GD)
    └─> Quet danh sach ma (watchlist)
        └─> Goi check_signal() cho tung ma
            └─> Neu co tin hieu → Zalo OA API → Tin nhan Zalo
```

## Luu y phap ly
- **Chi lam Bot canh bao (alert bot)**, KHONG auto-order
- Auto-trading hoan toan tu dong bi han che tai Viet Nam
- Luon kem theo canh bao "khong phai khuyen nghi dau tu"
