#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
⚖️ Risk Manager Persona: Portfolio Risk Analyzer
==================================================
Analyzes portfolio risk including correlation and volatility.

Author: Risk Manager Persona
Purpose: Ensure proper diversification and risk management
"""

import os
import json
import logging
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
from typing import Dict, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PortfolioRiskAnalyzer:
    """
    포트폴리오 리스크 분석
    
    분석 항목:
    - 상관관계 매트릭스: 종목 간 움직임 상관성
    - 변동성: 포트폴리오 전체 변동성
    - 집중 리스크: 섹터/종목 집중도
    - Value at Risk: 최대 손실 추정
    """
    
    def __init__(self, data_dir: str = '.'):
        self.data_dir = data_dir
        self.output_file = os.path.join(data_dir, 'portfolio_risk.json')
    
    def analyze_portfolio(self, tickers: List[str], weights: List[float] = None) -> Dict:
        """Analyze portfolio risk metrics"""
        logger.info(f"📊 Analyzing portfolio: {tickers}")
        
        if len(tickers) < 2:
            return {'error': 'Need at least 2 tickers for analysis'}
        
        # Default equal weights
        if weights is None:
            weights = [1/len(tickers)] * len(tickers)
        
        weights = np.array(weights)
        
        try:
            # Download historical data
            data = yf.download(tickers, period='6mo', progress=False)['Close']
            
            if data.empty:
                return {'error': 'No data available'}
            
            # Calculate returns
            returns = data.pct_change().dropna()
            
            # Correlation matrix
            corr = returns.corr()
            
            # Find high correlations
            high_correlations = []
            cols = corr.columns
            for i in range(len(cols)):
                for j in range(i+1, len(cols)):
                    correlation = corr.iloc[i, j]
                    if correlation > 0.7:
                        high_correlations.append({
                            'pair': [cols[i], cols[j]],
                            'correlation': round(correlation, 2),
                            'risk': 'High' if correlation > 0.85 else 'Medium'
                        })
            
            # Portfolio volatility
            cov_matrix = returns.cov() * 252  # Annualized
            portfolio_var = np.dot(weights.T, np.dot(cov_matrix, weights))
            portfolio_vol = np.sqrt(portfolio_var)
            
            # Individual volatilities
            individual_vols = (returns.std() * np.sqrt(252)).to_dict()
            
            # Sharpe Ratio approximation (assuming 5% risk-free rate)
            annual_return = (returns.mean() * 252).mean()
            sharpe = (annual_return - 0.05) / portfolio_vol if portfolio_vol > 0 else 0
            
            # Value at Risk (95% confidence)
            var_95 = portfolio_vol * 1.645  # 95% confidence
            var_99 = portfolio_vol * 2.326  # 99% confidence
            
            # Diversification ratio
            weighted_vols = np.dot(weights, list(individual_vols.values()))
            diversification_ratio = weighted_vols / portfolio_vol if portfolio_vol > 0 else 1
            
            # Risk assessment
            if portfolio_vol < 0.15:
                risk_level = "Low Risk"
            elif portfolio_vol < 0.25:
                risk_level = "Medium Risk"
            elif portfolio_vol < 0.35:
                risk_level = "High Risk"
            else:
                risk_level = "Very High Risk"
            
            # Recommendations
            recommendations = []
            if len(high_correlations) > len(tickers) / 2:
                recommendations.append("⚠️ 높은 상관관계 종목이 많습니다. 분산 투자 필요")
            if portfolio_vol > 0.30:
                recommendations.append("⚠️ 변동성이 높습니다. 방어주나 채권 ETF 추가 고려")
            if diversification_ratio < 1.1:
                recommendations.append("⚠️ 분산 효과가 낮습니다. 상관관계 낮은 종목 추가 고려")
            if not recommendations:
                recommendations.append("✅ 포트폴리오가 적절히 분산되어 있습니다")
            
            return {
                'portfolio': {
                    'tickers': tickers,
                    'weights': [round(w, 4) for w in weights.tolist()]
                },
                'risk_metrics': {
                    'volatility_annual': round(portfolio_vol * 100, 2),
                    'risk_level': risk_level,
                    'sharpe_ratio': round(sharpe, 2),
                    'var_95_pct': round(var_95 * 100, 2),
                    'var_99_pct': round(var_99 * 100, 2),
                    'diversification_ratio': round(diversification_ratio, 2)
                },
                'individual_volatilities': {k: round(v * 100, 2) for k, v in individual_vols.items()},
                'correlation_analysis': {
                    'high_correlations': high_correlations,
                    'correlation_matrix': {str(k): {str(kk): round(vv, 2) for kk, vv in v.items()} 
                                          for k, v in corr.to_dict().items()}
                },
                'recommendations': recommendations
            }
            
        except Exception as e:
            logger.error(f"Error: {e}")
            return {'error': str(e)}
    
    def run(self, tickers: List[str] = None) -> Dict:
        """Run portfolio risk analysis"""
        logger.info("🚀 Starting Portfolio Risk Analysis...")
        
        # Default portfolio if none provided
        if tickers is None:
            # Try to load from smart money picks
            picks_file = os.path.join(self.data_dir, 'smart_money_picks_v2.csv')
            if os.path.exists(picks_file):
                picks_df = pd.read_csv(picks_file)
                tickers = picks_df['ticker'].head(10).tolist()
            else:
                tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 
                          'META', 'TSLA', 'JPM', 'V', 'UNH']
        
        result = self.analyze_portfolio(tickers)
        
        # Add timestamp
        result['timestamp'] = datetime.now().isoformat()
        
        # Save to file
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ Saved to {self.output_file}")
        
        # Print summary
        if 'risk_metrics' in result:
            rm = result['risk_metrics']
            print("\n⚖️ Portfolio Risk Summary:")
            print(f"   Volatility: {rm['volatility_annual']:.1f}% ({rm['risk_level']})")
            print(f"   Sharpe Ratio: {rm['sharpe_ratio']:.2f}")
            print(f"   VaR 95%: -{rm['var_95_pct']:.1f}%")
            print(f"   Diversification: {rm['diversification_ratio']:.2f}x")
            
            if 'high_correlations' in result.get('correlation_analysis', {}):
                hc = result['correlation_analysis']['high_correlations']
                if hc:
                    print(f"\n⚠️ High Correlations ({len(hc)} pairs):")
                    for pair in hc[:3]:
                        print(f"   {pair['pair'][0]}-{pair['pair'][1]}: {pair['correlation']:.2f}")
            
            print("\n📋 Recommendations:")
            for rec in result.get('recommendations', []):
                print(f"   {rec}")
        
        return result


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Portfolio Risk Analyzer')
    parser.add_argument('--dir', default='.', help='Data directory')
    parser.add_argument('--tickers', nargs='+', help='Portfolio tickers')
    args = parser.parse_args()
    
    analyzer = PortfolioRiskAnalyzer(data_dir=args.dir)
    analyzer.run(tickers=args.tickers)


if __name__ == "__main__":
    main()
