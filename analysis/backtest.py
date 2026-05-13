"""
VN Stock Backtest - Kiem tra hieu suat chien luoc giao dich
============================================================
Backtest chien luoc MUA/BAN dua tren chi bao ky thuat.
Bao gom: PnL, Win Rate, Max Drawdown, Sharpe Ratio.
"""

import sys
import io
import os
import datetime



import pandas as pd
import numpy as np

# Them root vao sys.path de import core module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.stock_analyst import get_stock_data, add_indicators


def backtest_strategy(df: pd.DataFrame, initial_capital: float = 100_000_000,
                      take_profit: float = 0.07, stop_loss: float = -0.05,
                      position_pct: float = 0.20, commission: float = 0.0015) -> dict:
    """Backtest chien luoc giao dich tren du lieu lich su."""
    capital = initial_capital
    position = None
    trades = []
    equity_curve = []
    
    for i in range(2, len(df)):
        row = df.iloc[i]
        prev = df.iloc[i-1]
        date = df.index[i]
        price = row['close']
        
        if position:
            unrealized_pnl = (price - position['entry_price']) * position['shares']
            current_equity = capital + position['entry_price'] * position['shares'] + unrealized_pnl
        else:
            current_equity = capital
        
        equity_curve.append({'date': date, 'equity': current_equity, 'price': price})
        
        # === LOGIC MUA ===
        if position is None:
            price_cross_up = prev['close'] <= prev['SMA_20'] and price > row['SMA_20']
            rsi_ok = row['RSI_14'] < 60
            macd_cross_up = (prev['MACD_12_26_9'] < prev['MACDs_12_26_9'] and 
                           row['MACD_12_26_9'] > row['MACDs_12_26_9'])
            stoch_cross_up = (prev['STOCHk_14_3_3'] < prev['STOCHd_14_3_3'] and 
                            row['STOCHk_14_3_3'] > row['STOCHd_14_3_3'] and 
                            row['STOCHk_14_3_3'] < 30)
            
            buy_signal = (price_cross_up and rsi_ok) or stoch_cross_up or (macd_cross_up and row['Volume_ratio'] > 1.2)
            
            if buy_signal:
                invest_amount = capital * position_pct
                shares = int(invest_amount / price / 100) * 100
                if shares > 0:
                    cost = shares * price * (1 + commission)
                    capital -= cost
                    position = {
                        'entry_date': date, 'entry_price': price,
                        'shares': shares, 'cost': cost, 'reason': 'MUA',
                    }
        
        # === LOGIC BAN ===
        elif position is not None:
            pnl_pct = (price - position['entry_price']) / position['entry_price']
            price_cross_down = prev['close'] >= prev['SMA_20'] and price < row['SMA_20']
            
            sell_signal = False
            sell_reason = ""
            
            if pnl_pct >= take_profit:
                sell_signal = True
                sell_reason = f"Chot loi +{pnl_pct*100:.1f}%"
            elif pnl_pct <= stop_loss:
                sell_signal = True
                sell_reason = f"Cat lo {pnl_pct*100:.1f}%"
            elif price_cross_down:
                sell_signal = True
                sell_reason = f"Gia cat xuong MA20 (PnL: {pnl_pct*100:.1f}%)"
            
            if sell_signal:
                revenue = position['shares'] * price * (1 - commission)
                capital += revenue
                pnl = revenue - position['cost']
                trade = {
                    'entry_date': position['entry_date'], 'exit_date': date,
                    'entry_price': position['entry_price'], 'exit_price': price,
                    'shares': position['shares'], 'pnl': round(pnl),
                    'pnl_pct': round(pnl_pct * 100, 2), 'reason': sell_reason,
                    'holding_days': (date - position['entry_date']).days,
                }
                trades.append(trade)
                position = None
    
    df_trades = pd.DataFrame(trades) if trades else pd.DataFrame()
    df_equity = pd.DataFrame(equity_curve)
    
    if len(trades) > 0:
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t['pnl'] > 0])
        losing_trades = len([t for t in trades if t['pnl'] < 0])
        win_rate = winning_trades / total_trades * 100
        total_pnl = sum(t['pnl'] for t in trades)
        avg_pnl = total_pnl / total_trades
        avg_pnl_pct = sum(t['pnl_pct'] for t in trades) / total_trades
        max_win = max(t['pnl'] for t in trades)
        max_loss = min(t['pnl'] for t in trades)
        avg_holding = sum(t['holding_days'] for t in trades) / total_trades
        
        equity_values = df_equity['equity'].values
        peak = equity_values[0]
        max_drawdown = 0
        for eq in equity_values:
            if eq > peak: peak = eq
            drawdown = (peak - eq) / peak
            if drawdown > max_drawdown: max_drawdown = drawdown
        
        if len(df_equity) > 1:
            returns = df_equity['equity'].pct_change().dropna()
            sharpe = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() > 0 else 0
        else:
            sharpe = 0
        
        final_capital = equity_values[-1]
        total_return = (final_capital - initial_capital) / initial_capital * 100
    else:
        total_trades = winning_trades = losing_trades = 0
        win_rate = total_pnl = avg_pnl = avg_pnl_pct = 0
        max_win = max_loss = avg_holding = max_drawdown = sharpe = total_return = 0
        final_capital = initial_capital
    
    summary = {
        'initial_capital': initial_capital, 'final_capital': round(final_capital),
        'total_return_pct': round(total_return, 2), 'total_pnl': round(total_pnl),
        'total_trades': total_trades, 'winning_trades': winning_trades,
        'losing_trades': losing_trades, 'win_rate': round(win_rate, 1),
        'avg_pnl': round(avg_pnl), 'avg_pnl_pct': round(avg_pnl_pct, 2),
        'max_win': round(max_win), 'max_loss': round(max_loss),
        'avg_holding_days': round(avg_holding, 1),
        'max_drawdown_pct': round(max_drawdown * 100, 2),
        'sharpe_ratio': round(sharpe, 2),
        'take_profit': take_profit, 'stop_loss': stop_loss,
        'commission': commission,
    }
    
    return {'trades': df_trades, 'summary': summary, 'equity_curve': df_equity}


def print_backtest_report(symbol: str, result: dict):
    """In bao cao backtest dep."""
    s = result['summary']
    trades = result['trades']
    
    print(f"\n{'='*65}")
    print(f"  BAO CAO BACKTEST: {symbol}")
    print(f"{'='*65}")
    print(f"\n  📊 TONG QUAN")
    print(f"  {'─'*55}")
    print(f"  Von ban dau:       {s['initial_capital']:>15,.0f} VND")
    print(f"  Von cuoi ky:       {s['final_capital']:>15,.0f} VND")
    print(f"  Tong loi nhuan:    {s['total_pnl']:>15,.0f} VND ({s['total_return_pct']:+.2f}%)")
    print(f"\n  📈 CHI SO HIEU SUAT")
    print(f"  {'─'*55}")
    print(f"  Tong so lenh:      {s['total_trades']:>5d}")
    print(f"  Lenh thang:        {s['winning_trades']:>5d}")
    print(f"  Lenh thua:         {s['losing_trades']:>5d}")
    print(f"  Win Rate:          {s['win_rate']:>5.1f}%")
    print(f"  PnL trung binh:    {s['avg_pnl']:>15,.0f} VND ({s['avg_pnl_pct']:+.2f}%)")
    print(f"  Lenh thang lon nhat: {s['max_win']:>13,.0f} VND")
    print(f"  Lenh thua lon nhat:  {s['max_loss']:>13,.0f} VND")
    print(f"  Thoi gian giu TB:  {s['avg_holding_days']:>5.1f} ngay")
    print(f"\n  📉 RUI RO")
    print(f"  {'─'*55}")
    print(f"  Max Drawdown:      {s['max_drawdown_pct']:>5.2f}%")
    print(f"  Sharpe Ratio:      {s['sharpe_ratio']:>5.2f}")
    
    if len(trades) > 0:
        print(f"\n  📋 CHI TIET GIAO DICH (5 lenh gan nhat)")
        print(f"  {'─'*55}")
        recent = trades.tail(5)
        for _, t in recent.iterrows():
            entry_date = t['entry_date'].strftime('%Y-%m-%d') if hasattr(t['entry_date'], 'strftime') else str(t['entry_date'])[:10]
            exit_date = t['exit_date'].strftime('%Y-%m-%d') if hasattr(t['exit_date'], 'strftime') else str(t['exit_date'])[:10]
            pnl_icon = "✅" if t['pnl'] > 0 else "❌"
            print(f"  {entry_date:12s} {exit_date:12s} {t['entry_price']:>10,.0f} {t['exit_price']:>10,.0f} {t['pnl_pct']:>+6.1f}% {pnl_icon} {t['reason'][:20]}")
    
    print(f"\n  ⚠️ Ket qua qua khu khong dam bao loi nhuan tuong lai.")
    print(f"{'='*65}\n")


def run_backtest(symbol: str, start: str = "2023-01-01", end: str = None,
                 initial_capital: float = 100_000_000,
                 take_profit: float = 0.07, stop_loss: float = -0.05,
                 source: str = "VCI") -> dict:
    """Chay backtest day du cho 1 ma co phieu."""
    if end is None:
        end = datetime.date.today().strftime("%Y-%m-%d")
    
    print(f"\n[1/3] Lay du lieu {symbol}...")
    df = get_stock_data(symbol, start=start, end=end, source=source)
    print(f"  -> {len(df)} phien")
    
    print(f"[2/3] Tinh chi bao ky thuat...")
    df = add_indicators(df)
    print(f"  -> {len(df)} phien (sau loc NaN)")
    
    print(f"[3/3] Chay backtest...")
    result = backtest_strategy(df, initial_capital=initial_capital, take_profit=take_profit, stop_loss=stop_loss)
    print_backtest_report(symbol, result)
    return result


def compare_backtest(symbols: list, **kwargs) -> pd.DataFrame:
    """So sanh backtest nhieu ma co phieu."""
    results = {}
    for symbol in symbols:
        try:
            result = run_backtest(symbol, **kwargs)
            results[symbol] = result['summary']
        except Exception as e:
            print(f"[X] {symbol}: {e}")
    
    if results:
        df_compare = pd.DataFrame(results).T
        df_compare.index.name = 'Symbol'
        print(f"\n{'='*70}")
        print(f"  SO SANH BACKTEST")
        print(f"{'='*70}")
        cols = ['total_return_pct', 'win_rate', 'total_trades', 'max_drawdown_pct', 'sharpe_ratio']
        available_cols = [c for c in cols if c in df_compare.columns]
        print(df_compare[available_cols].to_string())
        print(f"{'='*70}\n")
        return df_compare
    
    return pd.DataFrame()
