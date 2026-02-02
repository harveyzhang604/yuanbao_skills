#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Trend Breakout Hunter v2 - Smart Google Suggest Mining"""
import sys
import os
sys.stdout.reconfigure(encoding='utf-8')

import requests
import time
import re

# Load seed words
def load_seed_words():
    seeds = []
    with open("words.md", "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) >= 2 and parts[0].isdigit():
                name = parts[1].split("（")[0].strip()
                seeds.append(name)
    return seeds

def google_suggest(query):
    """Get Google Suggest keywords"""
    url = "https://suggestqueries.google.com/complete/search"
    params = {"client": "firefox", "q": query, "hl": "en", "gl": "us"}
    try:
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            return r.json()[1]
    except:
        pass
    return []

def smart_mining(seed_words):
    """Smart keyword mining using Google Suggest"""
    all_keywords = []
    seen = set()

    # Common English words to prefix (not single letters)
    prefixes = [
        "ai ", "free ", "online ", "best ", "easy ", "simple ",
        "快速", "免费", "在线"  # 中文也试试
    ]

    for seed in seed_words:
        print(f"  Mining: {seed}")

        # Strategy 1: Seed alone -> base suggestions
        base = google_suggest(seed)
        for kw in base:
            if kw not in seen and len(kw.split()) >= 2:
                seen.add(kw)
                all_keywords.append({'keyword': kw, 'seed': seed, 'source': 'base'})
        time.sleep(0.3)

        # Strategy 2: Seed + space -> complete phrases (suffix expansion)
        suffix = google_suggest(f"{seed} ")
        for kw in suffix:
            if kw not in seen and len(kw.split()) >= 2:
                seen.add(kw)
                all_keywords.append({'keyword': kw, 'seed': seed, 'source': 'suffix'})
        time.sleep(0.3)

        # Strategy 3: Common prefixes + seed (not single letters)
        for prefix in prefixes[:3]:  # Limit to 3 to save time
            full_query = f"{prefix}{seed}"
            result = google_suggest(full_query)
            for kw in result:
                if kw not in seen and seed.lower() in kw.lower():
                    seen.add(kw)
                    all_keywords.append({'keyword': kw, 'seed': seed, 'source': 'prefix'})
            time.sleep(0.2)

    return all_keywords

def filter_and_score(keywords):
    """Filter and score keywords"""
    # Noise patterns
    noise_patterns = [
        r'\b(smith|johnson|williams|brown|jones|garcia|miller|davis)\b',
        r'\b(election|scandal|arrest|death|crash|attack)\b',
        r'\b(movie|song|album|episode|trailer)\b',
    ]

    candidates = []

    for item in keywords:
        kw = item['keyword']
        kw_lower = kw.lower()
        words = kw.split()

        # Must be multi-word phrase
        if len(words) < 2:
            continue

        # No single-letter words
        if any(len(w) == 1 for w in words):
            continue

        # No noise
        if any(re.search(p, kw_lower) for p in noise_patterns):
            continue

        # Must contain tool-related word
        tool_words = ['calculator', 'generator', 'converter', 'checker', 'maker',
                     'editor', 'analyzer', 'optimizer', 'translator', 'parser',
                     'formatter', 'encoder', 'decoder', 'builder', 'extractor',
                     'downloader', 'uploader', 'viewer', 'player', 'creator',
                     'processor', 'manager', 'tracker', 'planner', 'scheduler']
        if not any(tw in kw_lower for tw in tool_words):
            continue

        # Determine tool type
        if any(w in kw_lower for w in ['calculator', 'calc']):
            tool_type = 'calculator'
        elif any(w in kw_lower for w in ['generator', 'create', 'make']):
            tool_type = 'generator'
        elif any(w in kw_lower for w in ['converter', 'convert', ' to ', 'to jpg', 'to pdf', 'heic']):
            tool_type = 'converter'
        elif any(w in kw_lower for w in ['checker', 'check', 'verify', 'test']):
            tool_type = 'checker'
        elif any(w in kw_lower for w in ['editor', 'edit']):
            tool_type = 'editor'
        elif any(w in kw_lower for w in ['optimizer', 'optimize']):
            tool_type = 'optimizer'
        elif any(w in kw_lower for w in ['analyzer', 'analyze']):
            tool_type = 'analyzer'
        elif any(w in kw_lower for w in ['translator', 'translate']):
            tool_type = 'translator'
        elif any(w in kw_lower for w in ['extractor', 'extract']):
            tool_type = 'extractor'
        elif any(w in kw_lower for w in ['downloader', 'download']):
            tool_type = 'downloader'
        else:
            tool_type = 'other'

        # Score (1-5)
        score = 3
        if any(rp in kw_lower for rp in ['calculator', 'generator', 'converter', 'checker']):
            score += 1
        if any(w in kw_lower for w in [' ai ', 'online', 'free', 'tool']):
            score += 1
        word_count = len(words)
        if 2 <= word_count <= 4:
            score += 1

        # Decision
        if score >= 4:
            decision = "Build"
        elif score >= 3:
            decision = "Watch"
        else:
            decision = "Drop"

        candidates.append({
            'keyword': kw,
            'seed': item['seed'],
            'tool_type': tool_type,
            'buildability': score,
            'decision': decision,
            'source': item['source']
        })

    return candidates

def generate_html_report(candidates):
    """Generate HTML report"""
    os.makedirs("data", exist_ok=True)
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"data/keyword_report_{timestamp}.html"

    # Filter and sort
    qualified = [c for c in candidates if c['decision'] in ['Build', 'Watch']]
    qualified.sort(key=lambda x: (0 if x['decision'] == 'Build' else 1, -x['buildability']))

    # Group by type
    by_type = {}
    for c in qualified:
        t = c['tool_type']
        by_type.setdefault(t, []).append(c)

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>Trend Breakout Report - {datetime.now().strftime("%Y-%m-%d")}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, sans-serif; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); color: #eee; padding: 2rem; }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        h1 {{ font-size: 2.5rem; margin-bottom: 0.5rem; background: linear-gradient(90deg, #00d9ff, #00ff88); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; margin: 2rem 0; }}
        .stat-card {{ background: rgba(255,255,255,0.1); border-radius: 12px; padding: 1.5rem; text-align: center; }}
        .stat-card .num {{ font-size: 2.5rem; font-weight: bold; color: #00d9ff; }}
        .stat-card .label {{ color: #aaa; margin-top: 0.5rem; }}
        .section {{ margin: 3rem 0; }}
        .section h2 {{ font-size: 1.5rem; margin-bottom: 1rem; padding-bottom: 0.5rem; border-bottom: 2px solid rgba(0,217,255,0.3); }}
        table {{ width: 100%; border-collapse: collapse; margin: 1rem 0; background: rgba(255,255,255,0.05); border-radius: 12px; }}
        th, td {{ padding: 0.8rem 1rem; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.1); }}
        th {{ background: rgba(0,217,255,0.2); }}
        tr:hover {{ background: rgba(255,255,255,0.05); }}
        .priority-high {{ color: #ff6b6b; font-weight: bold; }}
        .priority-medium {{ color: #ffd93d; }}
        .badge {{ display: inline-block; padding: 0.2rem 0.6rem; border-radius: 15px; font-size: 0.75rem; background: rgba(0,217,255,0.2); }}
        .top-actions {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1rem; }}
        .action-card {{ background: linear-gradient(135deg, rgba(0,217,255,0.2), rgba(0,255,136,0.1)); border-radius: 12px; padding: 1.5rem; border-left: 4px solid #00d9ff; }}
        .action-card h3 {{ color: #00d9ff; margin-bottom: 0.5rem; }}
        .footer {{ text-align: center; margin-top: 3rem; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Trend Breakout Report</h1>
        <p style="color:#aaa;">Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>

        <div class="stats">
            <div class="stat-card"><div class="num">{len(candidates)}</div><div class="label">Total</div></div>
            <div class="stat-card"><div class="num">{len(qualified)}</div><div class="label">Qualified</div></div>
            <div class="stat-card"><div class="num">{sum(1 for c in qualified if c['decision']=='Build')}</div><div class="label">Build</div></div>
            <div class="stat-card"><div class="num">{sum(1 for c in qualified if c['decision']=='Watch')}</div><div class="label">Watch</div></div>
        </div>

        <div class="section">
            <h2>Top Actions</h2>
            <div class="top-actions">
"""

    for i, c in enumerate(qualified[:6], 1):
        html += f"""                <div class="action-card">
                    <h3>#{i} {c['keyword']}</h3>
                    <p><span class="badge">{c['tool_type']}</span> <span class="badge">{c['decision']}</span></p>
                    <p>Score: {c['buildability']}/5 | Seed: {c['seed']}</p>
                </div>
"""

    html += """            </div>
        </div>

        <div class="section">
            <h2>All Candidates</h2>
            <table>
                <thead>
                    <tr><th>Keyword</th><th>Seed</th><th>Type</th><th>Score</th><th>Decision</th></tr>
                </thead>
                <tbody>
"""

    for c in qualified:
        dc = c['decision']
        pc = 'priority-high' if dc == 'Build' else 'priority-medium'
        html += f"""                    <tr>
                        <td><strong>{c['keyword']}</strong></td>
                        <td>{c['seed']}</td>
                        <td><span class="badge">{c['tool_type']}</span></td>
                        <td>{c['buildability']}/5</td>
                        <td class="{pc}">{dc}</td>
                    </tr>
"""

    html += """                </tbody>
            </table>
        </div>

        <div class="footer">Generated by Trend Breakout Hunter Skill</div>
    </div>
</body>
</html>"""

    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)

    return filename, qualified

if __name__ == "__main__":
    print("="*60)
    print("[*] Trend Breakout Hunter v2 - Smart Suggest Mining")
    print("="*60)

    # Load seeds
    seed_words = load_seed_words()
    print(f"\n[+] Loaded {len(seed_words)} seeds")

    # Smart mining
    print("\n[*] Mining keywords via Google Suggest...")
    keywords = smart_mining(seed_words[:25])  # Limit to 25 seeds for speed

    # Filter and score
    print("\n[*] Filtering and scoring...")
    candidates = filter_and_score(keywords)
    print(f"    Qualified: {len(candidates)}")

    # Generate report
    print("\n[*] Generating report...")
    report, qualified = generate_html_report(candidates)

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print("="*60)
    print(f"  Keywords mined: {len(keywords)}")
    print(f"  Candidates: {len(candidates)}")
    print(f"  Build: {sum(1 for c in qualified if c['decision']=='Build')}")
    print(f"  Watch: {sum(1 for c in qualified if c['decision']=='Watch')}")
    print(f"\n  Report: {report}")

    if qualified:
        print(f"\n[*] TOP 20 CANDIDATES:")
        print("-"*60)
        for i, c in enumerate(qualified[:20], 1):
            print(f"  {i:2}. {c['keyword']:<45} | {c['tool_type']:<10} | {c['decision']}")

    print(f"\n[+] Done!")
