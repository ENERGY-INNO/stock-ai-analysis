#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
💹 Market Strategist Persona: ETF Flow Analysis
=================================================
Analyzes money flows across major ETFs to understand market sentiment:
- Sector rotation signals
- Risk-on/Risk-off indicators
- Asset class flows (Equity, Bond, Commodity)

Author: Market Strategist Persona
Purpose: Interpret macro-level fund flows for strategic positioning
"""

import os
import pandas as pd
import numpy as np
import yfinance as yf
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from tqdm import tqdm

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ETFFlowAnalyzer:
    """
    주요 ETF의 자금 흐름을 분석하여 시장 센티멘트 파악
    
    추적 ETF 카테고리:
    - 주요 지수: SPY, QQQ, IWM, DIA
    - 섹터: XLK, XLF, XLE, XLV 등
    - 채권: TLT, IEF, HYG, LQD
    - 원자재: GLD, SLV, USO
    - 변동성: VXX, UVXY
    """
    
    def __init__(self, data_dir: str = '.'):
        self.data_dir = data_dir
        self.output_file = os.path.join(data_dir, 'us_etf_flows.csv')
        self.analysis_file = os.path.join(data_dir, 'etf_flow_analysis.json')
        
        # 24 Major ETFs to track
        self.etf_list = {
            # Major Index ETFs
            'SPY': {
                'name': 'S&P 500',
                'category': 'Index',
                'asset': 'Equity',
                'description_ko': '미국 대형주 500개를 추종하는 가장 대표적인 ETF입니다. 미국 시장 전체에 분산 투자하고 싶을 때 적합합니다.',
                'description_en': 'The most iconic ETF tracking 500 US large-cap stocks. Ideal for broad US market exposure.'
            },
            'QQQ': {
                'name': 'Nasdaq 100',
                'category': 'Index',
                'asset': 'Equity',
                'description_ko': '나스닥 100 지수를 추종합니다. 기술주 중심으로 성장주에 투자하고 싶을 때 적합합니다.',
                'description_en': 'Tracks the Nasdaq 100 index. Great for exposure to tech and growth stocks.'
            },
            'IWM': {
                'name': 'Russell 2000',
                'category': 'Index',
                'asset': 'Equity',
                'description_ko': '미국 소형주 2000개를 추종합니다. 경기 회복 시 높은 수익을 기대할 수 있습니다.',
                'description_en': 'Tracks 2000 US small-cap stocks. Offers higher growth potential during economic recoveries.'
            },
            'DIA': {
                'name': 'Dow Jones',
                'category': 'Index',
                'asset': 'Equity',
                'description_ko': '다우존스 산업평균 30개 종목을 추종합니다. 미국 우량 대기업에 집중 투자합니다.',
                'description_en': 'Tracks the 30 Dow Jones Industrial Average stocks. Focuses on blue-chip US companies.'
            },
            
            # Sector ETFs
            'XLK': {
                'name': 'Technology',
                'category': 'Sector',
                'asset': 'Equity',
                'description_ko': 'S&P 500 기술 섹터 ETF입니다. 애플, 마이크로소프트, 엔비디아 등 빅테크에 투자합니다.',
                'description_en': 'S&P 500 Technology sector ETF. Invests in Apple, Microsoft, NVIDIA and other big tech.'
            },
            'XLF': {
                'name': 'Financials',
                'category': 'Sector',
                'asset': 'Equity',
                'description_ko': 'S&P 500 금융 섹터 ETF입니다. 은행, 보험, 자산운용사 등에 투자합니다.',
                'description_en': 'S&P 500 Financial sector ETF. Invests in banks, insurance, and asset managers.'
            },
            'XLE': {
                'name': 'Energy',
                'category': 'Sector',
                'asset': 'Equity',
                'description_ko': 'S&P 500 에너지 섹터 ETF입니다. 엑손모빌, 셰브론 등 석유/가스 기업에 투자합니다.',
                'description_en': 'S&P 500 Energy sector ETF. Invests in oil/gas companies like ExxonMobil and Chevron.'
            },
            'XLV': {
                'name': 'Healthcare',
                'category': 'Sector',
                'asset': 'Equity',
                'description_ko': 'S&P 500 헬스케어 섹터 ETF입니다. 제약, 바이오, 의료기기 회사에 투자합니다.',
                'description_en': 'S&P 500 Healthcare sector ETF. Invests in pharma, biotech, and medical devices.'
            },
            'XLI': {
                'name': 'Industrials',
                'category': 'Sector',
                'asset': 'Equity',
                'description_ko': 'S&P 500 산업재 섹터 ETF입니다. 항공, 방위, 기계, 운송 기업에 투자합니다.',
                'description_en': 'S&P 500 Industrial sector ETF. Invests in aerospace, defense, machinery, and transport.'
            },
            'XLY': {
                'name': 'Consumer Disc',
                'category': 'Sector',
                'asset': 'Equity',
                'description_ko': 'S&P 500 경기소비재 섹터 ETF입니다. 아마존, 테슬라, 홈디포 등에 투자합니다.',
                'description_en': 'S&P 500 Consumer Discretionary ETF. Invests in Amazon, Tesla, Home Depot and more.'
            },
            'XLP': {
                'name': 'Consumer Staples',
                'category': 'Sector',
                'asset': 'Equity',
                'description_ko': 'S&P 500 필수소비재 섹터 ETF입니다. P&G, 코카콜라 등 방어주에 투자합니다.',
                'description_en': 'S&P 500 Consumer Staples ETF. Defensive sector with P&G, Coca-Cola and similar.'
            },
            'XLU': {
                'name': 'Utilities',
                'category': 'Sector',
                'asset': 'Equity',
                'description_ko': 'S&P 500 유틸리티 섹터 ETF입니다. 전력, 가스 등 방어적 배당주에 투자합니다.',
                'description_en': 'S&P 500 Utilities sector ETF. Defensive dividend stocks in power and gas utilities.'
            },
            
            # Bond ETFs
            'TLT': {
                'name': '20+ Year Treasury',
                'category': 'Bond',
                'asset': 'Fixed Income',
                'description_ko': '미국 20년 이상 장기 국채 ETF입니다. 금리 하락 시 가격 상승, 안전자산 역할을 합니다.',
                'description_en': '20+ year US Treasury bonds. Rises when rates fall, serves as a safe-haven asset.'
            },
            'IEF': {
                'name': '7-10 Year Treasury',
                'category': 'Bond',
                'asset': 'Fixed Income',
                'description_ko': '미국 7-10년 중기 국채 ETF입니다. TLT보다 변동성이 낮은 채권 투자에 적합합니다.',
                'description_en': '7-10 year US Treasury bonds. Lower volatility than TLT for bond exposure.'
            },
            'HYG': {
                'name': 'High Yield Corp',
                'category': 'Bond',
                'asset': 'Fixed Income',
                'description_ko': '미국 하이일드(정크) 회사채 ETF입니다. 높은 이자 수익을 제공하지만 신용 위험이 있습니다.',
                'description_en': 'US high-yield corporate bonds (junk bonds). High income but with credit risk.'
            },
            'LQD': {
                'name': 'IG Corporate',
                'category': 'Bond',
                'asset': 'Fixed Income',
                'description_ko': '미국 투자등급 회사채 ETF입니다. 국채보다 높은 수익률, HYG보다 낮은 위험을 제공합니다.',
                'description_en': 'US investment-grade corporate bonds. Higher yield than Treasuries, lower risk than HYG.'
            },
            
            # Commodity ETFs
            'GLD': {
                'name': 'Gold',
                'category': 'Commodity',
                'asset': 'Commodity',
                'description_ko': '금 현물 가격을 추종하는 ETF입니다. 인플레이션 헤지 및 안전자산으로 활용됩니다.',
                'description_en': 'Tracks physical gold prices. Used for inflation hedging and as a safe-haven.'
            },
            'SLV': {
                'name': 'Silver',
                'category': 'Commodity',
                'asset': 'Commodity',
                'description_ko': '은 현물 가격을 추종하는 ETF입니다. 금보다 변동성이 크고 산업 수요에 영향받습니다.',
                'description_en': 'Tracks physical silver prices. More volatile than gold, influenced by industrial demand.'
            },
            'USO': {
                'name': 'Oil',
                'category': 'Commodity',
                'asset': 'Commodity',
                'description_ko': 'WTI 원유 선물을 추종하는 ETF입니다. 유가 상승 시 수익을 얻을 수 있습니다.',
                'description_en': 'Tracks WTI crude oil futures. Profits when oil prices rise.'
            },
            
            # Volatility ETFs
            'VXX': {
                'name': 'VIX Short-Term',
                'category': 'Volatility',
                'asset': 'Volatility',
                'description_ko': 'VIX 단기 선물을 추종합니다. 시장 하락 시 급등하여 헤지 목적으로 사용됩니다.',
                'description_en': 'Tracks short-term VIX futures. Spikes during market selloffs, used for hedging.'
            },
            
            # International
            'EEM': {
                'name': 'Emerging Markets',
                'category': 'International',
                'asset': 'Equity',
                'description_ko': '이머징마켓(신흥국) 주식 ETF입니다. 중국, 대만, 인도, 한국 등에 분산 투자합니다.',
                'description_en': 'Emerging markets equity ETF. Diversified exposure to China, Taiwan, India, Korea.'
            },
            'EFA': {
                'name': 'Developed Markets',
                'category': 'International',
                'asset': 'Equity',
                'description_ko': '선진국(미국 제외) 주식 ETF입니다. 유럽, 일본, 호주 등에 분산 투자합니다.',
                'description_en': 'Developed markets (ex-US) equity ETF. Exposure to Europe, Japan, Australia.'
            },
            'FXI': {
                'name': 'China Large-Cap',
                'category': 'International',
                'asset': 'Equity',
                'description_ko': '중국 대형주 50개를 추종합니다. 중국 시장에 집중 투자하고 싶을 때 적합합니다.',
                'description_en': 'Tracks 50 Chinese large-cap stocks. Concentrated exposure to Chinese market.'
            },
            
            # Real Estate
            'VNQ': {
                'name': 'Real Estate',
                'category': 'Real Estate',
                'asset': 'Equity',
                'description_ko': '미국 리츠(REITs) ETF입니다. 부동산에 간접 투자하며 배당 수익을 제공합니다.',
                'description_en': 'US REITs ETF. Indirect real estate investment with dividend income.'
            },
        }
    
    def download_etf_data(self, ticker: str, days: int = 60) -> pd.DataFrame:
        """Download ETF price and volume data"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            etf = yf.Ticker(ticker)
            hist = etf.history(start=start_date, end=end_date)
            
            if hist.empty:
                return pd.DataFrame()
            
            hist = hist.reset_index()
            hist['ticker'] = ticker
            
            return hist
            
        except Exception as e:
            logger.debug(f"Error downloading {ticker}: {e}")
            return pd.DataFrame()
    
    def calculate_flow_proxy(self, df: pd.DataFrame) -> Dict:
        """
        Calculate flow proxy using OBV and volume analysis
        
        실제 ETF 자금 흐름 데이터는 유료이므로, 
        가격/거래량 기반 프록시 지표를 사용:
        - OBV 변화율: 매수/매도 압력
        - 거래량 비율: 관심도 변화
        - 가격 모멘텀: 방향성
        """
        if len(df) < 20:
            return None
        
        df = df.sort_values('Date').reset_index(drop=True)
        
        # Calculate OBV
        obv = [0]
        for i in range(1, len(df)):
            if df['Close'].iloc[i] > df['Close'].iloc[i-1]:
                obv.append(obv[-1] + df['Volume'].iloc[i])
            elif df['Close'].iloc[i] < df['Close'].iloc[i-1]:
                obv.append(obv[-1] - df['Volume'].iloc[i])
            else:
                obv.append(obv[-1])
        
        obv = pd.Series(obv, index=df.index)
        
        # OBV change (20-day)
        obv_change = (obv.iloc[-1] - obv.iloc[-20]) / abs(obv.iloc[-20]) * 100 if obv.iloc[-20] != 0 else 0
        
        # Volume ratio (5d vs 20d)
        vol_5d = df['Volume'].tail(5).mean()
        vol_20d = df['Volume'].tail(20).mean()
        vol_ratio = vol_5d / vol_20d if vol_20d > 0 else 1
        
        # Price momentum (20-day return)
        price_return_20d = (df['Close'].iloc[-1] / df['Close'].iloc[-20] - 1) * 100
        
        # Price momentum (5-day return)
        price_return_5d = (df['Close'].iloc[-1] / df['Close'].iloc[-5] - 1) * 100
        
        # Flow Score (0-100)
        score = 50
        
        # OBV contribution (max ±20)
        if obv_change > 15:
            score += 20
        elif obv_change > 5:
            score += 10
        elif obv_change < -15:
            score -= 20
        elif obv_change < -5:
            score -= 10
        
        # Volume contribution (max ±15)
        if vol_ratio > 1.5:
            score += 15
        elif vol_ratio > 1.2:
            score += 8
        elif vol_ratio < 0.7:
            score -= 10
        
        # Price momentum contribution (max ±15)
        if price_return_20d > 5:
            score += 15
        elif price_return_20d > 2:
            score += 8
        elif price_return_20d < -5:
            score -= 15
        elif price_return_20d < -2:
            score -= 8
        
        score = max(0, min(100, score))
        
        # Determine flow status
        if score >= 70:
            flow_status = "Strong Inflow"
        elif score >= 55:
            flow_status = "Inflow"
        elif score >= 45:
            flow_status = "Neutral"
        elif score >= 30:
            flow_status = "Outflow"
        else:
            flow_status = "Strong Outflow"
        
        return {
            'date': df['Date'].iloc[-1],
            'current_price': round(df['Close'].iloc[-1], 2),
            'obv_change_20d': round(obv_change, 2),
            'vol_ratio_5d_20d': round(vol_ratio, 2),
            'return_5d': round(price_return_5d, 2),
            'return_20d': round(price_return_20d, 2),
            'flow_score': round(score, 1),
            'flow_status': flow_status
        }
    
    def analyze_market_sentiment(self, results_df: pd.DataFrame) -> Dict:
        """
        Analyze overall market sentiment from ETF flows
        
        분석 항목:
        - Risk-On vs Risk-Off 지표
        - 섹터 로테이션 신호
        - 자산 클래스 선호도
        """
        if results_df.empty:
            return {}
        
        # Calculate category averages
        category_scores = results_df.groupby('category')['flow_score'].mean().to_dict()
        asset_scores = results_df.groupby('asset')['flow_score'].mean().to_dict()
        
        # Risk-On/Off indicator
        equity_score = asset_scores.get('Equity', 50)
        bond_score = asset_scores.get('Fixed Income', 50)
        volatility_score = 100 - results_df[results_df['category'] == 'Volatility']['flow_score'].mean() if 'Volatility' in results_df['category'].values else 50
        
        risk_appetite = (equity_score * 0.5 + (100 - bond_score) * 0.3 + volatility_score * 0.2)
        
        if risk_appetite >= 60:
            risk_status = "Risk-On"
        elif risk_appetite >= 40:
            risk_status = "Neutral"
        else:
            risk_status = "Risk-Off"
        
        # Top sectors
        sector_df = results_df[results_df['category'] == 'Sector'].nlargest(3, 'flow_score')
        top_sectors = sector_df['name'].tolist() if not sector_df.empty else []
        
        # Bottom sectors
        bottom_df = results_df[results_df['category'] == 'Sector'].nsmallest(3, 'flow_score')
        bottom_sectors = bottom_df['name'].tolist() if not bottom_df.empty else []
        
        return {
            'analysis_date': datetime.now().isoformat(),
            'risk_appetite_score': round(risk_appetite, 1),
            'risk_status': risk_status,
            'category_scores': {k: round(v, 1) for k, v in category_scores.items()},
            'asset_scores': {k: round(v, 1) for k, v in asset_scores.items()},
            'top_sectors': top_sectors,
            'bottom_sectors': bottom_sectors,
            'summary': self._generate_summary(risk_status, top_sectors, bottom_sectors, category_scores)
        }
    
    def _generate_summary(self, risk_status: str, top_sectors: List, bottom_sectors: List, category_scores: Dict) -> str:
        """Generate text summary of market sentiment"""
        summary_parts = []
        
        # Risk status
        if risk_status == "Risk-On":
            summary_parts.append("시장은 리스크 선호(Risk-On) 상태입니다.")
        elif risk_status == "Risk-Off":
            summary_parts.append("시장은 리스크 회피(Risk-Off) 상태입니다.")
        else:
            summary_parts.append("시장은 중립적인 상태입니다.")
        
        # Top sectors
        if top_sectors:
            summary_parts.append(f"강세 섹터: {', '.join(top_sectors)}")
        
        # Bottom sectors
        if bottom_sectors:
            summary_parts.append(f"약세 섹터: {', '.join(bottom_sectors)}")
        
        # Special signals
        if category_scores.get('Commodity', 50) > 60:
            summary_parts.append("원자재 섹터로 자금 유입 중.")
        if category_scores.get('Bond', 50) > 60:
            summary_parts.append("채권으로 안전자산 선호 자금 이동 중.")
        
        return " ".join(summary_parts)
    
    def run(self, enable_ai_analysis: bool = False) -> pd.DataFrame:
        """Run ETF flow analysis"""
        logger.info("🚀 Starting ETF Flow Analysis...")
        
        results = []
        
        for ticker, info in tqdm(self.etf_list.items(), desc="Analyzing ETFs"):
            # Download data
            df = self.download_etf_data(ticker)
            
            if df.empty:
                logger.debug(f"No data for {ticker}")
                continue
            
            # Calculate flow proxy
            flow = self.calculate_flow_proxy(df)
            
            if flow:
                result = {
                    'ticker': ticker,
                    'name': info['name'],
                    'category': info['category'],
                    'asset': info['asset'],
                    'description_ko': info.get('description_ko', ''),
                    'description_en': info.get('description_en', ''),
                    **flow
                }
                results.append(result)
        
        # Create DataFrame
        results_df = pd.DataFrame(results)
        
        if results_df.empty:
            logger.warning("No results to save")
            return results_df
        
        # Save results
        results_df.to_csv(self.output_file, index=False)
        logger.info(f"✅ ETF analysis complete! Saved to {self.output_file}")
        
        # Analyze market sentiment
        sentiment = self.analyze_market_sentiment(results_df)
        
        # Save sentiment analysis
        with open(self.analysis_file, 'w', encoding='utf-8') as f:
            json.dump(sentiment, f, ensure_ascii=False, indent=2)
        logger.info(f"✅ Market sentiment saved to {self.analysis_file}")
        
        # Print summary
        logger.info("\n📊 ETF Flow Summary:")
        for category in results_df['category'].unique():
            cat_df = results_df[results_df['category'] == category]
            avg_score = cat_df['flow_score'].mean()
            logger.info(f"   {category}: Avg Score {avg_score:.1f}")
        
        logger.info(f"\n🎯 Market Status: {sentiment.get('risk_status', 'Unknown')}")
        logger.info(f"   Risk Appetite: {sentiment.get('risk_appetite_score', 0):.1f}/100")
        
        return results_df


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ETF Flow Analysis')
    parser.add_argument('--dir', default='.', help='Data directory')
    parser.add_argument('--ai', action='store_true', help='Enable AI analysis (requires Gemini API)')
    args = parser.parse_args()
    
    analyzer = ETFFlowAnalyzer(data_dir=args.dir)
    results = analyzer.run(enable_ai_analysis=args.ai)
    
    if not results.empty:
        # Show top inflows
        print("\n💰 Top 5 ETF Inflows:")
        top_5 = results.nlargest(5, 'flow_score')
        for _, row in top_5.iterrows():
            print(f"   {row['ticker']} ({row['name']}): Score {row['flow_score']} - {row['flow_status']}")
        
        # Show top outflows
        print("\n📉 Top 5 ETF Outflows:")
        bottom_5 = results.nsmallest(5, 'flow_score')
        for _, row in bottom_5.iterrows():
            print(f"   {row['ticker']} ({row['name']}): Score {row['flow_score']} - {row['flow_status']}")


if __name__ == "__main__":
    main()
