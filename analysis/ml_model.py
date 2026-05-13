"""
VN Stock ML Model - Du doan xu huong gia bang Machine Learning
==============================================================
Model: Random Forest + XGBoost
Input : 10 phien gan nhat cua [RSI, MACD, BB%, MA ratio, Volume change]
Output: Xac suat tang gia trong 3-5 phien toi (T+3)
Nguong: Xac suat > 0.65 → xem xet mua
"""

import sys
import io
import os
import datetime
import warnings
warnings.filterwarnings('ignore')



import pandas as pd
import numpy as np

try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import TimeSeriesSplit
    from sklearn.metrics import accuracy_score, classification_report
    from sklearn.preprocessing import StandardScaler
except ImportError:
    print("[!] Chua cai scikit-learn. Chay: pip install scikit-learn")

try:
    import xgboost as xgb
except ImportError:
    print("[!] Chua cai xgboost. Chay: pip install xgboost")
    xgb = None

# Them root vao sys.path de import core module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.stock_analyst import get_stock_data, add_indicators


def prepare_ml_features(df: pd.DataFrame, lookback: int = 10, forward: int = 3) -> tuple:
    """Tao feature matrix va label cho ML model."""
    indicator_cols = []
    for col in ['RSI_14', 'MACD_12_26_9', 'MACDh_12_26_9', 'MACDs_12_26_9',
                'STOCHk_14_3_3', 'STOCHd_14_3_3',
                'BBP_20_2.0', 'BBB_20_2.0',
                'Volume_ratio', 'price_change']:
        if col in df.columns:
            indicator_cols.append(col)
    
    if 'SMA_20' in df.columns:
        df['price_ma20_ratio'] = df['close'] / df['SMA_20']
        indicator_cols.append('price_ma20_ratio')
    if 'SMA_50' in df.columns:
        df['price_ma50_ratio'] = df['close'] / df['SMA_50']
        indicator_cols.append('price_ma50_ratio')
    if 'EMA_9' in df.columns:
        df['price_ema9_ratio'] = df['close'] / df['EMA_9']
        indicator_cols.append('price_ema9_ratio')
    
    df['volume_change'] = df['volume'].pct_change()
    indicator_cols.append('volume_change')
    
    if 'ATRr_14' in df.columns:
        df['atr_ratio'] = df['ATRr_14'] / df['close']
        indicator_cols.append('atr_ratio')
    
    df = df.dropna()
    
    df['future_return'] = df['close'].shift(-forward) / df['close'] - 1
    df['label'] = (df['future_return'] > 0).astype(int)
    df = df.dropna()
    
    feature_names = []
    X_list = []
    
    for i in range(lookback, len(df)):
        row_features = []
        for col in indicator_cols:
            values = df[col].iloc[i-lookback:i].values
            row_features.extend(values)
            if len(feature_names) < len(indicator_cols) * lookback:
                for j in range(lookback):
                    feature_names.append(f"{col}_t-{lookback-j}")
        X_list.append(row_features)
    
    X = np.array(X_list)
    y = df['label'].iloc[lookback:].values
    
    mask = np.isfinite(X).all(axis=1)
    X = X[mask]
    y = y[mask]
    
    return X, y, feature_names


def train_model(X, y, model_type: str = "random_forest", n_splits: int = 5) -> dict:
    """Huan luyen va danh gia model."""
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    if model_type == "xgboost" and xgb is not None:
        model = xgb.XGBClassifier(
            n_estimators=100, max_depth=5, learning_rate=0.1,
            use_label_encoder=False, eval_metric='logloss', random_state=42,
        )
        model_name = "XGBoost"
    else:
        model = RandomForestClassifier(
            n_estimators=100, max_depth=10, min_samples_split=10,
            min_samples_leaf=5, random_state=42, n_jobs=-1,
        )
        model_name = "Random Forest"
    
    print(f"\n  Model: {model_name}")
    print(f"  Features: {X.shape[1]} | Samples: {X.shape[0]}")
    print(f"  Label distribution: Tang={y.sum()} ({y.mean()*100:.1f}%) | Giam={len(y)-y.sum()} ({(1-y.mean())*100:.1f}%)")
    
    tscv = TimeSeriesSplit(n_splits=n_splits)
    cv_scores = []
    
    for fold, (train_idx, test_idx) in enumerate(tscv.split(X_scaled), 1):
        X_train, X_test = X_scaled[train_idx], X_scaled[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        model.fit(X_train, y_train)
        score = accuracy_score(y_test, model.predict(X_test))
        cv_scores.append(score)
        print(f"    Fold {fold}: Accuracy = {score:.3f}")
    
    avg_score = np.mean(cv_scores)
    print(f"  Average CV Accuracy: {avg_score:.3f}")
    
    model.fit(X_scaled, y)
    
    return {
        "model": model, "scaler": scaler, "accuracy": avg_score,
        "model_name": model_name, "cv_scores": cv_scores,
    }


def predict_stock(symbol: str, start: str = None, end: str = None,
                  lookback: int = 10, forward: int = 3,
                  model_type: str = "random_forest",
                  source: str = "VCI") -> dict:
    """Huan luyen model va du doan xu huong cho 1 ma co phieu."""
    if start is None:
        start = (datetime.date.today() - datetime.timedelta(days=730)).strftime("%Y-%m-%d")
    if end is None:
        end = datetime.date.today().strftime("%Y-%m-%d")
    
    print(f"\n{'='*60}")
    print(f"  AI DU DOAN: {symbol} (T+{forward})")
    print(f"  Model: {model_type.upper()}")
    print(f"  Du lieu: {start} -> {end}")
    print(f"{'='*60}")
    
    print(f"\n[1/3] Lay du lieu & tinh chi bao...")
    df = get_stock_data(symbol, start=start, end=end, source=source)
    df = add_indicators(df)
    print(f"  -> {len(df)} phien du lieu")
    
    print(f"\n[2/3] Huan luyen model...")
    X, y, feature_names = prepare_ml_features(df, lookback=lookback, forward=forward)
    
    if len(X) < 50:
        print(f"  [!] Khong du du lieu ({len(X)} mau). Can it nhat 50 mau.")
        return {"symbol": symbol, "error": "Khong du du lieu"}
    
    result = train_model(X, y, model_type=model_type)
    
    print(f"\n[3/3] Du doan...")
    last_features = X[-1:].copy()
    last_features_scaled = result['scaler'].transform(last_features)
    
    prob = result['model'].predict_proba(last_features_scaled)[0]
    prediction = result['model'].predict(last_features_scaled)[0]
    
    prob_up = prob[1] if len(prob) > 1 else prob[0]
    prob_down = prob[0] if len(prob) > 1 else 1 - prob[0]
    
    top_features = []
    if hasattr(result['model'], 'feature_importances_'):
        importances = result['model'].feature_importances_
        top_features_idx = np.argsort(importances)[-5:][::-1]
        top_features = [(feature_names[i], importances[i]) for i in top_features_idx if i < len(feature_names)]
    
    last = df.iloc[-1]
    
    print(f"\n{'─'*60}")
    print(f"  KET QUA DU DOAN AI: {symbol}")
    print(f"{'─'*60}")
    print(f"\n  📊 Gia hien tai:     {last['close']:,.0f}")
    print(f"  🤖 Model:            {result['model_name']}")
    print(f"  📏 Do chinh xac CV:  {result['accuracy']*100:.1f}%")
    print(f"\n  📈 Xac suat TANG:    {prob_up*100:.1f}%")
    print(f"  📉 Xac suat GIAM:    {prob_down*100:.1f}%")
    print(f"  🕐 Tam nhin:         T+{forward} phien")
    
    if prob_up > 0.65:
        print(f"\n  ✅ GOI Y: XEM XET MUA (xac suat > 65%)")
    elif prob_up < 0.35:
        print(f"\n  ⚠️ GOI Y: CANH GIAC GIAM GIA (xac suat tang < 35%)")
    else:
        print(f"\n  ⬜ GOI Y: TRUNG TINH, THEO DOI THEM")
    
    if top_features:
        print(f"\n  📋 Top 5 features quan trong nhat:")
        for fname, fimp in top_features:
            bar = "█" * int(fimp * 50)
            print(f"    {fname:30s} {fimp:.3f} {bar}")
    
    print(f"\n  ⚠️ AI chi la cong cu ho tro. Luon backtest truoc khi dung tien that,")
    print(f"     paper trade >= 1 thang, va theo doi tin tuc vi mo.")
    print(f"{'─'*60}\n")
    
    return {
        "symbol": symbol, "probability": round(prob_up, 4),
        "prediction": "TANG" if prediction == 1 else "GIAM",
        "accuracy": round(result['accuracy'], 4),
        "model_name": result['model_name'],
        "top_features": top_features, "price": last['close'],
    }


def predict_watchlist(watchlist: list, **kwargs) -> list:
    """Du doan cho nhieu ma co phieu."""
    results = []
    for symbol in watchlist:
        try:
            result = predict_stock(symbol, **kwargs)
            results.append(result)
        except Exception as e:
            print(f"[X] {symbol}: {e}")
            results.append({"symbol": symbol, "error": str(e)})
    
    print(f"\n{'='*60}")
    print(f"  TONG HOP DU DOAN AI")
    print(f"{'='*60}")
    
    valid = [r for r in results if 'probability' in r]
    valid.sort(key=lambda x: x['probability'], reverse=True)
    
    print(f"\n  {'Ma':5s} | {'Xac suat Tang':>13s} | {'Gia':>12s} | {'Goi Y':15s}")
    print(f"  {'─'*55}")
    for r in valid:
        icon = "✅" if r['probability'] > 0.65 else ("⚠️" if r['probability'] < 0.35 else "⬜")
        suggestion = "XEM XET MUA" if r['probability'] > 0.65 else ("CANH GIAC" if r['probability'] < 0.35 else "THEO DOI")
        print(f"  {r['symbol']:5s} | {r['probability']*100:>10.1f}%   | {r['price']:>10,.0f}  | {icon} {suggestion}")
    
    print(f"\n  ⚠️ AI chi la cong cu ho tro, khong phai khuyen nghi dau tu.")
    print(f"{'='*60}\n")
    
    return results
