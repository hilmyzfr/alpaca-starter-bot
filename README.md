# Alpaca Starter Bot

A beginner-friendly project for learning algorithmic trading with Alpaca Markets.

## Setup

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your Alpaca paper trading API keys
```

Get free paper trading API keys at https://alpaca.markets (no real money needed).

## 3-Step Workflow

### Step 1: Explore Data (`1_explore_data.py`)
No API keys needed. Downloads 2 years of SPY daily data via yfinance, computes RSI(14),
marks buy signals (RSI < 30) and sell signals (RSI > 70), and saves:
- `spy_data.csv` — raw data with signals for the backtest
- `spy_rsi_chart.png` — price chart with signal markers + RSI panel

```bash
python 1_explore_data.py
```

### Step 2: Backtest (`2_backtest.py`)
No API keys needed. Reads `spy_data.csv` and simulates the RSI strategy historically,
reporting total return, number of trades, and a equity curve chart.

```bash
python 2_backtest.py
```

### Step 3: Paper Trade (`3_paper_trade.py`)
Requires Alpaca paper trading API keys in `.env`. Connects to Alpaca, checks the
latest RSI value for SPY, and places a paper trade if a signal is present.

```bash
python 3_paper_trade.py
```

## Strategy

- **Buy** when RSI(14) drops below 30 (oversold)
- **Sell** when RSI(14) rises above 70 (overbought)
- RSI is computed using Wilder's smoothing (standard method)

> This is for educational purposes only. Past performance does not guarantee future results.
