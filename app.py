import os
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
from data_fetcher import fetch_ohlcv
from turtle_engine import run_backtest

# 한글 폰트 설정
import matplotlib.font_manager as fm
font_path = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
if os.path.exists(font_path):
    fm.fontManager.addfont(font_path)
    plt.rcParams["font.family"] = "NanumGothic"
else:
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = ["NanumGothic", "Noto Sans CJK KR", "Malgun Gothic", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

st.set_page_config(
    page_title="터틀 트레이딩 시뮬레이터",
    page_icon="🐢",
    layout="wide",
    initial_sidebar_state="expanded"
)

PRESETS = {
    "069500": "KODEX 200 (국내 대형주 지수 ETF)",
    "379800": "KODEX 미국나스닥100TR (미국 기술주 대표 TR)",
    "379810": "KODEX 미국S&P500TR (미국 500대 우량주 TR)",
    "381180": "TIGER 미국필라델피아반도체나스닥 (반도체 ETF)",
    "122630": "KODEX 레버리지 (코스피 200 2배)",
    "229200": "KODEX 코스닥150 (코스닥 성장주 ETF)",
    "005930": "삼성전자 (국내 시총 1위)",
    "000660": "SK하이닉스 (AI 반도체 대표주)"
}

st.title("🐢 터틀 트레이딩 시뮬레이터 (Turtle Trading Web Dashboard)")
st.caption("지수 ETF 및 대형주 추세추종 백테스트 웹 애플리케이션")

with st.sidebar:
    st.header("⚙️ 전략 및 파라미터")
    
    st.subheader("1. 분석 종목 선택")
    preset_k = st.selectbox("대표 종목 프리셋", list(PRESETS.keys()), format_func=lambda x: f"{x} | {PRESETS[x]}")
    custom_input = st.text_input("직접 종목코드 입력 (6자리)", placeholder="예: 005930")
    ticker = custom_input.strip() if custom_input.strip() else preset_k
    ticker_name = PRESETS.get(ticker, f"종목코드 {ticker}")

    st.subheader("2. 전략 프리셋")
    p_mode = st.radio(
        "빠른 설정",
        ["사용자 정의", "시스템 1 (20일/10일)", "시스템 2 (55일/20일)", "일목형 (26일/9일)", "2ATR 트레일링 스탑"],
        index=1
    )

    if p_mode == "시스템 1 (20일/10일)":
        d_en, d_ex, d_tr = 20, 10, False
    elif p_mode == "시스템 2 (55일/20일)":
        d_en, d_ex, d_tr = 55, 20, False
    elif p_mode == "일목형 (26일/9일)":
        d_en, d_ex, d_tr = 26, 9, False
    elif p_mode == "2ATR 트레일링 스탑":
        d_en, d_ex, d_tr = 20, 10, True
    else:
        d_en, d_ex, d_tr = 20, 10, False

    st.subheader("3. 상세 파라미터 조절")
    entry_n = st.slider("진입: N일 신고가 돌파", min_value=5, max_value=120, value=d_en, step=1)
    exit_n = st.slider("청산: N일 신저가 이탈", min_value=3, max_value=60, value=d_ex, step=1)
    stop_atr = st.slider("손절선 ATR 배수 (매수가 - N*ATR)", min_value=1.0, max_value=4.0, value=2.0, step=0.5)
    use_trailing = st.checkbox("2ATR 트레일링 스탑 단독 청산", value=d_tr, help="N일 신저가 대신 최고가 대비 2ATR 하락 시 즉시 익절")

    st.subheader("4. 비용 및 자본금")
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        fee_pct = st.number_input("수수료(%)", value=0.015, step=0.005, format="%.3f")
    with col_c2:
        slip_pct = st.number_input("슬리피지(%)", value=0.050, step=0.010, format="%.3f")

# 시뮬레이션 실행
try:
    with st.spinner(f"[{ticker}] {ticker_name} 일봉 데이터 수집 및 연산 중..."):
        df = fetch_ohlcv(ticker)
        res = run_backtest(
            df=df,
            entry_n=entry_n,
            exit_n=exit_n,
            atr_n=14,
            stop_atr_mult=stop_atr,
            use_trailing=use_trailing,
            commission=fee_pct / 100.0,
            slippage=slip_pct / 100.0,
            initial_capital=100_000_000.0
        )
except Exception as e:
    st.error(f"데이터 조회 또는 시뮬레이션 중 오류가 발생했습니다: {e}")
    st.stop()

# 성과 요약 메트릭
st.subheader(f"📊 [{ticker}] {ticker_name} 성과 요약 ({df.index[0].strftime('%Y.%m')} ~ {df.index[-1].strftime('%Y.%m')}, {res['years']:.1f}년)")

m1, m2, m3, m4 = st.columns(4)
with m1:
    delta_ret = res['total_return'] - res['bnh_return']
    st.metric(
        "최종 자산 (초기 1억원)",
        f"{res['final_capital']/1e8:.2f}억원",
        f"{res['total_return']:+.1f}% (B&H {res['bnh_return']:+.1f}%)"
    )
with m2:
    st.metric(
        "연평균 수익률 (CAGR)",
        f"{res['cagr']:+.2f}%",
        f"단순보유 {res['bnh_cagr']:+.2f}%"
    )
with m3:
    st.metric(
        "최대 낙폭 (MDD)",
        f"{res['mdd']:.1f}%",
        f"단순보유 {res['bnh_mdd']:.1f}%",
        delta_color="inverse"
    )
with m4:
    st.metric(
        "승률 / 손익비 (PF)",
        f"{res['win_rate']:.1f}% / {res['profit_factor']:.2f}",
        f"총 {res['trades_count']}회 매매 (샤프 {res['sharpe']:.2f})"
    )

# 차트 영역
tab_chart1, tab_chart2 = st.tabs(["📈 누적 자산 곡선 (로그 스케일)", "📉 수중 낙폭 (MDD 드로우다운)"])

with tab_chart1:
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(res["benchmark"], label=f"단순보유 (Buy & Hold: {res['bnh_return']:+.1f}%, MDD {res['bnh_mdd']:.1f}%)", color="#9ca3af", linestyle="--", linewidth=1.2)
    ax.plot(res["equity"], label=f"터틀 전략 ({res['total_return']:+.1f}%, MDD {res['mdd']:.1f}%)", color="#2563eb", linewidth=2.0)
    ax.set_yscale("log")
    ax.set_ylabel("자산 (원, 로그스케일)", fontsize=11)
    ax.grid(True, alpha=0.3, linestyle=":")
    ax.legend(loc="upper left", fontsize=10)
    st.pyplot(fig)

with tab_chart2:
    fig2, ax2 = plt.subplots(figsize=(12, 3))
    ax2.plot(res["benchmark_dd"], label=f"단순보유 낙폭 (MDD {res['bnh_mdd']:.1f}%)", color="#9ca3af", linewidth=1.0, linestyle=":")
    ax2.plot(res["drawdown"], label=f"전략 낙폭 (MDD {res['mdd']:.1f}%)", color="#ef4444", linewidth=1.5)
    ax2.fill_between(res["drawdown"].index, res["drawdown"], 0, color="#ef4444", alpha=0.15)
    ax2.set_ylabel("낙폭 (%)", fontsize=10)
    ax2.grid(True, alpha=0.3, linestyle=":")
    ax2.legend(loc="lower left", fontsize=9)
    st.pyplot(fig2)

# 매매 일지 테이블
st.subheader(f"📜 상세 매매 일지 ({res['trades_count']}건)")
tdf = res["trades"]
if not tdf.empty:
    st.dataframe(
        tdf.sort_values(by="청산일", ascending=False),
        use_container_width=True,
        hide_index=True
    )
    csv_bytes = tdf.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "📥 매매 일지 CSV 다운로드",
        data=csv_bytes,
        file_name=f"turtle_trades_{ticker}.csv",
        mime="text/csv"
    )
else:
    st.info("조건을 만족하는 거래 내역이 없습니다.")
