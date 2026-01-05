#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🇰🇷 Korean Market Quant Analyzer
================================
Calculates technical scores and grades for KR stocks.
"""

import os
import json
import pandas as pd
import numpy as np
import yfinance as yf
import logging
from datetime import datetime, timedelta
from tqdm import tqdm

# Logging Configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KRMarketAnalyzer:
    def __init__(self, data_dir: str = '.'):
        self.data_dir = data_dir
        self.prices_file = os.path.join(data_dir, 'kr_daily_prices.csv')
        self.output_file = os.path.join(data_dir, 'kr_smart_money_picks.json')
        self.benchmark_ticker = "^KS11" # KOSPI Composite

    def load_data(self):
        if not os.path.exists(self.prices_file):
            logger.error(f"❌ {self.prices_file} not found")
            return None
        return pd.read_csv(self.prices_file, parse_dates=['date'])

    def calculate_indicators(self, df):
        # RSI 14
        delta = df['current_price'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss.replace(0, 0.001)
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # MA
        df['ma20'] = df['current_price'].rolling(20).mean()
        df['ma50'] = df['current_price'].rolling(50).mean()
        df['ma200'] = df['current_price'].rolling(200).mean()

        # Bollinger Bands (20, 2)
        std20 = df['current_price'].rolling(20).std()
        df['bb_upper'] = df['ma20'] + (std20 * 2)
        df['bb_lower'] = df['ma20'] - (std20 * 2)
        
        # MACD
        ema12 = df['current_price'].ewm(span=12, adjust=False).mean()
        ema26 = df['current_price'].ewm(span=26, adjust=False).mean()
        df['macd'] = ema12 - ema26
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']

        # 52-Week High/Low (Rolling)
        df['high_52w'] = df['current_price'].rolling(window=250, min_periods=1).max()
        df['low_52w'] = df['current_price'].rolling(window=250, min_periods=1).min()
        
        return df

    def run_analysis(self):
        df_all = self.load_data()
        if df_all is None: return
        
        # Load benchmark for Relative Strength
        logger.info(f"📈 Loading benchmark {self.benchmark_ticker}...")
        bench = yf.download(self.benchmark_ticker, period="6mo", progress=False)
        bench_ret = (bench['Close'].iloc[-1] / bench['Close'].iloc[-21] - 1) * 100 if len(bench) >= 21 else 0

        tickers = df_all['ticker'].unique()
        results = []
        
        logger.info(f"🔍 Analyzing {len(tickers)} stocks...")
        for ticker in tqdm(tickers):
            pdf = df_all[df_all['ticker'] == ticker].sort_values('date').copy()
            if len(pdf) < 50: continue
            
            pdf = self.calculate_indicators(pdf)
            last = pdf.iloc[-1]
            
            # Technical Score
            tech_score = 50
            if 40 <= last['rsi'] <= 60: tech_score += 10
            elif last['rsi'] < 30: tech_score += 15
            
            if last['current_price'] > last['ma20'] > last['ma50']: tech_score += 15
            
            # Relative Strength (20d)
            stock_ret = (last['current_price'] / pdf['current_price'].iloc[-21] - 1) * 100 if len(pdf) >= 21 else 0
            # Ensure bench_ret is a scalar if bench['Close'] is a Series
            b_ret = float(bench_ret.iloc[0]) if isinstance(bench_ret, pd.Series) else float(bench_ret)
            rs_score = 50 + (stock_ret - b_ret) * 2
            
            # Volume Trend
            vol_ma20 = pdf['volume'].rolling(20).mean().iloc[-1]
            vol_score = 50 + (last['volume'] / vol_ma20 - 1) * 10 if vol_ma20 > 0 else 50
            
            # Composite
            composite = float(tech_score * 0.4 + rs_score * 0.3 + vol_score * 0.3)
            composite = max(0.0, min(100.0, composite))
            
            # Grade
            if composite >= 75: grade = "🔥 S급 (즉시 매수)"
            elif composite >= 65: grade = "🌟 A급 (적극 매수)"
            elif composite >= 55: grade = "📈 B급 (매수 고려)"
            elif composite >= 45: grade = "📊 C급 (관망)"
            else: grade = "⚠️ D급 (주의)"

            # Detailed Technicals
            bb_upper = last['bb_upper']
            bb_lower = last['bb_lower']
            bb_width = (bb_upper - bb_lower) / last['ma20'] if last['ma20'] != 0 else 0
            bb_pct_b = (last['current_price'] - bb_lower) / (bb_upper - bb_lower) if (bb_upper - bb_lower) != 0 else 0.5
            
            prox_high = (last['current_price'] / last['high_52w'] - 1) * 100
            prox_low = (last['current_price'] / last['low_52w'] - 1) * 100

            results.append({
                'ticker': str(ticker).zfill(6),
                'name': last['name'],
                'current_price': float(last['current_price']),
                'investment_grade': grade,
                'final_investment_score': round(composite, 1),
                'rsi': round(float(last['rsi']), 1),
                'ma_signal': 'Bullish' if last['current_price'] > last['ma20'] else 'Bearish',
                'macd': round(float(last['macd']), 1),
                'macd_hist': round(float(last['macd_hist']), 1),
                'bb_upper': round(float(bb_upper), 0),
                'bb_pct_b': round(float(bb_pct_b), 2),
                'bb_width': round(float(bb_width), 2),
                'prox_52w_high': round(float(prox_high), 1),
                'prox_52w_low': round(float(prox_low), 1),
                'price_change_20d': round(float(stock_ret / 100), 4),
                'wave_stage': 'N/A', # Placeholder
                'supply_demand_stage': 'Normal',
                'institutional_trend': 'Neutral',
                'current_date': last['date'].strftime('%Y-%m-%d'),
                'updated': datetime.now().strftime('%Y-%m-%d')
            })

        results.sort(key=lambda x: x['final_investment_score'], reverse=True)
        
        output = {
            'top_picks': results[:20],
            'market_indices': [], # Placeholder
            'updated': datetime.now().isoformat()
        }
        
        # Also save as CSV for system compatibility
        pd.DataFrame(results).to_csv(os.path.join(self.data_dir, 'wave_transition_analysis_results.csv'), index=False)
        
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
            
        logger.info(f"✅ Saved analysis results to {self.output_file}")
        return results

if __name__ == "__main__":
    analyzer = KRMarketAnalyzer()
    analyzer.run_analysis()
