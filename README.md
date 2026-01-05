# 🤖 AI Stock Analysis System (US/KR)

AI 기반 미국/한국 주식 분석 시스템

## 🚀 빠른 시작

### 1. 저장소 다운로드
```bash
git clone https://github.com/ENERGY-INNO/stock-ai-analysis.git
cd stock-ai-analysis
```

### 2. Python 가상환경 생성 (권장)
```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. 패키지 설치
```bash
pip install -r requirements.txt
```

### 4. 환경변수 설정
`.env` 파일을 생성하고 API 키를 입력하세요:
```bash
# .env 파일 내용
GOOGLE_API_KEY=your_google_api_key_here
```

> 💡 Google API 키는 [Google AI Studio](https://aistudio.google.com/apikey)에서 발급받을 수 있습니다.

### 5. 데이터 분석 실행
```bash
python run_all.py
```
이 명령은 다음 작업을 수행합니다:
- 미국/한국 주식 데이터 수집
- 기술적 분석 (RSI, MACD, 볼린저밴드)
- 스마트 머니 스크리닝
- AI 요약 생성

### 6. 웹 대시보드 실행
```bash
python flask_app.py
```
브라우저에서 http://localhost:5001 접속

---

## 📁 주요 파일 구조

```
stock-ai-analysis/
├── run_all.py              # 전체 분석 파이프라인 실행
├── flask_app.py            # 웹 대시보드 서버
├── smart_money_screener_v2.py  # 스마트 머니 스크리닝
├── ai_summary_generator.py # AI 종목 요약 생성
├── beginner_advisor.py     # AI 투자 브리핑 (US)
├── kr_beginner_advisor.py  # AI 투자 브리핑 (KR)
├── templates/
│   └── index.html          # 대시보드 UI
└── requirements.txt        # Python 패키지 목록
```

---

## 🌐 외부 접속 설정 (선택)

LocalTunnel을 사용하여 외부에서 접속할 수 있습니다:

```bash
# LocalTunnel 설치
npm install -g localtunnel

# 터널 실행 (Flask 서버 실행 후)
lt --port 5001 --subdomain my-stock-ai
```

접속 URL: `https://my-stock-ai.loca.lt`

---

## 🔑 필요한 API 키

| 서비스 | 용도 | 발급 |
|--------|------|------|
| Google API | AI 분석 (Gemini) | [Google AI Studio](https://aistudio.google.com/apikey) |

---

## ⚠️ 주의사항

- 이 시스템은 투자 권유가 아닌 참고용 분석 도구입니다
- 실제 투자 결정은 본인의 판단과 책임하에 이루어져야 합니다
- yfinance 데이터는 실시간이 아닐 수 있습니다

---

## 📝 라이선스

MIT License
