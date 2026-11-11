import os
import urllib.request
from xml.etree import ElementTree
import pandas as pd

def fetch_ohlcv(ticker: str, start_date: str = "20100101", end_date: str = "20261109", cache_dir: str = "data") -> pd.DataFrame:
    os.makedirs(cache_dir, exist_ok=True)
    
    # 1. 캐시 확인
    for f in os.listdir(cache_dir):
        if f.startswith(f"{ticker}_") and f.endswith(".csv"):
            path = os.path.join(cache_dir, f)
            df = pd.read_csv(path)
            df["Date"] = pd.to_datetime(df["Date"])
            df.set_index("Date", inplace=True)
            return df[df["Close"] > 0]

    # 2. 네이버 금융 일봉 스크래핑
    url = f"https://fchart.stock.naver.com/sise.nhn?symbol={ticker}&timeframe=day&count=4500&requestType=0"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        xml_data = resp.read()

    root = ElementTree.fromstring(xml_data)
    rows = []
    for item in root.findall(".//item"):
        d = item.attrib["data"].split("|")
        rows.append({
            "Date": pd.to_datetime(d[0]),
            "Open": float(d[1]),
            "High": float(d[2]),
            "Low": float(d[3]),
            "Close": float(d[4]),
            "Volume": float(d[5]),
        })

    if not rows:
        raise ValueError(f"종목코드 {ticker} 데이터를 가져올 수 없습니다.")

    df = pd.DataFrame(rows).set_index("Date")
    df = df[df["Close"] > 0]
    
    # 캐시 저장
    cache_path = os.path.join(cache_dir, f"{ticker}_{start_date}_{end_date}.csv")
    df.to_csv(cache_path)
    return df
