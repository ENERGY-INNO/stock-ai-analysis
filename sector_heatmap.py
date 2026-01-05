#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📊 Sector Analyst Persona: Sector Performance Heatmap
=======================================================
Collects performance data for 11 S&P sector ETFs for visualization.

Author: Sector Analyst Persona
Purpose: Identify sector rotation and relative strength
"""

import os
import json
import pandas as pd
import yfinance as yf
from datetime import datetime
from typing import Dict, List
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SectorHeatmapCollector:
    """
    11개 S&P 섹터 ETF 퍼포먼스 히트맵 데이터 수집
    
    Sectors:
    - XLK (Technology), XLF (Financials), XLV (Healthcare)
    - XLE (Energy), XLY (Consumer Disc), XLP (Consumer Staples)
    - XLI (Industrials), XLB (Materials), XLU (Utilities)
    - XLRE (Real Estate), XLC (Communication Services)
    """
    
    def __init__(self, data_dir: str = '.'):
        self.data_dir = data_dir
        self.output_file = os.path.join(data_dir, 'sector_heatmap.json')
        
        # Sector ETFs with full names and colors
        self.sector_etfs = {
            'XLK': {'name': 'Technology', 'color': '#4A90A4'},
            'XLF': {'name': 'Financials', 'color': '#6B8E23'},
            'XLV': {'name': 'Healthcare', 'color': '#FF69B4'},
            'XLE': {'name': 'Energy', 'color': '#FF6347'},
            'XLY': {'name': 'Consumer Disc.', 'color': '#FFD700'},
            'XLP': {'name': 'Consumer Staples', 'color': '#98D8C8'},
            'XLI': {'name': 'Industrials', 'color': '#DDA0DD'},
            'XLB': {'name': 'Materials', 'color': '#F0E68C'},
            'XLU': {'name': 'Utilities', 'color': '#87CEEB'},
            'XLRE': {'name': 'Real Estate', 'color': '#CD853F'},
            'XLC': {'name': 'Comm. Services', 'color': '#9370DB'},
        }
        
        # Representative stocks per sector
        self.sector_stocks = {
            'Technology': ['AAPL', 'MSFT', 'NVDA', 'AVGO', 'ORCL', 'CRM', 'AMD', 'ADBE'],
            'Financials': ['BRK-B', 'JPM', 'V', 'MA', 'BAC', 'WFC', 'GS', 'MS'],
            'Healthcare': ['UNH', 'JNJ', 'LLY', 'PFE', 'MRK', 'ABBV', 'TMO', 'ABT'],
            'Energy': ['XOM', 'CVX', 'COP', 'EOG', 'SLB', 'MPC', 'PSX', 'VLO'],
            'Consumer Disc.': ['AMZN', 'TSLA', 'HD', 'MCD', 'NKE', 'SBUX', 'TJX', 'LOW'],
            'Consumer Staples': ['PG', 'KO', 'PEP', 'COST', 'WMT', 'PM', 'MO', 'CL'],
            'Industrials': ['CAT', 'UNP', 'HON', 'UPS', 'BA', 'RTX', 'DE', 'GE'],
            'Materials': ['LIN', 'APD', 'SHW', 'FCX', 'NEM', 'NUE', 'DOW', 'DD'],
            'Utilities': ['NEE', 'DUK', 'SO', 'D', 'AEP', 'EXC', 'SRE', 'XEL'],
            'Real Estate': ['PLD', 'AMT', 'EQIX', 'PSA', 'SPG', 'O', 'WELL', 'AVB'],
            'Comm. Services': ['META', 'GOOGL', 'GOOG', 'NFLX', 'DIS', 'CMCSA', 'VZ', 'T'],
        }
    
    def get_sector_performance(self, period: str = '5d') -> Dict:
        """Get sector ETF performance data"""
        logger.info(f"📊 Fetching sector ETF data ({period})...")
        
        tickers = list(self.sector_etfs.keys())
        
        try:
            data = yf.download(tickers, period=period, progress=False)
            
            if data.empty:
                return {'error': 'No data'}
            
            sectors = []
            
            for ticker, info in self.sector_etfs.items():
                try:
                    if ticker not in data['Close'].columns:
                        continue
                    
                    prices = data['Close'][ticker].dropna()
                    if len(prices) < 2:
                        continue
                    
                    current = prices.iloc[-1]
                    prev = prices.iloc[0]
                    change = ((current / prev) - 1) * 100
                    
                    # Daily change
                    daily_change = ((prices.iloc[-1] / prices.iloc[-2]) - 1) * 100 if len(prices) >= 2 else 0
                    vol = data['Volume'][ticker].iloc[-1] if 'Volume' in data.columns else 1000000
                    
                    sectors.append({
                        'ticker': ticker,
                        'name': info['name'],
                        'price': round(current, 2),
                        'change': round(change, 2),
                        'daily_change': round(daily_change, 2),
                        'color': self._get_color(change),
                        'hex_color': info['color'],
                        'weight': round(current * vol, 0)
                    })
                except Exception as e:
                    logger.debug(f"Error processing {ticker}: {e}")
            
            # Sort by performance
            sectors.sort(key=lambda x: x['change'], reverse=True)
            
            return {
                'timestamp': datetime.now().isoformat(),
                'period': period,
                'sectors': sectors,
                'top_sectors': [s['name'] for s in sectors[:3]],
                'bottom_sectors': [s['name'] for s in sectors[-3:]]
            }
            
        except Exception as e:
            logger.error(f"Error: {e}")
            return {'error': str(e)}
    
    def get_full_market_map(self, period: str = '5d') -> Dict:
        """Get full market map data (Sectors -> Stocks) for Treemap"""
        logger.info(f"📊 Fetching full market map data ({period})...")
        
        all_tickers = []
        ticker_to_sector = {}
        for sector, stocks in self.sector_stocks.items():
            all_tickers.extend(stocks)
            for stock in stocks:
                ticker_to_sector[stock] = sector
                
        try:
            data = yf.download(all_tickers, period=period, progress=False)
            
            if data.empty:
                return {'error': 'No data'}
            
            market_map = {name: [] for name in self.sector_stocks.keys()}
            
            for ticker in all_tickers:
                try:
                    if ticker not in data['Close'].columns:
                        continue
                    prices = data['Close'][ticker].dropna()
                    if len(prices) < 2:
                        continue
                    
                    current = prices.iloc[-1]
                    prev = prices.iloc[-2]
                    change = ((current / prev) - 1) * 100
                    
                    # Weight by Volume * Price (Activity proxy)
                    vol = data['Volume'][ticker].iloc[-1] if 'Volume' in data.columns else 100000
                    weight = current * vol
                    
                    sector = ticker_to_sector.get(ticker, 'Unknown')
                    if sector in market_map:
                        market_map[sector].append({
                            'ticker': ticker,
                            'weight': round(weight, 0),
                            'price': round(current, 2),
                            'change': round(change, 2),
                            'color': self._get_color(change)
                        })
                except:
                    pass
            
            # Sort stocks within each sector
            for sector_name in market_map:
                market_map[sector_name].sort(key=lambda x: x['weight'], reverse=True)
            
            return {
                'timestamp': datetime.now().isoformat(),
                'period': period,
                'market_map': market_map
            }
            
        except Exception as e:
            logger.error(f"Error: {e}")
            return {'error': str(e)}
    
    def _get_color(self, change: float) -> str:
        """Get color based on performance"""
        if change >= 3: return 'strong_green'
        elif change >= 1: return 'green'
        elif change >= 0: return 'light_green'
        elif change >= -1: return 'light_red'
        elif change >= -3: return 'red'
        else: return 'strong_red'
    
    def run(self) -> Dict:
        """Run sector heatmap collection"""
        logger.info("🚀 Starting Sector Heatmap Collection...")
        
        result = {
            'sector_performance': self.get_sector_performance('5d'),
            'market_map': self.get_full_market_map('5d')
        }
        
        # Save to file
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ Saved to {self.output_file}")
        
        # Print summary
        if 'sectors' in result['sector_performance']:
            print("\n📊 Sector Performance (5-day):")
            for s in result['sector_performance']['sectors']:
                emoji = "🟢" if s['change'] > 0 else "🔴"
                print(f"   {emoji} {s['name']:20s}: {s['change']:+6.2f}%")
        
        return result


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Sector Heatmap Data Collector')
    parser.add_argument('--dir', default='.', help='Data directory')
    args = parser.parse_args()
    
    collector = SectorHeatmapCollector(data_dir=args.dir)
    collector.run()


if __name__ == "__main__":
    main()
