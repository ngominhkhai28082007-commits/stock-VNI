"""
VN Stock Analyst - Module phan tich ky thuat chung khoan Viet Nam
=================================================================
Bao gom:
  1. get_stock_data()   - Lay du lieu OHLCV tu vnstock
  2. add_indicators()   - Them chi bao ky thuat (RSI, MACD, BB, Stoch, ATR, OBV...)
  3. check_signal()     - Phat hien tin hieu MUA/BAN/THEO DOI
  4. analyze_market_psychology() - Phan tich tam ly thi truong
  5. analyze_stock()    - Phan tich toan dien 1 ma co phieu
"""

import sys
import io
import os
import datetime



import pandas as pd
import numpy as np

try:
    import pandas_ta as ta
except ImportError:
    print("[!] Chua cai pandas-ta. Chay: pip install pandas-ta")
    ta = None

try:
    from vnstock import Quote
except ImportError:
    try:
        from vnstock3 import Vnstock
    except ImportError:
        from vnstock import Vnstock
    Quote = None


# ============================================================================
# 1. LAY DU LIEU (Data Source)
# ============================================================================

def get_stock_data(symbol: str, start: str = "2023-01-01", end: str = None,
                   source: str = "VCI", interval: str = "1D") -> pd.DataFrame:
    """
    Lay du lieu OHLCV tu vnstock.
    
    Parameters:
        symbol : Ma CK viet hoa (VD: "FPT", "HPG", "VNM")
        start  : Ngay bat dau "YYYY-MM-DD"
        end    : Ngay ket thuc "YYYY-MM-DD" (mac dinh = hom nay)
        source : Nguon du lieu ("VCI", "TCBS", "KBS")
        interval : "1D" (ngay), "1W" (tuan)
    
    Returns:
        DataFrame voi cot: open, high, low, close, volume (index = time)
    """
    if end is None:
        end = datetime.date.today().strftime("%Y-%m-%d")
    
    if Quote:
        # vnstock v4.x API
        quote = Quote(symbol=symbol, source=source.lower())
        df = quote.history(start=start, end=end, interval=interval)
    else:
        # vnstock v3.x fallback
        stock = Vnstock().stock(symbol=symbol, source=source.lower())
        df = stock.quote.history(start=start, end=end, interval=interval)
    
    # Chuan hoa ten cot
    df.columns = [c.lower() for c in df.columns]
    
    # Dam bao cot time la datetime va set lam index
    if 'time' in df.columns:
        df['time'] = pd.to_datetime(df['time'])
        df.set_index('time', inplace=True)
    elif 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
    
    # Dam bao cot so la numeric
    for col in ['open', 'high', 'low', 'close', 'volume']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    df.sort_index(inplace=True)
    return df


# ============================================================================
# 2. TINH CHI BAO KY THUAT (Technical Indicators)
# ============================================================================

def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Them day du cac chi bao ky thuat vao DataFrame.
    
    Nhom 1: Dong luong (Momentum)     - RSI, Stochastic
    Nhom 2: Xu huong (Trend)          - SMA, EMA, MACD
    Nhom 3: Bien dong (Volatility)    - Bollinger Bands, ATR
    Nhom 4: Khoi luong (Volume)       - Volume MA, OBV, Volume Ratio
    """
    if ta is None:
        raise ImportError("Can cai dat pandas-ta: pip install pandas-ta")
    
    # ── Nhom 1: Dong luong (Momentum) ──────────────────────────────────
    df.ta.rsi(length=14, append=True)
    df.ta.stoch(k=14, d=3, smooth_k=3, append=True)
    
    # ── Nhom 2: Xu huong (Trend) ────────────────────────────────────────
    df.ta.sma(length=20, append=True)
    df.ta.sma(length=50, append=True)
    df.ta.sma(length=200, append=True)
    df.ta.ema(length=9, append=True)
    df.ta.ema(length=21, append=True)
    df.ta.macd(fast=12, slow=26, signal=9, append=True)
    
    # ── Nhom 3: Bien dong (Volatility) ─────────────────────────────────
    df.ta.bbands(length=20, std=2, append=True)
    df.ta.atr(length=14, append=True)
    
    # ── Nhom 4: Khoi luong (Volume) ─────────────────────────────────────
    df['Volume_MA20'] = df['volume'].rolling(window=20).mean()
    df['Volume_ratio'] = df['volume'] / df['Volume_MA20']
    df.ta.obv(append=True)
    df['price_change'] = df['close'].pct_change()
    df['vol_up']   = df['volume'].where(df['price_change'] > 0, 0)
    df['vol_down'] = df['volume'].where(df['price_change'] < 0, 0)
    
    return df.dropna()


# ============================================================================
# 3. KIEM TRA TIN HIEU GIAO DICH (Trading Signal)
# ============================================================================

def check_signal(df: pd.DataFrame, entry_price: float = None) -> dict:
    """
    Tra ve dict voi keys: signal, reason, price, rsi, ma20, target, stoploss
    Tich hop: RSI, MACD, Volume, Stochastic, ATR
    """
    last = df.iloc[-1]
    prev = df.iloc[-2]
    
    current_price  = last['close']
    rsi            = last['RSI_14']
    ma20           = last['SMA_20']
    ma20_prev      = prev['SMA_20']
    macd           = last['MACD_12_26_9']
    signal_line    = last['MACDs_12_26_9']
    stoch_k        = last['STOCHk_14_3_3']
    stoch_d        = last['STOCHd_14_3_3']
    stoch_k_prev   = prev['STOCHk_14_3_3']
    stoch_d_prev   = prev['STOCHd_14_3_3']
    volume_ratio   = last['Volume_ratio']
    atr            = last['ATRr_14']
    obv_trend      = last['OBV'] > prev['OBV']

    # ── Tin hieu MUA ────────────────────────────────────────────────────
    price_cross_up   = prev['close'] <= ma20_prev and current_price > ma20
    stoch_cross_up   = stoch_k_prev < stoch_d_prev and stoch_k > stoch_d
    macd_cross_up    = prev['MACD_12_26_9'] < prev['MACDs_12_26_9'] and macd > signal_line

    buy_conditions = [
        price_cross_up and rsi < 60,
        stoch_cross_up and stoch_k < 30,
        macd_cross_up and volume_ratio > 1.2,
    ]

    if any(buy_conditions):
        reasons = []
        if price_cross_up and rsi < 60:
            reasons.append(f"Gia cat len MA20 + RSI={rsi:.1f}")
        if stoch_cross_up and stoch_k < 30:
            reasons.append(f"Stoch %K={stoch_k:.1f} phuc hoi tu qua ban")
        if macd_cross_up and volume_ratio > 1.2:
            reasons.append(f"MACD cat len Signal + Vol={volume_ratio:.1f}x")
        if obv_trend:
            reasons.append("OBV tang (dong tien tich luy)")

        stoploss_atr = round(current_price - 1.5 * atr, 2)
        stoploss_pct = round(current_price * 0.95, 2)
        return {
            "signal"   : "MUA",
            "icon"     : "🟢",
            "reason"   : " | ".join(reasons),
            "price"    : current_price,
            "target"   : round(current_price * 1.07, 2),
            "stoploss" : max(stoploss_atr, stoploss_pct),
            "volume_ok": volume_ratio > 1.0,
            "rsi"      : round(rsi, 1),
        }
    
    # ── Tin hieu BAN (neu dang giu) ─────────────────────────────────────
    if entry_price:
        pnl_pct          = (current_price - entry_price) / entry_price * 100
        price_cross_down = prev['close'] >= ma20_prev and current_price < ma20
        stoch_cross_down = stoch_k_prev > stoch_d_prev and stoch_k < stoch_d
        
        if pnl_pct >= 7:
            return {"signal": "BAN", "icon": "🔴", "reason": f"Chot loi +{pnl_pct:.1f}%", "price": current_price, "pnl_pct": round(pnl_pct, 1)}
        if pnl_pct <= -5:
            return {"signal": "CAT LO", "icon": "🔴", "reason": f"Stoploss {pnl_pct:.1f}%", "price": current_price, "pnl_pct": round(pnl_pct, 1)}
        if price_cross_down and volume_ratio > 1.5:
            return {"signal": "BAN KHAN", "icon": "🔴", "reason": f"Gia cat xuong MA20 + Volume dot bien ({volume_ratio:.1f}x)", "price": current_price, "pnl_pct": round(pnl_pct, 1)}
        if stoch_cross_down and stoch_k > 80:
            return {"signal": "BAN", "icon": "🟡", "reason": f"Stoch %K={stoch_k:.1f} qua mua, dao chieu", "price": current_price, "pnl_pct": round(pnl_pct, 1)}
        if price_cross_down:
            return {"signal": "BAN", "icon": "🟡", "reason": "Gia cat xuong MA20", "price": current_price, "pnl_pct": round(pnl_pct, 1)}
    
    # ── Theo doi them ────────────────────────────────────────────────────
    rsi_note = "Qua mua ⚠️" if rsi > 70 else ("Qua ban 👀" if rsi < 30 else "Trung tinh")
    vol_note = f"Volume {volume_ratio:.1f}x {'(dot bien 🔥)' if volume_ratio > 1.5 else ''}"
    return {
        "signal"  : "THEO DOI",
        "icon"    : "⬜",
        "reason"  : f"RSI={rsi:.1f} ({rsi_note}), MA20={ma20:.2f}, {vol_note}",
        "price"   : current_price,
        "rsi"     : round(rsi, 1),
    }


# ============================================================================
# 4. PHAN TICH TAM LY THI TRUONG
# ============================================================================

def analyze_market_psychology(df: pd.DataFrame) -> list:
    """Phan tich tam ly thi truong dua tren cac chi bao."""
    last = df.iloc[-1]
    prev = df.iloc[-2]
    insights = []
    
    rsi = last['RSI_14']
    stoch_k = last['STOCHk_14_3_3']
    stoch_d = last['STOCHd_14_3_3']
    stoch_k_prev = prev['STOCHk_14_3_3']
    stoch_d_prev = prev['STOCHd_14_3_3']
    macd = last['MACD_12_26_9']
    macd_signal = last['MACDs_12_26_9']
    macd_prev = prev['MACD_12_26_9']
    macd_signal_prev = prev['MACDs_12_26_9']
    macd_hist = last['MACDh_12_26_9']
    macd_hist_prev = prev['MACDh_12_26_9']
    volume_ratio = last['Volume_ratio']
    price_change = last['price_change']
    obv_trend = last['OBV'] > prev['OBV']
    
    if rsi > 70:
        insights.append(("⚠️ RSI > 70: Qua mua", "Tham lam cuc do", "Can nhac chot loi"))
    elif rsi < 30:
        insights.append(("👀 RSI < 30: Qua ban", "So hai cuc do", "Quan sat de mua tich tru"))
    if stoch_k < 20 and stoch_k > stoch_d and stoch_k_prev < stoch_d_prev:
        insights.append(("📈 Stoch phuc hoi tu day", "Bat dau lac quan", "Tin hieu mua som"))
    if macd_prev < macd_signal_prev and macd > macd_signal:
        insights.append(("📊 MACD cat len Signal", "Niem tin tang dan", "Mo vi the mua"))
    if macd_hist_prev < 0 and macd_hist > 0:
        insights.append(("💪 MACD Histogram dao duong", "Luc mua ap dao", "Xac nhan xu huong tang"))
    if 'BBU_20_2.0' in last.index and last['close'] > last['BBU_20_2.0']:
        insights.append(("🔥 Gia vuot BB tren", "Hung phan qua da", "Cho dieu chinh ve BBM"))
    if 'BBB_20_2.0' in last.index:
        bbb = last['BBB_20_2.0']
        bbb_avg = df['BBB_20_2.0'].tail(20).mean()
        if bbb < bbb_avg * 0.5:
            insights.append(("🔋 BB Bandwidth thu hep", "Tich luy cho but pha", "Chuan bi von, cho breakout"))
    if price_change > 0 and volume_ratio > 1.5:
        insights.append(("📈 Gia tang + Volume tang manh", "Dong thuan manh", "Giu / mua them"))
    elif price_change > 0 and volume_ratio < 0.8:
        insights.append(("⚠️ Gia tang + Volume giam", "Hung phan gia tao", "Canh giac bull trap"))
    elif price_change < 0 and volume_ratio > 1.5:
        insights.append(("😱 Gia giam + Volume dot bien", "Ban thao hoang loan", "Theo doi tim day"))
    if obv_trend and abs(price_change) < 0.005:
        insights.append(("🦈 OBV tang, gia di ngang", "Ca map gom hang", "Quan sat, chuan bi theo"))
    elif not obv_trend and price_change > 0.01:
        insights.append(("⚠️ OBV giam, gia tang", "Phan phoi dinh", "Canh bao dao chieu sap den"))
    if 'EMA_9' in last.index and 'SMA_50' in last.index:
        ema9 = last['EMA_9']
        sma50 = last['SMA_50']
        ema9_prev = prev['EMA_9']
        sma50_prev = prev['SMA_50']
        if ema9_prev < sma50_prev and ema9 > sma50:
            insights.append(("🌟 Golden Cross (EMA9 > SMA50)", "Lac quan trung han", "Tang ty trong"))
        elif ema9_prev > sma50_prev and ema9 < sma50:
            insights.append(("💀 Death Cross (EMA9 < SMA50)", "Bi quan trung han", "Giam ty trong"))
    if 'ATRr_14' in last.index:
        atr = last['ATRr_14']
        atr_avg = df['ATRr_14'].tail(20).mean()
        if atr > atr_avg * 1.5:
            insights.append(("🌊 ATR tang dot bien", "Bien dong tang cao, bat on", "Thu hep position, noi stoploss"))
    
    return insights


# ============================================================================
# 5. PHAN TICH TONG HOP 1 MA CO PHIEU
# ============================================================================

def analyze_stock(symbol: str, start: str = None, end: str = None,
                  entry_price: float = None, source: str = "VCI") -> dict:
    """Phan tich toan dien 1 ma co phieu."""
    if start is None:
        start = (datetime.date.today() - datetime.timedelta(days=365)).strftime("%Y-%m-%d")
    if end is None:
        end = datetime.date.today().strftime("%Y-%m-%d")
    
    print(f"\n{'='*60}")
    print(f"  PHAN TICH CO PHIEU: {symbol}")
    print(f"  Giai doan: {start} -> {end}")
    print(f"{'='*60}")
    
    print(f"\n[1/4] Dang lay du lieu {symbol}...")
    df = get_stock_data(symbol, start=start, end=end, source=source)
    print(f"  -> {len(df)} phien giao dich")
    
    print(f"[2/4] Dang tinh chi bao ky thuat...")
    df = add_indicators(df)
    print(f"  -> {len(df.columns)} chi bao")
    
    print(f"[3/4] Dang kiem tra tin hieu...")
    signal = check_signal(df, entry_price=entry_price)
    
    print(f"[4/4] Dang phan tich tam ly thi truong...")
    psychology = analyze_market_psychology(df)
    
    last = df.iloc[-1]
    
    print(f"\n{'─'*60}")
    print(f"  KET QUA PHAN TICH: {symbol}")
    print(f"{'─'*60}")
    print(f"\n📊 GIA HIEN TAI: {last['close']:,.2f}")
    print(f"📈 RSI(14):      {last['RSI_14']:.1f}")
    print(f"📉 SMA(20):      {last['SMA_20']:,.0f}")
    print(f"📉 SMA(50):      {last['SMA_50']:,.0f}")
    if 'SMA_200' in last.index and not pd.isna(last['SMA_200']):
        print(f"📉 SMA(200):     {last['SMA_200']:,.0f}")
    print(f"📊 MACD:         {last['MACD_12_26_9']:.2f}")
    print(f"📊 Stoch %K:     {last['STOCHk_14_3_3']:.1f}")
    print(f"📊 Volume Ratio: {last['Volume_ratio']:.2f}x")
    if 'ATRr_14' in last.index:
        print(f"📊 ATR(14):      {last['ATRr_14']:.2f}")
    
    print(f"\n{'─'*60}")
    print(f"  TIN HIEU: {signal.get('icon', '')} {signal['signal']}")
    print(f"{'─'*60}")
    print(f"  Ly do: {signal['reason']}")
    if 'target' in signal:
        print(f"  🎯 Target:   {signal['target']:,.0f} (+7%)")
    if 'stoploss' in signal:
        print(f"  🛑 Stoploss: {signal['stoploss']:,.0f}")
    if 'pnl_pct' in signal:
        print(f"  💰 PnL:      {signal['pnl_pct']:+.1f}%")
    
    if psychology:
        print(f"\n{'─'*60}")
        print(f"  TAM LY THI TRUONG")
        print(f"{'─'*60}")
        for indicator, sentiment, action in psychology:
            print(f"  {indicator}")
            print(f"    Tam ly: {sentiment} | Hanh dong: {action}")
    
    print(f"\n{'─'*60}")
    print(f"  ⚠️ Chi la tin hieu tham khao, khong phai khuyen nghi dau tu.")
    print(f"  Luon backtest truoc khi dung tien that.")
    print(f"{'─'*60}\n")
    
    return {
        "symbol"     : symbol,
        "signal"     : signal,
        "psychology" : psychology,
        "data"       : df,
        "last_price" : last['close'],
        "rsi"        : round(last['RSI_14'], 1),
    }
