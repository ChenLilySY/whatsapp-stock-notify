import yfinance as yf
import os
from twilio.rest import Client
from datetime import datetime

# 讀取剛剛設定的密碼
SID = os.environ['TWILIO_SID']
TOKEN = os.environ['TWILIO_TOKEN']
TO_PHONE = os.environ['MY_PHONE']
FROM_PHONE = 'whatsapp:+14155238886' # 這通常是 Twilio 沙盒的公用號碼

def get_report():
    tickers = ["0050.TW", "2330.TW"]
    msg = f"📈 股市報價 ({datetime.now().strftime('%Y-%m-%d')})\n"
    for s in tickers:
        stock = yf.Ticker(s)
        # 抓取歷史資料計算均線
        h = stock.history(period="2y")
        if h.empty: continue
        
        t = h.iloc[-1]  # 今天
        p = h.iloc[-2]['Close'] # 昨天
        price = t['Close']
        
        # 計算指標
        ma20 = h['Close'].rolling(20).mean().iloc[-1]
        ma60 = h['Close'].rolling(60).mean().iloc[-1]
        ma240 = h['Close'].rolling(240).mean().iloc[-1]
        
        name = "0050" if "0050" in s else "台積電"
        msg += (
            f"\n【{name}】\n"
            f"💰 現價: {price:.2f} ({'+' if price>p else ''}{price-p:.2f})\n"
            f"↕️ 區間: {t['Low']:.1f}-{t['High']:.1f}\n"
            f"📅 一年區間: {h.iloc[-252:]['Low'].min():.1f}-{h.iloc[-252:]['High'].max():.1f}\n"
            f"📊 月/季/年線: {ma20:.1f} | {ma60:.1f} | {ma240:.1f}\n"
        )
    return msg

# 執行發送
client = Client(SID, TOKEN)
client.messages.create(body=get_report(), from_=FROM_PHONE, to=TO_PHONE)
