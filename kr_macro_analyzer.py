#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🇰🇷 KR Macro Market Analyzer
===========================
Collects KR macro indicators and generates AI market outlook.
"""

import os
import json
import requests
import yfinance as yf
import logging
from datetime import datetime
from typing import Dict, List
from dotenv import load_dotenv

# Load .env
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KRMacroCollector:
    def __init__(self):
        self.macro_tickers = {
            'KOSPI': '^KS11',
            'KOSDAQ': '^KQ11',
            'USD_KRW': 'KRW=X',
            'SAMSUNG': '005930.KS'
        }
    
    def get_current_macro_data(self) -> Dict:
        logger.info("📊 Fetching KR macro data...")
        macro_data = {}
        try:
            tickers = list(self.macro_tickers.values())
            data = yf.download(tickers, period='5d', progress=False)
            
            for name, ticker in self.macro_tickers.items():
                try:
                    if ticker not in data['Close'].columns:
                        continue
                    hist = data['Close'][ticker].dropna()
                    if len(hist) < 2:
                        continue
                    
                    val = hist.iloc[-1]
                    prev = hist.iloc[-2]
                    change = ((val / prev) - 1) * 100
                    
                    macro_data[name] = {
                        'value': round(float(val), 2),
                        'change_1d': round(float(change), 2)
                    }
                except: continue
        except Exception as e:
            logger.error(f"Error fetching macro data: {e}")
        return macro_data

class KRMacroAIAnalyzer:
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_API_KEY')
        self.url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent"
    
    def analyze(self, data: Dict, lang: str = 'ko') -> str:
        if not self.api_key: return "API Key missing."
        
        metrics = "\n".join([f"- {k}: {v.get('value', 'N/A')} ({v.get('change_1d', 0):+.1f}%)" for k, v in data.items()])
        
        prompt = f"""한국 거시경제 및 주식시장 상황을 분석하고 투자 전략을 제안하세요. (KOSPI/KOSDAQ/환율 등 기준)
        
지표:
{metrics}

다음 형식으로 분석해주세요({'Korean' if lang=='ko' else 'English'}):
1. 요약: 2-3문장 시장 개요
2. 기회: 주목할 2-3개 섹터/테마
3. 리스크: 모니터링할 2개 리스크
4. 전략: 구체적 실행 전략
"""
        try:
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            resp = requests.post(f"{self.url}?key={self.api_key}", json=payload, timeout=30)
            if resp.status_code == 200:
                return resp.json()['candidates'][0]['content']['parts'][0]['text']
        except: pass
        return "AI analysis failed."

def main():
    collector = KRMacroCollector()
    analyzer = KRMacroAIAnalyzer()
    data = collector.get_current_macro_data()
    analysis_ko = analyzer.analyze(data, 'ko')
    analysis_en = analyzer.analyze(data, 'en')
    
    output = {
        'timestamp': datetime.now().isoformat(),
        'macro_indicators': data,
        'ai_analysis': analysis_ko,
        'ai_analysis_en': analysis_en
    }
    
    output_path = 'kr_macro_analysis.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved KR macro analysis to {output_path}")

if __name__ == "__main__":
    main()
