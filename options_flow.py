#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎲 Options Strategist Persona: Options Flow Analyzer
======================================================
Analyzes options volume to detect large directional bets.

Author: Options Strategist Persona
Purpose: Track smart money through options activity
"""

import os
import json
import logging
import yfinance as yf
from datetime import datetime
from typing import Dict, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class OptionsFlowAnalyzer:
    """
    옵션 거래량 분석으로 대형 투자자 방향성 베팅 추적
    
    분석 지표:
    - Put/Call Ratio: < 0.7 = Bullish, > 1.0 = Bearish
    - Unusual Activity: 평균 대비 3배 이상 거래량
    - Open Interest: 미결제약정 변화
    """
    
    def __init__(self, data_dir: str = '.'):
        self.data_dir = data_dir
        self.output_file = os.path.join(data_dir, 'options_flow.json')
        
        # Most actively traded options
        self.watchlist = [
            'AAPL', 'NVDA', 'TSLA', 'MSFT', 'AMZN', 
            'META', 'GOOGL', 'SPY', 'QQQ', 'AMD',
            'NFLX', 'BA', 'DIS', 'COIN', 'PLTR'
        ]
    
    def get_options_summary(self, ticker: str) -> Dict:
        """Get options summary for a single ticker"""
        try:
            stock = yf.Ticker(ticker)
            exps = stock.options
            
            if not exps:
                return {'ticker': ticker, 'error': 'No options available'}
            
            # Get nearest expiration
            opt = stock.option_chain(exps[0])
            calls, puts = opt.calls, opt.puts
            
            # Volume and Open Interest
            call_vol = calls['volume'].sum() if 'volume' in calls.columns else 0
            put_vol = puts['volume'].sum() if 'volume' in puts.columns else 0
            call_oi = calls['openInterest'].sum() if 'openInterest' in calls.columns else 0
            put_oi = puts['openInterest'].sum() if 'openInterest' in puts.columns else 0
            
            # Put/Call Ratio
            pc_ratio = put_vol / call_vol if call_vol > 0 else 0
            
            # Sentiment
            if pc_ratio < 0.5:
                sentiment = "Very Bullish"
            elif pc_ratio < 0.7:
                sentiment = "Bullish"
            elif pc_ratio < 1.0:
                sentiment = "Neutral"
            elif pc_ratio < 1.3:
                sentiment = "Bearish"
            else:
                sentiment = "Very Bearish"
            
            # Unusual activity detection
            avg_call_vol = calls['volume'].mean() if 'volume' in calls.columns else 0
            avg_put_vol = puts['volume'].mean() if 'volume' in puts.columns else 0
            
            unusual_calls = calls[calls['volume'] > avg_call_vol * 3] if avg_call_vol > 0 else pd.DataFrame()
            unusual_puts = puts[puts['volume'] > avg_put_vol * 3] if avg_put_vol > 0 else pd.DataFrame()
            
            # High value unusual options
            high_value_calls = []
            if not unusual_calls.empty:
                for _, row in unusual_calls.nlargest(3, 'volume').iterrows():
                    high_value_calls.append({
                        'strike': row['strike'],
                        'volume': int(row['volume']),
                        'oi': int(row.get('openInterest', 0))
                    })
            
            return {
                'ticker': ticker,
                'expiration': exps[0],
                'metrics': {
                    'pc_ratio': round(pc_ratio, 2),
                    'sentiment': sentiment,
                    'call_volume': int(call_vol),
                    'put_volume': int(put_vol),
                    'call_oi': int(call_oi),
                    'put_oi': int(put_oi),
                    'total_volume': int(call_vol + put_vol)
                },
                'unusual_activity': {
                    'unusual_calls': len(unusual_calls) if not isinstance(unusual_calls, type(None)) else 0,
                    'unusual_puts': len(unusual_puts) if not isinstance(unusual_puts, type(None)) else 0,
                    'high_value_calls': high_value_calls
                }
            }
            
        except Exception as e:
            return {'ticker': ticker, 'error': str(e)}
    
    def analyze_watchlist(self) -> List[Dict]:
        """Analyze all watchlist tickers"""
        results = []
        
        for ticker in self.watchlist:
            logger.info(f"📊 Analyzing options for {ticker}...")
            summary = self.get_options_summary(ticker)
            if 'error' not in summary:
                results.append(summary)
        
        return results
    
    def run(self) -> Dict:
        """Run options flow analysis"""
        logger.info("🚀 Starting Options Flow Analysis...")
        
        results = self.analyze_watchlist()
        
        # Sort by total volume
        results.sort(key=lambda x: x.get('metrics', {}).get('total_volume', 0), reverse=True)
        
        # Summary
        bullish = [r for r in results if r.get('metrics', {}).get('sentiment', '') in ['Bullish', 'Very Bullish']]
        bearish = [r for r in results if r.get('metrics', {}).get('sentiment', '') in ['Bearish', 'Very Bearish']]
        
        output = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_analyzed': len(results),
                'bullish_count': len(bullish),
                'bearish_count': len(bearish),
                'bullish_tickers': [r['ticker'] for r in bullish],
                'bearish_tickers': [r['ticker'] for r in bearish]
            },
            'unusual_flows': [
                {
                    'ticker': r['ticker'],
                    'sentiment': r['metrics']['sentiment'],
                    'total_volume': r['metrics']['total_volume'],
                    'cp_ratio': r['metrics']['pc_ratio'],
                    'levels': f"Exp: {r['expiration']}"
                } for r in results
            ],
            'raw_results': results
        }
        
        # Save to file
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ Saved to {self.output_file}")
        
        # Print summary
        print("\n🎲 Options Flow Summary:")
        print(f"   Total analyzed: {len(results)}")
        print(f"   Bullish: {len(bullish)} ({', '.join([r['ticker'] for r in bullish[:5]])})")
        print(f"   Bearish: {len(bearish)} ({', '.join([r['ticker'] for r in bearish[:5]])})")
        
        print("\n📊 Top 5 by Volume:")
        for r in results[:5]:
            m = r.get('metrics', {})
            print(f"   {r['ticker']:6s}: P/C={m.get('pc_ratio', 0):.2f} | {m.get('sentiment', 'N/A'):12s} | Vol={m.get('total_volume', 0):,}")
        
        return output


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Options Flow Analyzer')
    parser.add_argument('--dir', default='.', help='Data directory')
    args = parser.parse_args()
    
    analyzer = OptionsFlowAnalyzer(data_dir=args.dir)
    analyzer.run()


if __name__ == "__main__":
    main()
