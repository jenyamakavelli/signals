import requests
import time
import pandas as pd

# ---------------------------
# 📌 Настройки
# ---------------------------
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1405226935604215838/OQElV-CBe-_Hb4D13nSR-OZDG4jaGznQok62qv_AJw6glQzA3blizSvbTugn9sD8yxRA"
PAIRS = ["EURUSD", "GBPUSD", "USDJPY"]  # только валютные пары
SLEEP_INTERVAL = 60  # интервал в секундах
EMA_PERIOD = 10
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30

# ---------------------------
# 📌 Хранилище цен
# ---------------------------
price_history = {pair: [] for pair in PAIRS}

# ---------------------------
# 📌 Функции
# ---------------------------
def send_to_discord(message):
    requests.post(DISCORD_WEBHOOK, json={"content": message})

def get_price(pair):
    base = pair[:3]
    quote = pair[3:]
    url = f"https://api.exchangerate.host/latest?base={base}&symbols={quote}"
    try:
        r = requests.get(url, timeout=10).json()
        return float(r["rates"][quote])
    except Exception as e:
        print(f"⚠️ Ошибка при получении {pair}: {e}")
        return None

def calculate_ema(series, period):
    return pd.Series(series).ewm(span=period, adjust=False).mean().iloc[-1]

def calculate_rsi(series, period):
    series = pd.Series(series)
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
    send_to_discord("✅ Forex скрипт запущен!")

    while True:
        for pair in PAIRS:
            price = get_price(pair)
            if price is None:
                continue

            # Обновляем историю (храним последние 100 цен)
            history = price_history[pair]
            history.append(price)
            if len(history) > 100:
                history.pop(0)

            # Рассчитываем индикаторы только если истории достаточно
            if len(history) >= EMA_PERIOD + RSI_PERIOD:
                ema = calculate_ema(history, EMA_PERIOD)
                rsi = calculate_rsi(history, RSI_PERIOD)
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

if __name__ == "__main__":
    main()
