#!/usr/bin/env python3
"""
GitHub Star History Collector - Fetches monthly star data for repos using GraphQL API

Usage:
    python3 github_star_history.py              # Default: 2025-01-01
    python3 github_star_history.py 2024-01-01   # Custom start date
"""

import subprocess
import json
import csv
import sys
from collections import defaultdict
from datetime import datetime

def run_graphql(query):
    result = subprocess.run(
        ["gh", "api", "graphql", "-f", f"query={query}"],
        capture_output=True, text=True, check=True
    )
    return json.loads(result.stdout)

def fetch_stars_since(owner, repo, since_date):
    all_stars = []
    cursor = None
    page = 0
    
    print(f"\nFetching {owner}/{repo} stars (newest first)...")
    
    while True:
        page += 1
        
        if cursor:
            query = f'''
            {{
              repository(owner: "{owner}", name: "{repo}") {{
                stargazers(last: 100, before: "{cursor}", orderBy: {{field: STARRED_AT, direction: ASC}}) {{
                  edges {{ starredAt node {{ login }} }}
                  pageInfo {{ hasPreviousPage startCursor }}
                }}
              }}
            }}
            '''
        else:
            query = f'''
            {{
              repository(owner: "{owner}", name: "{repo}") {{
                stargazers(last: 100, orderBy: {{field: STARRED_AT, direction: ASC}}) {{
                  edges {{ starredAt node {{ login }} }}
                  pageInfo {{ hasPreviousPage startCursor }}
                }}
              }}
            }}
            '''
        
        data = run_graphql(query)
        edges = data["data"]["repository"]["stargazers"]["edges"]
        page_info = data["data"]["repository"]["stargazers"]["pageInfo"]
        
        count = 0
        oldest_date = None
        
        for edge in edges:
            starred_at = edge["starredAt"]
            oldest_date = starred_at
            if starred_at >= since_date:
                all_stars.append({
                    "user": edge["node"]["login"],
                    "starred_at": starred_at,
                    "repo": f"{owner}/{repo}"
                })
                count += 1
        
        print(f"  Page {page}: {count} stars (oldest: {oldest_date[:10] if oldest_date else 'N/A'})")
        
        if oldest_date and oldest_date < since_date:
            break
        
        if not page_info["hasPreviousPage"]:
            break
        
        cursor = page_info["startCursor"]
    
    return all_stars

def get_repo_totals():
    query = '''
    {
      coder: repository(owner: "coder", name: "coder") { stargazerCount }
      codeServer: repository(owner: "coder", name: "code-server") { stargazerCount }
    }
    '''
    data = run_graphql(query)
    return data["data"]["coder"]["stargazerCount"], data["data"]["codeServer"]["stargazerCount"]

def main():
    since_date = sys.argv[1] if len(sys.argv) > 1 else "2025-01-01"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "github_stars.csv"
    
    print(f"Fetching stars since {since_date}")
    
    # Fetch star data
    all_stars = []
    all_stars.extend(fetch_stars_since("coder", "coder", since_date))
    all_stars.extend(fetch_stars_since("coder", "code-server", since_date))
    
    # Aggregate by month and repo
    monthly = defaultdict(lambda: defaultdict(int))
    for star in all_stars:
        month = star["starred_at"][:7]
        repo = star["repo"]
        monthly[month][repo] += 1
    
    # Get current totals
    coder_total, cs_total = get_repo_totals()
    print(f"\nCurrent totals: coder/coder={coder_total}, coder/code-server={cs_total}")
    
    # Calculate all-time by working backwards
    months = sorted(monthly.keys(), reverse=True)
    coder_cumulative = {}
    cs_cumulative = {}
    coder_running = coder_total
    cs_running = cs_total
    
    for month in months:
        coder_cumulative[month] = coder_running
        cs_cumulative[month] = cs_running
        coder_running -= monthly[month].get("coder/coder", 0)
        cs_running -= monthly[month].get("coder/code-server", 0)
    
    # Write CSV
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Month', 'coder/coder', 'code-server', 'coder/coder All-Time', 'code-server All-Time'])
        for month in sorted(monthly.keys()):
            coder = monthly[month].get("coder/coder", 0)
            cs = monthly[month].get("coder/code-server", 0)
            writer.writerow([month, coder, cs, coder_cumulative.get(month, ''), cs_cumulative.get(month, '')])
    
    print(f"\nWritten to {output_file}")
    
    # Also print to console
    print("\n" + "="*85)
    print(f"{'Month':<10} {'coder/coder':>12} {'code-server':>12} {'coder Total':>15} {'code-server Total':>18}")
    print("-"*85)
    for month in sorted(monthly.keys()):
        coder = monthly[month].get("coder/coder", 0)
        cs = monthly[month].get("coder/code-server", 0)
        print(f"{month:<10} {coder:>12,} {cs:>12,} {coder_cumulative.get(month, 0):>15,} {cs_cumulative.get(month, 0):>18,}")
    print("-"*85)

if __name__ == "__main__":
    main()
