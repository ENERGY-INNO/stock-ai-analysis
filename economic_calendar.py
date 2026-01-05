#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📅 Calendar Analyst Persona: Economic Calendar
================================================
Tracks major economic events and provides AI impact analysis.

Author: Calendar Analyst Persona
Purpose: Keep investors informed of market-moving events
"""

import os
import json
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, List
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class EconomicCalendar:
    """
    경제 이벤트 캘린더
    
    주요 추적 이벤트:
    - FOMC 금리 결정
    - 고용 보고서 (NFP)
    - CPI/PPI 인플레이션
    - GDP 발표
    - 실적 시즌
    """
    
    def __init__(self, data_dir: str = '.'):
        self.data_dir = data_dir
        self.output_file = os.path.join(data_dir, 'weekly_calendar.json')
        self.api_key = os.getenv('GOOGLE_API_KEY')
        self.finnhub_key = os.getenv('FINNHUB_API_KEY')
        self.ecos_key = os.getenv('ECOS_API_KEY')
        self.kr_indicators = {}  # Cache Korean indicator values
    
    def _fetch_ecos_indicators(self) -> Dict:
        """Fetch key Korean economic indicators from ECOS API"""
        if not self.ecos_key:
            return {}
        
        try:
            url = f"https://ecos.bok.or.kr/api/KeyStatisticList/{self.ecos_key}/json/kr/1/100"
            resp = requests.get(url, timeout=10)
            if resp.status_code != 200:
                logger.error(f"ECOS API error: {resp.status_code}")
                return {}
            
            data = resp.json()
            indicators = {}
            
            for item in data.get('KeyStatisticList', {}).get('row', []):
                name = item.get('KEYSTAT_NAME', '')
                value = item.get('DATA_VALUE', '')
                unit = item.get('UNIT_NAME', '')
                cycle = item.get('CYCLE', '')
                
                # Store useful indicators
                if '원/달러' in name:
                    indicators['usd_krw'] = f"₩{value}"
                elif 'GDP' in name and '명목' in name:
                    indicators['gdp'] = f"{value} {unit}"
                elif 'M2' in name:
                    indicators['m2'] = f"{value} {unit}"
                elif '기준금리' in name:
                    indicators['bok_rate'] = f"{value}%"
            
            logger.info(f"✅ Fetched {len(indicators)} Korean indicators from ECOS")
            return indicators
            
        except Exception as e:
            logger.error(f"ECOS fetch error: {e}")
            return {}
    
    def get_scheduled_events(self) -> List[Dict]:
        """Get major scheduled economic events (US & KR)"""
        events = []
        
        # Try to fetch real US events from Finnhub
        us_events = self._fetch_finnhub_events()
        
        # Fetch KR events (currently using curated list, can be expanded)
        kr_events = self._get_kr_events()
        
        all_events = us_events + kr_events
        
        # Filter to upcoming 45 days
        today = datetime.now().date()
        end_date = today + timedelta(days=45)
        
        for event in all_events:
            event_date = datetime.strptime(event['date'], '%Y-%m-%d').date()
            if today <= event_date <= end_date:
                days_until = (event_date - today).days
                event['days_until'] = days_until
                # Get bilingual descriptions
                descs = self._get_event_descriptions(event.get('event_en', event.get('event', '')))
                event['description_en'] = event.get('description_en', descs['en'])
                event['description_ko'] = event.get('description_ko', descs['ko'])
                event['event'] = event.get('event_en', event.get('event', ''))
                event['description'] = event['description_en']
                events.append(event)
        
        # Sort by date
        events.sort(key=lambda x: x['date'])
        
        return events
    
    def _fetch_finnhub_events(self) -> List[Dict]:
        """Fetch US economic events - try web scraping from Investing.com"""
        try:
            return self._scrape_investing_calendar()
        except Exception as e:
            logger.warning(f"⚠️ Investing.com scraping failed: {e}, using curated events")
            return self._get_curated_us_events()
    
    def _scrape_investing_calendar(self) -> List[Dict]:
        """Scrape economic calendar from Investing.com"""
        import re
        from datetime import datetime, timedelta
        
        # Get next 30 days of events
        today = datetime.now()
        events = []
        
        # Investing.com economic calendar URL
        url = "https://www.investing.com/economic-calendar/"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code != 200:
                logger.error(f"Investing.com returned {resp.status_code}")
                return self._get_curated_us_events()
            
            html = resp.text
            
            # Simple regex parsing for event data (Investing.com structures)
            # Look for US events with High/Medium impact
            us_events_parsed = []
            
            # Pattern for event rows - simplified extraction
            # Due to complexity of Investing.com, fallback to curated list
            logger.info("📊 Using curated US economic events (web scraping requires more complex parsing)")
            return self._get_curated_us_events()
            
        except Exception as e:
            logger.error(f"Investing.com scrape error: {e}")
            return self._get_curated_us_events()
    
    def _get_curated_us_events(self) -> List[Dict]:
        """Curated list of major US economic events based on Federal Reserve schedule"""
        today = datetime.now()
        year = today.year
        month = today.month
        
        events = []
        
        # Major US Economic Events - Dynamic based on current date
        # Source: Federal Reserve, BLS, BEA schedules
        
        # Calculate upcoming events based on typical release patterns
        # NFP: First Friday of month
        # CPI: Usually 10th-15th of month
        # FOMC: 8 meetings per year (Jan, Mar, May, Jun, Jul, Sep, Nov, Dec typically)
        # GDP: End of month (Advance ~30 days after quarter end)
        
        major_events = []
        
        # Generate events for next 3 months dynamically
        for month_offset in range(3):
            target_date = today + timedelta(days=30 * month_offset)
            year = target_date.year
            month = target_date.month
            
            # Nonfarm Payrolls - First Friday of month
            first_day = datetime(year, month, 1)
            first_friday = first_day + timedelta(days=(4 - first_day.weekday() + 7) % 7)
            major_events.append({
                'date': first_friday.strftime('%Y-%m-%d'),
                'event_en': f'Nonfarm Payrolls ({self._month_name((month - 2) % 12 + 1)})',
                'event_ko': f'비농업 고용지수 ({self._month_name_ko((month - 2) % 12 + 1)})',
                'impact': 'High',
                'category': 'Employment'
            })
            
            # CPI - Usually around 10th-15th
            cpi_date = datetime(year, month, 12)
            major_events.append({
                'date': cpi_date.strftime('%Y-%m-%d'),
                'event_en': f'CPI (YoY) ({self._month_name((month - 2) % 12 + 1)})',
                'event_ko': f'소비자물가지수 ({self._month_name_ko((month - 2) % 12 + 1)})',
                'impact': 'High',
                'category': 'Inflation'
            })
        
        # FOMC Meetings 2025-2026 (Fixed schedule from Federal Reserve)
        fomc_dates = [
            '2025-12-18', '2026-01-29', '2026-03-19', '2026-05-07',
            '2026-06-18', '2026-07-30', '2026-09-17', '2026-11-05', '2026-12-17'
        ]
        for fomc_date in fomc_dates:
            major_events.append({
                'date': fomc_date,
                'event_en': 'FOMC Interest Rate Decision',
                'event_ko': '연준 기준금리 결정',
                'impact': 'High',
                'category': 'Fed'
            })
        
        # GDP Releases (Advance estimate ~30 days after quarter end)
        gdp_dates = [
            ('2026-01-30', 'Q4', '4분기'),
            ('2026-04-30', 'Q1', '1분기'),
        ]
        for gdp_date, quarter_en, quarter_ko in gdp_dates:
            major_events.append({
                'date': gdp_date,
                'event_en': f'GDP (QoQ) ({quarter_en} Advance)',
                'event_ko': f'{quarter_ko} GDP 속보치',
                'impact': 'High',
                'category': 'Growth'
            })
        
        # Filter to upcoming 45 days and add country
        end_date = today + timedelta(days=45)
        today_date = today.date() if hasattr(today, 'date') else today
        
        for event in major_events:
            event_date = datetime.strptime(event['date'], '%Y-%m-%d').date()
            if today_date <= event_date <= end_date.date():
                event['country'] = 'US'
                events.append(event)
        
        # Remove duplicates based on date and event_en
        seen = set()
        unique_events = []
        for e in events:
            key = (e['date'], e['event_en'])
            if key not in seen:
                seen.add(key)
                unique_events.append(e)
        
        logger.info(f"✅ Loaded {len(unique_events)} curated US events")
        return unique_events
    
    def _translate_event_name(self, event_name: str) -> str:
        """Translate common US event names to Korean"""
        translations = {
            'Nonfarm Payrolls': '비농업 고용지수',
            'Non-Farm Payrolls': '비농업 고용지수',
            'CPI': '소비자물가지수(CPI)',
            'Consumer Price Index': '소비자물가지수(CPI)',
            'Core CPI': '근원 소비자물가지수',
            'PPI': '생산자물가지수(PPI)',
            'FOMC': 'FOMC 금리 결정',
            'Fed Interest Rate Decision': '연준 기준금리 결정',
            'GDP': 'GDP 성장률',
            'Gross Domestic Product': 'GDP 성장률',
            'Retail Sales': '소매판매',
            'Unemployment Rate': '실업률',
            'Initial Jobless Claims': '신규 실업수당 청구건수',
            'Durable Goods Orders': '내구재 주문',
            'ISM Manufacturing PMI': 'ISM 제조업 PMI',
            'ISM Services PMI': 'ISM 서비스업 PMI',
            'Housing Starts': '주택착공',
            'Building Permits': '건축허가',
            'Michigan Consumer Sentiment': '미시간 소비자심리지수',
            'Trade Balance': '무역수지',
            'Industrial Production': '산업생산',
            'Personal Income': '개인소득',
            'Personal Spending': '개인지출',
            'PCE Price Index': 'PCE 물가지수'
        }
        
        for en, ko in translations.items():
            if en.lower() in event_name.lower():
                # Append month/quarter if present
                if '(' in event_name:
                    period = event_name[event_name.find('('):]
                    return f"{ko} {period}"
                return ko
        
        return event_name  # Return original if no translation found
    
    def _categorize_event(self, event_name: str) -> str:
        """Categorize event by type"""
        categories = {
            'Employment': ['payroll', 'unemployment', 'jobless', 'jobs'],
            'Inflation': ['cpi', 'ppi', 'inflation', 'pce price'],
            'Fed': ['fomc', 'fed', 'interest rate'],
            'Growth': ['gdp', 'growth'],
            'Consumer': ['retail', 'consumer', 'spending', 'income', 'michigan'],
            'Manufacturing': ['ism', 'pmi', 'manufacturing', 'industrial', 'durable'],
            'Housing': ['housing', 'building', 'home'],
            'Trade': ['trade', 'export', 'import']
        }
        
        event_lower = event_name.lower()
        for category, keywords in categories.items():
            if any(kw in event_lower for kw in keywords):
                return category
        return 'Economic'
    
    def _get_kr_events(self) -> List[Dict]:
        """Get Korean economic events (curated list + potential API expansion)"""
        # These are major recurring Korean events
        # Can be expanded with ECOS API or web scraping
        today = datetime.now()
        year = today.year
        month = today.month
        
        events = []
        
        # BOK Interest Rate Decision - Usually 2nd or 4th Thursday
        # Trade Balance - Usually 1st day of month
        # CPI - Mid month
        # GDP - End of quarter
        
        # Generate events for next 2 months
        for m_offset in range(3):
            target_month = (month + m_offset - 1) % 12 + 1
            target_year = year + (month + m_offset - 1) // 12
            
            # Trade Balance (1st business day)
            events.append({
                'date': f'{target_year}-{target_month:02d}-01',
                'event_en': f'KOR Trade Balance ({self._month_name(target_month - 1 if target_month > 1 else 12)})',
                'event_ko': f'무역수지 ({self._month_name_ko(target_month - 1 if target_month > 1 else 12)})',
                'impact': 'Medium',
                'category': 'Trade',
                'country': 'KR'
            })
            
            # Korea CPI (Mid month, ~15th)
            events.append({
                'date': f'{target_year}-{target_month:02d}-15',
                'event_en': f'KOR Consumer Price Index ({self._month_name(target_month - 1 if target_month > 1 else 12)})',
                'event_ko': f'소비자물가지수 ({self._month_name_ko(target_month - 1 if target_month > 1 else 12)})',
                'impact': 'Medium',
                'category': 'Inflation',
                'country': 'KR'
            })
        
        # BOK Rate Decision (usually monthly, around mid-month)
        next_bok = self._get_next_bok_date()
        if next_bok:
            events.append({
                'date': next_bok,
                'event_en': 'BOK Interest Rate Decision',
                'event_ko': '한국은행 기준금리 결정',
                'impact': 'High',
                'category': 'Central Bank',
                'country': 'KR'
            })
        
        return events
    
    def _get_next_bok_date(self) -> str:
        """Calculate next BOK meeting date (approximation)"""
        # BOK usually meets on the 2nd or 4th Thursday of the month
        today = datetime.now()
        
        for month_offset in range(3):
            target = today + timedelta(days=30 * month_offset)
            year, month = target.year, target.month
            
            # Find 2nd Thursday
            first_day = datetime(year, month, 1)
            first_thursday = first_day + timedelta(days=(3 - first_day.weekday() + 7) % 7)
            second_thursday = first_thursday + timedelta(days=7)
            
            if second_thursday > today:
                return second_thursday.strftime('%Y-%m-%d')
        
        return None
    
    def _month_name(self, month: int) -> str:
        """Get English month abbreviation"""
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        return months[(month - 1) % 12]
    
    def _month_name_ko(self, month: int) -> str:
        """Get Korean month name"""
        return f'{((month - 1) % 12) + 1}월'
    
    def _get_fallback_us_events(self) -> List[Dict]:
        """Fallback demo events if API fails"""
        logger.info("📋 Using fallback US events")
        return [
            {'date': '2025-01-10', 'event_en': 'Nonfarm Payrolls (Dec)', 'event_ko': '비농업 고용지수 (12월)', 'impact': 'High', 'category': 'Employment', 'country': 'US'},
            {'date': '2025-01-15', 'event_en': 'CPI (YoY) (Dec)', 'event_ko': '소비자물가지수 (12월)', 'impact': 'High', 'category': 'Inflation', 'country': 'US'},
            {'date': '2025-01-29', 'event_en': 'Fed Interest Rate Decision', 'event_ko': '연준 기준금리 결정', 'impact': 'High', 'category': 'Fed', 'country': 'US'},
            {'date': '2025-01-30', 'event_en': 'GDP (QoQ) (Q4)', 'event_ko': '4분기 GDP 성장률', 'impact': 'High', 'category': 'Growth', 'country': 'US'},
        ]
    
    def _get_event_descriptions(self, event_name: str) -> Dict[str, str]:
        """Get bilingual descriptions for event"""
        descriptions = {
            'FOMC': {
                'en': 'Federal Reserve interest rate decision. Impacts global markets and KRW/USD.',
                'ko': '미국 연준 금리 결정. 글로벌 자산시장 및 원/달러 환율에 결정적 영향.'
            },
            'Fed': {
                'en': 'Federal Reserve interest rate decision. Impacts global markets and KRW/USD.',
                'ko': '미국 연준 금리 결정. 글로벌 자산시장 및 원/달러 환율에 결정적 영향.'
            },
            'Nonfarm': {
                'en': 'US employment report. Key indicator for global risk appetite.',
                'ko': '미국 노동시장 핵심 지표. 글로벌 위험자산 선호 심리를 좌우함.'
            },
            'Payroll': {
                'en': 'US employment report. Key indicator for global risk appetite.',
                'ko': '미국 노동시장 핵심 지표. 글로벌 위험자산 선호 심리를 좌우함.'
            },
            'CPI': {
                'en': 'Inflation measure. High US CPI often strengthens USD, weakening KRW.',
                'ko': '물가상승률 지표. 예상 상회 시 달러 강세 및 원화 약세 요인.'
            },
            'GDP': {
                'en': 'Economic growth measure. Global recession fears impact KR exports.',
                'ko': '경제성장률. 경기 침체 우려는 한국 수출주 심리에 부정적.'
            },
            'BOK': {
                'en': 'Bank of Korea rate decision. Critical for KOSPI valuation and housing market.',
                'ko': '한국은행 금통위. KOSPI 밸류에이션 및 부동산 시장에 직접적 영향.'
            },
            'Trade': {
                'en': 'Trade balance data. Leading indicator for export-dependent sectors.',
                'ko': '수출입 동향. 반도체 등 주력 수출 업종의 선행 지표.'
            },
            'Retail': {
                'en': 'Consumer spending indicator. Reflects economic health.',
                'ko': '소비 지표. 미국 내수 경기와 경기침체 여부를 가늠.'
            },
            'ISM': {
                'en': 'Business activity gauge. Key leading indicator for economic direction.',
                'ko': '기업 활동 지표. 경기 방향성을 가늠하는 선행지표.'
            },
            'Unemployment': {
                'en': 'Labor market health indicator.',
                'ko': '노동시장 건전성 지표.'
            },
            'Jobless': {
                'en': 'Weekly unemployment claims. High-frequency labor market data.',
                'ko': '주간 실업 청구건수. 고빈도 노동시장 데이터.'
            },
            'Housing': {
                'en': 'Housing market indicator. Sensitive to interest rates.',
                'ko': '주택시장 지표. 금리에 민감하게 반응.'
            },
            'Consumer': {
                'en': 'Consumer confidence indicator. Leads retail spending.',
                'ko': '소비자 심리 지표. 소비 지출을 선행.'
            },
            'PCE': {
                'en': 'Fed\'s preferred inflation gauge. Critical for rate decisions.',
                'ko': '연준이 선호하는 물가 지표. 금리 결정에 핵심적.'
            }
        }
        
        for key, desc in descriptions.items():
            if key.lower() in event_name.lower():
                return desc
        
        return {
            'en': 'Economic data release that may impact markets.',
            'ko': '시장에 영향을 줄 수 있는 주요 경제 지표 발표.'
        }
    
    def enrich_with_ai(self, events: List[Dict]) -> Dict:
        """Generate Global AI Outlook"""
        if not self.api_key:
            return {'global_outlook': "AI API Key missing."}
        
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent"
        
        # Filter mostly high impact events for the prompt
        high_impact = [e for e in events if e['impact'] == 'High']
        event_str = "\n".join([f"- [{e['country']}][{e['date']}] {e['event']}" for e in high_impact])

        prompt = f"""
        Act as a Global Macro Strategist. Analyze the upcoming economic calendar for US and Korea.
        
        Upcoming Major Events:
        {event_str}

        Task:
        Write a 'Weekly Global Market Briefing' (Korean).
        1. Highlight the interaction between US and KR events (e.g., How US CPI might affect BOK decision).
        2. Identify key risks (e.g., Currency volatility, Sector rotation).
        3. Provide a concise trading strategy for the week.
        
        Format as JSON:
        {{
            "weekly_outlook": "...",
            "key_risks": ["...", "..."],
            "trading_strategy": "..."
        }}
        """
        
        try:
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"response_mime_type": "application/json", "maxOutputTokens": 2048}
            }
            
            resp = requests.post(f"{url}?key={self.api_key}", json=payload, timeout=20)
            if resp.status_code == 200:
                text = resp.json()['candidates'][0]['content']['parts'][0]['text']
                # Clean markdown code blocks if present
                if "```" in text:
                    text = text.replace("```json", "").replace("```", "").strip()
                return json.loads(text)
        except Exception as ex:
            logger.error(f"AI enrichment error: {ex}")
            err_msg = str(ex)
            
        return {'weekly_outlook': f"AI Analysis Unavailable. Error: {err_msg if 'err_msg' in locals() else 'Unknown'}"}
    
    def get_market_moving_news(self) -> List[Dict]:
        """Get recent market-moving news"""
        news = []
        try:
            import xml.etree.ElementTree as ET
            url = "https://news.google.com/rss/search?q=Federal+Reserve+OR+FOMC+OR+inflation&hl=en-US&gl=US&ceid=US:en"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                for item in root.findall('.//item')[:5]:
                    title = item.find('title')
                    pub_date = item.find('pubDate')
                    if title is not None:
                        news.append({
                            'title': title.text,
                            'published': pub_date.text if pub_date is not None else '',
                            'source': 'Google News'
                        })
        except:
            pass
        return news
    
    def run(self) -> Dict:
        """Generate economic calendar"""
        logger.info("🚀 Starting Economic Calendar Generation...")
        
        # Fetch Korean indicators from ECOS
        self.kr_indicators = self._fetch_ecos_indicators()
        
        # Get events
        events = self.get_scheduled_events()
        logger.info(f"📅 Found {len(events)} upcoming events")
        
        # Enrich with Global AI Analysis
        ai_briefing = self.enrich_with_ai(events)
        
        # Get news
        news = self.get_market_moving_news()
        
        # Categorize events
        high_impact = [e for e in events if e['impact'] == 'High']
        
        # Build output
        output = {
            'updated': datetime.now().isoformat(),
            'week_start': datetime.now().strftime('%Y-%m-%d'),
            'summary': {
                'total_events': len(events),
                'high_impact': len(high_impact),
                'next_major_event': high_impact[0] if high_impact else None
            },
            'kr_indicators': self.kr_indicators,  # Real-time Korean data from ECOS
            'ai_briefing': ai_briefing,
            'events': events,
            'recent_news': news
        }
        
        # Save
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Saved economic calendar to {self.output_file}")
        
        # Print summary
        print("\n📅 Economic Calendar Summary")
        print(f"   Upcoming Events: {len(events)}")
        print(f"   High Impact: {len(high_impact)}")
        
        if 'weekly_outlook' in ai_briefing:
             print("\n🤖 AI Outlook Preview:")
             print(f"   {ai_briefing['weekly_outlook'][:100]}...")
        
        return output


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Economic Calendar')
    parser.add_argument('--dir', default='.', help='Data directory')
    args = parser.parse_args()
    
    calendar = EconomicCalendar(data_dir=args.dir)
    calendar.run()


if __name__ == "__main__":
    main()
