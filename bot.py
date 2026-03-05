import yfinance as yf
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import requests
import base64
from twilio.rest import Client
from datetime import datetime, timedelta, timezone

# --- 1. 讀取密鑰 ---
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

    # --- 繪圖 ---
    plt.figure(figsize=(10, 5))
    plt.plot(df_now.index, df_now['Close'], color='red', linewidth=2)
    prev_close = df_hist.iloc[-2]['Close']
    plt.axhline(y=prev_close, color='gray', linestyle='--')
    plt.title(f"{name} ({symbol}) Daily Trend", fontsize=15)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    img_path = f"{symbol.split('.')[0]}.png"
    plt.savefig(img_path)
    plt.close()

    # --- 上傳並計算數據 ---
    img_url = upload_image(img_path)
    now_p = df_now['Close'].iloc[-1]
    diff = now_p - prev_close
    pct = (diff / prev_close) * 100
    ma20 = df_hist['Close'].rolling(20).mean().iloc[-1]
    ma60 = df_hist['Close'].rolling(60).mean().iloc[-1]
    y_high = df_hist.iloc[-252:]['High'].max()
    dist_high = ((now_p - y_high) / y_high) * 100

    tz = timezone(timedelta(hours=8))
    tw_now = datetime.now(tz).strftime('%H:%M:%S')

    content = (
        f"⏰ 時間：{tw_now} (盤中) | 台北時間\n"
        f"📌 標的：{symbol.split('.')[0]} {name}\n"
        f"昨收：{prev_close:.2f} | 現價：{now_p:.2f}\n"
        f"漲跌：{'+' if diff>0 else ''}{diff:.2f} ({pct:+.2f}%)\n"
        f"--------------------------------\n"
        f"🏆 距52週高點：{dist_high:.2f}%\n"
        f"📐 技術均線：月{ma20:.1f} | 季{ma60:.1f}\n"
    )

    # --- 透過 Twilio 發送 ---
    try:
        client = Client(SID, TOKEN)
        if img_url:
            message = client.messages.create(
                from_=FROM_PHONE,
                body=content,
                media_url=[img_url],
                to=TO_PHONE
            )
            print(f"✅ {name} 圖片訊息已送出 (SID: {message.sid})")
        else:
            client.messages.create(from_=FROM_PHONE, body=content, to=TO_PHONE)
            print(f"⚠️ {name} 僅發送文字")
    except Exception as e:
        print(f"❌ {name} 發送失敗: {e}")

def main():
    print("--- 任務啟動 ---")
    stock_map = {"2330.TW": "台積電", "0050.TW": "元大台灣50"}
    for s, n in stock_map.items():
        process_stock(s, n)
    print("--- 任務結束 ---")

# 最重要的一行：確保程式會執行 main 函數
if __name__ == "__main__":
    main()
