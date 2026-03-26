# alpaca-starter-bot

A hands-on repo for learning algorithmic trading while sharpening vibe coding skills. The idea: pick a simple strategy, test it honestly, then wire it up to real paper trades.

No magic libraries. The backtest engine is written from scratch in pandas so you can actually see what's happening.

## Setup

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Add your Alpaca paper trading keys to .env (step 3 only)
```

Free paper trading keys from Alpaca Markets — no real money involved.

## Steps

### Step 1 — explore the data (`1_explore_data.py`)

No API keys needed. Downloads 2 years of SPY daily OHLCV from yfinance, computes RSI(14) using Wilder's smoothing, and saves:

- `spy_data.csv` — price + RSI + signal columns
- `spy_rsi_chart.png` — price panel with buy/sell markers, RSI panel below

```bash
python 1_explore_data.py
```

### Step 2 — backtest (`2_backtest.py`)

No API keys needed. Reads `spy_data.csv` and runs the strategy day-by-day. Prints every trade, then reports total return, win rate, max drawdown, Sharpe ratio, and an honest comparison against buy-and-hold. Saves the equity curve to `backtest_equity.csv`.

Spoiler: SPY rarely dips below RSI 30, so the strategy fires twice in two years and still loses to buy-and-hold by ~14 percentage points. That's a useful thing to know before trading real money.

```bash
python 2_backtest.py
```

### Step 3 — paper trade (`3_paper_trade.py`) *(coming soon)*

Will use Alpaca's paper trading API to check live RSI and place orders when a signal fires. Not built yet.

## Strategy

Buy when RSI(14) drops below 30, sell when it rises above 70. Fully in or fully out. 0.1% fee applied on each side to simulate spread and slippage.

RSI is computed with Wilder's smoothing (alpha = 1/14), same method TradingView uses.

---

*For learning only. Past results don't predict future ones.*
