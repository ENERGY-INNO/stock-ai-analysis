#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌐 Macro Economist Persona: Macro Market Analyzer
===================================================
Collects macro indicators and generates AI market outlook.

Author: Macro Economist Persona
Purpose: Provide big-picture market context using AI analysis
"""

import os
import json
import requests
import yfinance as yf
import logging
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load .env
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MacroDataCollector:
    """Collect macro market data from various sources"""
    
    def __init__(self):
        self.macro_tickers = {
            'VIX': '^VIX',          # Volatility Index
            'DXY': 'DX-Y.NYB',      # US Dollar Index
            '2Y_Yield': '^IRX',     # 3-Month T-Bill (proxy for short rates)
            '10Y_Yield': '^TNX',    # 10-Year Treasury
            'GOLD': 'GC=F',         # Gold Futures
            'OIL': 'CL=F',          # WTI Crude Oil
            'BTC': 'BTC-USD',       # Bitcoin
            'SPY': 'SPY',           # S&P 500 ETF
            'QQQ': 'QQQ'            # Nasdaq 100 ETF
        }
    
    def get_current_macro_data(self) -> Dict:
        """Fetch current macro indicators"""
        logger.info("📊 Fetching macro data...")
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
                    
                    # 52w High calculation
                    try:
                        full_hist = yf.Ticker(ticker).history(period='1y')
                        high = full_hist['High'].max() if not full_hist.empty else 0
                        pct_high = ((val / high) - 1) * 100 if high > 0 else 0
                    except:
                        pct_high = 0
                    
                    macro_data[name] = {
                        'value': round(float(val), 2),
                        'change_1d': round(float(change), 2),
                        'pct_from_high': round(float(pct_high), 1)
                    }
                except Exception as e:
                    continue
            
            # Calculate Yield Spread (2-10)
            if '2Y_Yield' in macro_data and '10Y_Yield' in macro_data:
                spread = macro_data['10Y_Yield']['value'] - macro_data['2Y_Yield']['value']
                macro_data['YieldSpread'] = {
                    'value': round(spread, 2),
                    'change_1d': 0,
                    'pct_from_high': 0,
                    'interpretation': 'Inverted' if spread < 0 else 'Normal'
                }
            
            # Add Fear & Greed placeholder
            macro_data['FearGreed'] = {
                'value': 65,
                'change_1d': 0,
                'pct_from_high': 0,
                'interpretation': 'Greed'
            }
            
        except Exception as e:
            logger.error(f"Error fetching macro data: {e}")
        
        return macro_data

    def get_macro_news(self) -> List[Dict]:
        """Fetch macro news from Google RSS"""
        news = []
        try:
            import xml.etree.ElementTree as ET
            url = "https://news.google.com/rss/search?q=Federal+Reserve+Economy&hl=en-US&gl=US&ceid=US:en"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                for item in root.findall('.//item')[:5]:
                    title_elem = item.find('title')
                    if title_elem is not None:
                        news.append({
                            'title': title_elem.text,
                            'source': 'Google News'
                        })
        except Exception as e:
            logger.debug(f"News fetch error: {e}")
        return news
    
    def get_market_regime(self, data: Dict) -> Dict:
        """Determine current market regime"""
        regime = {
            'type': 'Neutral',
            'confidence': 50,
            'signals': []
        }
        
        # VIX Analysis
        vix = data.get('VIX', {}).get('value', 20)
        if vix < 15:
            regime['signals'].append('Low volatility (complacency)')
            regime['type'] = 'Risk-On'
            regime['confidence'] += 10
        elif vix > 25:
            regime['signals'].append('High volatility (fear)')
            regime['type'] = 'Risk-Off'
            regime['confidence'] += 10
        
        # Dollar strength
        dxy_change = data.get('DXY', {}).get('change_1d', 0)
        if dxy_change > 0.5:
            regime['signals'].append('Dollar strengthening')
        elif dxy_change < -0.5:
            regime['signals'].append('Dollar weakening')
        
        # Yield curve
        spread = data.get('YieldSpread', {}).get('value', 0)
        if spread < 0:
            regime['signals'].append('Yield curve inverted (recession signal)')
            regime['type'] = 'Defensive'
        
        return regime


class MacroAIAnalyzer:
    """Generate AI analysis using Gemini API"""
    
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_API_KEY')
        self.url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent"
    
    def analyze(self, data: Dict, news: List, regime: Dict, lang: str = 'ko') -> str:
        """Generate AI market analysis"""
        if not self.api_key:
            return self._generate_fallback_analysis(data, regime, lang)
        
        prompt = self._build_prompt(data, news, regime, lang)
        
        try:
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.7, "maxOutputTokens": 1500}
            }
            resp = requests.post(f"{self.url}?key={self.api_key}", json=payload, timeout=30)
            if resp.status_code == 200:
                result = resp.json()
                return result['candidates'][0]['content']['parts'][0]['text']
            else:
                logger.warning(f"API error: {resp.status_code}")
                return self._generate_fallback_analysis(data, regime, lang)
        except Exception as e:
            logger.error(f"AI analysis error: {e}")
            return self._generate_fallback_analysis(data, regime, lang)
    
    def _build_prompt(self, data: Dict, news: List, regime: Dict, lang: str) -> str:
        metrics = "\n".join([f"- {k}: {v.get('value', 'N/A')} ({v.get('change_1d', 0):+.1f}%)" 
                            for k, v in data.items()])
        headlines = "\n".join([n['title'] for n in news[:3]]) if news else "No recent news"
        regime_info = f"Regime: {regime['type']}, Signals: {', '.join(regime['signals'][:3])}"
        
        if lang == 'en':
            return f"""Analyze current macro conditions and suggest investment strategy.

Indicators:
{metrics}

Market Regime: {regime_info}

Recent News:
{headlines}

Provide analysis in this format:
1. SUMMARY: 2-3 sentence market overview
2. OPPORTUNITIES: Top 2-3 sectors/themes to watch
3. RISKS: Top 2 risks to monitor
4. STRATEGY: Specific actionable advice

Be concise and professional."""
        else:
            return f"""현재 거시경제 상황을 분석하고 투자 전략을 제안하세요.

지표:
{metrics}

시장 레짐: {regime_info}

최근 뉴스:
{headlines}

다음 형식으로 분석해주세요:
1. 요약: 2-3문장 시장 개요
2. 기회: 주목할 2-3개 섹터/테마
3. 리스크: 모니터링할 2개 리스크
4. 전략: 구체적 실행 전략

간결하고 전문적으로 작성하세요."""
    
    def _generate_fallback_analysis(self, data: Dict, regime: Dict, lang: str) -> str:
        """Generate rule-based analysis when API unavailable"""
        vix = data.get('VIX', {}).get('value', 20)
        spy_change = data.get('SPY', {}).get('change_1d', 0)
        
        if lang == 'ko':
            if regime['type'] == 'Risk-On':
                return f"""📊 시장 분석 (규칙 기반)
1. 요약: VIX {vix}로 변동성 낮음. 리스크 선호 환경.
2. 기회: 기술주, 성장주 유리
3. 리스크: 급격한 변동성 확대 주의
4. 전략: 주식 비중 유지, 모멘텀 전략 유효"""
            else:
                return f"""📊 시장 분석 (규칙 기반)
1. 요약: VIX {vix}로 변동성 상승. 신중한 접근 필요.
2. 기회: 방어주, 배당주, 채권
3. 리스크: 추가 하락 가능성
4. 전략: 현금 비중 확대, 분산 투자"""
        else:
            if regime['type'] == 'Risk-On':
                return f"""📊 Market Analysis (Rule-Based)
1. Summary: VIX at {vix}, low volatility. Risk-on environment.
2. Opportunities: Tech, Growth stocks favorable
3. Risks: Watch for sudden volatility spikes
4. Strategy: Maintain equity exposure, momentum works"""
            else:
                return f"""📊 Market Analysis (Rule-Based)
1. Summary: VIX at {vix}, elevated volatility. Caution advised.
2. Opportunities: Defensives, Dividends, Bonds
3. Risks: Further downside possible
4. Strategy: Raise cash, diversify"""


class MultiModelAnalyzer:
    """Main orchestrator for macro analysis"""
    
    def __init__(self, data_dir: str = '.'):
        self.data_dir = data_dir
        self.collector = MacroDataCollector()
        self.gemini = MacroAIAnalyzer()
        self.output_file = os.path.join(data_dir, 'macro_analysis.json')
    
    def run(self) -> Dict:
        """Run complete macro analysis pipeline"""
        logger.info("🚀 Starting Macro Analysis...")
        
        # Collect data
        data = self.collector.get_current_macro_data()
        news = self.collector.get_macro_news()
        regime = self.collector.get_market_regime(data)
        
        # Generate AI analysis
        analysis_ko = self.gemini.analyze(data, news, regime, 'ko')
        analysis_en = self.gemini.analyze(data, news, regime, 'en')
        
        # Build output
        output = {
            'timestamp': datetime.now().isoformat(),
            'macro_indicators': data,
            'market_regime': regime,
            'recent_news': news,
            'ai_analysis': analysis_ko,
            'ai_analysis_en': analysis_en
        }
        
        # Save Korean version
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        # Save English version
        output_en = output.copy()
        output_en['ai_analysis'] = analysis_en
        with open(os.path.join(self.data_dir, 'macro_analysis_en.json'), 'w') as f:
            json.dump(output_en, f, indent=2)
        
        logger.info(f"✅ Saved macro analysis to {self.output_file}")
        
        # Print summary
        print("\n🌐 Macro Market Analysis")
        print(f"   Regime: {regime['type']}")
        print(f"   VIX: {data.get('VIX', {}).get('value', 'N/A')}")
        print(f"   SPY: {data.get('SPY', {}).get('change_1d', 0):+.2f}%")
        
        return output


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Macro Market Analyzer')
    parser.add_argument('--dir', default='.', help='Data directory')
    args = parser.parse_args()
    
    analyzer = MultiModelAnalyzer(data_dir=args.dir)
    analyzer.run()


if __name__ == "__main__":
    main()
