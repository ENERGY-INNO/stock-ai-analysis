#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 Stock AI Analysis System: Unified Master Runner
===================================================
Runs all data collection scripts (US, KR, Global) with automatic periodic refresh.

Usage:
    python3 run_all.py                    # Default: 30-minute refresh
    python3 run_all.py --interval 15      # Custom: 15-minute refresh
    python3 run_all.py --no-refresh       # One-time update, no auto-refresh
"""

import subprocess
import time
import os
import sys
import threading
import signal
import argparse
import webbrowser
from datetime import datetime

# Configuration
DEFAULT_REFRESH_INTERVAL = 30  # minutes
DASHBOARD_URL = "http://localhost:5001"

# All analysis scripts to run
ANALYSIS_SCRIPTS = [
    # 🇺🇸 US Market
    "sector_heatmap.py",
    "macro_analyzer.py",
    "ai_summary_generator.py",
    "options_flow.py",
    "final_report_generator.py",
    "beginner_advisor.py",
    
    # 🇰🇷 KR Market
    "kr_data_collector.py",
    "kr_market_analyzer.py",
    "kr_ai_advisor.py",
    
    # 🌏 Global Outlook
    "economic_calendar.py",
]

# Global flag for graceful shutdown
running = True

def run_script(script_name: str, silent: bool = False) -> bool:
    """Run a single analysis script"""
    try:
        result = subprocess.run(
            [sys.executable, script_name], 
            check=True, 
            capture_output=True, 
            text=True,
            timeout=120  # 2 minute timeout per script
        )
        if not silent:
            print(f"  ✅ {script_name}")
        return True
    except subprocess.CalledProcessError as e:
        if not silent:
            print(f"  ❌ {script_name}: {e}")
        return False
    except subprocess.TimeoutExpired:
        if not silent:
            print(f"  ⏱️ {script_name}: Timeout (2min)")
        return False

def run_all_updates(silent: bool = False):
    """Run all analysis scripts"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if not silent:
        print(f"\n{'='*60}")
        print(f"🔄 Data Update Started at {timestamp}")
        print(f"{'='*60}")
    
    success_count = 0
    fail_count = 0
    
    for script in ANALYSIS_SCRIPTS:
        if run_script(script, silent):
            success_count += 1
        else:
            fail_count += 1
    
    if not silent:
        print(f"\n📊 Update Complete: {success_count} succeeded, {fail_count} failed")
        print(f"{'='*60}\n")
    
    return success_count, fail_count

def auto_refresh_worker(interval_minutes: int):
    """Background worker that periodically refreshes data"""
    global running
    interval_seconds = interval_minutes * 60
    
    print(f"📡 Auto-refresh enabled: every {interval_minutes} minutes")
    print(f"   (Press Ctrl+C to stop)")
    
    while running:
        # Sleep in small chunks to respond to shutdown quickly
        for _ in range(interval_seconds):
            if not running:
                return
            time.sleep(1)
        
        if running:
            print(f"\n🔔 Auto-refresh triggered...")
            run_all_updates(silent=False)

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    global running
    print("\n\n👋 Shutting down gracefully...")
    running = False

def main():
    global running
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Stock AI Analysis System')
    parser.add_argument('--interval', type=int, default=DEFAULT_REFRESH_INTERVAL,
                        help=f'Refresh interval in minutes (default: {DEFAULT_REFRESH_INTERVAL})')
    parser.add_argument('--no-refresh', action='store_true',
                        help='Disable auto-refresh (one-time update only)')
    parser.add_argument('--server-only', action='store_true',
                        help='Start server without running updates')
    args = parser.parse_args()
    
    # Setup signal handler
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║       🌟 Stock AI Analysis System - Unified Runner 🌟        ║
║                                                              ║
║   📈 US Stocks  |  🇰🇷 KR Stocks  |  🌏 Global Outlook      ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Run initial update (unless server-only mode)
    if not args.server_only:
        print("🚀 Running initial data update...")
        run_all_updates(silent=False)
    
    # Start auto-refresh thread (unless disabled)
    refresh_thread = None
    if not args.no_refresh:
        refresh_thread = threading.Thread(
            target=auto_refresh_worker, 
            args=(args.interval,),
            daemon=True
        )
        refresh_thread.start()
    else:
        print("📡 Auto-refresh: DISABLED (one-time update mode)")
    
    # Start Flask server
    print("\n" + "="*60)
    print("🌐 Starting Web Server...")
    print(f"   Dashboard: {DASHBOARD_URL}")
    print("="*60 + "\n")
    
    # Open browser after short delay (gives Flask time to start)
    def open_browser():
        time.sleep(2)  # Wait for Flask to initialize
        print(f"🌐 Opening browser: {DASHBOARD_URL}")
        webbrowser.open(DASHBOARD_URL)
    
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    try:
        # Run flask_app.py in main thread
        subprocess.run([sys.executable, "flask_app.py"])
    except KeyboardInterrupt:
        pass
    finally:
        running = False
        print("\n✅ System stopped.")

if __name__ == "__main__":
    main()
