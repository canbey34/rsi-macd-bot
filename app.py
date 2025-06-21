import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt

# Başlık
st.title("📊 RSI + MACD Sinyal Botu (Demo)")
st.markdown("Bu bot, RSI ve MACD göstergelerine göre **AL/SAT sinyali** üretir. Gerçek fiyat verileriyle çalışır.")

# Kullanıcıdan coin ve tarih aralığı al
symbol = st.text_input("Coin Sembolü (örn: DOGE-USD, BTC-USD)", value="DOGE-USD")
date_range = st.date_input("Veri Aralığı", [pd.to_datetime("2024-01-01"), pd.to_datetime("2024-06-01")])

if len(date_range) == 2:
    start_date, end_date = date_range

    data = yf.download(symbol, start=start_date, end=end_date, interval="1d")
    if data.empty:
        st.warning("⚠️ Veri alınamadı. Lütfen geçerli bir sembol girin.")
    else:
        # RSI Hesaplama
        delta = data['Close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        data['RSI'] = 100 - (100 / (1 + rs))

        # MACD Hesaplama
        ema12 = data['Close'].ewm(span=12, adjust=False).mean()
        ema26 = data['Close'].ewm(span=26, adjust=False).mean()
        data['MACD'] = ema12 - ema26
        data['Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()
        data['Histogram'] = data['MACD'] - data['Signal']

        # Al / Sat sinyalleri
        data['Buy_Signal'] = (data['RSI'] < 30) & (data['MACD'] > data['Signal'])
        data['Sell_Signal'] = (data['RSI'] > 70) & (data['MACD'] < data['Signal'])

        # Son veri
        latest = data.iloc[-1]
        st.subheader("📍 Son Durum")
        st.write(f"Kapanış Fiyatı: ${float(latest['Close']):.4f}")
        st.write(f"RSI: {float(latest['RSI']):.2f}")
        st.write(f"MACD: {float(latest['MACD']):.5f} / Signal: {float(latest['Signal']):.5f}")

        if latest['Buy_Signal'].any():
            st.success("✅ ALIM SİNYALİ (RSI < 30 ve MACD yukarı kesişim)")
        elif bool(latest['Sell_Signal']):
            st.error("❌ SATIM SİNYALİ (RSI > 70 ve MACD aşağı kesişim)")
        else:
            st.info("📉 Nötr - Henüz net bir sinyal oluşmadı")

        # Grafikler
        st.subheader("📈 Fiyat & RSI Grafiği")
        fig, ax = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
        ax[0].plot(data['Close'], label='Fiyat')
        ax[0].set_ylabel("Fiyat ($)")
        ax[0].legend()

        ax[1].plot(data['RSI'], label='RSI', color='orange')
        ax[1].axhline(70, color='red', linestyle='--', linewidth=1)
        ax[1].axhline(30, color='green', linestyle='--', linewidth=1)
        ax[1].set_ylabel("RSI")
        ax[1].legend()

        st.pyplot(fig)

        # Sinyal Tablosu
        st.subheader("🔍 Alım / Satım Sinyalleri")
        signal_df = data[(data['Buy_Signal']) | (data['Sell_Signal'])][['Close', 'RSI', 'MACD', 'Signal', 'Buy_Signal', 'Sell_Signal']]
        st.dataframe(signal_df.tail(10))
