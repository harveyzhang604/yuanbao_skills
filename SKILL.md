---
name: trend-breakout-hunter
description: "THE ULTIMATE micro-SaaS idea discovery engine. Integrates mining (Alphabet Soup), validation (GPTs benchmark), and competition analysis (SERP check). Automatically finds high-intent keywords where Google's top results are weak (blogs/forums), signaling a 'Green Light' to build. Daily automated execution recommended."
license: MIT
---

# Trend Hunter Ultimate

## Overview

This is the definitive tool for Independent Developers to find **validated** business ideas. It replaces manual market research with an automated pipeline that checks:
1.  **Demand**: Is anyone searching? (Alphabet Soup)
2.  **Intent**: Are they trying to solve a problem? (Pain Identification)
3.  **Volume**: Is it worth my time? (GPTs Benchmark)
4.  **Competition**: Can I rank? (SERP Analysis)

## The Core Pipeline

### 1. Alphabet Mining (The "Wide Net")
Scans `[seed] + a...z` and `a...z + [seed]` to find long-tail queries that standard tools miss.
*   *Input*: "calculator"
*   *Output*: "army body fat calculator", "z score calculator"

### 2. Pain & Intent Filtering (The "Filter")
Discard navigational queries. Keep only High Intent keywords:
*   **Pain**: "fix", "struggling with", "manual"
*   **Commercial**: "tool", "generator", "builder"
*   **Competitor**: "alternative to", "vs"

### 3. GPTs Benchmarking (The "Volume Check")
Compares the keyword's search volume against the baseline keyword **"GPTs"**.
*   **> 20% of GPTs**: Major Hit.
*   **5-20%**: Sweet Spot (Niche).
*   **< 5%**: Too small (Ignore).

### 4. SERP Competition Analysis (The "Green Light")
**This is the killer feature.** The agent browses Google and checks the Top 3 results.
*   **🟢 BUILD NOW**: Top results are Reddit, Quora, Medium, or Forums. (Users are discussing the problem, but no tool exists!)
*   **🟡 WATCH**: Mixed results (1 tool, 2 blogs).
*   **🔴 DROP**: Top results are established tools (e.g., calculator.net, adobe.com).

## Usage

### Run Manually
```bash
# Full pipeline
run trend hunter ultimate
```

### Automated Schedule (Recommended)
Add this to your daily cron:
```
0 9 * * * python3 skills/ai-tool-keyword-hunter/trend_hunter_ultimate.py
```

## Output Interpretation

The skill generates an HTML report `data/ultimate_report_YYYYMMDD.html`.

**Decision Matrix:**
| Decision | Meaning | Action |
| :--- | :--- | :--- |
| **BUILD NOW** | High Pain + Weak Competitors | Start coding MVP today. |
| **WATCH** | Good volume, but mixed competition | Check if you can niche down further. |
| **DROP** | Low intent OR High competition | Move to next seed. |

## Configuration
*   **Seeds**: `words.md`
*   **Benchmarks**: Edit `BENCHMARK_KEYWORD` in `trend_hunter_ultimate.py` to change the volume baseline.
