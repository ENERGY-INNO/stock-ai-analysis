#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🇰🇷 KR ETF Flow Analyzer
=======================
Analyzes money flows across major KR ETFs via volume/price proxies.
"""

import os
import json
import pandas as pd
import numpy as np
import yfinance as yf
import logging
from datetime import datetime, timedelta
from tqdm import tqdm

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KRETFFlowAnalyzer:
    def __init__(self, data_dir: str = '.'):
        self.data_dir = data_dir
        self.output_file = os.path.join(data_dir, 'kr_etf_flows.json')
        self.etf_list = {
            '069500.KS': {
                'name': 'KODEX 200',
                'category': 'Broad Market',
                'description_ko': 'KOSPI 200 지수를 추종하는 대표적인 ETF입니다. 한국 시장 전체에 분산 투자하고 싶을 때 적합합니다.',
                'description_en': 'The flagship ETF tracking the KOSPI 200 index. Ideal for broad Korean market exposure.'
            },
            '122630.KS': {
                'name': 'KODEX Leverage',
                'category': 'Long Bias',
                'description_ko': 'KOSPI 200 지수의 일일 수익률을 2배로 추종합니다. 상승장에서 고수익을 노리는 공격적 투자자에게 적합합니다.',
                'description_en': 'Tracks 2x daily returns of KOSPI 200. For aggressive investors seeking amplified gains in bull markets.'
            },
            '114800.KS': {
                'name': 'KODEX Inverse',
                'category': 'Short Bias',
                'description_ko': 'KOSPI 200 지수의 반대 방향(-1배)으로 움직입니다. 하락장 헤지 또는 숏 포지션에 활용됩니다.',
                'description_en': 'Moves inversely (-1x) to KOSPI 200. Used for hedging or short positions during market downturns.'
            },
            '252670.KS': {
                'name': 'KODEX 200 Inv 2X',
                'category': 'Short Bias',
                'description_ko': 'KOSPI 200 지수의 일일 수익률을 -2배로 추종하는 인버스 레버리지 ETF입니다. 급락장에서 고수익을 노릴 수 있습니다.',
                'description_en': 'Inverse leveraged ETF tracking -2x daily returns of KOSPI 200. High-risk tool for profiting from sharp declines.'
            },
            '153130.KS': {
                'name': 'KODEX Short Bond',
                'category': 'Safe Haven',
                'description_ko': '단기 국채에 투자하는 안전자산 ETF입니다. 시장 변동성이 클 때 현금 대안으로 활용됩니다.',
                'description_en': 'Safe-haven ETF investing in short-term government bonds. Used as a cash alternative during market volatility.'
            },
            '132030.KS': {
                'name': 'KODEX Gold Futures',
                'category': 'Commodity',
                'description_ko': '금 선물에 투자하는 상품 ETF입니다. 인플레이션 헤지 및 안전자산 분산 투자에 적합합니다.',
                'description_en': 'Commodity ETF investing in gold futures. Suitable for inflation hedging and safe-haven diversification.'
            }
        }

    def calculate_score(self, df):
        if len(df) < 20: return 50
        # Simple OBV based flow proxy
        closes = df['Close']
        vols = df['Volume']
        obv = [0]
        for i in range(1, len(closes)):
            if closes.iloc[i] > closes.iloc[i-1]: obv.append(obv[-1] + vols.iloc[i])
            elif closes.iloc[i] < closes.iloc[i-1]: obv.append(obv[-1] - vols.iloc[i])
            else: obv.append(obv[-1])
        
        obv_change = (obv[-1] - obv[-10]) / (abs(obv[-10]) + 1) * 100
        ret_10d = (closes.iloc[-1] / closes.iloc[-10] - 1) * 100
        score = 50 + obv_change * 2 + ret_10d * 3
        return max(0, min(100, score))

    def run(self):
        logger.info("🚀 Starting KR ETF Flow Analysis...")
        results = []
        tickers = list(self.etf_list.keys())
        try:
            data = yf.download(tickers, period='1mo', progress=False)
            for ticker, info in self.etf_list.items():
                try:
                    pdf = pd.DataFrame({
                        'Close': data['Close'][ticker],
                        'Volume': data['Volume'][ticker]
                    }).dropna()
                    score = self.calculate_score(pdf)
                    results.append({
                        'ticker': ticker,
                        'name': info['name'],
                        'category': info['category'],
                        'description_ko': info.get('description_ko', ''),
                        'description_en': info.get('description_en', ''),
                        'flow_score': round(score, 1)
                    })
                except: continue
            
            top_inflows = sorted(results, key=lambda x: x['flow_score'], reverse=True)[:5]
            top_outflows = sorted(results, key=lambda x: x['flow_score'])[:5]
            
            # Simple sentiment
            broad_score = next((r['flow_score'] for r in results if r['name'] == 'KODEX 200'), 50)
            
            output = {
                'timestamp': datetime.now().isoformat(),
                'market_sentiment_score': broad_score,
                'top_inflows': top_inflows,
                'top_outflows': top_outflows,
                'ai_analysis': f"KOSPI 200 지표 기준 현재 시장 심리 점수는 {broad_score}점입니다."
            }
            
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(output, f, ensure_ascii=False, indent=2)
            logger.info(f"✅ Saved KR ETF flows to {self.output_file}")
            
        except Exception as e:
            logger.error(f"Error: {e}")

if __name__ == "__main__":
    analyzer = KRETFFlowAnalyzer()
    analyzer.run()
