"""
VN Stock Zalo OA Bot - Bot canh bao tin hieu qua Zalo Official Account
======================================================================
Gui tin nhan canh bao mua/ban qua Zalo OA khi phat hien tin hieu.

HUONG DAN THIET LAP:
1. Tao Zalo Official Account tai: https://oa.zalo.me (mien phi)
2. Nguoi nhan phai follow OA cua ban tren Zalo
3. Lay Access Token tu trang quan ly OA (het han sau 90 ngay)
4. Dien thong tin vao phan CAU HINH ben duoi
"""

import sys
import io
import os
import datetime
import time
import json



try:
    import requests
except ImportError:
    print("[!] Chua cai requests. Chay: pip install requests")
    requests = None

try:
    import schedule
except ImportError:
    print("[!] Chua cai schedule. Chay: pip install schedule")
    schedule = None

# Them root vao sys.path de import core module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.stock_analyst import get_stock_data, add_indicators, check_signal


# ============================================================================
# CAU HINH
# ============================================================================

ZALO_OA_ACCESS_TOKEN = "YOUR_ZALO_OA_ACCESS_TOKEN"
ZALO_USER_IDS = []
WATCHLIST = ["FPT", "HPG", "VNM", "MBB", "TCB", "DXG", "VCB", "VHM"]
ENTRY_PRICES = {}
DATA_SOURCE = "VCI"
ALERT_SIGNALS = ["MUA", "BAN", "CAT LO", "BAN KHAN"]


def send_zalo_oa_message(user_id: str, message: str, access_token: str = None) -> bool:
    """Gui tin nhan text qua Zalo OA API."""
    if requests is None:
        print("[!] Thu vien requests chua duoc cai dat")
        return False
    if access_token is None:
        access_token = ZALO_OA_ACCESS_TOKEN
    if access_token == "YOUR_ZALO_OA_ACCESS_TOKEN":
        print("[!] Chua cau hinh ZALO_OA_ACCESS_TOKEN!")
        return False
    
    url = "https://openapi.zalo.me/v3.0/oa/message/cs"
    headers = {"Content-Type": "application/json", "access_token": access_token}
    payload = {"recipient": {"user_id": user_id}, "message": {"text": message}}
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        result = response.json()
        if result.get("error") == 0:
            print(f"  [OK] Da gui tin nhan Zalo cho user {user_id[:8]}...")
            return True
        else:
            print(f"  [!] Loi Zalo API: {result.get('message', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"  [X] Loi gui tin nhan: {e}")
        return False


def broadcast_zalo_message(message: str, user_ids: list = None, access_token: str = None):
    """Gui tin nhan cho nhieu nguoi qua Zalo OA."""
    if user_ids is None:
        user_ids = ZALO_USER_IDS
    if not user_ids:
        print("[!] Chua cau hinh ZALO_USER_IDS!")
        return
    for user_id in user_ids:
        send_zalo_oa_message(user_id, message, access_token)
        time.sleep(0.5)


def format_alert_message(symbol: str, signal: dict) -> str:
    """Format tin nhan canh bao theo mau chuan."""
    icon = signal.get('icon', '🔔')
    signal_type = signal['signal']
    price = signal.get('price', 0)
    reason = signal.get('reason', '')
    
    msg = f"🔔 {icon} {signal_type}: {symbol}\n"
    msg += f"💰 Gia: {price:,.0f} VND\n"
    if 'target' in signal:
        msg += f"🎯 Target: {signal['target']:,.0f} (+7%)\n"
    if 'stoploss' in signal:
        msg += f"🛑 Stoploss: {signal['stoploss']:,.0f}\n"
    if 'pnl_pct' in signal:
        msg += f"💹 PnL: {signal['pnl_pct']:+.1f}%\n"
    msg += f"📝 {reason}\n"
    msg += f"─────────────────\n"
    msg += f"⏰ {datetime.datetime.now().strftime('%H:%M %d/%m/%Y')}\n"
    msg += f"⚠️ Chi la tin hieu tham khao, khong phai khuyen nghi dau tu."
    return msg


def scan_and_alert():
    """Quet watchlist va gui canh bao qua Zalo OA."""
    now = datetime.datetime.now()
    print(f"\n[{now.strftime('%H:%M:%S')}] Bat dau quet {len(WATCHLIST)} ma...")
    
    alerts = []
    for symbol in WATCHLIST:
        try:
            start = (datetime.date.today() - datetime.timedelta(days=180)).strftime("%Y-%m-%d")
            df = get_stock_data(symbol, start=start, source=DATA_SOURCE)
            df = add_indicators(df)
            entry_price = ENTRY_PRICES.get(symbol, None)
            signal = check_signal(df, entry_price=entry_price)
            
            if signal['signal'] in ALERT_SIGNALS:
                alerts.append((symbol, signal))
                message = format_alert_message(symbol, signal)
                print(f"\n  📢 CANH BAO: {symbol} - {signal['icon']} {signal['signal']}")
                print(f"     {signal['reason']}")
                broadcast_zalo_message(message)
            else:
                print(f"  {symbol}: {signal['icon']} {signal['signal']} (bo qua)")
        except Exception as e:
            print(f"  [X] {symbol}: Loi - {e}")
    
    print(f"\n[{now.strftime('%H:%M:%S')}] Hoan tat quet. {len(alerts)} canh bao da gui.")
    return alerts


def is_trading_hours() -> bool:
    """Kiem tra co dang trong gio giao dich khong."""
    now = datetime.datetime.now()
    hour = now.hour
    minute = now.minute
    weekday = now.weekday()
    if weekday >= 5: return False
    if 9 <= hour < 11 or (hour == 11 and minute <= 30): return True
    if 13 <= hour < 15: return True
    return False


def run_bot():
    """Chay bot lien tuc, quet moi 10 phut trong gio giao dich."""
    if schedule is None:
        print("[!] Thu vien schedule chua duoc cai dat.")
        return
    
    print(f"{'='*60}")
    print(f"  ZALO OA ALERT BOT - DANG CHAY")
    print(f"{'='*60}")
    print(f"  Watchlist: {', '.join(WATCHLIST)}")
    print(f"  Nhan Ctrl+C de dung bot")
    print(f"{'='*60}\n")
    
    def job():
        if is_trading_hours():
            scan_and_alert()
        else:
            print(f"  [{datetime.datetime.now().strftime('%H:%M')}] Ngoai gio giao dich - bo qua")
    
    schedule.every(10).minutes.do(job)
    job()
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n\n  Bot da dung. 👋")


def test_scan():
    """Quet thu khong gui tin nhan Zalo (de test)."""
    print(f"\n{'='*60}")
    print(f"  CHE DO TEST - Khong gui tin nhan Zalo")
    print(f"{'='*60}")
    alerts = scan_and_alert()
    if alerts:
        print(f"\n{'─'*60}")
        print(f"  MAU TIN NHAN SE DUOC GUI:")
        print(f"{'─'*60}")
        for symbol, signal in alerts:
            msg = format_alert_message(symbol, signal)
            print(f"\n{msg}")
    else:
        print("\n  Khong co tin hieu canh bao nao.")
    return alerts


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Zalo OA Alert Bot")
    parser.add_argument("--test", action="store_true", help="Chay che do test")
    parser.add_argument("--run", action="store_true", help="Chay bot lien tuc")
    args = parser.parse_args()
    
    if args.run:
        run_bot()
    else:
        test_scan()
