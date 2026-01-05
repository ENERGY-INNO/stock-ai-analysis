#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🇰🇷 KR Sector Heatmap Collector
==============================
Collects performance data for major KR sector ETFs.
"""

import os
import json
import pandas as pd
import yfinance as yf
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KRSectorHeatmapCollector:
    def __init__(self, data_dir: str = '.'):
        self.data_dir = data_dir
        self.output_file = os.path.join(data_dir, 'kr_sector_heatmap.json')
        
        # KR Sector ETFs (KODEX)
        self.sector_etfs = {
            '091160.KS': {'name': 'Semicon (반도체)'},
            '091170.KS': {'name': 'Auto (자동차)'},
            '305720.KS': {'name': '2nd Battery (2차전지)'},
            '244580.KS': {'name': 'Bio (바이오)'},
            '091180.KS': {'name': 'Banking (은행)'},
            '292150.KS': {'name': 'Games (게임)'},
            '117460.KS': {'name': 'Steel (철강)'},
            '091160?': {'name': 'Chemicals (화학)'} # Need to verify chemical ticker
        }
        # Fixed list
        self.sector_etfs = {
            '091160.KS': '반도체',
            '091170.KS': '자동차',
            '305720.KS': '2차전지',
            '244580.KS': '바이오',
            '091180.KS': '은행',
            '292150.KS': '게임',
            '117460.KS': '철강',
            '102170.KS': '화학'
        }

    def run(self):
        logger.info("🚀 Starting KR Sector Heatmap Collection...")
        tickers = list(self.sector_etfs.keys())
        try:
            data = yf.download(tickers, period='5d', progress=False)
            sectors = []
            for ticker, name in self.sector_etfs.items():
                try:
                    if ticker not in data['Close'].columns: continue
                    prices = data['Close'][ticker].dropna()
                    if len(prices) < 2: continue
                    
                    curr = prices.iloc[-1]
                    prev = prices.iloc[0]
                    change = ((curr / prev) - 1) * 100
                    
                    vol = data['Volume'][ticker].iloc[-1] if 'Volume' in data.columns else 1000000
                    
                    sectors.append({
                        'ticker': ticker,
                        'name': name,
                        'price': round(curr, 2),
                        'change': round(change, 2),
                        'weight': round(curr * vol, 0)
                    })
                except: continue
            
            sectors.sort(key=lambda x: x['change'], reverse=True)
            result = {
                'timestamp': datetime.now().isoformat(),
                'sectors': sectors
            }
            
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            logger.info(f"✅ Saved KR sector heatmap to {self.output_file}")
            
        except Exception as e:
            logger.error(f"Error: {e}")

if __name__ == "__main__":
    collector = KRSectorHeatmapCollector()
    collector.run()
