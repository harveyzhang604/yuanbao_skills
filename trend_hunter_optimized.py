#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Trend Breakout Hunter - Optimized AI Tool Keyword Discovery"""
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

def optimized_mining(seed_words):
    """Optimized keyword mining with multiple strategies"""
    all_keywords = []
    seen = set()

    # Strategy 1: Common English prefixes (not single letters)
    en_prefixes = [
        "ai ", "free ", "online ", "best ", "easy ", "simple ",
        "quick ", "fast ", "secure ", "pdf ", "jpg ", "png ",
        "music ", "video ", "image ", "text ", "code ", "word "
    ]

    # Strategy 2: Question patterns
    question_patterns = [
        "how to ", "what is ", "where to ", "why is ",
        "how do i ", "what is the best ", "how can i "
    ]

    # Strategy 3: Comparison patterns
    compare_patterns = [
        " vs ", " versus ", " alternative to ", " like ",
        " similar to ", " better than "
    ]

    for seed in seed_words:
        print(f"  Mining: {seed}")

        # Strategy A: Base query
        base = google_suggest(seed)
        for kw in base:
            if kw not in seen and len(kw.split()) >= 2:
                seen.add(kw)
                all_keywords.append({'keyword': kw, 'seed': seed, 'source': 'base'})
        time.sleep(0.2)

        # Strategy B: Suffix expansion (seed + space)
        suffix = google_suggest(f"{seed} ")
        for kw in suffix:
            if kw not in seen and len(kw.split()) >= 2:
                seen.add(kw)
                all_keywords.append({'keyword': kw, 'seed': seed, 'source': 'suffix'})
        time.sleep(0.2)

        # Strategy C: English prefixes
        for prefix in en_prefixes[:5]:
            result = google_suggest(f"{prefix}{seed}")
            for kw in result:
                if kw not in seen and seed.lower() in kw.lower():
                    seen.add(kw)
                    all_keywords.append({'keyword': kw, 'seed': seed, 'source': 'prefix'})
            time.sleep(0.15)

        # Strategy D: Question patterns
        for pattern in question_patterns[:2]:
            result = google_suggest(f"{pattern}{seed}")
            for kw in result:
                if kw not in seen and seed.lower() in kw.lower():
                    seen.add(kw)
                    all_keywords.append({'keyword': kw, 'seed': seed, 'source': 'question'})
            time.sleep(0.15)

    return all_keywords

def filter_and_score(keywords):
    """Enhanced filtering and scoring"""
    noise_patterns = [
        r'\b(smith|johnson|williams|brown|jones|garcia|miller|davis|wilson|taylor)\b',
        r'\b(election|scandal|arrest|death|crash|attack|lawsuit|scandal)\b',
        r'\b(movie|song|album|episode|trailer|season)\b',
        r'\b(news|breaking|update|report)\b',
    ]

    # Extended tool words
    tool_words = [
        'calculator', 'generator', 'converter', 'checker', 'maker',
        'editor', 'analyzer', 'optimizer', 'translator', 'parser',
        'formatter', 'encoder', 'decoder', 'builder', 'extractor',
        'downloader', 'uploader', 'viewer', 'player', 'creator',
        'processor', 'manager', 'tracker', 'planner', 'scheduler',
        'remover', 'joiner', 'splitter', 'merger', 'resize',
        'compress', 'convert', 'extract', 'generate', 'create',
        'validate', 'verify', 'test', 'detect', 'scan',
        'encrypt', 'decrypt', 'hash', 'minify', 'beautify',
        'crop', 'rotate', 'flip', 'trim', 'merge', 'split'
    ]

    candidates = []

    for item in keywords:
        kw = item['keyword']
        kw_lower = kw.lower()
        words = kw.split()

        # Basic filters
        if len(words) < 2:
            continue
        if any(len(w) == 1 for w in words):
            continue
        if any(re.search(p, kw_lower) for p in noise_patterns):
            continue

        # Must contain tool word
        if not any(tw in kw_lower for tw in tool_words):
            continue

        # Tool type detection
        tool_type = 'other'
        type_scores = []
        type_keywords = {
            'calculator': ['calculator', 'calc', 'calculate'],
            'generator': ['generator', 'generate', 'create', 'make', 'maker'],
            'converter': ['converter', 'convert', 'to ', ' to'],
            'checker': ['checker', 'check', 'verify', 'validate', 'test', 'detect'],
            'editor': ['editor', 'edit', 'modify', 'adjust'],
            'optimizer': ['optimizer', 'optimize', 'improve', 'enhance'],
            'analyzer': ['analyzer', 'analyze', 'analysis'],
            'translator': ['translator', 'translate', 'translation'],
            'extractor': ['extractor', 'extract', 'pull'],
            'downloader': ['downloader', 'download'],
            'uploader': ['uploader', 'upload'],
            'viewer': ['viewer', 'view', 'viewing'],
            'player': ['player', 'play'],
            'joiner': ['joiner', 'join', 'merge', 'combine'],
            'splitter': ['splitter', 'split', 'divide'],
            'remover': ['remover', 'remove', 'delete', 'erase'],
            'resizer': ['resize', 'scale'],
            'compressor': ['compress', 'compress'],
        }

        max_matches = 0
        for t, keywords_list in type_keywords.items():
            matches = sum(1 for kw in keywords_list if kw in kw_lower)
            if matches > max_matches:
                max_matches = matches
                tool_type = t

        # Scoring (1-5)
        score = 3
        if any(rp in kw_lower for rp in ['calculator', 'generator', 'converter', 'checker']):
            score += 1
        if any(w in kw_lower for w in [' ai ', 'online', 'free', 'tool']):
            score += 1
        if any(w in kw_lower for w in ['jpg', 'png', 'pdf', 'mp3', 'mp4', 'wav']):
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
    """Generate comprehensive HTML report"""
    os.makedirs("data", exist_ok=True)
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"data/keyword_report_{timestamp}.html"

    # Filter and sort
    qualified = [c for c in candidates if c['decision'] in ['Build', 'Watch']]
    qualified.sort(key=lambda x: (0 if x['decision'] == 'Build' else 1, -x['buildability']))

    # Stats by type
    type_stats = {}
    for c in qualified:
        t = c['tool_type']
        if t not in type_stats:
            type_stats[t] = {'build': 0, 'watch': 0, 'total': 0}
        type_stats[t]['total'] += 1
        if c['decision'] == 'Build':
            type_stats[t]['build'] += 1
        else:
            type_stats[t]['watch'] += 1

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>Trend Breakout Report - {datetime.now().strftime("%Y-%m-%d")}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, sans-serif; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); color: #eee; padding: 2rem; }}
        .container {{ max-width: 1500px; margin: 0 auto; }}
        h1 {{ font-size: 2.5rem; margin-bottom: 0.5rem; background: linear-gradient(90deg, #00d9ff, #00ff88); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 1rem; margin: 2rem 0; }}
        .stat-card {{ background: rgba(255,255,255,0.1); border-radius: 12px; padding: 1.2rem; text-align: center; }}
        .stat-card .num {{ font-size: 2.2rem; font-weight: bold; color: #00d9ff; }}
        .stat-card .label {{ color: #aaa; margin-top: 0.3rem; font-size: 0.9rem; }}
        .section {{ margin: 2.5rem 0; }}
        .section h2 {{ font-size: 1.4rem; margin-bottom: 1rem; padding-bottom: 0.5rem; border-bottom: 2px solid rgba(0,217,255,0.3); }}
        .type-stats {{ display: flex; flex-wrap: wrap; gap: 0.5rem; margin: 1rem 0; }}
        .type-badge {{ padding: 0.3rem 0.8rem; border-radius: 20px; font-size: 0.8rem; background: rgba(0,217,255,0.15); }}
        table {{ width: 100%; border-collapse: collapse; margin: 1rem 0; background: rgba(255,255,255,0.05); border-radius: 12px; }}
        th, td {{ padding: 0.7rem 1rem; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.1); }}
        th {{ background: rgba(0,217,255,0.2); font-weight: 600; }}
        tr:hover {{ background: rgba(255,255,255,0.05); }}
        .priority-high {{ color: #ff6b6b; font-weight: bold; }}
        .priority-medium {{ color: #ffd93d; }}
        .badge {{ display: inline-block; padding: 0.2rem 0.6rem; border-radius: 15px; font-size: 0.75rem; background: rgba(0,217,255,0.2); }}
        .top-actions {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1rem; }}
        .action-card {{ background: linear-gradient(135deg, rgba(0,217,255,0.2), rgba(0,255,136,0.1)); border-radius: 12px; padding: 1.3rem; border-left: 4px solid #00d9ff; }}
        .action-card h3 {{ color: #00d9ff; margin-bottom: 0.5rem; font-size: 1.1rem; }}
        .footer {{ text-align: center; margin-top: 3rem; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Trend Breakout Report</h1>
        <p style="color:#aaa;">Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>

        <div class="stats">
            <div class="stat-card"><div class="num">{len(candidates)}</div><div class="label">Total Keywords</div></div>
            <div class="stat-card"><div class="num">{len(qualified)}</div><div class="label">Qualified</div></div>
            <div class="stat-card"><div class="num">{sum(1 for c in qualified if c['decision']=='Build')}</div><div class="label">Build</div></div>
            <div class="stat-card"><div class="num">{sum(1 for c in qualified if c['decision']=='Watch')}</div><div class="label">Watch</div></div>
        </div>

        <div class="section">
            <h2>By Tool Type</h2>
            <div class="type-stats">
"""

    for t, s in sorted(type_stats.items(), key=lambda x: -x[1]['total']):
        html += f'<span class="type-badge">{t}: {s["total"]} (Build:{s["build"]})</span>'

    html += """            </div>
        </div>

        <div class="section">
            <h2>Top Actions</h2>
            <div class="top-actions">
"""

    for i, c in enumerate(qualified[:8], 1):
        html += f"""                <div class="action-card">
                    <h3>#{i} {c['keyword']}</h3>
                    <p>
                        <span class="badge">{c['tool_type']}</span>
                        <span class="badge">{c['decision']}</span>
                    </p>
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
    print("[*] Trend Breakout Hunter - Optimized Edition")
    print("="*60)

    # Load all seeds
    seed_words = load_seed_words()
    print(f"\n[+] Loaded {len(seed_words)} seeds")

    # Optimized mining with all seeds
    print("\n[*] Mining keywords (optimized strategies)...")
    keywords = optimized_mining(seed_words)

    # Filter and score
    print("\n[*] Filtering and scoring...")
    candidates = filter_and_score(keywords)
    print(f"    Qualified: {len(candidates)}")

    # Generate report
    print("\n[*] Generating HTML report...")
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
        print(f"\n[*] TOP 25 CANDIDATES:")
        print("-"*60)
        for i, c in enumerate(qualified[:25], 1):
            print(f"  {i:2}. {c['keyword']:<45} | {c['tool_type']:<12} | {c['decision']}")

    print(f"\n[+] Done!")
