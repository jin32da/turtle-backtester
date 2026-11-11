import os
import urllib.request
from datetime import datetime
from xml.etree import ElementTree

import pandas as pd

def fetch_ohlcv(ticker: str, start_date: str = "20100101", end_date: str = None,
                cache_dir: str = "data") -> pd.DataFrame:
    """네이버 금융 일봉 조회.

    end_date를 넘기지 않으면 실행 시점의 당일(YYYYMMDD)을 종료일로 사용하므로,
    언제 실행하더라도 그날까지의 최신 일봉이 반영된다.
    """
    if not end_date:
        end_date = datetime.now().strftime("%Y%m%d")

    os.makedirs(cache_dir, exist_ok=True)

    # 1. 캐시 확인 (당일 기준 파일만 사용: 날짜가 지난 캐시는 무시하고 새로 조회)
    cache_path = os.path.join(cache_dir, f"{ticker}_{start_date}_{end_date}.csv")
    if os.path.exists(cache_path):
        df = pd.read_csv(cache_path)
        df["Date"] = pd.to_datetime(df["Date"])
        df.set_index("Date", inplace=True)
        return df[df["Close"] > 0]

    # 2. 네이버 금융 일봉 스크래핑
    url = f"https://fchart.stock.naver.com/sise.nhn?symbol={ticker}&timeframe=day&count=4500&requestType=0"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        xml_data = resp.read()

    xml_str = xml_data.decode("euc-kr", errors="ignore")
    if xml_str.startswith("<?xml"):
        xml_str = xml_str.split("?>", 1)[-1].strip()

    root = ElementTree.fromstring(xml_str)
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
    df.to_csv(cache_path)
    return df
