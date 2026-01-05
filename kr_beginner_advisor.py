#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🇰🇷 Korean Beginner Strategic Briefing Advisor
=============================================
Synthesizes KR market data into a friendly briefing.
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

class KRBeginnerAdvisor:
    def __init__(self, data_dir: str = '.'):
        self.data_dir = data_dir
        self.output_file = os.path.join(data_dir, 'kr_beginner_briefing.json')
        self.api_key = os.getenv('GOOGLE_API_KEY')
        self.model_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent"

    def generate_briefing(self):
        logger.info("🧠 Generating KR Beginner Strategic Briefing...")
        
        # Load KR data
        picks_file = os.path.join(self.data_dir, 'kr_smart_money_picks.json')
        if not os.path.exists(picks_file):
            return "한국 시장 분석 데이터가 아직 준비되지 않았습니다."
            
        with open(picks_file, 'r', encoding='utf-8') as f:
            kr_data = json.load(f)
            
        top_picks = kr_data.get('top_picks', [])[:5]
        
        prompt = f"""
당신은 '주린이(주식 초보자)'를 위한 친절한 한국 주식 시장 어드바이저입니다.
오늘의 한국 시장 상황과 주요 종목들을 바탕으로 전략 브리핑을 작성해 주세요.

[분석 데이터]
- 주요 상위 종목: {', '.join([f"{p['name']}({p['ticker']}, 점수:{p['final_investment_score']})" for p in top_picks])}

요구사항:
1. 아주 친절하고 쉬운 말투(해요체)로 작성할 것.
2. 현재 한국 시장의 전반적인 분위기를 요약할 것.
3. 상위 점수 종목들 중 주목할 만한 종목 3개를 추천할 것.
4. 초보자를 위한 오늘의 한 줄 조언을 포함할 것.
5. 출력을 반드시 다음 JSON 형식으로 할 것:
{{
  "title": "...",
  "briefing": "...",
  "top_recommendations": [
    {{ "ticker": "6자리숫자만(예:012330)", "reason": "..." }},
    {{ "ticker": "6자리숫자만(예:000660)", "reason": "..." }},
    {{ "ticker": "6자리숫자만(예:005380)", "reason": "..." }}
  ],
  "action_tip": "..."
}}

중요: ticker 필드에는 반드시 6자리 숫자 종목코드만 입력하세요. 종목명이나 괄호를 포함하지 마세요.
"""
        try:
            headers = {'Content-Type': 'application/json'}
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"response_mime_type": "application/json"}
            }
            response = requests.post(f"{self.model_url}?key={self.api_key}", headers=headers, json=payload)
            res_json = response.json()
            if 'candidates' in res_json:
                text = res_json['candidates'][0]['content']['parts'][0]['text']
                briefing_data = json.loads(text)
                briefing_data['updated'] = datetime.now().isoformat()
                
                with open(self.output_file, 'w', encoding='utf-8') as f:
                    json.dump(briefing_data, f, ensure_ascii=False, indent=2)
                return briefing_data
        except Exception as e:
            logger.error(f"❌ Gemini Error for KR Briefing: {e}")
        return None

if __name__ == "__main__":
    advisor = KRBeginnerAdvisor()
    advisor.generate_briefing()
