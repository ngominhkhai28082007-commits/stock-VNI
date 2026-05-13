"""
VN Stock Analyst - Entry Point
===============================
File chinh de chay toan bo he thong phan tich chung khoan VN.

Cach dung:
    python main.py analyze FPT              # Phan tich 1 ma
    python main.py scan                     # Quet watchlist
    python main.py predict FPT              # Du doan AI
    python main.py backtest FPT             # Backtest
    python main.py bot --test               # Test bot Zalo
    python main.py bot --run                # Chay bot Zalo
"""

import sys
import io
import os
import argparse

# Fix encoding cho Windows console
if sys.stdout and hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Dam bao root dir nam trong sys.path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT_DIR)


def cmd_analyze(args):
    """Phan tich ky thuat 1 ma co phieu."""
    from core.stock_analyst import analyze_stock
    analyze_stock(
        symbol=args.symbol,
        start=args.start,
        entry_price=args.entry,
        source=args.source,
    )


def cmd_scan(args):
    """Quet nhieu ma co phieu."""
    from analysis.scanner import scan_watchlist, VN30_WATCHLIST, BANK_WATCHLIST, BDS_WATCHLIST, TECH_WATCHLIST
    
    watchlist_map = {
        "vn30": VN30_WATCHLIST,
        "bank": BANK_WATCHLIST,
        "bds":  BDS_WATCHLIST,
        "tech": TECH_WATCHLIST,
    }
    
    if args.group and args.group in watchlist_map:
        watchlist = watchlist_map[args.group]
    elif args.symbols:
        watchlist = [s.strip().upper() for s in args.symbols.split(",")]
    else:
        watchlist = ["FPT", "HPG", "VNM", "MBB", "TCB", "DXG", "VCB", "VHM"]
    
    scan_watchlist(watchlist=watchlist, start=args.start, source=args.source)


def cmd_predict(args):
    """Du doan AI cho 1 ma co phieu."""
    from analysis.ml_model import predict_stock
    predict_stock(
        symbol=args.symbol,
        start=args.start,
        model_type=args.model,
        forward=args.forward,
        source=args.source,
    )


def cmd_backtest(args):
    """Backtest chien luoc cho 1 ma co phieu."""
    from analysis.backtest import run_backtest
    run_backtest(
        symbol=args.symbol,
        start=args.start,
        initial_capital=args.capital,
        take_profit=args.tp / 100,
        stop_loss=-args.sl / 100,
        source=args.source,
    )


def cmd_bot(args):
    """Chay bot canh bao Zalo OA."""
    from bot.zalo_bot import test_scan, run_bot
    if args.run:
        run_bot()
    else:
        test_scan()


def main():
    parser = argparse.ArgumentParser(
        description="VN Stock Analyst - He thong phan tich chung khoan Viet Nam",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Vi du:
  python main.py analyze FPT                    # Phan tich FPT
  python main.py analyze DXG --entry 15000      # Phan tich DXG (dang giu gia 15k)
  python main.py scan --group vn30              # Quet VN30
  python main.py scan --symbols FPT,HPG,VNM     # Quet danh sach tu chon
  python main.py predict FPT --model xgboost    # Du doan AI bang XGBoost
  python main.py backtest FPT --tp 10 --sl 7    # Backtest voi TP 10%, SL 7%
  python main.py bot --test                     # Test bot Zalo
        """,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Lenh thuc hien")
    
    # --- analyze ---
    p_analyze = subparsers.add_parser("analyze", help="Phan tich ky thuat 1 ma")
    p_analyze.add_argument("symbol", help="Ma co phieu (VD: FPT)")
    p_analyze.add_argument("--start", default="2025-01-01", help="Ngay bat dau (YYYY-MM-DD)")
    p_analyze.add_argument("--entry", type=float, default=None, help="Gia mua vao (neu dang giu)")
    p_analyze.add_argument("--source", default="VCI", help="Nguon du lieu: VCI, TCBS, KBS")
    p_analyze.set_defaults(func=cmd_analyze)
    
    # --- scan ---
    p_scan = subparsers.add_parser("scan", help="Quet nhieu ma co phieu")
    p_scan.add_argument("--group", choices=["vn30", "bank", "bds", "tech"], help="Nhom co phieu")
    p_scan.add_argument("--symbols", help="Danh sach ma, cach nhau dau phay (VD: FPT,HPG,VNM)")
    p_scan.add_argument("--start", default="2025-01-01", help="Ngay bat dau")
    p_scan.add_argument("--source", default="VCI", help="Nguon du lieu")
    p_scan.set_defaults(func=cmd_scan)
    
    # --- predict ---
    p_predict = subparsers.add_parser("predict", help="Du doan AI")
    p_predict.add_argument("symbol", help="Ma co phieu")
    p_predict.add_argument("--start", default="2024-01-01", help="Ngay bat dau du lieu training")
    p_predict.add_argument("--model", default="random_forest", choices=["random_forest", "xgboost"], help="Loai model")
    p_predict.add_argument("--forward", type=int, default=3, help="Du doan T+N phien (mac dinh 3)")
    p_predict.add_argument("--source", default="VCI", help="Nguon du lieu")
    p_predict.set_defaults(func=cmd_predict)
    
    # --- backtest ---
    p_backtest = subparsers.add_parser("backtest", help="Backtest chien luoc")
    p_backtest.add_argument("symbol", help="Ma co phieu")
    p_backtest.add_argument("--start", default="2024-01-01", help="Ngay bat dau")
    p_backtest.add_argument("--capital", type=float, default=100_000_000, help="Von ban dau (VND)")
    p_backtest.add_argument("--tp", type=float, default=7, help="Take profit %% (mac dinh 7)")
    p_backtest.add_argument("--sl", type=float, default=5, help="Stop loss %% (mac dinh 5)")
    p_backtest.add_argument("--source", default="VCI", help="Nguon du lieu")
    p_backtest.set_defaults(func=cmd_backtest)
    
    # --- bot ---
    p_bot = subparsers.add_parser("bot", help="Bot canh bao Zalo OA")
    p_bot.add_argument("--test", action="store_true", help="Chay che do test (khong gui Zalo)")
    p_bot.add_argument("--run", action="store_true", help="Chay bot lien tuc")
    p_bot.set_defaults(func=cmd_bot)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        print("\n💡 Thu chay: python main.py analyze FPT")
        return
    
    try:
        args.func(args)
    except Exception as e:
        print(f"\n[X] Loi: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
