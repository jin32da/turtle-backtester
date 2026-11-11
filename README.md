# 🐢 터틀 트레이딩 시뮬레이터 웹앱 (Turtle Backtest WebApp)

국내 및 미국 지수 ETF, 개별 대형주를 대상으로 터틀 트레이딩(신고가 돌파 매수 / 신저가 이탈 청산 / ATR 손절 / 트레일링 스탑)의 파라미터를 자유롭게 조절하며 백테스트하는 반응형 웹 대시보드입니다.

---

## 📂 디렉토리 구조
```text
turtle-backtester/
├── app.py                      # Streamlit 웹 대시보드 메인
├── turtle_engine.py            # 터틀 전략 및 지표 시뮬레이션 엔진
├── data_fetcher.py             # 네이버 금융 일봉 수집 및 캐싱 (종료일은 실행 당일)
├── requirements.txt            # 파이썬 의존성 목록
├── packages.txt                # Streamlit Cloud용 apt 패키지 (한글 폰트)
├── Dockerfile                  # 도커 이미지 빌드 파일
├── docker-compose.yml          # 원클릭 도커 실행 파일
├── turtle-backtester.service   # Vultr Linux용 systemd 서비스
├── run.sh                      # Linux / macOS 원클릭 실행 스크립트
├── run.bat                     # Windows 원클릭 실행 배치 파일
├── .gitignore                  # 캐시·가상환경 등 제외 규칙
└── data/                       # 일봉 캐시 (실행 시 자동 생성, .gitignore로 제외)
```

---

## 💻 1. 로컬 PC에서 실행하기

### Windows
1. 압축 해제 후 `run.bat` 더블 클릭
2. 자동으로 가상환경 및 패키지 설치 후 브라우저(`http://localhost:8501`) 자동 오픈

### Linux / macOS
```bash
bash run.sh
```

### 수동 실행
```bash
python3 -m venv venv
source venv/bin/activate  # (Windows: venv\Scripts\activate)
pip install -r requirements.txt
streamlit run app.py
```

---

## ☁️ 2. Vultr 서버에 배포하기 (2가지 방법)

### 방법 A: Docker Compose (가장 추천)
```bash
# 1. 서버에 압축 해제
unzip turtle_backtest_webapp.zip -d /opt/turtle_backtest_webapp
cd /opt/turtle_backtest_webapp

# 2. 백그라운드 원클릭 실행
docker compose up -d --build

# 3. 접속: http://<Vultr_서버_IP>:8501
```

### 방법 B: systemd 서비스 데몬 등록
```bash
# 1. 패키지 복사 및 가상환경 구성
sudo cp -r turtle_backtest_webapp /opt/
cd /opt/turtle_backtest_webapp
python3 -m venv venv
./venv/bin/pip install -r requirements.txt

# 2. 서비스 등록 및 시작
sudo cp turtle-backtester.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now turtle-backtester

# 3. 상태 확인
sudo systemctl status turtle-backtester
```

---

## 🎯 주요 기능
- **프리셋 종목**: KODEX 200, 미국나스닥100TR, 미국S&P500TR, 미국필라반도체, KODEX 레버리지, 코스닥150, 삼성전자, SK하이닉스
- **임의 종목 지원**: 사이드바에 6자리 종목코드 입력 시 네이버 금융에서 전체 일봉 자동 수집
- **전략 프리셋**: 시스템 1(20/10), 시스템 2(55/20), 일목형(26/9), 2ATR 트레일링 스탑 원터치 적용
- **실전 비용 반영**: 편도 수수료(0.015%), 편도 슬리피지(0.05%) 기본 반영 (커스텀 가능)
- **차트 & 다운로드**: 누적 자산 로그 곡선, MDD 낙폭 차트, 건별 매매일지 CSV 다운로드
