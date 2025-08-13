import requests
import time
import pandas as pd

# ---------------------------
# 📌 Настройки
# ---------------------------
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1405226935604215838/OQElV-CBe-_Hb4D13nSR-OZDG4jaGznQok62qv_AJw6glQzA3blizSvbTugn9sD8yxRA"
PAIRS = ["EURUSD=X", "GBPUSD=X", "BTC-USD"]  # Yahoo Finance символы
SLEEP_INTERVAL = 60  # секунда
EMA_PERIOD = 10
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30

# ---------------------------
# 📌 Функции
# ---------------------------
def send_to_discord(message):
    requests.post(DISCORD_WEBHOOK, json={"content": message})

def get_price_history(pair, interval="1m", range_="1d"):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{pair}?interval={interval}&range={range_}"
    r = requests.get(url).json()
    try:
        close = r["chart"]["result"][0]["indicators"]["quote"][0]["close"]
        close = [c for c in close if c is not None]
        return pd.Series(close)
    except:
        return pd.Series([])

def calculate_ema(series, period):
    return series.ewm(span=period, adjust=False).mean().iloc[-1]

def calculate_rsi(series, period):
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ma_up = up.ewm(span=period, adjust=False).mean()
    ma_down = down.ewm(span=period, adjust=False).mean()
    rs = ma_up / ma_down
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

# ---------------------------
# 📌 Основной цикл
# ---------------------------
def main():
    last_signal = {pair: None for pair in PAIRS}
    send_to_discord("✅ Продвинутый скрипт запущен!")
    
    while True:
        try:
            for pair in PAIRS:
                series = get_price_history(pair)
                if series.empty or len(series) < EMA_PERIOD + RSI_PERIOD:
                    continue
                
                ema = calculate_ema(series, EMA_PERIOD)
                rsi = calculate_rsi(series, RSI_PERIOD)
                price = series.iloc[-1]

                signal = None
                if price > ema and rsi < RSI_OVERBOUGHT:
                    signal = "BUY"
                elif price < ema and rsi > RSI_OVERSOLD:
                    signal = "SELL"

                # Отправляем сигнал только если он новый
                if signal and signal != last_signal[pair]:
                    send_to_discord(f"💡 {pair} сигнал: {signal}\nЦена: {price:.5f}, EMA{EMA_PERIOD}: {ema:.5f}, RSI{RSI_PERIOD}: {rsi:.2f}")
                    last_signal[pair] = signal

            time.sleep(SLEEP_INTERVAL)
        except Exception as e:
            send_to_discord(f"⚠️ Ошибка скрипта: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()


