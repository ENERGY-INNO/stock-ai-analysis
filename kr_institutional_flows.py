#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🇰🇷 KR Institutional Flow Analyzer (수급 분석)
=========================================
Analyzes unusual volume and price action as a proxy for institutional flow.
"""

import os
import json
import pandas as pd
import numpy as np
import yfinance as yf
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KRInstitutionalFlowAnalyzer:
    def __init__(self, data_dir: str = '.'):
        self.data_dir = data_dir
        self.output_file = os.path.join(data_dir, 'kr_options_flow.json')
        # Representative major KR stocks
        self.tickers = ['005930.KS', '000660.KS', '035420.KS', '005490.KS', '051910.KS', 
                        '005380.KS', '207940.KS', '068270.KS', '105560.KS', '028260.KS',
                        '128940.KS', '012450.KS', '030200.KS', '017670.KS', '096770.KS',
                        '051900.KS', '000100.KS', '000150.KS', '010140.KS', '259960.KS',
                        '247540.KS', '086520.KS', '293490.KS', '003670.KS', '003540.KS']

    def run(self):
        logger.info("🚀 Starting KR Institutional Flow Analysis...")
        results = []
        try:
            data = yf.download(self.tickers, period='1mo', progress=False)
            for ticker in self.tickers:
                try:
                    pdf = pd.DataFrame({
                        'Close': data['Close'][ticker],
                        'Volume': data['Volume'][ticker]
                    }).dropna()
                    
                    if len(pdf) < 5: continue
                    
                    last_vol = pdf['Volume'].iloc[-1]
                    avg_vol = pdf['Volume'].tail(20).mean()
                    vol_surge = last_vol / avg_vol if avg_vol > 0 else 1
                    
                    price_change = (pdf['Close'].iloc[-1] / pdf['Close'].iloc[-2] - 1) * 100
                    
                    # Logic: Higher vol + positive price change = Strong Institutional Buying
                    score = 50 + (vol_surge - 1) * 20 + price_change * 5
                    score = max(0, min(100, score))
                    
                    if vol_surge > 1.1:
                        results.append({
                            'ticker': ticker.split('.')[0],
                            'name': ticker, # Will be replaced by name in flask
                            'type': 'Institutional' if price_change > 0 else 'Sell-off',
                            'sentiment': 'Bullish' if price_change > 0 else 'Bearish',
                            'score': round(score, 1),
                            'vol_multiplier': round(vol_surge, 1),
                            'timestamp': datetime.now().strftime('%H:%M:%S')
                        })
                except: continue
            
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            logger.info(f"✅ Saved KR institutional flows to {self.output_file}")
            
        except Exception as e:
            logger.error(f"Error: {e}")

if __name__ == "__main__":
    analyzer = KRInstitutionalFlowAnalyzer()
    analyzer.run()
