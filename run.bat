@echo off
chcp 65001 >nul
echo === 터틀 트레이딩 웹앱 실행 스크립트 ===

if not exist venv (
    echo 가상환경(venv) 생성 중...
    python -m venv venv
)

echo 패키지 의존성 확인 중...
call venv\Scripts\pip install -q --upgrade pip
call venv\Scripts\pip install -q -r requirements.txt

echo Streamlit 웹앱 실행: http://localhost:8501
call venv\Scripts\streamlit run app.py
pause
