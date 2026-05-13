"""
Script lay du lieu OHLCV (Open, High, Low, Close, Volume) cho chung khoan Viet Nam.
Su dung thu vien vnstock v4.x (API moi nhat)
"""
import sys
import io
import os

# Fix encoding cho Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

try:
    from vnstock import Quote
except ImportError:
    from vnstock import Vnstock
    Quote = None

def get_stock_data(symbol="PC1", start_date="2024-05-05", end_date="2025-12-31", interval="d"):
    """
    Lay du lieu OHLCV cho mot ma co phieu.
    """
    if Quote:
        # Su dung API moi theo document
        quote = Quote(symbol=symbol, source="KBS")
        df = quote.history(start=start_date, end=end_date, interval=interval)
    else:
        # Fallback neu khong tim thay Quote api
        stock = Vnstock().stock(symbol=symbol, source="KBS")
        df = stock.quote.history(start=start_date, end=end_date, interval=interval)
    
    return df


def get_multiple_stocks(symbols, start_date="2024-01-01", end_date="2025-12-31", interval="1D"):
    """
    Lay du lieu OHLCV cho nhieu ma co phieu cung luc.
    """
    results = {}
    for sym in symbols:
        try:
            print(f"  Dang lay du lieu {sym}...")
            results[sym] = get_stock_data(sym, start_date, end_date, interval)
            print(f"  [OK] {sym}: {len(results[sym])} dong du lieu")
        except Exception as e:
            print(f"  [FAIL] {sym}: Loi - {e}")
    return results


if __name__ == "__main__":
    from datetime import datetime
    
    # ========================
    # CAU HINH O DAY
    # ========================
    SYMBOL = "DXG"                  # Ma co phieu
    END_DATE = "2026-05-12"         # Ngay ket thuc
    START_DATE = "2025-11-12"       # Ngay bat dau (6 thang truoc ngay ket thuc)
    INTERVAL = "d"                  # d = ngay, w = tuan, m = thang
    
    # Lay thu muc home cua user de tranh loi OneDrive
    home_dir = os.path.expanduser("~")
    
    print("=" * 60)
    print(f"LAY DU LIEU OHLCV - {SYMBOL} | 6 THANG (VNSTOCK 4.x)")
    print(f"Tu {START_DATE} den {END_DATE}")
    print("=" * 60)
    
    # --- 1. Lay du lieu 1 ma ---
    print(f"\nMa: {SYMBOL} | Tu {START_DATE} -> {END_DATE} | Interval: {INTERVAL}")
    print("-" * 60)
    
    try:
        df = get_stock_data(SYMBOL, START_DATE, END_DATE, INTERVAL)
        
        if df is not None and not df.empty:
            print(f"\nSo dong du lieu: {len(df)}")
            print(f"Cac cot: {list(df.columns)}")
            
            # --- 2. Xuat ra file CSV ---
            csv_filename = f"{SYMBOL}_ohlcv.csv"
            # Luu vao home dir truoc
            csv_path = os.path.join(home_dir, csv_filename)
            
            try:
                df.to_csv(csv_path, index=False, encoding="utf-8-sig")
                print(f"\nDa luu file CSV tam thoi tai: {csv_path}")
                print(f"MO_FILE_CSV: {csv_path}") # Tag de script khac hoac tool move file
            except Exception as e_save:
                print(f"\n[!] Khong the luu file vao {csv_path}: {e_save}")
                print("\n--- DU LIEU CSV (DANG TEXT) ---")
                print(df.to_csv(index=False, encoding="utf-8-sig"))
                print("--- KET THUC DU LIEU ---")
            
            print(f"\n--- 5 dong dau tien ---")
            print(df.head(5).to_string(index=False))
        else:
            print("\n[!] Khong co du lieu tra ve.")
            
    except Exception as e:
        print(f"\n[X] Da xay ra loi: {e}")
        import traceback
        traceback.print_exc()
    
    print("\nHoan tat!")
