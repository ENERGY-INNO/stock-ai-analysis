import os
import json
import threading
import pandas as pd
import numpy as np
import yfinance as yf
import subprocess
from flask import Flask, render_template, jsonify, request
import traceback
from datetime import datetime

app = Flask(__name__)

# Suffix helper for KR stocks
def fix_ticker(ticker):
    if not ticker: return ticker
    # Case: 6-digit numeric ticker or ticker starts with 0 (KR stock)
    if (len(ticker) == 6 and ticker.isdigit()):
        return f"{ticker}.KS"
    return ticker

def robust_jsonify(data):
    """Recursively replace NaN with None for JSON compatibility."""
    def clean(obj):
        if isinstance(obj, dict):
            return {k: clean(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [clean(x) for x in obj]
        elif isinstance(obj, float):
            if np.isnan(obj) or np.isinf(obj):
                return None
            return obj
        elif pd.isna(obj): # Support for pandas NA types
            return None
        return obj
    return jsonify(clean(data))

# Sector mapping for major US stocks (S&P 500 + popular stocks)
SECTOR_MAP = {
    # Technology
    'AAPL': 'Tech', 'MSFT': 'Tech', 'NVDA': 'Tech', 'AVGO': 'Tech', 'ORCL': 'Tech',
    'CRM': 'Tech', 'AMD': 'Tech', 'ADBE': 'Tech', 'CSCO': 'Tech', 'INTC': 'Tech',
    'IBM': 'Tech', 'MU': 'Tech', 'QCOM': 'Tech', 'TXN': 'Tech', 'NOW': 'Tech',
    'AMAT': 'Tech', 'LRCX': 'Tech', 'KLAC': 'Tech', 'SNPS': 'Tech', 'CDNS': 'Tech',
    'ADI': 'Tech', 'MRVL': 'Tech', 'FTNT': 'Tech', 'PANW': 'Tech', 'CRWD': 'Tech',
    'SNOW': 'Tech', 'DDOG': 'Tech', 'ZS': 'Tech', 'NET': 'Tech', 'PLTR': 'Tech',
    'DELL': 'Tech', 'HPQ': 'Tech', 'HPE': 'Tech', 'KEYS': 'Tech', 'SWKS': 'Tech',
    # Financials
    'BRK-B': 'Fin', 'JPM': 'Fin', 'V': 'Fin', 'MA': 'Fin', 'BAC': 'Fin',
    'WFC': 'Fin', 'GS': 'Fin', 'MS': 'Fin', 'SPGI': 'Fin', 'AXP': 'Fin',
    'C': 'Fin', 'BLK': 'Fin', 'SCHW': 'Fin', 'CME': 'Fin', 'CB': 'Fin',
    'PGR': 'Fin', 'MMC': 'Fin', 'AON': 'Fin', 'ICE': 'Fin', 'MCO': 'Fin',
    'USB': 'Fin', 'PNC': 'Fin', 'TFC': 'Fin', 'AIG': 'Fin', 'MET': 'Fin',
    'PRU': 'Fin', 'ALL': 'Fin', 'TRV': 'Fin', 'COIN': 'Fin', 'HOOD': 'Fin',
    # Healthcare
    'LLY': 'Health', 'UNH': 'Health', 'JNJ': 'Health', 'ABBV': 'Health', 'MRK': 'Health',
    'PFE': 'Health', 'TMO': 'Health', 'ABT': 'Health', 'DHR': 'Health', 'BMY': 'Health',
    'AMGN': 'Health', 'GILD': 'Health', 'VRTX': 'Health', 'ISRG': 'Health', 'MDT': 'Health',
    'SYK': 'Health', 'BSX': 'Health', 'REGN': 'Health', 'ZTS': 'Health', 'ELV': 'Health',
    'CI': 'Health', 'HUM': 'Health', 'CVS': 'Health', 'MCK': 'Health', 'CAH': 'Health',
    'GEHC': 'Health', 'DXCM': 'Health', 'IQV': 'Health', 'BIIB': 'Health', 'MRNA': 'Health',
    # Energy
    'XOM': 'Energy', 'CVX': 'Energy', 'COP': 'Energy', 'SLB': 'Energy', 'EOG': 'Energy',
    'MPC': 'Energy', 'PSX': 'Energy', 'VLO': 'Energy', 'OXY': 'Energy', 'WMB': 'Energy',
    'DVN': 'Energy', 'HES': 'Energy', 'HAL': 'Energy', 'BKR': 'Energy', 'KMI': 'Energy',
    'FANG': 'Energy', 'PXD': 'Energy', 'TRGP': 'Energy', 'OKE': 'Energy', 'ET': 'Energy',
    # Consumer Discretionary
    'AMZN': 'Cons', 'TSLA': 'Cons', 'HD': 'Cons', 'MCD': 'Cons', 'NKE': 'Cons',
    'LOW': 'Cons', 'SBUX': 'Cons', 'TJX': 'Cons', 'BKNG': 'Cons', 'CMG': 'Cons',
    'ORLY': 'Cons', 'AZO': 'Cons', 'ROST': 'Cons', 'DHI': 'Cons', 'LEN': 'Cons',
    'GM': 'Cons', 'F': 'Cons', 'MAR': 'Cons', 'HLT': 'Cons', 'YUM': 'Cons',
    'DG': 'Cons', 'DLTR': 'Cons', 'BBY': 'Cons', 'ULTA': 'Cons', 'POOL': 'Cons',
    'LULU': 'Cons',
    # Consumer Staples
    'WMT': 'Staple', 'PG': 'Staple', 'COST': 'Staple', 'KO': 'Staple', 'PEP': 'Staple',
    'PM': 'Staple', 'MDLZ': 'Staple', 'MO': 'Staple', 'CL': 'Staple', 'KMB': 'Staple',
    'GIS': 'Staple', 'K': 'Staple', 'HSY': 'Staple', 'SYY': 'Staple', 'STZ': 'Staple',
    'KHC': 'Staple', 'KR': 'Staple', 'EL': 'Staple', 'CHD': 'Staple', 'CLX': 'Staple',
    'KDP': 'Staple', 'TAP': 'Staple', 'ADM': 'Staple', 'BG': 'Staple', 'MNST': 'Staple',
    # Industrials
    'CAT': 'Indust', 'GE': 'Indust', 'RTX': 'Indust', 'HON': 'Indust', 'UNP': 'Indust',
    'BA': 'Indust', 'DE': 'Indust', 'LMT': 'Indust', 'UPS': 'Indust', 'MMM': 'Indust',
    'GD': 'Indust', 'NOC': 'Indust', 'CSX': 'Indust', 'NSC': 'Indust', 'WM': 'Indust',
    'EMR': 'Indust', 'ETN': 'Indust', 'ITW': 'Indust', 'PH': 'Indust', 'ROK': 'Indust',
    'FDX': 'Indust', 'CARR': 'Indust', 'TT': 'Indust', 'PCAR': 'Indust', 'FAST': 'Indust',
    # Materials
    'LIN': 'Mater', 'APD': 'Mater', 'SHW': 'Mater', 'FCX': 'Mater', 'ECL': 'Mater',
    'NEM': 'Mater', 'NUE': 'Mater', 'DOW': 'Mater', 'DD': 'Mater', 'VMC': 'Mater',
    'CTVA': 'Mater', 'PPG': 'Mater', 'MLM': 'Mater', 'IP': 'Mater', 'PKG': 'Mater',
    'ALB': 'Mater', 'GOLD': 'Mater', 'FMC': 'Mater', 'CF': 'Mater', 'MOS': 'Mater',
    # Utilities
    'NEE': 'Util', 'SO': 'Util', 'DUK': 'Util', 'CEG': 'Util', 'SRE': 'Util',
    'AEP': 'Util', 'D': 'Util', 'PCG': 'Util', 'EXC': 'Util', 'XEL': 'Util',
    'ED': 'Util', 'WEC': 'Util', 'ES': 'Util', 'AWK': 'Util', 'DTE': 'Util',
    # Real Estate
    'PLD': 'REIT', 'AMT': 'REIT', 'EQIX': 'REIT', 'SPG': 'REIT', 'PSA': 'REIT',
    'O': 'REIT', 'WELL': 'REIT', 'DLR': 'REIT', 'CCI': 'REIT', 'AVB': 'REIT',
    'CBRE': 'REIT', 'SBAC': 'REIT', 'WY': 'REIT', 'EQR': 'REIT', 'VTR': 'REIT',
    # Communication Services
    'META': 'Comm', 'GOOGL': 'Comm', 'GOOG': 'Comm', 'NFLX': 'Comm', 'DIS': 'Comm',
    'T': 'Comm', 'VZ': 'Comm', 'CMCSA': 'Comm', 'TMUS': 'Comm', 'CHTR': 'Comm',
    'EA': 'Comm', 'TTWO': 'Comm', 'RBLX': 'Comm', 'PARA': 'Comm', 'WBD': 'Comm',
    'MTCH': 'Comm', 'LYV': 'Comm', 'OMC': 'Comm', 'IPG': 'Comm', 'FOXA': 'Comm',
    # IT Services & Software
    'EPAM': 'Tech', 'ALGN': 'Health',
}

# Persistent sector cache file
SECTOR_CACHE_FILE = os.path.join(os.path.dirname(__file__), 'sector_cache.json')

def _load_sector_cache() -> dict:
    """Load sector cache from file"""
    try:
        if os.path.exists(SECTOR_CACHE_FILE):
            with open(SECTOR_CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return {}

def _save_sector_cache(cache: dict):
    """Save sector cache to file"""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(SECTOR_CACHE_FILE), exist_ok=True)
        with open(SECTOR_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving sector cache: {e}")

# Load cache at startup
_sector_cache = _load_sector_cache()

def get_sector(ticker: str) -> str:
    """Get sector for a ticker, auto-fetch from yfinance if not in SECTOR_MAP"""
    global _sector_cache
    
    # Check static map first
    if ticker in SECTOR_MAP:
        return SECTOR_MAP[ticker]
    
    # Check persistent cache
    if ticker in _sector_cache:
        return _sector_cache[ticker]
    
    # Fetch from yfinance and save to file
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        sector = info.get('sector', '')
        
        # Map sector to short code
        sector_short_map = {
            'Technology': 'Tech',
            'Information Technology': 'Tech',
            'Healthcare': 'Health',
            'Health Care': 'Health',
            'Financials': 'Fin',
            'Financial Services': 'Fin',
            'Consumer Discretionary': 'Cons',
            'Consumer Cyclical': 'Cons',
            'Consumer Staples': 'Staple',
            'Consumer Defensive': 'Staple',
            'Energy': 'Energy',
            'Industrials': 'Indust',
            'Materials': 'Mater',
            'Basic Materials': 'Mater',
            'Utilities': 'Util',
            'Real Estate': 'REIT',
            'Communication Services': 'Comm',
        }
        
        short_sector = sector_short_map.get(sector, sector[:5] if sector else '-')
        
        # Save to cache and persist to file
        _sector_cache[ticker] = short_sector
        _save_sector_cache(_sector_cache)
        print(f"✅ Cached sector for {ticker}: {short_sector}")
        
        return short_sector
    except Exception as e:
        print(f"Error fetching sector for {ticker}: {e}")
        _sector_cache[ticker] = '-'
        _save_sector_cache(_sector_cache)
        return '-'

def calculate_rsi(series, period=14):
    delta = series.diff(1)
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def analyze_trend(df):
    if len(df) < 50: return 50, "Neutral", 0
    curr = df.iloc[-1]
    prev = df.iloc[-2]
    
    # Calculate MAs
    ma20 = curr.get('MA20', 0)
    ma50 = curr.get('MA50', 0)
    ma200 = curr.get('MA200', 0)
    price = curr.get('Close', 0)
    rsi = curr.get('RSI', 50)
    
    score = 50
    signal = "Neutral"
    
    # Simple Trend Logic
    if price > ma20 > ma50 > ma200:
        score = 90
        signal = "Strong Buy"
    elif ma20 > ma50 and (prev.get('MA20', 0) <= prev.get('MA50', 0) or price > ma20):
        score = 80
        signal = "Buy (Golden Cross)"
    elif price < ma20 < ma50:
        score = 30
        signal = "Sell (Downtrend)"
    elif rsi > 75:
        score -= 10
        signal = "Overbought"
        
    return score, signal, rsi

# Load Ticker Map for Korea
try:
    map_df = pd.read_csv('ticker_to_yahoo_map.csv', dtype=str)
    TICKER_TO_YAHOO_MAP = dict(zip(map_df['ticker'], map_df['yahoo_ticker']))
    print(f"Loaded {len(TICKER_TO_YAHOO_MAP)} verified KR ticker mappings.")
except:
    TICKER_TO_YAHOO_MAP = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/kr/recommendations')
def get_kr_recommendations():
    try:
        csv_path = 'recommendation_history.csv'
        if not os.path.exists(csv_path):
            return jsonify({'error': 'Recommendation history not found'}), 404
        df = pd.read_csv(csv_path)
        recommendations = df.to_dict(orient='records')
        dates = sorted(df['recommendation_date'].unique().tolist(), reverse=True)
        return jsonify({'dates': dates, 'data': recommendations})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/kr/performance')
def get_kr_performance():
    try:
        csv_path = 'performance_report.csv'
        if not os.path.exists(csv_path):
            return jsonify({'error': 'Performance report not found'}), 404
        df = pd.read_csv(csv_path)
        summary = {
            'total_count': len(df),
            'avg_return': float(df['return'].mean()) if not df.empty else 0,
            'win_rate': float((df['return'] > 0).mean() * 100) if not df.empty else 0,
            'top_performers': df.sort_values('return', ascending=False).head(5).to_dict(orient='records')
        }
        return jsonify({'summary': summary, 'data': df.to_dict(orient='records')})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/kr/market-status')
def get_kr_market_status():
    try:
        prices_path = 'daily_prices.csv'
        if not os.path.exists(prices_path):
            return jsonify({'status': 'UNKNOWN', 'reason': 'No price data'}), 404
        df = pd.read_csv(prices_path, dtype={'ticker': str})
        target_ticker = '069500' # KODEX 200
        market_df = df[df['ticker'] == target_ticker].copy()
        if market_df.empty:
            target_ticker = '005930' # Samsung
            market_df = df[df['ticker'] == target_ticker].copy()
        if market_df.empty:
             return jsonify({'status': 'UNKNOWN', 'reason': 'Market proxy data not found'}), 404
        market_df['date'] = pd.to_datetime(market_df['date'])
        market_df = market_df.sort_values('date')
        if len(market_df) < 200:
             return jsonify({'status': 'NEUTRAL', 'reason': 'Insufficient data'}), 200
        market_df['MA200'] = market_df['current_price'].rolling(200).mean()
        last = market_df.iloc[-1]
        price = last['current_price']
        ma200 = last['MA200']
        status = "RISK_ON" if price > ma200 else "RISK_OFF"
        return jsonify({
            'status': status,
            'score': 80 if status == "RISK_ON" else 20,
            'current_price': float(price),
            'ma200': float(ma200),
            'date': last['date'].strftime('%Y-%m-%d'),
            'symbol': target_ticker
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/portfolio')
def get_portfolio_data(market=None):
    try:
        if market == 'KR':
            json_path = 'kr_smart_money_picks.json'
            if not os.path.exists(json_path):
                 return jsonify({'error': 'KR data not found'}), 404
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            top_holdings = []
            for p in data.get('top_picks', [])[:10]:
                top_holdings.append({
                    'ticker': p['ticker'],
                    'name': p['name'],
                    'price': float(p['current_price']),
                    'recommendation_price': float(p['current_price']),
                    'return_pct': 0.0,
                    'score': float(p['final_investment_score']),
                    'grade': p['investment_grade'],
                    'wave': 'N/A',
                    'ytd': 0
                })
            latest_date = data.get('updated', datetime.now().strftime('%Y-%m-%d'))
        else: 
            target_date = request.args.get('date')
            if target_date:
                csv_path = 'recommendation_history.csv'
                if not os.path.exists(csv_path): return jsonify({'error': 'History not found'}), 404
                df = pd.read_csv(csv_path, dtype={'ticker': str})
                df = df[df['recommendation_date'] == target_date]
                top_holdings_df = df.sort_values(by='final_investment_score', ascending=False).head(10)
                top_holdings = []
                for _, row in top_holdings_df.iterrows():
                    top_holdings.append({
                        'ticker': str(row['ticker']).zfill(6),
                        'name': row['name'],
                        'price': float(row['current_price']),
                        'recommendation_price': float(row['current_price']),
                        'return_pct': 0.0,
                        'score': float(row['final_investment_score']),
                        'grade': row['investment_grade'],
                        'wave': row.get('wave_stage', 'N/A'),
                        'ytd': 0
                    })
                latest_date = target_date
            else:
                csv_path = 'wave_transition_analysis_results.csv'
                if not os.path.exists(csv_path):
                    return jsonify({'error': 'Live analysis results not found'}), 404
                df = pd.read_csv(csv_path, dtype={'ticker': str})
                # Handle grades with or without emojis
                top_picks = df[df['investment_grade'].str.contains('S급|A급', na=False)]
                
                # US Filtering (Default)
                top_picks = top_picks[top_picks['ticker'].astype(str).str.match(r'^[A-Za-z]+$')]

                top_holdings_df = top_picks.sort_values(by='final_investment_score', ascending=False).head(10)
                top_holdings = []
                for _, row in top_holdings_df.iterrows():
                    top_holdings.append({
                        'ticker': str(row['ticker']).zfill(6),
                        'name': row['name'],
                        'price': float(row['current_price']),
                        'recommendation_price': float(row['current_price']),
                        'return_pct': 0.0,
                        'score': float(row['final_investment_score']),
                        'grade': row['investment_grade'],
                        'wave': row.get('wave_stage', 'N/A'),
                        'sd_stage': row.get('supply_demand_stage', 'N/A'),
                        'inst_trend': row.get('institutional_trend', 'N/A'),
                        'ytd': float(row.get('price_change_20d', 0)) * 100
                    })
                latest_date = df['current_date'].iloc[0] if not df.empty else None

        # Performance Data
        performance_data = []
        perf_csv_path = 'performance_report.csv'
        if os.path.exists(perf_csv_path):
            perf_df = pd.read_csv(perf_csv_path)
            recent_perf = perf_df.sort_values('rec_date', ascending=False).head(10)
            for _, row in recent_perf.iterrows():
                performance_data.append({
                    'ticker': row['ticker'],
                    'name': row['name'],
                    'return': f"{row['return']:.1f}%",
                    'date': row['rec_date'],
                    'days': row['days']
                })

        # Style Box
        style_box = {'large_value': 20, 'large_core': 30, 'large_growth': 10, 'mid_value': 10, 'mid_core': 15, 'mid_growth': 5, 'small_value': 3, 'small_core': 5, 'small_growth': 2}

        # Market Indices
        market_indices = []
        indices_list = ['^DJI', '^GSPC', '^IXIC', '^VIX', 'GC=F', 'CL=F', 'BTC-USD', 'KRW=X']
        try:
            idx_data = yf.download(indices_list, period='5d', progress=False)
            if not idx_data.empty:
                closes = idx_data['Close']
                for ticker in indices_list:
                    if ticker in closes.columns:
                        series = closes[ticker].dropna()
                        if len(series) >= 2:
                            curr, prev = series.iloc[-1], series.iloc[-2]
                            market_indices.append({
                                'name': ticker.replace('^', ''),
                                'price': f"{curr:,.2f}",
                                'change': f"{curr-prev:,.2f}",
                                'change_pct': round(((curr/prev)-1)*100, 2),
                                'color': 'red' if curr >= prev else 'blue'
                            })
        except: pass

        return robust_jsonify({
            'market_indices': market_indices,
            'top_holdings': top_holdings,
            'style_box': style_box,
            'performance': performance_data,
            'latest_date': latest_date
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/kr/portfolio')
def get_kr_portfolio_data():
    return get_portfolio_data(market='KR')

@app.route('/api/us/portfolio')
def get_us_portfolio_data():
    try:
        indices_map = {'^DJI': 'Dow Jones', '^GSPC': 'S&P 500', '^IXIC': 'NASDAQ', '^VIX': 'VIX', 'BTC-USD': 'Bitcoin'}
        market_indices = []
        for ticker, name in indices_map.items():
            try:
                hist = yf.Ticker(ticker).history(period='5d')
                if not hist.empty:
                    curr, prev = hist['Close'].iloc[-1], hist['Close'].iloc[-2]
                    market_indices.append({
                        'name': name, 'price': f"{curr:,.2f}", 'change': f"{curr-prev:+,.2f}",
                        'change_pct': round(((curr/prev)-1)*100, 2),
                        'color': 'green' if curr >= prev else 'red'
                    })
            except: pass
        # Populate holdings from final report for US market visibility
        top_holdings = []
        report_path = os.path.join(os.path.dirname(__file__), 'final_top10_report.json')
        if os.path.exists(report_path):
            with open(report_path, 'r', encoding='utf-8') as f:
                report = json.load(f)
                for p in report.get('top_picks', []):
                    top_holdings.append({
                        'ticker': p['ticker'],
                        'name': p.get('name', p['ticker']),
                        'score': p.get('final_score', 0),
                        'current_price': p.get('current_price', 0),
                        'recommendation': p.get('ai_recommendation', 'N/A'),
                        'grade': p.get('final_grade', 'N/A')
                    })
        
        return robust_jsonify({'market_indices': market_indices, 'top_holdings': top_holdings, 'style_box': {}})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/us/smart-money')
def get_us_smart_money():
    try:
        csv_path = os.path.join(os.path.dirname(__file__), 'smart_money_picks_v2.csv')
        if not os.path.exists(csv_path):
            csv_path = os.path.join(os.path.dirname(__file__), 'smart_money_picks.csv')
        if not os.path.exists(csv_path):
            return jsonify({'error': 'Smart money picks not found'}), 404
        df = pd.read_csv(csv_path)
        top_picks = []
        for _, row in df.head(20).iterrows():
            ticker = row['ticker']
            top_picks.append({
                'ticker': ticker, 'name': row.get('name', ticker), 'sector': get_sector(ticker),
                'final_score': row.get('smart_money_score', row.get('composite_score', 0)),
                'current_price': row.get('current_price', 0),
                'price_at_rec': row.get('current_price', 0),
                'change_since_rec': 0,
                'category': row.get('category', 'N/A'),
                'grade': row.get('grade', 'N/A')
            })
        return jsonify({'top_picks': top_picks, 'summary': {'total_analyzed': len(df)}})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/us/etf-flows')
def get_us_etf_flows():
    try:
        csv_path = os.path.join(os.path.dirname(__file__), 'us_etf_flows.csv')
        if not os.path.exists(csv_path):
            return jsonify({'error': 'ETF flows not found'}), 404
        df = pd.read_csv(csv_path)
        broad_market = df[df['category'] == 'Broad Market']
        broad_score = round(broad_market['flow_score'].mean(), 1) if not broad_market.empty else 50
        ai_path = os.path.join(os.path.dirname(__file__), 'etf_flow_analysis.json')
        ai_text = ""
        if os.path.exists(ai_path):
            with open(ai_path, 'r', encoding='utf-8') as f:
                ai_text = json.load(f).get('ai_analysis', '')
        return jsonify({
            'market_sentiment_score': broad_score,
            'top_inflows': df.nlargest(5, 'flow_score').to_dict(orient='records'),
            'top_outflows': df.nsmallest(5, 'flow_score').to_dict(orient='records'),
            'ai_analysis': ai_text
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/kr/smart-money')
def get_kr_smart_money():
    try:
        path = os.path.join(os.path.dirname(__file__), 'kr_smart_money_picks.json')
        if not os.path.exists(path): return jsonify({'error': 'Not found'}), 404
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Map for frontend compatibility
            for p in data.get('top_picks', []):
                p['final_score'] = p.get('final_investment_score', 0)
                p['grade'] = p.get('investment_grade', 'N/A')
            return robust_jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/us/stock-chart/<ticker>')
def get_us_stock_chart(ticker):
    try:
        ticker = fix_ticker(ticker)
        period = request.args.get('period', '1y')
        hist = yf.Ticker(ticker).history(period=period)
        if hist.empty: return jsonify({'error': 'No data'}), 404
        candles = [{'time': int(d.timestamp()), 'open': round(r['Open'], 2), 'high': round(r['High'], 2), 'low': round(r['Low'], 2), 'close': round(r['Close'], 2)} for d, r in hist.iterrows()]
        return jsonify({'ticker': ticker, 'candles': candles})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/us/history-dates')
def get_us_history_dates():
    try:
        h_dir = os.path.join(os.path.dirname(__file__), 'history')
        if not os.path.exists(h_dir): return jsonify({'dates': []})
        dates = sorted([f[6:-5] for f in os.listdir(h_dir) if f.startswith('picks_')], reverse=True)
        return jsonify({'dates': dates})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/us/macro-analysis')
def get_us_macro_analysis():
    try:
        lang = request.args.get('lang', 'ko')
        path = os.path.join(os.path.dirname(__file__), "macro_analysis.json")
        ai_analysis = "N/A"
        macro_indicators = {}
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                ai_analysis = data.get(f'ai_analysis{"_en" if lang=="en" else ""}', data.get('ai_analysis', ai_analysis))
                macro_indicators = data.get('macro_indicators', {})
        return robust_jsonify({'macro_indicators': macro_indicators, 'ai_analysis': ai_analysis})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/us/sector-heatmap')
def get_us_sector_heatmap():
    try:
        path = os.path.join(os.path.dirname(__file__), 'sector_heatmap.json')
        if not os.path.exists(path): return jsonify({'error': 'Not found'}), 404
        with open(path, 'r', encoding='utf-8') as f:
            return jsonify(json.load(f))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/us/beginner-briefing')
def get_us_beginner_briefing():
    try:
        path = os.path.join(os.path.dirname(__file__), 'beginner_briefing.json')
        if not os.path.exists(path): return jsonify({'error': 'Not found'}), 404
        with open(path, 'r', encoding='utf-8') as f:
            return jsonify(json.load(f))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/us/options-flow')
def get_us_options_flow():
    try:
        path = os.path.join(os.path.dirname(__file__), 'options_flow.json')
        if not os.path.exists(path): return jsonify({'error': 'Not found'}), 404
        with open(path, 'r', encoding='utf-8') as f:
            return jsonify(json.load(f))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/kr/beginner-briefing')
def get_kr_beginner_briefing():
    try:
        path = os.path.join(os.path.dirname(__file__), 'kr_beginner_briefing.json')
        if not os.path.exists(path): return jsonify({'error': 'Not found'}), 404
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Add stock names to recommendations from kr_smart_money_picks.json
        picks_path = os.path.join(os.path.dirname(__file__), 'kr_smart_money_picks.json')
        if os.path.exists(picks_path):
            with open(picks_path, 'r', encoding='utf-8') as f:
                picks_data = json.load(f)
                # Create ticker -> name mapping
                ticker_name_map = {p['ticker']: p['name'] for p in picks_data.get('top_picks', [])}
                
                # Add name to each recommendation
                for rec in data.get('top_recommendations', []):
                    ticker = rec.get('ticker', '')
                    rec['name'] = ticker_name_map.get(ticker, ticker)
        
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/us/ai-summary/<ticker>')
def get_us_ai_summary(ticker):
    try:
        lang = request.args.get('lang', 'ko')
        # Check KR summaries first if 6-digit
        if len(ticker) == 6 and ticker.isdigit():
            path = os.path.join(os.path.dirname(__file__), 'kr_ai_summaries.json')
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    summaries = json.load(f)
                    if ticker in summaries:
                        s = summaries[ticker]
                        return jsonify({
                            'ticker': ticker,
                            'summary': s.get('summary', ''),
                            'bull_points': s.get('bull_points', []),
                            'bear_points': s.get('bear_points', []),
                            'final_opinion': s.get('final_opinion', ''),
                            'updated': s.get('updated', '')
                        })

        path = os.path.join(os.path.dirname(__file__), 'ai_summaries.json')
        if not os.path.exists(path): return jsonify({'error': 'Not found'}), 404
        with open(path, 'r', encoding='utf-8') as f:
            summaries = json.load(f)
        if ticker not in summaries: return jsonify({'error': 'No summary'}), 404
        s = summaries[ticker]
        
        # Priority: requested language field, then default summary
        summary_text = s.get(f'summary_{lang}', s.get('summary', ''))
        
        return jsonify({
            'ticker': ticker,
            'summary': summary_text,
            'updated': s.get('updated', '')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stock/<ticker>')
def get_stock_detail(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y")
        price_history = [{'time': d.strftime('%Y-%m-%d'), 'open': float(r['Open']), 'high': float(r['High']), 'low': float(r['Low']), 'close': float(r['Close']), 'volume': int(r['Volume'])} for d, r in hist.iterrows()]
        return jsonify({'ticker': ticker, 'price_history': price_history})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/realtime-prices', methods=['POST'])
def get_realtime_prices():
    try:
        tickers = request.get_json().get('tickers', [])
        if not tickers: return jsonify({})
        df = yf.download(tickers, period='1d', interval='1m', progress=False)
        if df.empty: return jsonify({})
        prices = {}
        for t in tickers:
            try:
                row = df.iloc[-1]
                val = row['Close'][t] if isinstance(row['Close'], pd.Series) else row['Close']
                prices[t] = {'current': float(val), 'date': datetime.now().strftime('%Y-%m-%d')}
            except: pass
        return jsonify(prices)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/us/calendar')
def get_us_calendar():
    try:
        path = os.path.join(os.path.dirname(__file__), 'weekly_calendar.json')
        if not os.path.exists(path): return jsonify({'events': []}), 404
        with open(path, 'r', encoding='utf-8') as f:
            return jsonify(json.load(f))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/us/technical-indicators/<ticker>')
def get_technical_indicators(ticker):
    try:
        import ta
        ticker = fix_ticker(ticker)
        hist = yf.Ticker(ticker).history(period='1y')
        if hist.empty: return jsonify({'error': 'No data'}), 404
        close = hist['Close']
        rsi = ta.momentum.RSIIndicator(close).rsi()
        macd = ta.trend.MACD(close)
        bb = ta.volatility.BollingerBands(close)
        
        def make_ser(s): return [{'time': int(d.timestamp()), 'value': round(float(v), 2)} for d, v in s.dropna().items()]
        
        return jsonify({
            'rsi': make_ser(rsi),
            'macd': {'macd_line': make_ser(macd.macd()), 'signal_line': make_ser(macd.macd_signal()), 'histogram': make_ser(macd.macd_diff())},
            'bollinger': {'upper': make_ser(bb.bollinger_hband()), 'middle': make_ser(bb.bollinger_mavg()), 'lower': make_ser(bb.bollinger_lband())}
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/kr/etf-flows')
def get_kr_etf_flows():
    try:
        path = os.path.join(os.path.dirname(__file__), 'kr_etf_flows.json')
        if not os.path.exists(path): return jsonify({'error': 'Not found'}), 404
        with open(path, 'r', encoding='utf-8') as f:
            return jsonify(json.load(f))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/kr/macro-analysis')
def get_kr_macro_analysis():
    try:
        lang = request.args.get('lang', 'ko')
        path = os.path.join(os.path.dirname(__file__), 'kr_macro_analysis.json')
        if not os.path.exists(path): return jsonify({'error': 'Not found'}), 404
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Match US structure
            ai_analysis = data.get(f'ai_analysis{"_en" if lang=="en" else ""}', data.get('ai_analysis', 'N/A'))
            macro_indicators = data.get('macro_indicators', {})
            return robust_jsonify({'macro_indicators': macro_indicators, 'ai_analysis': ai_analysis})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/kr/sector-heatmap')
def get_kr_sector_heatmap():
    try:
        path = os.path.join(os.path.dirname(__file__), 'kr_sector_heatmap.json')
        if not os.path.exists(path): return jsonify({'sector_performance': {'sectors': []}})
        with open(path, 'r', encoding='utf-8') as f:
            payload = json.load(f)
            # Ensure it has the nested structure the frontend expects
            return jsonify({'sector_performance': payload})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/calendar')
def get_global_calendar():
    try:
        path = os.path.join(os.path.dirname(__file__), 'weekly_calendar.json')
        if not os.path.exists(path): return jsonify({'events': [], 'ai_briefing': {'weekly_outlook': 'No data available.'}})
        with open(path, 'r', encoding='utf-8') as f:
            return jsonify(json.load(f))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/kr/options-flow')
def get_kr_options_flow():
    try:
        path = os.path.join(os.path.dirname(__file__), 'kr_options_flow.json')
        if not os.path.exists(path): return jsonify([])
        with open(path, 'r', encoding='utf-8') as f:
            return jsonify(json.load(f))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(port=5001, debug=True, use_reloader=False)
