#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🇰🇷 Korean Stock AI Advisor
==========================
Generates AI summaries for the top KR stocks using Gemini.
"""

import os
import json
import logging
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KRAIAdvisor:
    def __init__(self, data_dir: str = '.'):
        self.data_dir = data_dir
        self.output_file = os.path.join(data_dir, 'kr_ai_summaries.json')
        self.api_key = os.getenv('GOOGLE_API_KEY')
        self.model_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent"

    def get_stock_summary(self, ticker, name, price, grade, score, tech_data=None):
        logger.info(f"🧠 Generating AI summary for {name} ({ticker})...")
        
        tech_context = ""
        if tech_data:
            tech_context = f"""
[상세 기술적 지표]
RSI: {tech_data.get('rsi', 'N/A')}
MACD: {tech_data.get('macd', 'N/A')} (Signal: {tech_data.get('ma_signal', 'N/A')})
MACD Hist: {tech_data.get('macd_hist', 'N/A')} (양수=상승, 음수=하락)
볼린저밴드 상단: {tech_data.get('bb_upper', 'N/A')}
볼린저밴드 %B: {tech_data.get('bb_pct_b', 'N/A')} (1.0 초과=과매수, 0.0 미만=과매도)
볼린저밴드 폭: {tech_data.get('bb_width', 'N/A')} (변동성)
52주 신고가 대비: {tech_data.get('prox_52w_high', 'N/A')}%
"""

        prompt = f"""
당신은 한국 주식 전략가입니다. 다음 종목에 대한 투자 요약(Summary)을 작성해 주세요.
종목명: {name} ({ticker})
현재가: {price}원
투자등급: {grade} (Composite Score: {score})

{tech_context}

요구사항:
1. 한국어로 작성할 것.
2. 기술적 분석 시, 단순 지표 나열이 아니라 **'RSI와 볼린저밴드 위치의 관계', 'MACD 추세와 가격의 다이버전스' 등을 복합적으로 해석**하여 인사이트를 제공할 것.
3. 이 종목의 최근 사업 현황, 주요 뉴스도 함께 고려할 것.
4. 초보 투자자도 알기 쉽게 친절하게 설명할 것.
5. 출력을 반드시 다음 JSON 형식으로 할 것:
{{
  "summary": "...",
  "bull_points": ["...", "..."],
  "bear_points": ["...", "..."],
  "final_opinion": "..."
}}
"""
        try:
            headers = {'Content-Type': 'application/json'}
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "response_mime_type": "application/json",
                    "maxOutputTokens": 2048
                }
            }
            response = requests.post(f"{self.model_url}?key={self.api_key}", headers=headers, json=payload, timeout=30)
            res_json = response.json()
            if 'candidates' in res_json:
                text = res_json['candidates'][0]['content']['parts'][0]['text']
                return json.loads(text)
        except Exception as e:
            logger.error(f"❌ Gemini Error for {ticker}: {e}")
        return None

    def run(self, limit=10):
        picks_file = os.path.join(self.data_dir, 'kr_smart_money_picks.json')
        if not os.path.exists(picks_file):
            logger.error("❌ Smart money picks not found")
            return
            
        with open(picks_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        top_picks = data.get('top_picks', [])[:limit]
        summaries = {}
        
        # Check existing to avoid redundant API calls during development (optional)
        if os.path.exists(self.output_file):
            with open(self.output_file, 'r', encoding='utf-8') as f:
                summaries = json.load(f)

        for p in top_picks:
            ticker = p['ticker']
            if ticker in summaries: continue # Skip if already exists
            
            # Extract technical data
            tech_data = {
                'rsi': p.get('rsi'),
                'macd': p.get('macd'),
                'ma_signal': p.get('ma_signal'),
                'macd_hist': p.get('macd_hist'),
                'bb_upper': p.get('bb_upper'),
                'bb_pct_b': p.get('bb_pct_b'),
                'bb_width': p.get('bb_width'),
                'prox_52w_high': p.get('prox_52w_high')
            }
            
            summary = self.get_stock_summary(ticker, p['name'], p['current_price'], p['investment_grade'], p['final_investment_score'], tech_data)
            if summary:
                summaries[ticker] = {
                    **summary,
                    'updated': datetime.now().isoformat()
                }

        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(summaries, f, ensure_ascii=False, indent=2)
            
        logger.info(f"✅ Saved KR AI summaries to {self.output_file}")

if __name__ == "__main__":
    advisor = KRAIAdvisor()
    advisor.run(limit=5) # Focus on top 5 for speed
