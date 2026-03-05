import yfinance as yf
import os
from twilio.rest import Client
from datetime import datetime

# 讀取設定
SID = os.environ['TWILIO_SID']
TOKEN = os.environ['TWILIO_TOKEN']
TO_PHONE = os.environ['MY_PHONE']
FROM_PHONE = 'whatsapp:+14155238886' 

def get_report():
    # 標的清單
    stock_map = {"2330.TW": "台積電", "0050.TW": "元大台灣50"}
    full_msg = ""
    
    for symbol, name in stock_map.items():
        stock = yf.Ticker(symbol)
        # 抓取 2 年資料確保年線準確
        hist = stock.history(period="2y")
        if hist.empty: continue
        
        # 今日與昨日數據
        today = hist.iloc[-1]
        prev_close = hist.iloc[-2]['Close']
        now_price = today['Close']
        diff = now_price - prev_close
        pct = (diff / prev_close) * 100
        
        # 均線計算
        ma20 = hist['Close'].rolling(20).mean().iloc[-1]
        ma60 = hist['Close'].rolling(60).mean().iloc[-1]
        ma240 = hist['Close'].rolling(240).mean().iloc[-1]
        
        # 52 週 (1年) 區間與距離計算
        year_data = hist.iloc[-252:]
        year_low = year_data['Low'].min()
        year_high = year_data['High'].max()
        dist_high = ((now_price - year_high) / year_high) * 100

        # 依照你的照片格式排版
        msg = (
            f"⏰ 時間：{datetime.now().strftime('%H:%M:%S')} (盤中) | 台北時間\n"
            f"📌 標的：{symbol.split('.')[0]} {name}\n"
            f"📈 昨收：{prev_close:.2f}\n"
            f"💰 現價：{now_price:.2f}\n"
            f"🔺 漲跌：{'+' if diff>0 else ''}{diff:.2f} | {pct:+.2f}%\n"
            f"----------------------------------------\n"
            f"📊 本日區間：{today['Low']:.2f} ~ {today['High']:.2f}\n"
            f"🏆 52週區間：{year_low:.2f} ~ {year_high:.2f} (距高 {dist_high:.2f}%)\n"
            f"📐 技術均線：月 {ma20:.2f} | 季 {ma60:.2f} | 年 {ma240:.2f}\n"
            f"========================\n"
        )
        full_msg += msg
    return full_msg

# 執行發送
try:
    client = Client(SID, TOKEN)
    client.messages.create(body=get_report(), from_=FROM_PHONE, to=TO_PHONE)
    print("發送成功！")
except Exception as e:
    print(f"錯誤：{e}")
