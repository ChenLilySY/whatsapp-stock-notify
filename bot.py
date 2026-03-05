import yfinance as yf
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import requests
import base64
from twilio.rest import Client
from datetime import datetime, timedelta, timezone

# --- 讀取密鑰並檢查 ---
SID = os.environ.get('TWILIO_SID')
TOKEN = os.environ.get('TWILIO_TOKEN')
TO_PHONE = os.environ.get('MY_PHONE')
IMGBB_KEY = os.environ.get('IMGBB_API_KEY')
FROM_PHONE = 'whatsapp:+14155238886' 

def upload_image(file_path):
    """上傳圖片到 ImgBB"""
    try:
        with open(file_path, "rb") as file:
            url = "https://api.imgbb.com/1/upload"
            payload = {"key": IMGBB_KEY, "image": base64.b64encode(file.read())}
            res = requests.post(url, payload)
            if res.status_code == 200:
                print(f"✅ 圖片上傳成功: {file_path}")
                return res.json()['data']['url']
            else:
                print(f"❌ 圖片上傳失敗，狀態碼: {res.status_code}")
    except Exception as e:
        print(f"❌ 上傳過程出錯: {e}")
    return None

def get_stock_data(symbol, name):
    """抓取數據並產出文字報表與圖表網址"""
    print(f"🔍 正在抓取 {name} ({symbol})...")
    stock = yf.Ticker(symbol)
    df_now = stock.history(period="1d", interval="1m")
    df_hist = stock.history(period="2y")
    
    if df_now.empty or df_hist.empty:
        return f"⚠️ {name} 數據抓取為空"

    # 畫圖邏輯
    plt.figure(figsize=(10, 5))
    plt.plot(df_now.index, df_now['Close'], color='red', linewidth=2)
    prev_close = df_hist.iloc[-2]['Close']
    plt.axhline(y=prev_close, color='gray', linestyle='--')
    plt.title(f"{name} ({symbol}) Daily Trend")
    plt.tight_layout()
    
    img_path = f"{symbol.split('.')[0]}.png"
    plt.savefig(img_path)
    plt.close()

    img_url = upload_image(img_path)

    # 計算指標
    now_p = df_now['Close'].iloc[-1]
    diff = now_p - prev_close
    pct = (diff / prev_close) * 100
    ma20 = df_hist['Close'].rolling(20).mean().iloc[-1]
    ma60 = df_hist['Close'].rolling(60).mean().iloc[-1]
    y_high = df_hist.iloc[-252:]['High'].max()
    dist_high = ((now_p - y_high) / y_high) * 100

    return (
        f"📌 標的：{symbol.split('.')[0]} {name}\n"
        f"💰 現價：{now_p:.2f} ({'+' if diff>0 else ''}{diff:.2f} | {pct:+.2f}%)\n"
        f"🏆 距52週高點：{dist_high:.2f}%\n"
        f"📐 均線：月{ma20:.1f} | 季{ma60:.1f}\n"
        f"🖼️ 走勢圖：{img_url if img_url else '無網址'}\n"
        f"--------------------------\n"
    )

def main():
    print("--- 程式執行開始 ---")
    # 檢查 Secrets
    print(f"檢查連線資訊: SID長度={len(SID) if SID else 0}, TOKEN長度={len(TOKEN) if TOKEN else 0}")
    print(f"發送至: {TO_PHONE}")

    stock_map = {"2330.TW": "台積電", "0050.TW": "元大台灣50"}
    reports = []
    
    for s, n in stock_map.items():
        reports.append(get_stock_data(s, n))
    
    # 台灣時間處理
    tz = timezone(timedelta(hours=8))
    tw_now = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
    
    full_report = f"⏰ 台北時間：{tw_now}\n\n" + "".join(reports)
    
    # 執行傳送
    try:
        client = Client(SID, TOKEN)
        msg = client.messages.create(body=full_report, from_=FROM_PHONE, to=TO_PHONE)
        print(f"✅ Twilio 請求成功送出！SID: {msg.sid}")
    except Exception as e:
        print(f"❌ Twilio 發送失敗: {e}")
    print("--- 程式執行結束 ---")

if __name__ == "__main__":
    main()
