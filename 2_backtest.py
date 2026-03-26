"""
Step 2: RSI(14) mean-reversion backtest on SPY.
Strategy: buy when RSI < 30, sell when RSI > 70.
Fully in or fully out, 0.1% fee on each side.
Run step 1 first to generate spy_data.csv.
"""

import sys
import os
import pandas as pd
import numpy as np

CSV_FILE = "spy_data.csv"
STARTING_CAPITAL = 10_000.0
FEE_RATE = 0.001  # 0.1% per trade


def load_data() -> pd.DataFrame:
    if not os.path.exists(CSV_FILE):
        print(f"ERROR: '{CSV_FILE}' not found. Please run 1_explore_data.py first.")
        sys.exit(1)

    df = pd.read_csv(CSV_FILE, parse_dates=["Date"], index_col="Date")

    if "RSI" not in df.columns or "Close" not in df.columns:
        print("ERROR: CSV is missing required columns (Close, RSI). Re-run 1_explore_data.py.")
        sys.exit(1)

    # Drop rows where RSI is NaN (warm-up period)
    df = df.dropna(subset=["RSI"]).copy()
    return df


def run_backtest(df: pd.DataFrame):
    in_position = False
    cash = STARTING_CAPITAL
    shares = 0.0

    entry_date = None
    entry_price = None
    entry_rsi = None

    trades = []       # completed round trips
    equity_curve = [] # (date, portfolio_value)

    for date, row in df.iterrows():
        price = row["Close"]
        rsi = row["RSI"]

        # --- Entry ---
        if not in_position and rsi < 30:
            fee = cash * FEE_RATE
            cash_after_fee = cash - fee
            shares = cash_after_fee / price
            in_position = True
            entry_date = date
            entry_price = price
            entry_rsi = rsi
            cash = 0.0
            print(f"  BUY   {date.date()}  price=${price:.2f}  RSI={rsi:.1f}")

        # --- Exit ---
        elif in_position and rsi > 70:
            gross = shares * price
            fee = gross * FEE_RATE
            cash = gross - fee
            pnl_pct = (cash - STARTING_CAPITAL) / STARTING_CAPITAL * 100
            # PnL relative to what we put in (starting capital)
            trade_pnl_pct = (price / entry_price - 1) * 100 - 0.2  # approx round-trip fee impact
            trades.append({
                "entry_date": entry_date,
                "exit_date": date,
                "entry_price": entry_price,
                "exit_price": price,
                "entry_rsi": entry_rsi,
                "exit_rsi": rsi,
                "pnl_pct": trade_pnl_pct,
                "won": price > entry_price,
            })
            print(f"  SELL  {date.date()}  price=${price:.2f}  RSI={rsi:.1f}  P&L={trade_pnl_pct:+.2f}%")
            shares = 0.0
            in_position = False
            entry_date = entry_price = entry_rsi = None

        # Portfolio value today
        portfolio_value = cash + shares * price
        equity_curve.append({"date": date, "equity": portfolio_value})

    # If still holding at end, mark as open (don't close it, just record current value)
    if in_position:
        last_price = df["Close"].iloc[-1]
        gross = shares * last_price
        fee = gross * FEE_RATE
        open_value = gross - fee
        print(f"\n  (Open position still held — valued at ${open_value:.2f} if closed today)")

    return trades, pd.DataFrame(equity_curve).set_index("date")


def compute_max_drawdown(equity: pd.Series) -> float:
    peak = equity.cummax()
    drawdown = (equity - peak) / peak
    return drawdown.min() * 100  # negative number, as %


def compute_sharpe(equity: pd.Series, periods: int = 252) -> float:
    daily_returns = equity.pct_change().dropna()
    if daily_returns.std() == 0:
        return 0.0
    return (daily_returns.mean() / daily_returns.std()) * np.sqrt(periods)


def main():
    df = load_data()
    print(f"Loaded {len(df)} trading days from {df.index[0].date()} to {df.index[-1].date()}")
    print(f"Starting capital: ${STARTING_CAPITAL:,.2f}\n")

    print("=== TRADE LOG ===")
    trades, equity_df = run_backtest(df)

    # --- Buy-and-hold ---
    bh_start = df["Close"].iloc[0]
    bh_end = df["Close"].iloc[-1]
    bh_return_pct = (bh_end / bh_start - 1) * 100

    # --- Strategy stats ---
    final_equity = equity_df["equity"].iloc[-1]
    strategy_return_pct = (final_equity / STARTING_CAPITAL - 1) * 100

    num_trades = len(trades)
    win_rate = (sum(1 for t in trades if t["won"]) / num_trades * 100) if num_trades > 0 else 0.0

    max_dd = compute_max_drawdown(equity_df["equity"])
    sharpe = compute_sharpe(equity_df["equity"])

    print("\n=== SUMMARY ===")
    print(f"  Strategy total return : {strategy_return_pct:+.2f}%")
    print(f"  Buy-and-hold return   : {bh_return_pct:+.2f}%")
    print(f"  Number of round trips : {num_trades}")
    print(f"  Win rate              : {win_rate:.1f}%")
    print(f"  Max drawdown          : {max_dd:.2f}%")
    print(f"  Sharpe ratio (annual) : {sharpe:.2f}")

    # --- Verdict ---
    print("\n=== VERDICT ===")
    diff = strategy_return_pct - bh_return_pct
    if num_trades == 0:
        print("  The strategy never triggered a buy signal over this period.")
        print("  RSI(14) < 30 is a rare condition for SPY. The strategy sat in cash the entire time.")
        print(f"  Buy-and-hold returned {bh_return_pct:+.2f}% while this strategy returned ~0%.")
        print("  VERDICT: Strategy significantly UNDERPERFORMED buy-and-hold.")
    elif diff >= 2:
        print(f"  Strategy outperformed buy-and-hold by {diff:+.2f} percentage points.")
        print("  VERDICT: Strategy OUTPERFORMED buy-and-hold.")
    elif diff >= -2:
        print(f"  Strategy was roughly in line with buy-and-hold (difference: {diff:+.2f} pp).")
        print("  VERDICT: Strategy roughly MATCHED buy-and-hold, but with higher cash drag and fewer days invested.")
    else:
        print(f"  Strategy underperformed buy-and-hold by {abs(diff):.2f} percentage points.")
        print(f"  The strategy spent most of its time in cash waiting for RSI < 30,")
        print(f"  which rarely happens on a broad-market ETF like SPY.")
        print("  VERDICT: Strategy UNDERPERFORMED buy-and-hold. Simple buy-and-hold wins.")

    # --- Save equity curve ---
    equity_df.to_csv("backtest_equity.csv")
    print("\nSaved equity curve to backtest_equity.csv")


if __name__ == "__main__":
    main()
