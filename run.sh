#!/usr/bin/env bash
set -e

echo "=== 터틀 트레이딩 웹앱 실행 스크립트 ==="

if [ ! -d "venv" ]; then
    echo "가상환경(venv) 생성 중..."
    python3 -m venv venv
fi

echo "패키지 의존성 확인 중..."
./venv/bin/pip install -q --upgrade pip
./venv/bin/pip install -q -r requirements.txt

echo "Streamlit 웹앱 실행: http://localhost:8501"
./venv/bin/streamlit run app.py --server.port 8501 --server.address 0.0.0.0
