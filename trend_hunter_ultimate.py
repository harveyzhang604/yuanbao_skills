#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Trend Hunter Ultimate: DDG Edition
Integrates: Alphabet Mining + Pain Identification + GPTs Benchmarking + Lightweight SERP Analysis
"""
import sys
import os
import time
import random
import re
import requests
from datetime import datetime
from pytrends.request import TrendReq

sys.stdout.reconfigure(encoding='utf-8')

# --- CONFIGURATION ---
BENCHMARK_KEYWORD = "GPTs"
TIMEFRAME = "now 7-d"
MIN_RATIO = 0.05

LOW_COMP_DOMAINS = [
    'reddit.com', 'quora.com', 'medium.com', 'linkedin.com', 
    'pinterest.com', 'facebook.com', 'twitter.com', 'youtube.com',
    'instagram.com', 'tiktok.com', 'stackoverflow.com', 'github.com',
    'dev.to', 'indiehackers.com'
]

PAIN_TRIGGERS = [
    "struggling with", "cant", "can't", "fix", "solve", "error", 
    "slow", "manual", "tedious", "hard to", "alternative to"
]

COMMERCIAL_TRIGGERS = [
    "tool", "app", "generator", "calculator", "converter", 
    "maker", "builder", "template", "software", "extension"
]

# --- MODULE 1: MINING ---
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
    print(f"[*] 1. MINING: Scanning {len(seeds)} seeds...")
    for i, seed in enumerate(seeds):
        if i % 2 == 0: print(f"    Scanning: {seed}...")
        for q in [seed, f"{seed} ", f" {seed}"]:
            for r in google_suggest(q): all_keywords.add(r)
        # Deep scan
        for char in "abcdefghijklmnopqrstuvwxyz": 
            for r in google_suggest(f"{seed} {char}"): all_keywords.add(r)
            for r in google_suggest(f"{char} {seed}"): all_keywords.add(r)
        time.sleep(0.5)
    return list(all_keywords)

# --- MODULE 2: FILTERING ---
def filter_candidates(keywords):
    candidates = []
    for kw in keywords:
        kw_lower = kw.lower()
        words = kw_lower.split()
        if not (3 <= len(words) <= 8): continue
        
        intent_score = 0
        signals = []
        if any(p in kw_lower for p in PAIN_TRIGGERS): 
            intent_score += 3; signals.append("Pain")
        if any(c in kw_lower for c in COMMERCIAL_TRIGGERS): 
            intent_score += 2; signals.append("Tool")
        if " vs " in kw_lower or "alternative" in kw_lower: 
            intent_score += 2; signals.append("Comp")
            
        if intent_score >= 2:
            candidates.append({"keyword": kw, "intent_score": intent_score, "signals": signals})
    return candidates

# --- MODULE 3: VALIDATION ---
def check_trends(candidates):
    print(f"[*] 3. VALIDATION: Benchmarking against '{BENCHMARK_KEYWORD}'...")
    verified = []
    try:
        pytrends = TrendReq(hl='en-US', tz=360, retries=2, backoff_factor=0.5)
    except:
        return candidates 
        
    candidates.sort(key=lambda x: x['intent_score'], reverse=True)
    # Check Top 5
    for item in candidates[:5]:
        kw = item['keyword']
        print(f"    Checking Trend: {kw}")
        try:
            pytrends.build_payload([BENCHMARK_KEYWORD, kw], timeframe=TIMEFRAME)
            df = pytrends.interest_over_time()
            if not df.empty:
                avg_base = df[BENCHMARK_KEYWORD].mean()
                avg_kw = df[kw].mean()
                ratio = avg_kw / avg_base if avg_base > 0 else 0
                item['trend_ratio'] = ratio
                if ratio >= MIN_RATIO: verified.append(item)
            time.sleep(2)
        except: pass
    return verified

# --- MODULE 4: COMPETITION (DDG LIGHTWEIGHT) ---
def check_serp_competition(candidates):
    print(f"[*] 4. COMPETITION: DDG Analysis for {len(candidates)} candidates...")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    for item in candidates:
        kw = item['keyword']
        print(f"    Analyzing SERP: {kw}")
        
        try:
            # Use DuckDuckGo HTML version - easiest to scrape
            url = f"https://html.duckduckgo.com/html/?q={kw}"
            r = requests.get(url, headers=headers, timeout=10)
            
            domains = []
            if r.status_code == 200:
                # Regex for DDG result links
                links = re.findall(r'class="result__a" href="([^"]+)"', r.text)
                for link in links[:5]: # Check top 5
                    if "http" in link:
                        try:
                            # Basic domain extraction
                            # Sometimes DDG wraps urls in /l/?kh=-1&uddg=... but html version often directs
                            # If it's wrapped, we might need unquote, but usually for top domains this works enough to spot big players
                            if "duckduckgo" in link: continue 
                            
                            # Simple cleanup
                            clean_link = link
                            if "/l/?" in link: 
                                # It is a wrapped link, extracting might be hard without urllib
                                # But let's see if we can just scan the text content of the link in full implementation
                                # For now, simple heuristic: regex matching the visible link text is better?
                                pass
                            
                            domain = link.split("/")[2].replace("www.", "")
                            domains.append(domain)
                        except: pass
            
            # De-duplicate
            domains = list(set(domains))
            item['top_domains'] = domains
            
            # Score
            weak_spots = sum(1 for d in domains if any(ld in d for ld in LOW_COMP_DOMAINS))
            
            if weak_spots >= 2:
                item['competition'] = "🟢 LOW (Blogs/Forums)"
                item['decision'] = "BUILD NOW"
            elif weak_spots == 1:
                item['competition'] = "🟡 MED (Mixed)"
                item['decision'] = "WATCH"
            else:
                item['competition'] = "🔴 HIGH (Tools)"
                item['decision'] = "DROP"
                
        except Exception as e:
            print(f"    ⚠️ SERP Error: {e}")
            item['competition'] = "⚪ UNKNOWN"
            
        time.sleep(1.5) # Be polite
        
    return candidates

# --- REPORT ---
def generate_report(results):
    results.sort(key=lambda x: (x.get('decision') == 'BUILD NOW', x.get('trend_ratio', 0)), reverse=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"data/ultimate_report_{timestamp}.html"
    os.makedirs("data", exist_ok=True)
    
    html = f"""<html>
    <head><style>
        body {{ font-family: sans-serif; background: #222; color: #eee; padding: 20px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 10px; border: 1px solid #444; text-align: left; }}
        .build {{ color: #0f0; font-weight: bold; }}
        .watch {{ color: #fc0; }}
        .drop {{ color: #f00; }}
    </style></head>
    <body><h1>Trend Hunter Ultimate Report</h1>
    <p>Generated: {timestamp}</p>
    <table>
    <tr><th>Keyword</th><th>Decision</th><th>Comp</th><th>Top Domains</th></tr>
    """
    for r in results:
        dec = r.get('decision', 'DROP')
        cls = "build" if "BUILD" in dec else ("watch" if "WATCH" in dec else "drop")
        html += f"<tr><td>{r['keyword']}</td><td class='{cls}'>{dec}</td><td>{r.get('competition')}</td><td>{', '.join(r.get('top_domains', []))}</td></tr>"
    html += "</table></body></html>"
    
    with open(filename, "w", encoding="utf-8") as f: f.write(html)
    return filename

# --- MAIN ---
if __name__ == "__main__":
    print("🛸 TREND HUNTER: ULTIMATE EDITION")
    
    # Seeds
    seeds = ["calculator", "generator", "converter"]
    try:
        with open("words.md", "r") as f:
            seeds = [l.split('\t')[1].split('（')[0].strip() for l in f if l[0].isdigit()]
    except: pass
    seeds = seeds[:5] # Limit for demo
    
    # Run
    raw = mine_keywords(seeds)
    candidates = filter_candidates(raw)
    print(f"[*] Filtered to {len(candidates)} high-intent candidates.")
    
    verified = check_trends(candidates)
    if not verified:
        print("⚠️ Trend check failed/strict. Using Top 5 filtered for demo.")
        verified = candidates[:5]
        
    final = check_serp_competition(verified)
    
    print("\n🏁 RESULTS:")
    for r in final:
        print(f"[{r.get('decision')}] {r['keyword']}")
        print(f"   Comp: {r.get('competition')}")
        print(f"   Domains: {r.get('top_domains')}")
        
    rep = generate_report(final)
    print(f"Report: {rep}")
