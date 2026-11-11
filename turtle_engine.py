import math
import pandas as pd
import numpy as np

def run_backtest(df: pd.DataFrame, entry_n: int = 20, exit_n: int = 10,
                 atr_n: int = 14, stop_atr_mult: float = 2.0,
                 use_trailing: bool = False,
                 commission: float = 0.00015, slippage: float = 0.00050,
                 initial_capital: float = 100_000_000.0) -> dict:
    data = df.copy()
    prev_close = data["Close"].shift(1)
    tr = pd.concat([
        data["High"] - data["Low"],
        (data["High"] - prev_close).abs(),
        (data["Low"] - prev_close).abs()
    ], axis=1).max(axis=1)
    
    data["ATR"] = tr.rolling(atr_n, min_periods=atr_n).mean()
    data["entry_high"] = data["High"].rolling(entry_n, min_periods=entry_n).max().shift(1)
    data["exit_low"] = data["Low"].rolling(exit_n, min_periods=exit_n).min().shift(1)

    cash = initial_capital
    qty = 0
    stop_price = 0.0
    highest_px = 0.0
    entry_cost = 0.0
    entry_date = None
    entry_idx = -1
    entry_px = 0.0
    entry_atr = 0.0

    trades = []
    equity_values = []
    dates = data.index

    for i in range(len(data)):
        row = data.iloc[i]
        date = dates[i]
        o, h, l, c = row["Open"], row["High"], row["Low"], row["Close"]
        atr_val = row["ATR"] if pd.notna(row["ATR"]) else 0.0
        sig_entry = (c > row["entry_high"]) and (atr_val > 0)
        sig_exit = (c < row["exit_low"]) and (not use_trailing)
        exited_today = False

        if qty > 0:
            reason = None
            fill = None
            if l <= stop_price:
                reason = "TRAILING_STOP" if use_trailing and stop_price > (entry_px - stop_atr_mult * entry_atr) else "STOP_LOSS"
                fill = stop_price if o >= stop_price else o
            elif sig_exit:
                reason = "TREND_EXIT"
                fill = c

            if reason is not None:
                sell_px = fill * (1 - slippage)
                proceeds = qty * sell_px * (1 - commission)
                cash += proceeds
                pnl = proceeds - entry_cost
                trades.append({
                    "진입일": entry_date.strftime("%Y-%m-%d"),
                    "청산일": date.strftime("%Y-%m-%d"),
                    "진입가": int(round(entry_px)),
                    "청산가": int(round(sell_px)),
                    "수량": qty,
                    "실현손익(원)": int(round(pnl)),
                    "수익률(%)": round((pnl / entry_cost) * 100, 2),
                    "보유일수": i - entry_idx,
                    "청산사유": "손절 (2ATR)" if reason == "STOP_LOSS" else ("트레일링 익절" if reason == "TRAILING_STOP" else "추세청산 (신저가)")
                })
                qty = 0
                exited_today = True
            else:
                if use_trailing:
                    highest_px = max(highest_px, h)
                    new_stop = highest_px - stop_atr_mult * atr_val
                    stop_price = max(stop_price, new_stop)

        if qty == 0 and not exited_today and sig_entry:
            px = c * (1 + slippage)
            q = int(math.floor(cash / (px * (1 + commission))))
            if q > 0:
                cost = q * px * (1 + commission)
                cash -= cost
                qty = q
                entry_px = px
                entry_atr = atr_val
                stop_price = px - stop_atr_mult * entry_atr
                highest_px = max(px, h)
                entry_date = date
                entry_cost = cost
                entry_idx = i

        equity_values.append(cash + qty * c)

    eq = pd.Series(equity_values, index=dates)
    total_ret = (eq.iloc[-1] / initial_capital - 1) * 100
    years = max(0.1, (dates[-1] - dates[0]).days / 365.25)
    cagr = ((eq.iloc[-1] / initial_capital) ** (1 / years) - 1) * 100
    cummax = eq.cummax()
    dd = (eq - cummax) / cummax * 100
    mdd = float(dd.min())

    bnh = (data["Close"] / data["Close"].iloc[0]) * initial_capital
    bnh_ret = (bnh.iloc[-1] / initial_capital - 1) * 100
    bnh_cagr = ((bnh.iloc[-1] / initial_capital) ** (1 / years) - 1) * 100
    bnh_cummax = bnh.cummax()
    bnh_dd = (bnh - bnh_cummax) / bnh_cummax * 100
    bnh_mdd = float(bnh_dd.min())

    tdf = pd.DataFrame(trades)
    win_rate = (tdf["실현손익(원)"] > 0).mean() * 100 if len(tdf) > 0 else 0
    w_sum = tdf[tdf["실현손익(원)"] > 0]["실현손익(원)"].sum() if len(tdf) > 0 else 0
    l_sum = abs(tdf[tdf["실현손익(원)"] < 0]["실현손익(원)"].sum()) if len(tdf) > 0 else 1
    pf = (w_sum / l_sum) if l_sum > 0 else 999.0
    
    # Sharpe (무위험 수익률 2% 가정)
    daily_returns = eq.pct_change().dropna()
    rf_daily = 0.02 / 252
    excess_ret = daily_returns - rf_daily
    sharpe = float((excess_ret.mean() / excess_ret.std()) * np.sqrt(252)) if excess_ret.std() > 0 else 0.0

    return {
        "equity": eq, "benchmark": bnh, "drawdown": dd, "benchmark_dd": bnh_dd,
        "trades": tdf, "final_capital": eq.iloc[-1], "total_return": total_ret,
        "cagr": cagr, "mdd": mdd, "sharpe": sharpe,
        "bnh_final": bnh.iloc[-1], "bnh_return": bnh_ret, "bnh_cagr": bnh_cagr, "bnh_mdd": bnh_mdd,
        "trades_count": len(tdf), "win_rate": win_rate, "profit_factor": pf, "years": years
    }
