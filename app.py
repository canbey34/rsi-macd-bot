import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import requests
import datetime

# Başlık
st.title("📊 RSI + MACD Sinyal Botu (MEXC Veri Kaynağı)")
st.markdown("Bu bot, MEXC borsasından gerçek zamanlı verilerle RSI ve MACD göstergelerine göre **AL/SAT sinyali** üretir.")

# Kullanıcıdan coin ve tarih aralığı al
symbol_input = st.text_input("Coin Sembolü (örn: BTCUSDT, DOGEUSDT)", value="BTCUSDT")
date_range = st.date_input("Veri Aralığı", [datetime.date(2024, 1, 1), datetime.date(2024, 6, 1)])
interval = "1d"

if len(date_range) == 2:
    start_date, end_date = date_range
    days = (end_date - start_date).days
    limit = min(max(days, 10), 1000)  # MEXC maksimum 1000 veri döner

    # MEXC API'den veri çek
    url = f"https://api.mexc.com/api/v3/klines?symbol={symbol_input}&interval={interval}&limit={limit}"
    response = requests.get(url)

    if response.status_code != 200:
        st.error("❌ MEXC verileri alınamadı. Sembolü kontrol et.")
    else:
        raw_data = response.json()

        if not raw_data:
            st.warning("⚠️ Veri bulunamadı.")
        else:
            df = pd.DataFrame(raw_data, columns=[
                "Open Time", "Open", "High", "Low", "Close", "Volume",
                "Close Time", "Quote Asset Volume", "Number of Trades",
                "Taker Buy Base", "Taker Buy Quote", "Ignore"])

            df['Close'] = df['Close'].astype(float)
            df['Open Time'] = pd.to_datetime(df['Open Time'], unit='ms')
            df.set_index('Open Time', inplace=True)

            # RSI Hesapla
            delta = df['Close'].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()
            rs = avg_gain / avg_loss
            df['RSI'] = 100 - (100 / (1 + rs))

            # MACD Hesapla
            ema12 = df['Close'].ewm(span=12, adjust=False).mean()
            ema26 = df['Close'].ewm(span=26, adjust=False).mean()
            df['MACD'] = ema12 - ema26
            df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
            df['Histogram'] = df['MACD'] - df['Signal']

            # Al / Sat sinyalleri
            df['Buy_Signal'] = (df['RSI'] < 30) & (df['MACD'] > df['Signal'])
            df['Sell_Signal'] = (df['RSI'] > 70) & (df['MACD'] < df['Signal'])

            # Son veri
            latest = df.iloc[-1]
            st.subheader("📍 Son Durum")
            st.write(f"Kapanış Fiyatı: ${float(latest['Close']):.4f}")
            st.write(f"RSI: {float(latest['RSI']):.2f}")
            st.write(f"MACD: {float(latest['MACD']):.5f} / Signal: {float(latest['Signal']):.5f}")

            try:
                if bool(latest['Buy_Signal'].item() if hasattr(latest['Buy_Signal'], 'item') else latest['Buy_Signal']):
                    st.success("✅ ALIM SİNYALİ (RSI < 30 ve MACD yukarı kesişim)")
                elif bool(latest['Sell_Signal'].item() if hasattr(latest['Sell_Signal'], 'item') else latest['Sell_Signal']):
                    st.error("❌ SATIM SİNYALİ (RSI > 70 ve MACD aşağı kesişim)")
                else:
                    st.info("📉 Nötr - Henüz net bir sinyal oluşmadı")
            except Exception as e:
                st.warning(f"Sinyal kontrolü sırasında hata oluştu: {e}")

            # Grafikler
            st.subheader("📈 Fiyat & RSI Grafiği")
            fig, ax = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
            ax[0].plot(df['Close'], label='Fiyat')
            ax[0].set_ylabel("Fiyat ($)")
            ax[0].legend()

            ax[1].plot(df['RSI'], label='RSI', color='orange')
            ax[1].axhline(70, color='red', linestyle='--', linewidth=1)
            ax[1].axhline(30, color='green', linestyle='--', linewidth=1)
            ax[1].set_ylabel("RSI")
            ax[1].legend()

            st.pyplot(fig)

            # Sinyal Tablosu
            st.subheader("🔍 Alım / Satım Sinyalleri")
            signal_df = df[(df['Buy_Signal']) | (df['Sell_Signal'])][['Close', 'RSI', 'MACD', 'Signal', 'Buy_Signal', 'Sell_Signal']]
            st.dataframe(signal_df.tail(10))
