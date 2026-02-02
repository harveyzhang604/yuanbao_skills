#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Profit Hunter Ultimate: Discovery + Trend Validation
Combines "Alphabet Soup" mining with "Google Trends Benchmark" verification.
"""
import sys
import os
import requests
import time
import pandas as pd
from datetime import datetime
from pytrends.request import TrendReq

sys.stdout.reconfigure(encoding='utf-8')

# --- CONFIGURATION ---
BENCHMARK_KEYWORD = "GPTs"  # The Gold Standard for volume
TIMEFRAME = "now 7-d"       # Look for recent breakouts
MIN_RATIO_THRESHOLD = 0.05  # Keyword must have at least 5% of GPTs volume to be considered "real"

PAIN_TRIGGERS = [
    "struggling with", "cant", "can't", "how to fix", "solve", "error", 
    "problem with", "slow", "broken", "manual", "tedious", "hard to"
]

COMMERCIAL_TRIGGERS = [
    "best app for", "tool for", "software for", "generator", "calculator", 
    "converter", "maker", "builder", "template", "plugin", "extension"
]

ALPHABET = "abcdefghijklmnopqrstuvwxyz"

# --- INIT PYTRENDS ---
# Handle connection errors gracefully
try:
    pytrends = TrendReq(hl='en-US', tz=360, timeout=(10,25), retries=2, backoff_factor=0.1)
except:
    pytrends = None

# --- MODULE 1: DISCOVERY (Google Suggest) ---
def google_suggest(query):
    url = "https://suggestqueries.google.com/complete/search"
    params = {"client": "firefox", "q": query, "hl": "en", "gl": "us"}
    try:
        r = requests.get(url, params=params, timeout=3)
        if r.status_code == 200:
            return r.json()[1]
    except:
        pass
    return []

def mine_keywords(seeds):
    all_keywords = set()
    print(f"[*] 1. DISCOVERY: Mining {len(seeds)} seeds using Alphabet Soup...")
    
    for i, seed in enumerate(seeds):
        if i % 5 == 0: print(f"    Scanning: {seed}...")
        
        # 1. Base & Spaces
        for q in [seed, f"{seed} ", f" {seed}"]:
            for r in google_suggest(q): all_keywords.add(r)
            
        # 2. Alphabet Soup (Prefix/Suffix)
        # Scan only a few chars to save time for Trends check
        for char in ALPHABET[:10]: 
            for r in google_suggest(f"{seed} {char}"): all_keywords.add(r)
            for r in google_suggest(f"{char} {seed}"): all_keywords.add(r)
        
        time.sleep(0.2)

    return list(all_keywords)

# --- MODULE 2: FILTERING ---
def filter_candidates(keywords):
    candidates = []
    for kw in keywords:
        kw_lower = kw.lower()
        words = kw_lower.split()
        
        # Must be long-tail (3-7 words)
        if not (3 <= len(words) <= 7): continue
        
        # Must have Intent
        score = 0
        if any(p in kw_lower for p in PAIN_TRIGGERS): score += 3
        if any(c in kw_lower for c in COMMERCIAL_TRIGGERS): score += 2
        if " vs " in kw_lower or "alternative" in kw_lower: score += 2
        
        if score >= 2: # Keep if it has at least some signal
            candidates.append(kw)
            
    return candidates

# --- MODULE 3: VALIDATION (Google Trends vs GPTs) ---
def validate_trend(keyword):
    """
    Checks 3 things:
    1. Relative Volume: Is it > 5% of 'GPTs' volume?
    2. Trend Shape: Is it rising in the last 7 days?
    3. Breakout Related: Are there 'Breakout' related queries?
    """
    if not pytrends:
        return None 
        
    print(f"    🔎 Validating '{keyword}' vs '{BENCHMARK_KEYWORD}'...")
    
    try:
        # Compare against Benchmark
        kw_list = [BENCHMARK_KEYWORD, keyword]
        pytrends.build_payload(kw_list, cat=0, timeframe=TIMEFRAME, geo='', gprop='')
        
        # A. Interest Over Time (Volume & Shape)
        df = pytrends.interest_over_time()
        if df.empty: return None
        
        avg_gpts = df[BENCHMARK_KEYWORD].mean()
        avg_kw = df[keyword].mean()
        
        if avg_gpts == 0: return None # Should not happen
        
        ratio = avg_kw / avg_gpts
        
        # Check Trend (Is end higher than start?)
        start_vol = df[keyword].iloc[0]
        end_vol = df[keyword].iloc[-1]
        is_rising = end_vol > start_vol
        
        # B. Related Queries (Breakout Check)
        # We only check related queries if the volume is decent
        related_breakouts = []
        if ratio > 0.01: # Even 1% is worth checking for related breakouts
            related_payload = pytrends.related_queries()
            if related_payload and keyword in related_payload:
                rising_df = related_payload[keyword]['rising']
                if rising_df is not None and not rising_df.empty:
                    # Filter for "Breakout" or huge %
                    breakouts = rising_df[rising_df['value'].astype(str).str.contains('Breakout', na=False)]
                    if not breakouts.empty:
                        related_breakouts = breakouts['query'].tolist()

        return {
            "keyword": keyword,
            "ratio": ratio,
            "is_rising": is_rising,
            "breakouts": related_breakouts,
            "volume_score": round(ratio * 100, 2)
        }
        
    except Exception as e:
        if "429" in str(e):
            print("    ⚠️  Google Trends Rate Limit (429). Pausing...")
            time.sleep(30) # Cool down
        return None

# --- MAIN WORKFLOW ---
def run():
    print("🚀 PROFIT HUNTER: TREND VALIDATION EDITION")
    print("="*60)
    
    # 1. Load Seeds
    seeds = []
    try:
        with open("words.md", "r") as f:
            seeds = [line.split('\t')[1].split('（')[0].strip() for line in f if line[0].isdigit()]
    except:
        seeds = ["calculator", "generator", "converter", "maker"]
    
    seeds = seeds[:5] # Limit seeds for demo speed
    print(f"[*] Seeds: {seeds}")
    
    # 2. Mine
    raw = mine_keywords(seeds)
    print(f"[*] Found {len(raw)} raw keywords.")
    
    # 3. Filter
    candidates = filter_candidates(raw)
    print(f"[*] Filtered down to {len(candidates)} high-intent candidates.")
    
    # 4. Validate (The "GPTs Test")
    verified = []
    print(f"[*] 3. VALIDATION: Benchmarking Top 5 Candidates against '{BENCHMARK_KEYWORD}'...")
    
    # Only validate top 5 to avoid immediate rate limits in this demo
    for cand in candidates[:5]: 
        res = validate_trend(cand)
        if res:
            verified.append(res)
        time.sleep(2) # Be nice to Google
        
    # 5. Report
    print("\n🏆 VERIFIED BREAKOUT OPPORTUNITIES")
    print("="*60)
    print(f"{'KEYWORD':<30} | {'VS GPTs (%)':<12} | {'TREND':<8} | {'RELATED BREAKOUTS'}")
    print("-" * 100)
    
    for v in verified:
        trend_icon = "📈" if v['is_rising'] else "➖"
        breakout_txt = ", ".join(v['breakouts'][:2]) if v['breakouts'] else "None"
        print(f"{v['keyword']:<30} | {v['volume_score']:>10}% | {trend_icon:<8} | {breakout_txt}")

if __name__ == "__main__":
    run()
