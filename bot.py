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
    print(f"🔍 正在處理 {name} ({symbol})...")
    stock = yf.Ticker(symbol)
    df_now = stock.history(period="1d", interval="1m")
    df_hist = stock.history(period="2y")
    
    if df_now.empty or df_hist.empty:
        return

    # --- 判斷狀態 ---
    tz = timezone(timedelta(hours=8))
    now = datetime.now(tz)
    is_open = now.weekday() <= 4 and 9 <= now.hour < 13 or (now.hour == 13 and now.minute <= 35)
    status_text = "盤中" if is_open else "收盤"

    # --- 繪圖 ---
    plt.figure(figsize=(10, 5))
    plt.plot(df_now.index, df_now['Close'], color='red', linewidth=2)
    prev_close = df_hist.iloc[-2]['Close']
    plt.axhline(y=prev_close, color='gray', linestyle='--')
    plt.title(f"{name} ({symbol}) - {status_text} Trend", fontsize=15)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    img_path = f"{symbol.split('.')[0]}.png"
    plt.savefig(img_path)
    plt.close()

    # --- 數據計算 ---
    img_url = upload_image(img_path)
    now_p = df_now['Close'].iloc[-1]
    diff = now_p - prev_close
    pct = (diff / prev_close) * 100
    
    # 均線
    ma20 = df_hist['Close'].rolling(20).mean().iloc[-1]
    ma60 = df_hist['Close'].rolling(60).mean().iloc[-1]
    ma240 = df_hist['Close'].rolling(240).mean().iloc[-1]
    
    # 區間
    y_low = df_hist.iloc[-252:]['Low'].min()
    y_high = df_hist.iloc[-252:]['High'].max()
    dist_high = ((now_p - y_high) / y_high) * 100

    # --- 重新組合完整文字 (包含你消失的欄位) ---
    content = (
        f"⏰ 時間：{now.strftime('%H:%M:%S')} ({status_text})\n"
        f"📍 標的：{symbol.split('.')[0]} {name}\n"
        f"昨收：{prev_close:.2f} | 現價：{now_p:.2f}\n"
        f"漲跌：{'+' if diff>0 else ''}{diff:.2f} ({pct:+.2f}%)\n"
        f"--------------------------------\n"
        f"📊 本日區間：{df_now['Low'].min():.2f} ~ {df_now['High'].max():.2f}\n"
        f"🏆 52週區間：{y_low:.2f} ~ {y_high:.2f} (距高{dist_high:.1f}%)\n"
        f"📐 均線：月{ma20:.1f} | 季{ma60:.1f} | 年{ma240:.1f}"
    )

    try:
        client = Client(SID, TOKEN)
        if img_url:
            client.messages.create(from_=FROM_PHONE, body=content, media_url=[img_url], to=TO_PHONE)
        else:
            client.messages.create(from_=FROM_PHONE, body=content, to=TO_PHONE)
        print(f"✅ {name} 訊息已發送")
    except Exception as e:
        print(f"❌ 發送錯誤: {e}")

def main():
    stock_map = {"2330.TW": "台積電", "0050.TW": "元大台灣50"}
    for s, n in stock_map.items():
        process_stock(s, n)

if __name__ == "__main__":
    main()
