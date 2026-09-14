import yfinance as yf
import pandas as pd
import datetime
import warnings
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# Suppress warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.simplefilter(action='ignore', category=UserWarning)

CURRENT_DATE = datetime.date.today()
END_DATE = CURRENT_DATE.strftime("%Y-%m-%d")
START_DATE = (CURRENT_DATE - pd.DateOffset(months=6)).strftime("%Y-%m-%d")

nasdaq_100_tickers = [
    "AAPL", "ABNB", "ADBE", "ADI", "ADP", "ADSK", "AEP", "ALAB", "ALNY", "AMAT",
    "AMD", "AMGN", "AMZN", "APP", "ARM", "ASML", "AVGO", "AXON", "BKR", "BKNG",
    "CDNS", "CEG", "CHTR", "CMCSA", "COST", "CPRT", "CRWD", "CSCO", "CSX", "CTAS",
    "CTSH", "DASH", "DDOG", "DXCM", "EXC", "FAST", "FTNT", "GEHC", "GILD", "GOOG",
    "GOOGL", "HON", "IDXX", "INTC", "INTU", "ISRG", "KDP", "KHC", "KLAC", "LITE",
    "LIN", "LRCX", "MAR", "MCHP", "MDLZ", "MELI", "META", "MNST", "MRVL", "MSFT",
    "MU", "NFLX", "NVDA", "NXPI", "ODFL", "ON", "ORLY", "PANW", "PAYX", "PCAR",
    "PDD", "PEP", "PLTR", "QCOM", "REGN", "ROP", "ROST", "SBUX", "SNPS", "TEAM",
    "TMUS", "TSLA", "TTD", "TTWO", "TXN", "VRSK", "VRTX", "WBD", "WDAY", "XEL", "ZS"
]

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

scan_results = []

for ticker in nasdaq_100_tickers:
    try:
        df = yf.download(ticker, start=START_DATE, end=END_DATE, interval="1d", progress=False, auto_adjust=True)
        if df.empty or len(df) < 30:
            continue
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        df['RSI'] = calculate_rsi(df['Close'], period=14)
        
        if len(df) >= 2:
            prev_rsi = df['RSI'].iloc[-2]
            curr_rsi = df['RSI'].iloc[-1]
            
            if prev_rsi < 50 and curr_rsi >= 50:
                scan_results.append({
                    'Ticker': ticker,
                    'Previous RSI': round(prev_rsi, 1),
                    'Current RSI': round(curr_rsi, 1),
                    'Latest Close ($)': round(float(df['Close'].iloc[-1]), 2),
                    'As of Date': df.index[-1].strftime("%Y-%m-%d")
                })
    except Exception:
        pass

df_all = pd.DataFrame(scan_results)

# Build HTML Email Body
if not df_all.empty:
    html_table = df_all.to_html(index=False, classes='table', border=0)
    body_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; color: #333; }}
            h3 {{ color: #111; }}
            table.table {{ border-collapse: collapse; width: 100%; margin-top: 10px; }}
            table.table th {{ background-color: #f4f4f4; padding: 10px; border: 1px solid #ddd; text-align: left; }}
            table.table td {{ padding: 8px; border: 1px solid #ddd; text-align: left; }}
        </style>
    </head>
    <body>
        <h3>🚀 NASDAQ-100 RSI 50-CENTERLINE CROSSOVER REPORT — {CURRENT_DATE}</h3>
        <p>The following stocks crossed above the 50 RSI threshold, signaling potential bullish momentum continuation:</p>
        {html_table}
    </body>
    </html>
    """
else:
    body_content = f"<p>No Nasdaq-100 stocks triggered an RSI 50-centerline crossover as of {CURRENT_DATE}.</p>"

# Email Configuration
SENDER_EMAIL = os.environ.get("MAIL_USER")
RECEIVER_EMAIL = os.environ.get("MAIL_USER")
EMAIL_PASSWORD = os.environ.get("MAIL_PASS")

if not SENDER_EMAIL or not EMAIL_PASSWORD:
    raise ValueError("Missing MAIL_USER or MAIL_PASS environment variables.")

msg = MIMEMultipart()
msg['From'] = SENDER_EMAIL
msg['To'] = RECEIVER_EMAIL
msg['Subject'] = f"RSI-50 Crossover Alert - {CURRENT_DATE}"
msg.attach(MIMEText(body_content, 'html'))

try:
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(SENDER_EMAIL, EMAIL_PASSWORD)
    server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
    server.quit()
    print("Email sent successfully!")
except Exception as e:
    print(f"Failed to send email: {e}")