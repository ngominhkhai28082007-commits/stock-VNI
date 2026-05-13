# Backtest - Huong dan chi tiet

## Tong quan
Module backtest cho phep kiem tra hieu suat chien luoc giao dich tren du lieu lich su.

## Chien luoc mac dinh

### Dieu kien MUA
- Gia cat len SMA_20 **VA** RSI_14 < 60
- HOAC: Stochastic %K phuc hoi tu vung qua ban (%K < 30, %K cat len %D)
- HOAC: MACD cat len Signal line + Volume > 1.2x trung binh

### Dieu kien BAN
- Lai >= 7% (take profit)
- HOAC Lo >= 5% (stop loss)
- HOAC Gia cat xuong SMA_20

### Quan ly von
- Ty trong toi da moi lenh: 20% von
- Phi giao dich: 0.15% moi chieu

## Cach su dung

### Backtest 1 ma
```python
from backtest import run_backtest

result = run_backtest(
    symbol="FPT",
    start="2024-01-01",
    initial_capital=100_000_000,  # 100 trieu VND
    take_profit=0.07,             # Chot loi 7%
    stop_loss=-0.05,              # Cat lo 5%
)
```

### So sanh nhieu ma
```python
from backtest import compare_backtest

df = compare_backtest(
    ["FPT", "HPG", "VNM", "TCB"],
    start="2024-01-01",
)
```

## Chi so bao cao
| Chi so | Y nghia |
|--------|---------|
| Win Rate | Ty le lenh thang / tong so lenh |
| Max Drawdown | Muc sut giam lon nhat tu dinh |
| Sharpe Ratio | Ty le loi nhuan / rui ro (> 1 = tot) |
| Avg Holding | Thoi gian giu trung binh (ngay) |

## Luu y
- **Ket qua qua khu KHONG dam bao loi nhuan tuong lai**
- Phi truot gia (slippage) chua duoc tinh trong backtest
- Nen test tren nhieu giai doan thi truong khac nhau
- Paper trade >= 1 thang truoc khi dung tien that
