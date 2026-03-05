import yfinance as yf
import os
import matplotlib.pyplot as plt
import requests
import base64
from twilio.rest import Client
from datetime import datetime
import matplotlib; matplotlib.use('Agg')

# 設定區
SID = os.environ['TWILIO_SID']
TOKEN = os.environ['TWILIO_TOKEN']
TO_PHONE = os.environ['MY_PHONE']
IMGBB_KEY = os.environ['IMGBB_API_KEY']
FROM_PHONE = 'whatsapp:+14155238886'

def upload_image(file_path):
    with open(file_path, "rb") as file:
        url = "https://api.imgbb.com/1/upload"
        payload = {"key": IMGBB_KEY, "image": base64.b64encode(file.read())}
        res = requests.post(url, payload)
        return res.json()['data']['url'] if res.status_code == 200 else None

def get_stock_data(symbol, name):
    stock = yf.Ticker(symbol)
    # 抓取盤中即時走勢 (1分K)
    df_now = stock.history(period="1d", interval="1m")
    # 抓取長線資料算均線
    df_hist = stock.history(period="2y")
    
    if df_now.empty or df_hist.empty: return None

    # 1. 畫圖
    plt.figure(figsize=(8, 4))
    plt.plot(df_now.index, df_now['Close'], color='red', linewidth=2)
    plt.axhline(y=df_hist.iloc[-2]['Close'], color='gray', linestyle='--') # 昨收線
    plt.title(f"{symbol} {name} Daily Trend", fontsize=14)
    plt.grid(True, alpha=0.3)
    img_path = f"{symbol}.png"
    plt.savefig(img_path)
    plt.close()

    # 2. 上傳圖表
    img_url = upload_image(img_path)

    # 3. 計算數據
    now_p = df_now['Close'].iloc[-1]
    prev_p = df_hist.iloc[-2]['Close']
    diff = now_p - prev_p
    pct = (diff / prev_p) * 100
    ma20 = df_hist['Close'].rolling(20).mean().iloc[-1]
    ma60 = df_hist['Close'].rolling(60).mean().iloc[-1]
    ma240 = df_hist['Close'].rolling(240).mean().iloc[-1]
    y_low = df_hist.iloc[-252:]['Low'].min()
    y_high = df_hist.iloc[-252:]['High'].max()

    msg = (
        f"📍 {name} ({symbol.split('.')[0]})\n"
        f"💰 現價：{now_p:.2f} ({'+' if diff>0 else ''}{diff:.2f} | {pct:+.2f}%)\n"
        f"📊 區間：{df_now['Low'].min():.2f} - {df_now['High'].max():.2f}\n"
        f"📅 52週：{y_low:.2f} - {y_high:.2f}\n"
        f"📐 均線：月{ma20:.1f}/季{ma60:.1f}/年{ma240:.1f}\n"
        f"🖼️ 走勢圖：{img_url}\n"
        f"--------------------------"
    )
    return msg

def main():
    stocks = {"2330.TW": "台積電", "0050.TW": "元大台灣50"}
    reports = []
    for s, n in stocks.items():
        res = get_stock_data(s, n)
        if res: reports.append(res)
    
    full_report = f"⏰ {datetime.now().strftime('%H:%M')} 股市快報\n\n" + "\n".join(reports)
    client = Client(SID, TOKEN)
    client.messages.create(body=full_report, from_=FROM_PHONE, to=TO_PHONE)

if __name__ == "__main__":
    main()
