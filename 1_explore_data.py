"""
Step 1: Explore SPY data and compute RSI signals.
No Alpaca API keys needed.
Outputs: spy_data.csv, spy_rsi_chart.png
"""

import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta


def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """RSI using Wilder's smoothing (RMA / SMMA)."""
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    # Wilder's smoothing: seed with simple average, then apply alpha = 1/period
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def main():
    end = datetime.today()
    start = end - timedelta(days=2 * 365)

    print(f"Downloading SPY daily data from {start.date()} to {end.date()} ...")
    raw = yf.download("SPY", start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d"), auto_adjust=True)

    if raw.empty:
        print("ERROR: No data returned by yfinance. Check your internet connection.")
        return

    # Flatten MultiIndex columns if present (yfinance sometimes returns them)
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = [col[0] for col in raw.columns]

    df = raw[["Open", "High", "Low", "Close", "Volume"]].copy()
    df.index.name = "Date"

    print(f"Downloaded {len(df)} trading days.")

    # Compute RSI
    df["RSI"] = compute_rsi(df["Close"], period=14)

    # Signal columns: 1 = signal present, 0 = no signal
    df["Buy_Signal"] = ((df["RSI"] < 30) & (df["RSI"].shift(1) >= 30)).astype(int)
    df["Sell_Signal"] = ((df["RSI"] > 70) & (df["RSI"].shift(1) <= 70)).astype(int)

    buy_count = df["Buy_Signal"].sum()
    sell_count = df["Sell_Signal"].sum()

    print(f"\nRSI(14) signal summary:")
    print(f"  Buy signals  (RSI crosses below 30): {buy_count}")
    print(f"  Sell signals (RSI crosses above 70): {sell_count}")

    if buy_count == 0:
        print(
            "\n  Note: Zero buy signals found. SPY rarely spends time below RSI=30 — "
            "this itself is useful information about the strategy: it fires infrequently "
            "on a broad-market ETF. Consider a lower threshold (e.g. RSI < 40) for more signals."
        )

    # Save CSV
    df.to_csv("spy_data.csv")
    print("\nSaved data to spy_data.csv")

    # --- Chart ---
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True,
                                    gridspec_kw={"height_ratios": [2, 1]})
    fig.suptitle("SPY — RSI(14) Strategy Signals", fontsize=14, fontweight="bold")

    # Price panel
    ax1.plot(df.index, df["Close"], color="#1f77b4", linewidth=1.2, label="SPY Close")
    buys = df[df["Buy_Signal"] == 1]
    sells = df[df["Sell_Signal"] == 1]
    ax1.scatter(buys.index, buys["Close"], marker="^", color="green", s=80,
                zorder=5, label=f"Buy signal ({len(buys)})")
    ax1.scatter(sells.index, sells["Close"], marker="v", color="red", s=80,
                zorder=5, label=f"Sell signal ({len(sells)})")
    ax1.set_ylabel("Price (USD)")
    ax1.legend(loc="upper left", fontsize=9)
    ax1.grid(alpha=0.3)

    # RSI panel
    ax2.plot(df.index, df["RSI"], color="#ff7f0e", linewidth=1.2, label="RSI(14)")
    ax2.axhline(70, color="red", linestyle="--", linewidth=0.8, alpha=0.7, label="Overbought (70)")
    ax2.axhline(30, color="green", linestyle="--", linewidth=0.8, alpha=0.7, label="Oversold (30)")
    ax2.fill_between(df.index, df["RSI"], 70, where=(df["RSI"] > 70),
                     alpha=0.15, color="red")
    ax2.fill_between(df.index, df["RSI"], 30, where=(df["RSI"] < 30),
                     alpha=0.15, color="green")
    ax2.set_ylim(0, 100)
    ax2.set_ylabel("RSI")
    ax2.set_xlabel("Date")
    ax2.legend(loc="upper left", fontsize=9)
    ax2.grid(alpha=0.3)

    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    fig.autofmt_xdate(rotation=30)

    plt.tight_layout()
    plt.savefig("spy_rsi_chart.png", dpi=150, bbox_inches="tight")
    print("Saved chart to spy_rsi_chart.png")
    plt.show()


if __name__ == "__main__":
    main()
