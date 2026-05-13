"""
VN Stock Scanner - Quet danh muc co phieu va phat hien tin hieu
================================================================
Quet nhieu ma co phieu cung luc, loc tin hieu MUA/BAN/CANH BAO.
"""

import sys
import io
import os
import datetime



# Them root vao sys.path de import core module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.stock_analyst import get_stock_data, add_indicators, check_signal, analyze_market_psychology


# ============================================================================
# DANH SACH MA CO PHIEU PHO BIEN
# ============================================================================

VN30_WATCHLIST = [
    "VIC", "VHM", "VNM", "VCB", "BID", "CTG", "TCB", "MBB",
    "HPG", "HSG", "FPT", "MWG", "SAB", "GAS", "POW", "PLX",
    "PVD", "REE", "VJC", "HVN",
]
BANK_WATCHLIST = ["VCB", "BID", "CTG", "TCB", "MBB", "ACB", "VPB", "STB", "HDB", "TPB"]
BDS_WATCHLIST = ["VIC", "VHM", "NVL", "DXG", "KDH", "NLG", "PDR", "DIG", "HDG", "CEO"]
TECH_WATCHLIST = ["FPT", "CMG", "ELC", "FOX", "ITD"]


def scan_watchlist(watchlist: list, start: str = None, end: str = None,
                   entry_prices: dict = None, source: str = "VCI") -> list:
    """Quet danh sach ma co phieu va tra ve tin hieu."""
    if start is None:
        start = (datetime.date.today() - datetime.timedelta(days=365)).strftime("%Y-%m-%d")
    if end is None:
        end = datetime.date.today().strftime("%Y-%m-%d")
    if entry_prices is None:
        entry_prices = {}
    
    results = []
    errors = []
    
    print(f"\n{'='*70}")
    print(f"  QUET DANH MUC - {len(watchlist)} ma co phieu")
    print(f"  Giai doan: {start} -> {end} | Nguon: {source}")
    print(f"{'='*70}\n")
    
    for i, symbol in enumerate(watchlist, 1):
        try:
            print(f"  [{i}/{len(watchlist)}] Dang quet {symbol}...", end="")
            df = get_stock_data(symbol, start=start, end=end, source=source)
            df = add_indicators(df)
            entry = entry_prices.get(symbol, None)
            signal = check_signal(df, entry_price=entry)
            signal['symbol'] = symbol
            last = df.iloc[-1]
            signal['rsi'] = round(last['RSI_14'], 1)
            signal['volume_ratio'] = round(last['Volume_ratio'], 2)
            results.append(signal)
            icon = signal.get('icon', '⬜')
            print(f" {icon} {signal['signal']} | Gia: {signal['price']:,.0f} | RSI: {signal['rsi']}")
        except Exception as e:
            errors.append((symbol, str(e)))
            print(f" [X] Loi: {e}")
    
    # === TONG HOP KET QUA ===
    print(f"\n{'='*70}")
    print(f"  TONG HOP KET QUA")
    print(f"{'='*70}")
    
    buy_signals = [r for r in results if r['signal'] in ('MUA',)]
    sell_signals = [r for r in results if r['signal'] in ('BAN', 'CAT LO', 'BAN KHAN')]
    watch_signals = [r for r in results if r['signal'] == 'THEO DOI']
    
    if buy_signals:
        print(f"\n  🟢 TIN HIEU MUA ({len(buy_signals)} ma):")
        for s in buy_signals:
            print(f"    • {s['symbol']:5s} | Gia: {s['price']:>10,.0f} | {s['reason']}")
            if 'target' in s:
                print(f"      🎯 Target: {s['target']:,.0f} | 🛑 Stoploss: {s['stoploss']:,.0f}")
    if sell_signals:
        print(f"\n  🔴 TIN HIEU BAN ({len(sell_signals)} ma):")
        for s in sell_signals:
            print(f"    • {s['symbol']:5s} | Gia: {s['price']:>10,.0f} | {s['reason']}")
    if watch_signals:
        print(f"\n  ⬜ THEO DOI ({len(watch_signals)} ma):")
        for s in watch_signals:
            print(f"    • {s['symbol']:5s} | Gia: {s['price']:>10,.0f} | RSI: {s['rsi']}")
    if errors:
        print(f"\n  ❌ LOI ({len(errors)} ma):")
        for sym, err in errors:
            print(f"    • {sym}: {err}")
    
    print(f"\n  ⚠️ Chi la tin hieu tham khao, khong phai khuyen nghi dau tu.")
    print(f"{'='*70}\n")
    
    return results


def scan_and_export(watchlist: list, filename: str = None, **kwargs) -> str:
    """Quet va xuat ket qua ra file CSV."""
    import pandas as pd
    results = scan_watchlist(watchlist, **kwargs)
    if not results:
        print("Khong co ket qua de xuat.")
        return None
    df_results = pd.DataFrame(results)
    if filename is None:
        today = datetime.date.today().strftime("%Y%m%d")
        filename = f"scan_results_{today}.csv"
    home_dir = os.path.expanduser("~")
    filepath = os.path.join(home_dir, filename)
    try:
        df_results.to_csv(filepath, index=False, encoding="utf-8-sig")
        print(f"\n📁 Da luu ket qua tai: {filepath}")
    except Exception as e:
        print(f"\n[!] Khong the luu file: {e}")
        filepath = None
    return filepath
