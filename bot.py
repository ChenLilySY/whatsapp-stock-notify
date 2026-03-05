import yfinance as yf
import os
import matplotlib
matplotlib.use('Agg')  # 必備：確保在 GitHub 雲端無顯示器環境下能畫圖
import matplotlib.pyplot as plt
import requests
import base64
from twilio.rest import Client
from datetime import datetime, timedelta, timezone

# 1. 從 GitHub Secrets 讀取密鑰
SID = os.environ['TWILIO_SID']
TOKEN = os.environ['TWILIO_TOKEN']
TO_PHONE = os.environ['MY_PHONE']
IMGBB_KEY = os.environ['IMGBB_API_KEY']
FROM_PHONE = 'whatsapp:+14155238886' # Twilio 沙盒公用號碼

def upload_image(file_path):
    """將圖片上傳到 ImgBB 並取得網址"""
    try:
        with open(file_path, "rb") as file:
            url = "https://api.imgbb.com/1/upload"
            payload = {"key": IMGBB_KEY, "image": base64.b64encode(file.read())}
            res = requests.post(url, payload)
            if res.status_code == 200:
                return res.json()['data']['url']
    except Exception as e:
        print(f"圖片上傳失敗: {e}")
    return None

def get_stock_data(symbol, name):
    """抓取股市數據並畫圖"""
    stock = yf.Ticker(symbol)
    
    # 抓取盤中即時走勢 (1分鐘頻率)
    df_now = stock.history(period="1d", interval="1m")
    # 抓取長線資料計算均線 (2年)
    df_hist = stock.history(period="2y")
    
    if df_now.empty or df_hist.empty:
        return f"⚠️ 無法取得 {name} ({symbol}) 的數據"

    # --- 繪製走勢圖 ---
    plt.figure(figsize=(10, 5))
    plt.plot(df_now.index, df_now['Close'], color='red', linewidth=2, label='Price')
    # 畫出昨日收盤價的虛線
    prev_close = df_hist.iloc[-2]['Close']
    plt.axhline(y=prev_close, color='gray', linestyle='--', label='Prev Close')
    
    plt.title(f"{name} ({symbol}) Daily Chart", fontsize=15)
    plt.xlabel("Time")
    plt.ylabel("Price")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    img_path = f"{symbol.split('.')[0]}.png"
    plt.savefig(img_path)
    plt.close()

    # --- 上傳圖片 ---
    img_url = upload_image(img_path)

    # --- 計算報價數據 ---
    now_p = df_now['Close'].iloc[-1]
    diff = now_p - prev_close
    pct = (diff / prev_close) * 100
    
    # 技術指標
    ma20 = df_hist['Close'].rolling(20).mean().iloc[-1]
    ma60 = df_hist['Close'].rolling(60).mean().iloc[-1]
    ma240 = df_hist['Close'].rolling(240).mean().iloc[-1]
    
    # 52週區間
    y_low = df_hist.iloc
