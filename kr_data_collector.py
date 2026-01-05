#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🇰🇷 Korean Stock Daily Prices Collection Script
==============================================
Collects daily price data for KOSPI Top 50 stocks using yfinance
"""

import os
import pandas as pd
import numpy as np
import yfinance as yf
import logging
from datetime import datetime, timedelta
from tqdm import tqdm

# Logging Configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KRDataCollector:
    def __init__(self, data_dir: str = '.'):
        self.data_dir = data_dir
        self.prices_file = os.path.join(data_dir, 'kr_daily_prices.csv')
        self.stocks_list_file = os.path.join(data_dir, 'kr_stocks_list.csv')
        self.start_date = datetime(2020, 1, 1)

    def get_kospi_top50(self):
        # KOSPI Top 50 tickers (approximate for reconstruction)
        # Note: In a production environment, this should be scraped or fetched from a dynamic list.
        # We append .KS for KOSPI and .KQ for KOSDAQ.
        tickers = [
            ('005930.KS', '삼성전자'), ('000660.KS', 'SK하이닉스'), ('373220.KS', 'LG에너지솔루션'),
            ('207940.KS', '삼성바이오로직스'), ('005935.KS', '삼성전자우'), ('068270.KS', '셀트리온'),
            ('005380.KS', '현대차'), ('005490.KS', 'POSCO홀딩스'), ('051910.KS', 'LG화학'),
            ('035420.KS', 'NAVER'), ('000270.KS', '기아'), ('105560.KS', 'KB금융'),
            ('006400.KS', '삼성SDI'), ('035720.KS', '카카오'), ('114800.KS', 'KODEX 200선물인버스2X'),
            ('003670.KS', '포스코푸드'), ('066570.KS', 'LG전자'), ('012330.KS', '현대모비스'),
            ('055550.KS', '신한지주'), ('003550.KS', 'LG'), ('032830.KS', '삼성생명'),
            ('010130.KS', '고려아연'), ('033780.KS', 'KT&G'), ('000810.KS', '삼성화재'),
            ('015760.KS', '한국전력'), ('018260.KS', '삼성에스디에스'), ('329180.KS', 'HD현대중공업'),
            ('009150.KS', '삼성전기'), ('086790.KS', '하나금융지주'), ('011780.KS', '금호석유'),
            ('034220.KS', 'LG디스플레이'), ('010950.KS', 'S-Oil'), ('028260.KS', '삼성물산'),
            ('000100.KS', '유한양행'), ('005830.KS', 'DB손해보험'), ('010620.KS', '현대미포조선'),
            ('000060.KS', '메리츠금융지주'), ('000720.KS', '현대건설'), ('011170.KS', '롯데케미칼'),
            ('024110.KS', '기업은행'), ('036570.KS', '엔씨소프트'), ('004020.KS', '현대제철'),
            ('009540.KS', '한국조선해양'), ('001040.KS', 'CJ'), ('002380.KS', 'KCC'),
            ('003410.KS', '쌍용C&E'), ('003490.KS', '대한항공'), ('005940.KS', 'NH투자증권'),
            ('006800.KS', '미래에셋증권'), ('008770.KS', '호텔신라')
        ]
        return pd.DataFrame(tickers, columns=['ticker', 'name'])

    def download_data(self, tickers_df):
        all_data = []
        logger.info(f"📊 Downloading data for {len(tickers_df)} KR stocks...")
        
        for _, row in tqdm(tickers_df.iterrows(), total=len(tickers_df)):
            try:
                ticker = row['ticker']
                name = row['name']
                hist = yf.download(ticker, start=self.start_date, progress=False)
                
                if hist.empty: continue
                
                hist = hist.reset_index()
                hist['ticker'] = ticker.split('.')[0] # Save as 6-digit code
                hist['name'] = name
                
                # Standardize columns to match US/Previous KR format
                hist = hist.rename(columns={
                    'Date': 'date',
                    'Open': 'open',
                    'High': 'high',
                    'Low': 'low',
                    'Close': 'current_price',
                    'Volume': 'volume'
                })
                
                # yfinance returns multi-index if using multiple tickers or just single column
                # Ensure flatten
                if isinstance(hist.columns, pd.MultiIndex):
                    hist.columns = hist.columns.get_level_values(0)

                hist['change'] = hist['current_price'].diff()
                hist['change_rate'] = hist['current_price'].pct_change() * 100
                
                all_data.append(hist[['ticker', 'name', 'date', 'open', 'high', 'low', 'current_price', 'volume', 'change', 'change_rate']])
            except Exception as e:
                logger.error(f"⚠️ Error downloading {row['ticker']}: {e}")

        if all_data:
            final_df = pd.concat(all_data, ignore_index=True)
            final_df.to_csv(self.prices_file, index=False)
            logger.info(f"✅ Saved {len(final_df)} records to {self.prices_file}")
            
            tickers_df['ticker'] = tickers_df['ticker'].str.split('.').str[0]
            tickers_df.to_csv(self.stocks_list_file, index=False)
            return True
        return False

if __name__ == "__main__":
    collector = KRDataCollector()
    df = collector.get_kospi_top50()
    collector.download_data(df)
