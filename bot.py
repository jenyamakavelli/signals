import requests
import time
import pandas as pd

# ---------------------------
# 📌 Настройки
# ---------------------------
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1405226935604215838/OQElV-CBe-_Hb4D13nSR-OZDG4jaGznQok62qv_AJw6glQzA3blizSvbTugn9sD8yxRA"
PAIRS = ["EURUSD", "GBPUSD", "USDJPY"]  # валютные пары
SLEEP_INTERVAL = 60  # интервал между проверками в секундах
EMA_PERIOD = 10
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
MAX_HISTORY = 100  # максимальное количество цен для индикаторов

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

def get_price(pairs):
    """Запрашиваем сразу все пары одним запросом"""
    if not pairs:
        return {}

    url = f"https://www.freeforexapi.com/api/live?pairs={','.join(pairs)}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json() if r.content else {}

        # Проверяем, что это словарь и содержит rates
        if not isinstance(data, dict):
            print(f"⚠️ Некорректный ответ API (не dict): {data}")
            return {}
        if "rates" not in data or data.get("code") != 200:
            print(f"⚠️ Некорректный ответ API: {data}")
            return {}

        rates = {}
        for pair in pairs:
            rate_info = data["rates"].get(pair)
            if rate_info is not None:
                rates[pair] = rate_info.get("rate")
            else:
                print(f"⚠️ Нет котировки для {pair} в ответе API")
        return rates
    except Exception as e:
        print(f"⚠️ Ошибка при получении котировок: {e}")
        return {}

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
    send_to_discord("✅ Forex скрипт на Free Forex API запущен!")

    while True:
        rates = get_price(PAIRS)
        if not rates:
            time.sleep(SLEEP_INTERVAL)
            continue

        for pair, price in rates.items():
            # Обновляем историю цен
            history = price_history[pair]
            history.append(price)
            if len(history) > MAX_HISTORY:
                history.pop(0)

            # Рассчитываем индикаторы только если истории достаточно
            if len(history) >= EMA_PERIOD + RSI_PERIOD:
                ema = calculate_ema(history, EMA_PERIOD)
                rsi = calculate_rsi(history, RSI_PERIOD)
                signal = None

                # Логика сигналов
                if price > ema and rsi < RSI_OVERBOUGHT:
                    signal = "BUY"
                elif price < ema and rsi > RSI_OVERSOLD:
                    signal = "SELL"

                # Отправка сигнала только если он новый
                if signal and signal != last_signal[pair]:
                    send_to_discord(f"💡 {pair} сигнал: {signal}\nЦена: {price:.5f}, EMA{EMA_PERIOD}: {ema:.5f}, RSI{RSI_PERIOD}: {rsi:.2f}")
                    last_signal[pair] = signal

        time.sleep(SLEEP_INTERVAL)

if __name__ == "__main__":
    main()
