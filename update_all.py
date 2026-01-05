#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 US Stock Data Collection - Unified Update Script
=====================================================
Orchestrates all data collection and analysis scripts:
1. Price data collection (S&P 500)
2. Volume/supply-demand analysis
3. Institutional holdings analysis
4. ETF flow analysis

Author: System Orchestrator
Purpose: Single command to update all data
"""

import os
import sys
import subprocess
import logging
import argparse
from datetime import datetime

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class USMarketUpdater:
    """
    모든 데이터 수집/분석 스크립트를 순차 실행
    
    실행 순서:
    1. 가격 데이터 수집 (create_us_daily_prices.py)
    2. 거래량 분석 (analyze_volume.py)
    3. 기관 분석 (analyze_13f.py)
    4. ETF 자금 흐름 (analyze_etf_flows.py)
    """
    
    def __init__(self, data_dir: str = '.'):
        self.data_dir = data_dir
        self.scripts = [
            {
                'name': 'Price Collection',
                'file': 'create_us_daily_prices.py',
                'emoji': '📈',
                'required': True
            },
            {
                'name': 'Volume Analysis',
                'file': 'analyze_volume.py',
                'emoji': '📊',
                'required': True
            },
            {
                'name': 'Institutional Analysis',
                'file': 'analyze_13f.py',
                'emoji': '🏦',
                'required': True
            },
            {
                'name': 'ETF Flow Analysis',
                'file': 'analyze_etf_flows.py',
                'emoji': '💹',
                'required': True
            }
        ]
    
    def run_script(self, script_info: dict, extra_args: list = None) -> bool:
        """Run a single script"""
        script_path = os.path.join(self.data_dir, script_info['file'])
        
        if not os.path.exists(script_path):
            logger.error(f"❌ Script not found: {script_path}")
            return False
        
        logger.info(f"\n{script_info['emoji']} Running {script_info['name']}...")
        logger.info(f"   Script: {script_info['file']}")
        
        try:
            cmd = [sys.executable, script_path, '--dir', self.data_dir]
            if extra_args:
                cmd.extend(extra_args)
            
            result = subprocess.run(
                cmd,
                cwd=self.data_dir,
                capture_output=False,
                text=True
            )
            
            if result.returncode != 0:
                logger.warning(f"⚠️ {script_info['name']} completed with warnings")
                return script_info['required'] == False
            
            logger.info(f"✅ {script_info['name']} completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error running {script_info['name']}: {e}")
            return False
    
    def run_all(self, quick: bool = False, full_refresh: bool = False) -> bool:
        """Run all scripts in sequence"""
        start_time = datetime.now()
        
        logger.info("=" * 60)
        logger.info("🚀 US Market Data Update Started")
        logger.info(f"   Mode: {'Quick' if quick else 'Full'}")
        logger.info(f"   Data Directory: {self.data_dir}")
        logger.info(f"   Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)
        
        results = []
        
        for script in self.scripts:
            extra_args = []
            
            # Price collection with full refresh option
            if script['file'] == 'create_us_daily_prices.py' and full_refresh:
                extra_args.append('--full')
            
            # Skip AI analysis in quick mode
            if quick and script['file'] == 'analyze_etf_flows.py':
                # AI analysis is optional
                pass
            
            success = self.run_script(script, extra_args)
            results.append({
                'name': script['name'],
                'success': success
            })
            
            # Stop if required script fails
            if not success and script['required']:
                logger.error(f"❌ Required script failed: {script['name']}")
                break
        
        # Summary
        end_time = datetime.now()
        duration = end_time - start_time
        
        logger.info("\n" + "=" * 60)
        logger.info("📊 Update Summary")
        logger.info("=" * 60)
        
        success_count = sum(1 for r in results if r['success'])
        total_count = len(results)
        
        for r in results:
            status = "✅" if r['success'] else "❌"
            logger.info(f"   {status} {r['name']}")
        
        logger.info(f"\n   Success: {success_count}/{total_count}")
        logger.info(f"   Duration: {duration.total_seconds():.1f} seconds")
        logger.info(f"   End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # List output files
        logger.info("\n📁 Output Files:")
        output_files = [
            'us_daily_prices.csv',
            'us_stocks_list.csv',
            'us_volume_analysis.csv',
            'us_13f_holdings.csv',
            'us_etf_flows.csv',
            'etf_flow_analysis.json'
        ]
        for f in output_files:
            path = os.path.join(self.data_dir, f)
            if os.path.exists(path):
                size = os.path.getsize(path)
                logger.info(f"   ✓ {f} ({size:,} bytes)")
            else:
                logger.info(f"   ✗ {f} (not created)")
        
        return success_count == total_count


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description='US Market Data Collection - Unified Updater',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python update_all.py              # Full update
  python update_all.py --quick      # Quick update (skip AI)
  python update_all.py --full       # Full refresh (re-download all data)
        """
    )
    parser.add_argument('--dir', default='.', help='Data directory')
    parser.add_argument('--quick', action='store_true', help='Quick update (skip AI analysis)')
    parser.add_argument('--full', action='store_true', help='Full refresh (ignore existing data)')
    args = parser.parse_args()
    
    updater = USMarketUpdater(data_dir=args.dir)
    success = updater.run_all(quick=args.quick, full_refresh=args.full)
    
    if success:
        print("\n🎉 All updates completed successfully!")
    else:
        print("\n⚠️ Some updates failed. Check the logs above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
