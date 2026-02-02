#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Niche Keyword Hunter - Advanced Long-tail Discovery for Micro-SaaS
Based on 'find.md' strategy: Focus on 'How to', 'Alternative to', 'Pain points'.
"""
import sys
import os
import requests
import time
import re
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

# --- CONFIGURATION ---
NICHE_PATTERNS = [
    "how to {}", 
    "best app for {}", 
    "is there a tool for {}", 
    "struggling with {}", 
    "alternative to {}", 
    "vs {}", 
    "{} generator", 
    "{} calculator", 
    "{} converter",
    "remove {} from",
    "convert {} to",
    "download {} from"
]

PAIN_POINT_TRIGGERS = [
    "struggling with", "cant", "can't", "how do i", "fix", "solve", "error", "problem"
]

# --- LOAD SEEDS ---
def load_seeds():
    """Load seeds from words.md and add custom niche seeds"""
    seeds = []
    # 1. Load from file
    try:
        with open("words.md", "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split("\t")
                if len(parts) >= 2 and parts[0].isdigit():
                    name = parts[1].split("（")[0].strip()
                    seeds.append(name.lower())
    except FileNotFoundError:
        pass
    
    # 2. Add 'find.md' recommended seeds
    niche_seeds = [
        "video", "audio", "image", "pdf", "text", "file", 
        "recording", "streaming", "writing", "coding", "design",
        "email", "calendar", "meeting", "notes", "task",
        "instagram", "tiktok", "youtube", "twitter", "linkedin"
    ]
    
    return list(set(seeds + niche_seeds))

# --- GOOGLE SUGGEST API ---
def google_suggest(query):
    """Get Google Suggest keywords"""
    url = "https://suggestqueries.google.com/complete/search"
    params = {"client": "firefox", "q": query, "hl": "en", "gl": "us"}
    try:
        r = requests.get(url, params=params, timeout=5)
        if r.status_code == 200:
            return r.json()[1]
    except:
        pass
    return []

# --- MINING ENGINE ---
def mine_niche_keywords(seeds):
    all_keywords = []
    seen = set()
    
    print(f"[*] Starting mining with {len(seeds)} seeds...")
    
    for i, seed in enumerate(seeds):
        # Progress indicator
        if i % 5 == 0:
            print(f"    Progress: {i}/{len(seeds)} (Current: {seed})")
            
        # 1. Apply Niche Patterns
        for pattern in NICHE_PATTERNS:
            query = pattern.format(seed)
            suggestions = google_suggest(query)
            
            for s in suggestions:
                if s not in seen:
                    seen.add(s)
                    all_keywords.append({
                        'keyword': s,
                        'seed': seed,
                        'pattern': pattern,
                        'source': 'suggest'
                    })
            time.sleep(0.1) # Respect rate limits
            
        # 2. Alphabet Soup (A-Z) for depth
        # Only do this for high-value seeds to save time
        if seed in ["video", "pdf", "image", "ai"]:
            for char in "abcdefghijklmnopqrstuvwxyz":
                query = f"{seed} {char}"
                suggestions = google_suggest(query)
                for s in suggestions:
                    if s not in seen:
                        seen.add(s)
                        all_keywords.append({
                            'keyword': s,
                            'seed': seed,
                            'pattern': 'alphabet',
                            'source': 'suggest'
                        })
                time.sleep(0.1)

    return all_keywords

# --- INTELLIGENT FILTERING ---
def analyze_candidates(keywords):
    candidates = []
    
    for item in keywords:
        kw = item['keyword'].lower()
        words = kw.split()
        word_count = len(words)
        
        # Filter 1: Length (Long-tail focus)
        # User wants "smaller words" (meaning lower competition, usually longer tail)
        # "free pdf converter" (3 words) is hard. "how to convert pdf to word without losing formatting" (9 words) is easy.
        if word_count < 3: 
            continue
            
        # Filter 2: Navigational/Brand garbage
        if any(x in kw for x in ["login", "signin", "sign in", "customer service", "phone number", "support"]):
            continue
            
        # Filter 3: Intent Scoring
        score = 0
        intent = "Info"
        
        # Commercial/Tool Intent
        if any(x in kw for x in ["tool", "app", "software", "generator", "calculator", "converter", "maker", "builder"]):
            score += 2
            intent = "Tool"
            
        # Pain Point Intent
        if any(x in kw for x in PAIN_POINT_TRIGGERS):
            score += 3
            intent = "Pain"
            
        # Comparison Intent
        if " vs " in kw or "alternative" in kw:
            score += 2
            intent = "Compare"
            
        # Transactional modifiers
        if any(x in kw for x in ["best", "top", "free", "online", "buy", "price"]):
            score += 1
            
        # Long-tail bonus
        if word_count >= 5:
            score += 2
        elif word_count == 4:
            score += 1
            
        # Decision Logic
        # Score >= 4 is a "Build" candidate (High value)
        # Score 3 is "Watch"
        if score >= 4:
            decision = "Build"
        elif score == 3:
            decision = "Watch"
        else:
            decision = "Drop"
            
        # Final Candidates List
        if decision != "Drop":
            candidates.append({
                'keyword': kw,
                'seed': item['seed'],
                'length': word_count,
                'intent': intent,
                'score': score,
                'decision': decision
            })
            
    return candidates

# --- REPORTING ---
def generate_report(candidates):
    # Sort by Score (Desc) then Length (Desc)
    candidates.sort(key=lambda x: (x['score'], x['length']), reverse=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"data/niche_report_{timestamp}.html"
    os.makedirs("data", exist_ok=True)
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Niche Hunter Report {timestamp}</title>
        <style>
            body {{ font-family: sans-serif; padding: 20px; background: #f0f2f5; }}
            .card {{ background: white; padding: 15px; margin-bottom: 10px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .tag {{ display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 12px; margin-right: 5px; }}
            .tag.pain {{ background: #ffebee; color: #c62828; }}
            .tag.tool {{ background: #e3f2fd; color: #1565c0; }}
            .tag.compare {{ background: #fff3e0; color: #ef6c00; }}
            .score {{ font-weight: bold; color: #2e7d32; }}
            table {{ width: 100%; border-collapse: collapse; background: white; }}
            th, td {{ padding: 10px; border-bottom: 1px solid #eee; text-align: left; }}
            th {{ background: #f8f9fa; }}
        </style>
    </head>
    <body>
        <h1>🎯 Niche Keyword Opportunities</h1>
        <p>Focus: Long-tail, Low Competition, High Intent</p>
        
        <h2>🔥 Top 20 "Hidden Gem" Opportunities</h2>
        <div class="cards">
    """
    
    for c in candidates[:20]:
        tag_class = c['intent'].lower()
        html += f"""
        <div class="card">
            <h3>{c['keyword']}</h3>
            <div>
                <span class="tag {tag_class}">{c['intent']}</span>
                <span class="tag">Len: {c['length']}</span>
                <span class="score">Score: {c['score']}/10</span>
            </div>
        </div>
        """
        
    html += """
        </div>
        <h2>📊 Full Data Table</h2>
        <table>
            <thead><tr><th>Keyword</th><th>Intent</th><th>Length</th><th>Score</th></tr></thead>
            <tbody>
    """
    
    for c in candidates:
        html += f"<tr><td>{c['keyword']}</td><td>{c['intent']}</td><td>{c['length']}</td><td>{c['score']}</td></tr>"
        
    html += """
            </tbody>
        </table>
    </body>
    </html>
    """
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)
        
    return filename

if __name__ == "__main__":
    print("🚀 Niche Hunter Initializing...")
    seeds = load_seeds()
    print(f"📦 Loaded {len(seeds)} seeds (including niche modifiers)")
    
    raw_keywords = mine_niche_keywords(seeds)
    print(f"⛏️  Mined {len(raw_keywords)} raw suggestions")
    
    candidates = analyze_candidates(raw_keywords)
    print(f"🎯 Found {len(candidates)} qualified candidates")
    
    report_file = generate_report(candidates)
    print(f"📄 Report generated: {report_file}")
    
    # Print Top 10 to Console
    print("\n🏆 TOP 10 OPPORTUNITIES:")
    candidates.sort(key=lambda x: x['score'], reverse=True)
    for i, c in enumerate(candidates[:10], 1):
        print(f"{i}. {c['keyword']} [{c['intent']}] (Score: {c['score']})")
