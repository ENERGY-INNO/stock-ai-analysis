#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎓 Beginner Advisor Persona: AI Daily Briefing Generator
========================================================
Synthesizes complex market data into a friendly, actionable daily report for beginners.

Author: AI Advisor
Purpose: Make complex data accessible for beginners
"""

import os
import json
import logging
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BeginnerAdvisor:
    def __init__(self, data_dir: str = '.'):
        self.data_dir = data_dir
        self.output_file = os.path.join(data_dir, 'beginner_briefing.json')
        self.api_key = os.getenv('GOOGLE_API_KEY')
        self.model_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent"

    def _load_json(self, filename):
        path = os.path.join(self.data_dir, filename)
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {}

    def generate_briefing(self):
        logger.info("🚀 Generating beginner-friendly briefing...")
        
        # Load all available data
        macro = self._load_json('macro_analysis.json')
        sector = self._load_json('sector_heatmap.json')
        picks = self._load_json('final_top10_report.json')
        options = self._load_json('options_flow.json')
        
        # Prepare content for AI
        context = {
            "market_regime": macro.get('market_regime', {}).get('type', 'Neutral'),
            "macro_summary": macro.get('ai_analysis', 'N/A'),
            "top_sector": sector.get('sector_performance', {}).get('sectors', [{}])[0].get('name', 'N/A'),
            "top_3_picks": picks.get('top_picks', [])[:3],
            "options_sentiment": options.get('summary', {}).get('bullish_count', 0) > options.get('summary', {}).get('bearish_count', 0) and "Bullish" or "Bearish"
        }

        prompt = f"""
전문의 투자 전략가로서 초보 투자자를 위한 '오늘의 투자 브리핑'을 작성해줘. 
다음 데이터를 종합해서 아주 친절하고 이해하기 쉽게 설명해줘:
1. 시장 상태: {context['market_regime']} ({context['macro_summary'][:200]}...)
2. 가장 뜨거운 섹터: {context['top_sector']}
3. 오늘 주목할 Top 3 종목: {', '.join([p['ticker'] for p in context['top_3_picks']])}
4. 큰손들의 옵션 심리: {context['options_sentiment']}

보고서 구성:
1. 🌡️ 오늘의 시장 온도 (한줄 요약)
2. 🚀 지금 가장 핫한 곳 (섹터/테마 설명)
3. 💎 초보자를 위한 추천 종목 (왜 좋은지 쉽게 설명)
4. 💡 오늘의 투자 한마디 (초보자를 위한 주의사항이나 팁)

최종 출력은 반드시 이 JSON 형식을 지켜줘:
{{
  "today_summary": "...",
  "hot_sector": "...",
  "top_recommendations": [
    {{"ticker": "...", "reason": "..."}}
  ],
  "pro_tip": "...",
  "updated": "{datetime.now().isoformat()}"
}}
"""

        try:
            headers = {'Content-Type': 'application/json'}
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"response_mime_type": "application/json"}
            }
            
            response = requests.post(f"{self.model_url}?key={self.api_key}", headers=headers, json=payload)
            response_json = response.json()
            
            if 'candidates' in response_json:
                result_text = response_json['candidates'][0]['content']['parts'][0]['text']
                briefing = json.loads(result_text)
                
                with open(self.output_file, 'w', encoding='utf-8') as f:
                    json.dump(briefing, f, ensure_ascii=False, indent=2)
                logger.info(f"✅ Beginner briefing saved to {self.output_file}")
                return briefing
        except Exception as e:
            logger.error(f"❌ Failed to generate briefing: {e}")
            return None

if __name__ == "__main__":
    advisor = BeginnerAdvisor()
    advisor.generate_briefing()
