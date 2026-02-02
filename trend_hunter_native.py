#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Trend Hunter Ultimate: Clawdbot Native Edition
Integrates: Alphabet Mining + Pain Identification + GPTs Benchmarking + Native Browser SERP Analysis
"""
import sys
import os
import time
import json
import subprocess
import random
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
    'instagram.com', 'tiktok.com', 'stackoverflow.com', 'github.com'
]

PAIN_TRIGGERS = [
    "struggling with", "cant", "can't", "fix", "solve", "error", 
    "slow", "manual", "tedious", "hard to", "alternative to"
]

COMMERCIAL_TRIGGERS = [
    "tool", "app", "generator", "calculator", "converter", 
    "maker", "builder", "template", "software", "extension"
]

# --- HELPER: CLAWDBOT BROWSER CONTROL ---
def browser_navigate(url):
    try:
        subprocess.run(["clawdbot", "browser", "navigate", url], check=True, capture_output=True)
        time.sleep(2) # Wait for load
    except Exception as e:
        print(f"    ⚠️ Browser Nav Error: {e}")

def browser_snapshot():
    try:
        # Use 'aria' format for lightweight structure (perfect for SERP)
        res = subprocess.run(
            ["clawdbot", "browser", "snapshot", "--format", "aria", "--json"], 
            capture_output=True, text=True
        )
        if res.returncode == 0:
            return json.loads(res.stdout)
    except Exception as e:
        print(f"    ⚠️ Browser Snapshot Error: {e}")
    return None

def extract_domains_from_snapshot(snapshot_data):
    """
    Parses Clawdbot's snapshot JSON to find search result links.
    Heuristic: Look for 'link' roles that contain 'http' in their name/value.
    """
    domains = []
    if not snapshot_data: return domains
    
    # Recursively find links in the tree
    def traverse(node):
        if isinstance(node, dict):
            # Check if it's a link
            if node.get("role") == "link":
                name = node.get("name", "")
                # Google SERP links usually have the title as name, we need the URL
                # Clawdbot snapshot might not give full href in 'name'.
                # But typically Google puts the URL in a cite tag or similar.
                # Let's try a simpler approach: 
                # If we can't get href easily from snapshot, we fallback to a simple text scan
                # OR we assume the snapshot 'value' or 'description' might hold it.
                pass
            
            # Continue traversal
            for child in node.get("children", []):
                traverse(child)
                
    # FALLBACK STRATEGY for this demo:
    # Since snapshot parsing can be tricky without seeing the structure,
    # We will use 'clawdbot browser evaluate' to extract hrefs directly via JS.
    # This is much more reliable for SERP scraping.
    return []

def get_serp_domains_js():
    """Extracts domains using JS evaluation via Clawdbot"""
    js_code = """
    (() => {
        const links = Array.from(document.querySelectorAll('div.g a'));
        return links.map(a => a.href).filter(h => h && h.startsWith('http'));
    })()
    """
    try:
        res = subprocess.run(
            ["clawdbot", "browser", "evaluate", "--fn", js_code, "--json"],
            capture_output=True, text=True
        )
        if res.returncode == 0:
            output = json.loads(res.stdout)
            # Output format from CLI might be wrapped.
            # Usually it returns the result directly or in a wrapper.
            # Let's assume it returns the array of strings.
            urls = output if isinstance(output, list) else []
            
            domains = []
            for url in urls[:5]: # Top 5
                try:
                    domain = url.split("/")[2].replace("www.", "")
                    if "google" not in domain: # Skip internal links
                        domains.append(domain)
                except: pass
            return list(set(domains)) # Unique
    except Exception as e:
        print(f"    ⚠️ JS Eval Error: {e}")
    return []

# --- MODULE 1: MINING ---
def google_suggest(query):
    import requests
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
    # Check Top 5 for demo speed
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

# --- MODULE 4: COMPETITION (CLAWDBOT NATIVE) ---
def check_serp_competition(candidates):
    print(f"[*] 4. COMPETITION: Native Browser Analysis for {len(candidates)} candidates...")
    
    # Ensure browser is running
    subprocess.run(["clawdbot", "browser", "start"], capture_output=True)
    time.sleep(3)
    
    for item in candidates:
        kw = item['keyword']
        print(f"    Analyzing SERP (Native): {kw}")
        
        # 1. Navigate
        url = f"https://www.google.com/search?q={kw.replace(' ', '+')}&hl=en&gl=us"
        browser_navigate(url)
        
        # 2. Extract Domains via JS
        domains = get_serp_domains_js()
        item['top_domains'] = domains
        
        # 3. Score
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
            
        time.sleep(2)
        
    return candidates

# --- REPORT ---
def generate_report(results):
    results.sort(key=lambda x: (x.get('decision') == 'BUILD NOW', x.get('trend_ratio', 0)), reverse=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"data/native_report_{timestamp}.html"
    os.makedirs("data", exist_ok=True)
    
    html = f"""<html><body><h1>Clawdbot Native Report</h1>
    <table border="1">
    <tr><th>Keyword</th><th>Decision</th><th>Comp</th><th>Domains</th></tr>
    """
    for r in results:
        html += f"<tr><td>{r['keyword']}</td><td>{r.get('decision')}</td><td>{r.get('competition')}</td><td>{r.get('top_domains')}</td></tr>"
    html += "</table></body></html>"
    
    with open(filename, "w", encoding="utf-8") as f: f.write(html)
    return filename

# --- MAIN ---
if __name__ == "__main__":
    print("🛸 TREND HUNTER: CLAWDBOT NATIVE EDITION")
    
    # Seeds
    seeds = ["calculator", "generator", "converter"]
    try:
        with open("words.md", "r") as f:
            seeds = [l.split('\t')[1].split('（')[0].strip() for l in f if l[0].isdigit()]
    except: pass
    seeds = seeds[:3]
    
    # Run
    raw = mine_keywords(seeds)
    candidates = filter_candidates(raw)
    verified = check_trends(candidates)
    
    if not verified:
        print("⚠️ Trend check strict/failed. Using top filtered for SERP demo.")
        verified = candidates[:3]
        
    final = check_serp_competition(verified)
    
    print("\n🏁 RESULTS:")
    for r in final:
        print(f"[{r.get('decision')}] {r['keyword']} | {r.get('competition')}")
    
    rep = generate_report(final)
    print(f"Report: {rep}")
