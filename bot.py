import yfinance as yf
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import requests
import base64
from twilio.rest import Client
from datetime import datetime, timedelta, timezone

# --- 讀取密鑰 ---
SID = os.environ.get('TWILIO_SID')
TOKEN = os.environ.get('TWILIO_TOKEN')
TO_PHONE = os.environ.get('MY_PHONE')
IMGBB_KEY = os.environ.get('IMGBB_API_KEY')
FROM_PHONE = 'whatsapp:+14155238886' 

def upload_image(file_path):
    """上傳圖片到 ImgBB 並取得直接圖檔連結"""
    try:
        with open(file_path, "rb") as file:
            url = "https://api.imgbb.com/1/upload"
            payload = {"key": IMGBB_KEY, "image": base64.b64encode(file.read())}
            res = requests.post(url, payload)
            if res.status_code == 200:
                # 這裡要確保拿到的網址是直接圖檔路徑
                return res.json()['data']['url']
    except Exception as e:
        print(f"❌ 圖片上傳錯誤: {e}")
    return None

def process_stock(symbol, name):
    """抓取數據、畫圖、並傳送單則圖片訊息"""
    print(f"🔍 正在處理 {name} ({symbol})...")
    stock = yf.Ticker(symbol)
    df_now = stock.history(period="1d", interval="1m")
    df_hist = stock.history(period="2y")
    
    if df_now.empty or df_hist.empty:
        print(f"⚠️ {name} 數據缺失")
        return

    # --- 1. 繪圖邏輯 ---
    plt.figure(figsize=(10, 5))
    plt.plot(df_now.index, df_now['Close'], color='red', linewidth=2)
    prev_close = df_hist.iloc[-2]['Close']
    plt.axhline(y=prev_close, color='gray', linestyle='--')
    plt.title(f"{name} ({symbol}) Daily Trend", fontsize
