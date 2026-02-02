#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Profit Hunter: The Independent Developer's Idea Engine
Focus: High Intent, Low Competition, Verified Pain Points.
"""
import sys
import os
import requests
import time
import re
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

# --- CONFIGURATION ---

# Pain & Intent Modifiers (The "Buying Signals")
# Words that indicate user is trying to SOLVE something, not just browse.
PAIN_TRIGGERS = [
    "struggling with", "cant", "can't", "how to fix", "solve", "error", 
    "problem with", "slow", "broken", "manual", "tedious", "hard to"
]

COMMERCIAL_TRIGGERS = [
    "best app for", "tool for", "software for", "generator", "calculator", 
    "converter", "maker", "builder", "template", "plugin", "extension"
]

# B2B / High Value Modifiers (The "Money Words")
MONEY_MODIFIERS = [
    "bulk", "batch", "api", "export", "team", "business", "pro", 
    "unlimited", "white label", "agency", "automate"
]

# Niche Discovery Patterns (The "Google Suggest Hacks")
# Based on the strategy: [Space] + Keyword, Keyword + [Space]
# And: [a-z] + Keyword, Keyword + [a-z]
ALPHABET = "abcdefghijklmnopqrstuvwxyz"

# --- LOAD SEEDS ---
def load_seeds():
    """Load seeds from words.md and add custom niche seeds"""
    seeds = []
    try:
        with open("words.md", "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split("\t")
                if len(parts) >= 2 and parts[0].isdigit():
                    name = parts[1].split("（")[0].strip()
                    seeds.append(name.lower())
    except FileNotFoundError:
        pass
    
    # Add manual seeds if words.md is empty or missing
    if not seeds:
        seeds = ["calculator", "generator", "converter", "maker", "tracker"]
        
    return list(set(seeds))

# --- GOOGLE SUGGEST API ---
def google_suggest(query):
    """Get Google Suggest keywords with robust error handling"""
    url = "https://suggestqueries.google.com/complete/search"
    # Firefox client returns richer suggestions for some queries
    params = {"client": "firefox", "q": query, "hl": "en", "gl": "us"}
    try:
        r = requests.get(url, params=params, timeout=5)
        if r.status_code == 200:
            return r.json()[1]
    except Exception as e:
        # Silently fail on network error to keep scanning
        pass
    return []

# --- MINING ENGINE (The "Alphabet Soup" Strategy) ---
def mine_keywords(seeds):
    all_keywords = []
    seen = set()
    
    print(f"[*] Starting Profit Hunter mining with {len(seeds)} seeds...")
    print("[*] Strategy: Prefix/Suffix/Alphabet Soup scanning for hidden gems.")
    
    for i, seed in enumerate(seeds):
        # Progress (every 10 seeds)
        if i % 10 == 0:
            print(f"    Scanning seed {i+1}/{len(seeds)}: '{seed}'...")
            
        seed_suggestions = []

        # 1. Base Query
        seed_suggestions.extend(google_suggest(seed))
        
        # 2. Suffix Scan (Space After) -> "calculator " -> "calculator app", "calculator online"
        seed_suggestions.extend(google_suggest(f"{seed} "))
        
        # 3. Prefix Scan (Space Before) -> " calculator" -> "age calculator", "love calculator"
        seed_suggestions.extend(google_suggest(f" {seed}"))
        
        # 4. Alphabet Soup - Prefix (a...z + seed)
        # Finds: "american dating standards calculator", "bmi calculator"
        # We limit to first 5 matches to save time per char, unless it's a high potential seed
        for char in ALPHABET:
            # Prefix: "a calculator", "b calculator"
            seed_suggestions.extend(google_suggest(f"{char} {seed}"))
            time.sleep(0.05) # Rate limit respect
            
        # 5. Alphabet Soup - Suffix (seed + a...z)
        # Finds: "calculator a...", "calculator for b..."
        # Useful for "calculator for [audience]" queries
        for char in ALPHABET:
            seed_suggestions.extend(google_suggest(f"{seed} {char}"))
            time.sleep(0.05)
            
        # Process suggestions for this seed
        for s in seed_suggestions:
            if s not in seen and len(s) > len(seed): # Must be longer than seed
                seen.add(s)
                all_keywords.append({
                    'keyword': s,
                    'seed': seed,
                    'source': 'suggest'
                })
        
        # Pause slightly between seeds
        time.sleep(0.2)

    return all_keywords

# --- INTELLIGENT SCORING (The "Investor's Eye") ---
def score_candidate(kw):
    kw_lower = kw.lower()
    words = kw_lower.split()
    word_count = len(words)
    
    score = 0
    reasons = []
    
    # 1. Pain Point (Problem = Money)
    if any(p in kw_lower for p in PAIN_TRIGGERS):
        score += 3
        reasons.append("Pain Point")
        
    # 2. Commercial Intent (Ready to buy/use)
    if any(c in kw_lower for c in COMMERCIAL_TRIGGERS):
        score += 2
        reasons.append("Tool Intent")
        
    # 3. B2B / High Value (Rich niche)
    if any(m in kw_lower for m in MONEY_MODIFIERS):
        score += 2
        reasons.append("High Value")
        
    # 4. Comparison / Alternative (Competitor weakness)
    if " vs " in kw_lower or "alternative" in kw_lower:
        score += 2
        reasons.append("Competitor Gap")
        
    # 5. Long Tail (Low Competition)
    # The "Goldilocks Zone": 4-7 words.
    # Too short (1-2) = Impossible competition.
    # Too long (>8) = No volume.
    if 4 <= word_count <= 7:
        score += 2
        reasons.append("Long Tail (Low Comp)")
    elif word_count == 3:
        score += 1
        reasons.append("Mid Tail")
        
    # 6. Specific Question (How to)
    if kw_lower.startswith("how to"):
        score += 1
        reasons.append("Content/SaaS Gap")
        
    # 7. Negative Filters (Garbage collection)
    if any(x in kw_lower for x in ["login", "sign in", "support", "number", "customer service"]):
        score = -10 # Kill it
        
    return score, reasons

# --- REPORT GENERATION ---
def generate_report(candidates):
    # Sort by score desc
    candidates.sort(key=lambda x: x['score'], reverse=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"data/profit_hunter_{timestamp}.html"
    os.makedirs("data", exist_ok=True)
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Profit Hunter Report {timestamp}</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; padding: 20px; background: #f0f2f5; color: #333; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .header {{ margin-bottom: 30px; text-align: center; }}
            .header h1 {{ margin: 0; color: #1a73e8; }}
            .header p {{ color: #666; }}
            
            .card-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; margin-bottom: 40px; }}
            .card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); border-left: 5px solid #ccc; }}
            .card.tier-1 {{ border-left-color: #34a853; }} /* High score */
            .card.tier-2 {{ border-left-color: #fbbc04; }} /* Mid score */
            .card h3 {{ margin: 0 0 10px 0; font-size: 18px; }}
            .tags {{ display: flex; flex-wrap: wrap; gap: 5px; margin-top: 10px; }}
            .tag {{ font-size: 12px; padding: 3px 8px; border-radius: 10px; background: #e8f0fe; color: #1967d2; }}
            .tag.pain {{ background: #fce8e6; color: #c5221f; }}
            .tag.value {{ background: #e6f4ea; color: #137333; }}
            
            table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
            th, td {{ padding: 12px 15px; text-align: left; border-bottom: 1px solid #eee; }}
            th {{ background: #f8f9fa; font-weight: 600; }}
            tr:hover {{ background: #f1f3f4; }}
            
            .score-badge {{ display: inline-block; width: 30px; height: 30px; line-height: 30px; text-align: center; border-radius: 50%; background: #333; color: white; font-weight: bold; }}
            .score-high {{ background: #34a853; }}
            .score-mid {{ background: #fbbc04; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Profit Hunter: Verified Opportunities</h1>
                <p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")} | Candidates Scanned: {len(candidates)}</p>
            </div>
            
            <h2>💎 Top 12 "Gold Mine" Opportunities</h2>
            <div class="card-grid">
    """
    
    # Top Cards
    for c in candidates[:12]:
        tier = "tier-1" if c['score'] >= 6 else "tier-2"
        html += f"""
            <div class="card {tier}">
                <h3>{c['keyword']}</h3>
                <div>Score: <span class="score-badge {('score-high' if c['score']>=6 else 'score-mid')}">{c['score']}</span></div>
                <div class="tags">
        """
        for r in c['reasons']:
            tag_type = "pain" if "Pain" in r else ("value" if "Value" in r or "Gap" in r else "")
            html += f'<span class="tag {tag_type}">{r}</span>'
        html += """
                </div>
            </div>
        """
        
    html += """
            </div>
            
            <h2>📊 Full Opportunity List</h2>
            <table>
                <thead>
                    <tr>
                        <th>Keyword</th>
                        <th>Score</th>
                        <th>Intent Signals</th>
                        <th>Seed</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    # Table Rows
    for c in candidates:
        if c['score'] < 3: continue # Skip low quality
        
        score_class = 'score-high' if c['score'] >= 6 else 'score-mid'
        html += f"""
            <tr>
                <td><strong>{c['keyword']}</strong></td>
                <td><span class="score-badge {score_class}">{c['score']}</span></td>
                <td>{', '.join(c['reasons'])}</td>
                <td>{c['seed']}</td>
            </tr>
        """
        
    html += """
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)
        
    return filename

# --- MAIN ---
if __name__ == "__main__":
    print("🚀 Profit Hunter Initializing...")
    
    # 1. Load Seeds
    seeds = load_seeds()
    print(f"📦 Loaded {len(seeds)} base seeds.")
    
    # 2. Mine Keywords (Alphabet Soup Strategy)
    raw_keywords = mine_keywords(seeds)
    print(f"⛏️  Collected {len(raw_keywords)} raw suggestions.")
    
    # 3. Score & Validate
    valid_candidates = []
    print("[*] Scoring and validating candidates...")
    for item in raw_keywords:
        score, reasons = score_candidate(item['keyword'])
        if score > 0:
            valid_candidates.append({
                'keyword': item['keyword'],
                'seed': item['seed'],
                'score': score,
                'reasons': reasons
            })
            
    print(f"🎯 Found {len(valid_candidates)} profitable opportunities.")
    
    # 4. Generate Report
    report_file = generate_report(valid_candidates)
    print(f"📄 Full Report Generated: {report_file}")
    
    # 5. Console Summary (Top 10)
    print("\n🏆 TOP 10 PROFIT OPPORTUNITIES:")
    print("-" * 60)
    valid_candidates.sort(key=lambda x: x['score'], reverse=True)
    for i, c in enumerate(valid_candidates[:10], 1):
        print(f"{i}. {c['keyword']} (Score: {c['score']})")
        print(f"   -> Signals: {', '.join(c['reasons'])}")
    print("-" * 60)
