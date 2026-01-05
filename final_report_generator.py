#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📑 Investment Strategist Persona: Final Report Generator
==========================================================
Combines quant scores with AI analysis to generate final Top 10 report.

Author: Investment Strategist Persona
Purpose: Deliver actionable final investment recommendations
"""

import os
import json
import logging
import pandas as pd
from datetime import datetime
from typing import Dict, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class FinalReportGenerator:
    """
    최종 투자 리포트 생성기
    
    점수 산정:
    - Quant Score (80%): smart_money_screener_v2 결과
    - AI Bonus (20%): AI 분석 sentiment 기반 가산점
    """
    
    def __init__(self, data_dir: str = '.'):
        self.data_dir = data_dir
        self.output_file = os.path.join(data_dir, 'final_top10_report.json')
        self.dashboard_file = os.path.join(data_dir, 'smart_money_current.json')
    
    def run(self, top_n: int = 10) -> Dict:
        """Generate final report"""
        logger.info("🚀 Starting Final Report Generation...")
        
        # Load Quant Data
        quant_path = os.path.join(self.data_dir, 'smart_money_picks_v2.csv')
        if not os.path.exists(quant_path):
            logger.warning(f"⚠️ {quant_path} not found")
            return {}
        
        df = pd.read_csv(quant_path)
        logger.info(f"📊 Loaded {len(df)} stocks from quant analysis")
        
        # Load AI Summaries
        ai_path = os.path.join(self.data_dir, 'ai_summaries.json')
        ai_data = {}
        if os.path.exists(ai_path):
            try:
                with open(ai_path, 'r', encoding='utf-8') as f:
                    ai_data = json.load(f)
                logger.info(f"📊 Loaded AI summaries for {len(ai_data)} stocks")
            except:
                logger.warning("⚠️ Failed to load AI summaries")
        
        # Load Macro Analysis
        macro_path = os.path.join(self.data_dir, 'macro_analysis.json')
        macro_summary = ""
        market_regime = "Neutral"
        if os.path.exists(macro_path):
            try:
                with open(macro_path, 'r', encoding='utf-8') as f:
                    macro = json.load(f)
                    macro_summary = macro.get('ai_analysis', '')[:500]
                    market_regime = macro.get('market_regime', {}).get('type', 'Neutral')
            except:
                pass
        
        # Calculate Final Scores
        results = []
        
        for _, row in df.iterrows():
            ticker = row['ticker']
            
            # Base quant score
            quant_score = row.get('composite_score', 50)
            
            # AI Bonus calculation
            ai_score = 0
            ai_recommendation = "Hold"
            ai_summary = ""
            
            if ticker in ai_data:
                summary = ai_data[ticker].get('summary', '')
                ai_summary = summary
                
                # Analyze sentiment from summary
                summary_lower = summary.lower()
                
                if '적극 매수' in summary or 'strong buy' in summary_lower:
                    ai_score = 20
                    ai_recommendation = "Strong Buy"
                elif '매수' in summary or 'buy' in summary_lower or '분할 매수' in summary:
                    ai_score = 10
                    ai_recommendation = "Buy"
                elif '회피' in summary or 'avoid' in summary_lower or '매도' in summary:
                    ai_score = -10
                    ai_recommendation = "Avoid"
                elif '관망' in summary or 'hold' in summary_lower or '확인' in summary:
                    ai_score = 0
                    ai_recommendation = "Hold"
            
            # Final score: 80% quant + 20% AI bonus (capped)
            final_score = quant_score * 0.8 + max(0, ai_score)
            
            # Final grade
            if final_score >= 75:
                final_grade = "🔥 S급"
            elif final_score >= 65:
                final_grade = "🌟 A급"
            elif final_score >= 55:
                final_grade = "📈 B급"
            elif final_score >= 45:
                final_grade = "📊 C급"
            else:
                final_grade = "⚠️ D급"
            
            results.append({
                'ticker': ticker,
                'name': row.get('name', ticker),
                'final_score': round(final_score, 1),
                'quant_score': round(quant_score, 1),
                'ai_bonus': ai_score,
                'final_grade': final_grade,
                'ai_recommendation': ai_recommendation,
                'current_price': row.get('current_price', 0),
                'target_upside': row.get('target_upside', 0),
                'rsi': row.get('rsi', 50),
                'ma_signal': row.get('ma_signal', 'N/A'),
                'pe_ratio': row.get('pe_ratio', 'N/A'),
                'size': row.get('size', 'N/A'),
                'ai_summary': ai_summary[:300] if ai_summary else '',
                'sd_score': row.get('sd_score', 50),
                'inst_score': row.get('inst_score', 50),
                'tech_score': row.get('tech_score', 50)
            })
        
        # Sort by final score
        results.sort(key=lambda x: x['final_score'], reverse=True)
        
        # Add ranks
        top_picks = results[:top_n]
        for i, pick in enumerate(top_picks, 1):
            pick['rank'] = i
        
        # Build output
        output = {
            'timestamp': datetime.now().isoformat(),
            'market_regime': market_regime,
            'total_analyzed': len(df),
            'top_picks': top_picks,
            'macro_summary': macro_summary[:300] if macro_summary else ''
        }
        
        # Save main report
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        # Save for dashboard
        with open(self.dashboard_file, 'w', encoding='utf-8') as f:
            json.dump({'picks': top_picks, 'updated': output['timestamp']}, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Saved final report to {self.output_file}")
        
        # Print summary
        print(f"\n📑 Final Top {top_n} Report")
        print(f"   Market Regime: {market_regime}")
        print("=" * 60)
        
        for pick in top_picks:
            print(f"#{pick['rank']:2d} {pick['ticker']:6s} | {pick['final_grade']:8s} | "
                  f"Score: {pick['final_score']:5.1f} | ${pick['current_price']:8.2f} | "
                  f"{pick['ai_recommendation']}")
        
        return output


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Final Report Generator')
    parser.add_argument('--dir', default='.', help='Data directory')
    parser.add_argument('--top', type=int, default=10, help='Top N stocks')
    args = parser.parse_args()
    
    generator = FinalReportGenerator(data_dir=args.dir)
    generator.run(top_n=args.top)


if __name__ == "__main__":
    main()
