#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
👔 Insider Analyst Persona: Insider Trading Tracker
=====================================================
Tracks insider (CEO, CFO, Directors) buying/selling activity.

Author: Insider Analyst Persona
Purpose: Follow the insiders - they know their company best
"""

import os
import json
import logging
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class InsiderTracker:
    """
    인사이더 매매 추적
    
    분석 포인트:
    - 내부자 매수 = 강한 긍정 신호 (자기 돈으로 매수)
    - 내부자 매도 = 약한 부정 신호 (다양한 이유 가능)
    - 클러스터 매수 = 여러 내부자가 동시 매수
    """
    
    def __init__(self, data_dir: str = '.'):
        self.data_dir = data_dir
        self.output_file = os.path.join(data_dir, 'insider_moves.json')
    
    def get_insider_activity(self, ticker: str) -> Dict:
        """Get recent insider transactions"""
        try:
            stock = yf.Ticker(ticker)
            
            # Try to get insider transactions
            try:
                df = stock.insider_transactions
            except:
                df = None
            
            if df is None or df.empty:
                return {'ticker': ticker, 'transactions': [], 'score': 0}
            
            # Filter transactions in last 6 months
            cutoff = datetime.now() - timedelta(days=180)
            
            transactions = []
            buys = 0
            sells = 0
            buy_value = 0
            sell_value = 0
            
            for idx, row in df.iterrows():
                try:
                    # Parse date
                    if isinstance(idx, pd.Timestamp):
                        date = idx
                    else:
                        date = pd.to_datetime(idx)
                    
                    if date < cutoff:
                        continue
                    
                    # Determine transaction type
                    text = str(row.get('Text', '') or row.get('Transaction', '')).lower()
                    shares = int(row.get('Shares', 0) or 0)
                    value = float(row.get('Value', 0) or 0)
                    insider = str(row.get('Insider', '') or row.get('Name', 'Unknown'))
                    
                    if 'purchase' in text or 'buy' in text or 'acquisition' in text:
                        tx_type = 'Buy'
                        buys += 1
                        buy_value += value
                    elif 'sale' in text or 'sell' in text or 'disposition' in text:
                        tx_type = 'Sell'
                        sells += 1
                        sell_value += value
                    else:
                        tx_type = 'Other'
                    
                    transactions.append({
                        'date': str(date.date()),
                        'insider': insider[:30],
                        'type': tx_type,
                        'shares': shares,
                        'value': value
                    })
                    
                except Exception as e:
                    continue
            
            # Calculate insider score (0-100)
            score = 50
            
            # Buy/Sell ratio
            if buys > sells * 2:
                score += 30
            elif buys > sells:
                score += 15
            elif sells > buys * 2:
                score -= 20
            elif sells > buys:
                score -= 10
            
            # Value-weighted
            if buy_value > 1000000:
                score += 15
            elif buy_value > 100000:
                score += 10
            
            if sell_value > 10000000:
                score -= 15
            
            score = max(0, min(100, score))
            
            # Sentiment
            if score >= 70:
                sentiment = "Strong Insider Buying"
            elif score >= 55:
                sentiment = "Insider Buying"
            elif score >= 45:
                sentiment = "Neutral"
            elif score >= 30:
                sentiment = "Insider Selling"
            else:
                sentiment = "Strong Insider Selling"
            
            return {
                'ticker': ticker,
                'summary': {
                    'total_transactions': len(transactions),
                    'buys': buys,
                    'sells': sells,
                    'buy_value': round(buy_value, 0),
                    'sell_value': round(sell_value, 0),
                    'score': score,
                    'sentiment': sentiment
                },
                'transactions': transactions[:10]  # Top 10 recent
            }
            
        except Exception as e:
            return {'ticker': ticker, 'error': str(e), 'transactions': [], 'score': 50}
    
    def analyze_tickers(self, tickers: List[str]) -> Dict:
        """Analyze multiple tickers"""
        results = {}
        
        for ticker in tickers:
            logger.info(f"👔 Analyzing insider activity for {ticker}...")
            activity = self.get_insider_activity(ticker)
            if activity.get('summary', {}).get('total_transactions', 0) > 0:
                results[ticker] = activity
        
        return results
    
    def run(self, tickers: List[str] = None) -> Dict:
        """Run insider tracking"""
        logger.info("🚀 Starting Insider Tracking...")
        
        # Default tickers if none provided
        if tickers is None:
            # Load from stock list if exists
            stocks_file = os.path.join(self.data_dir, 'us_stocks_list.csv')
            if os.path.exists(stocks_file):
                stocks_df = pd.read_csv(stocks_file)
                tickers = stocks_df['ticker'].head(50).tolist()
            else:
                tickers = ['AAPL', 'NVDA', 'TSLA', 'MSFT', 'AMZN', 'META', 'GOOGL',
                          'JPM', 'BAC', 'WFC', 'V', 'MA', 'UNH', 'JNJ', 'PFE']
        
        details = self.analyze_tickers(tickers)
        
        # Sort by score
        sorted_tickers = sorted(
            details.items(), 
            key=lambda x: x[1].get('summary', {}).get('score', 0), 
            reverse=True
        )
        
        # Top buyers
        top_buyers = [
            {'ticker': t, 'score': d.get('summary', {}).get('score', 0), 
             'buys': d.get('summary', {}).get('buys', 0)}
            for t, d in sorted_tickers 
            if d.get('summary', {}).get('score', 0) >= 55
        ][:10]
        
        output = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_analyzed': len(tickers),
                'with_activity': len(details),
                'top_buyers': top_buyers
            },
            'details': {t: d for t, d in sorted_tickers}
        }
        
        # Save to file
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ Saved to {self.output_file}")
        
        # Print summary
        print("\n👔 Insider Activity Summary:")
        print(f"   Analyzed: {len(tickers)}, With Activity: {len(details)}")
        
        if top_buyers:
            print("\n📈 Top Insider Buying:")
            for b in top_buyers[:5]:
                print(f"   {b['ticker']:6s}: Score {b['score']}, {b['buys']} buys")
        
        return output


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Insider Trading Tracker')
    parser.add_argument('--dir', default='.', help='Data directory')
    parser.add_argument('--tickers', nargs='+', help='Specific tickers to analyze')
    args = parser.parse_args()
    
    tracker = InsiderTracker(data_dir=args.dir)
    tracker.run(tickers=args.tickers)


if __name__ == "__main__":
    main()
