#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🤖 AI Research Analyst Persona: Stock Summary Generator
=========================================================
Generates AI-powered investment summaries for top stocks.

Author: AI Research Analyst Persona
Purpose: Provide concise AI analysis for each recommended stock
"""

import os
import json
import logging
import time
import requests
import pandas as pd
from datetime import datetime
from typing import Dict, List
from tqdm import tqdm
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class NewsCollector:
    """Collect recent news for stocks"""
    
    def get_news(self, ticker: str, max_items: int = 3) -> List[Dict]:
        """Fetch news from Google RSS"""
        news = []
        try:
            import xml.etree.ElementTree as ET
            url = f"https://news.google.com/rss/search?q={ticker}+stock&hl=en-US&gl=US&ceid=US:en"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                for item in root.findall('.//item')[:max_items]:
                    title_elem = item.find('title')
                    pub_elem = item.find('pubDate')
                    if title_elem is not None:
                        news.append({
                            'title': title_elem.text,
                            'published': pub_elem.text if pub_elem is not None else ''
                        })
        except Exception as e:
            logger.debug(f"News fetch error for {ticker}: {e}")
        return news


class GeminiGenerator:
    """Generate AI summaries using Gemini API"""
    
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_API_KEY')
        self.url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent"
    
    def generate(self, ticker: str, data: Dict, news: List, lang: str = 'ko') -> str:
        """Generate investment summary"""
        if not self.api_key:
            return self._generate_fallback(ticker, data, lang)
        
        prompt = self._build_prompt(ticker, data, news, lang)
        
        try:
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.7, "maxOutputTokens": 2048}
            }
            resp = requests.post(f"{self.url}?key={self.api_key}", json=payload, timeout=30)
            if resp.status_code == 200:
                result = resp.json()
                candidate = result['candidates'][0]
                finish_reason = candidate.get('finishReason', 'UNKNOWN')
                if finish_reason != 'STOP':
                    logger.warning(f"⚠️ Generation stopped due to {finish_reason} for {ticker}")
                
                return candidate['content']['parts'][0]['text']
            else:
                logger.error(f"API Error {resp.status_code}: {resp.text}")
                return self._generate_fallback(ticker, data, lang)
        except Exception as e:
            logger.debug(f"AI generation error for {ticker}: {e}")
            return self._generate_fallback(ticker, data, lang)
    
    def _build_prompt(self, ticker: str, data: Dict, news: List, lang: str) -> str:
        news_txt = "\n".join([n['title'] for n in news[:3]]) if news else "No recent news"
        
        score_info = f"""
Score: {data.get('composite_score', 'N/A')}/100
Grade: {data.get('grade', 'N/A')}
Technical: {data.get('tech_score', 'N/A')}, Fundamental: {data.get('fund_score', 'N/A')}

[Deep Technicals]
RSI: {data.get('rsi', 'N/A')}
MA Signal: {data.get('ma_signal', 'N/A')}
MACD Hist: {data.get('macd_hist', 'N/A')} (Positive=Bullish, Negative=Bearish)
Bollinger %B: {data.get('bb_pct_b', 'N/A')} (Over 1.0=Overbought, Under 0.0=Oversold)
BB Width: {data.get('bb_width', 'N/A')} (Volatility)
Prox 52W High: {data.get('prox_52w_high', 'N/A')}%
"""
        
        if lang == 'ko':
            return f"""종목: {ticker} ({data.get('name', ticker)})

분석 데이터:
{score_info}

최근 뉴스:
{news_txt}

요청: 3-4문장으로 투자 의견을 요약하세요.
- 수급과 기술적 상황 (RSI, 볼린저밴드 위치, MACD 추세, 지지/저항의 복합적 해석 필수)
- 펀더멘털 및 밸류에이션
- 투자 전략 (매수/관망/회피)
이모지 없이 전문적으로 작성. 지표들을 단순 나열하지 말고, 서로의 관계를 분석하여 인사이트를 제공하세요."""
        else:
            return f"""Stock: {ticker} ({data.get('name', ticker)})

Analysis Data:
{score_info}

Recent News:
{news_txt}

Request: Provide a 3-4 sentence investment summary covering:
- Supply/demand and technical composite analysis (Interpret RSI, Bollinger Bands, MACD, and S/R together)
- Fundamentals and valuation
- Investment strategy (Buy/Hold/Avoid)
No emojis, professional tone. Synthesize indicators rather than listing them."""
    
    def _generate_fallback(self, ticker: str, data: Dict, lang: str) -> str:
        """Generate rule-based summary when API unavailable"""
        score = data.get('composite_score', 50)
        grade = data.get('grade', 'C급')
        rsi = data.get('rsi', 50)
        
        if lang == 'ko':
            if score >= 70:
                return f"{ticker}는 종합점수 {score}점으로 {grade}에 해당합니다. 수급과 기술적 지표가 모두 긍정적이며, RSI {rsi}로 과매수 구간이 아닙니다. 현재 가격대에서 분할 매수 진입을 고려할 수 있습니다."
            elif score >= 50:
                return f"{ticker}는 종합점수 {score}점으로 {grade}에 해당합니다. 기술적 지표는 중립적이며, 추가적인 확인 후 진입을 권장합니다. RSI {rsi} 수준입니다."
            else:
                return f"{ticker}는 종합점수 {score}점으로 {grade}에 해당합니다. 수급이 약화되고 있어 신중한 접근이 필요합니다. 현재는 관망을 권장합니다."
        else:
            if score >= 70:
                return f"{ticker} scores {score}/100, rated {grade}. Both supply-demand and technicals are positive with RSI at {rsi}. Consider accumulating at current levels."
            elif score >= 50:
                return f"{ticker} scores {score}/100, rated {grade}. Technicals are neutral. Wait for confirmation before entry. RSI at {rsi}."
            else:
                return f"{ticker} scores {score}/100, rated {grade}. Supply-demand weakening. Caution advised, consider avoiding for now."


class AIStockAnalyzer:
    """Main AI stock analysis orchestrator"""
    
    def __init__(self, data_dir: str = '.'):
        self.data_dir = data_dir
        self.output_file = os.path.join(data_dir, 'ai_summaries.json')
        self.generator = GeminiGenerator()
        self.news_collector = NewsCollector()
    
    def run(self, top_n: int = 20) -> Dict:
        """Generate AI summaries for top stocks"""
        logger.info("🚀 Starting AI Summary Generation...")
        
        # Load smart money picks
        csv_path = os.path.join(self.data_dir, 'smart_money_picks_v2.csv')
        if not os.path.exists(csv_path):
            logger.warning(f"⚠️ {csv_path} not found. Run smart_money_screener_v2.py first.")
            return {}
        
        df = pd.read_csv(csv_path).head(top_n)
        logger.info(f"📊 Generating summaries for {len(df)} stocks")
        
        # Load existing summaries
        results = {}
        if os.path.exists(self.output_file):
            try:
                with open(self.output_file, 'r', encoding='utf-8') as f:
                    results = json.load(f)
            except:
                results = {}
        
        # Generate new summaries
        for _, row in tqdm(df.iterrows(), total=len(df), desc="Generating AI summaries"):
            ticker = row['ticker']
            
            # Skip if already exists (within 24 hours)
            if ticker in results:
                existing_time = results[ticker].get('updated', '')
                if existing_time:
                    try:
                        dt = datetime.fromisoformat(existing_time.replace('Z', '+00:00'))
                        if (datetime.now() - dt.replace(tzinfo=None)).days < 1:
                            continue
                    except:
                        pass
            
            # Collect news
            news = self.news_collector.get_news(ticker)
            
            # Generate summaries
            data = row.to_dict()
            summary_ko = self.generator.generate(ticker, data, news, 'ko')
            summary_en = self.generator.generate(ticker, data, news, 'en')
            
            results[ticker] = {
                'name': row.get('name', ticker),
                'summary': summary_ko,
                'summary_ko': summary_ko,
                'summary_en': summary_en,
                'composite_score': row.get('composite_score', 0),
                'grade': row.get('grade', 'N/A'),
                'updated': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
            }
            
            time.sleep(0.5)  # Rate limiting
        
        # Save results
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Saved {len(results)} summaries to {self.output_file}")
        
        # Print sample
        print("\n🤖 AI Summary Samples:")
        for ticker in list(results.keys())[:3]:
            print(f"\n{ticker}:")
            print(f"   {results[ticker].get('summary', '')[:100]}...")
        
        return results


def main():
    import argparse
    parser = argparse.ArgumentParser(description='AI Stock Summary Generator')
    parser.add_argument('--dir', default='.', help='Data directory')
    parser.add_argument('--top', type=int, default=20, help='Number of stocks to analyze')
    args = parser.parse_args()
    
    analyzer = AIStockAnalyzer(data_dir=args.dir)
    analyzer.run(top_n=args.top)


if __name__ == "__main__":
    main()
