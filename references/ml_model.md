# ML Model - Huong dan chi tiet

## Tong quan
Module ML su dung **Random Forest** va **XGBoost** de du doan xu huong gia co phieu
trong 3-5 phien toi (T+3).

## Kien truc Model

### Input Features (10 phien gan nhat)
- **RSI_14**: Chi so suc manh tuong doi
- **MACD_12_26_9**: Duong MACD chinh
- **MACDh_12_26_9**: MACD Histogram
- **BBP_20_2.0**: Bollinger %B
- **BBB_20_2.0**: Bollinger Bandwidth
- **STOCHk_14_3_3**: Stochastic %K
- **STOCHd_14_3_3**: Stochastic %D
- **Volume_ratio**: Ty le volume/MA20
- **price_change**: Thay doi gia %
- **price_ma20_ratio**: Gia / SMA_20
- **price_ma50_ratio**: Gia / SMA_50
- **price_ema9_ratio**: Gia / EMA_9
- **volume_change**: Thay doi volume %
- **atr_ratio**: ATR / Gia (do bien dong)

### Output
- Xac suat tang gia trong 3-5 phien toi
- Nguong hanh dong: **Xac suat > 0.65** → xem xet mua

### Cross-Validation
- Su dung **TimeSeriesSplit** (khong shuffle vi la time series)
- Mac dinh 5 folds
- Bao cao accuracy tung fold va trung binh

## Cach su dung

```python
from ml_model import predict_stock, predict_watchlist

# Du doan 1 ma
result = predict_stock("FPT", start="2024-01-01", model_type="xgboost")

# Du doan nhieu ma
results = predict_watchlist(["FPT", "HPG", "VNM"], start="2024-01-01")
```

## Luu y quan trong
1. **Can it nhat 1 nam du lieu** de training co y nghia
2. **Ket qua qua khu khong dam bao loi nhuan tuong lai**
3. **Nen ket hop voi phan tich ky thuat** (check_signal) va tin tuc vi mo
4. **Paper trade >= 1 thang** truoc khi dung tien that
5. **Model can re-train dinh ky** (moi thang 1 lan) vi thi truong thay doi
