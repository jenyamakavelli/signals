import requests
import time
import pandas as pd

# ---------------------------
# 📌 Настройки
# ---------------------------
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1405226935604215838/OQElV-CBe-_Hb4D13nSR-OZDG4jaGznQok62qv_AJw6glQzA3blizSvbTugn9sD8yxRA"
ALPHA_VANTAGE_KEY = "C7TDP5RHZBZ4YULR"  # получаем бесплатно на https://www.alphavantage.co
PAIRS = ["EURUSD", "GBPUSD", "USDJPY"]
SLEEP_INTERVAL = 60  # секунд
EMA_PERIOD = 10
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
MAX_HISTORY = 100

# ---------------------------
# 📌 Хранилище цен
# ---------------------------
price_history = {pair: [] for pair in PAIRS}

# ---------------------------
# 📌 Функции
# ---------------------------
def send_to_discord(message):
    try:
        requests.post(DISCORD_WEBHOOK, json={"content": message}, timeout=5)
    except Exception as e:
        print(f"⚠️ Ошибка при отправке в Discord: {e}")

def get_price(pair):
    """Запрашиваем последнюю цену валютной пары через Alpha Vantage"""
    symbol_from = pair[:3]
    symbol_to = pair[3:]
    url = (
        f"https://www.alphavantage.co/query"
        f"?function=CURRENCY_EXCHANGE_RATE"
        f"&from_currency={symbol_from}"
        f"&to_currency={symbol_to}"
        f"&apikey={ALPHA_VANTAGE_KEY}"
    )
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        rate_info = data.get("Realtime Currency Exchange Rate")
        if not rate_info:
            print(f"⚠️ Нет котировки для {pair}: {data}")
            return None
        return float(rate_info["5. Exchange Rate"])
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
    send_to_discord("✅ Forex скрипт на Alpha Vantage запущен!")

    while True:
        for pair in PAIRS:
            price = get_price(pair)
            if price is None:
                continue

            history = price_history[pair]
            history.append(price)
            if len(history) > MAX_HISTORY:
                history.pop(0)

            if len(history) >= EMA_PERIOD + RSI_PERIOD:
                ema = calculate_ema(history, EMA_PERIOD)
                rsi = calculate_rsi(history, RSI_PERIOD)
                signal = None

                if price > ema and rsi < RSI_OVERBOUGHT:
                    signal = "BUY"
                elif price < ema and rsi > RSI_OVERSOLD:
                    signal = "SELL"

                if signal and signal != last_signal[pair]:
                    send_to_discord(
                        f"💡 {pair} сигнал: {signal}\n"
                        f"Цена: {price:.5f}, EMA{EMA_PERIOD}: {ema:.5f}, RSI{RSI_PERIOD}: {rsi:.2f}"
                    )
                    last_signal[pair] = signal

        time.sleep(SLEEP_INTERVAL)

if __name__ == "__main__":
    main()
