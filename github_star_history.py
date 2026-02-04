#!/usr/bin/env python3
"""
GitHub Star History Collector - Fetches monthly star data for repos using GraphQL API

Usage:
    python3 github_star_history.py              # Default: 2025-01-01
    python3 github_star_history.py 2024-01-01   # Custom start date
    python3 github_star_history.py 2025-01-01 output.csv  # Custom output file
"""

import subprocess
import json
import csv
import sys
from collections import defaultdict
from datetime import datetime

# ============================================================================
# CONFIGURATION - Add or remove repositories here
# ============================================================================
REPOSITORIES = [
    ("coder", "coder"),
    ("coder", "code-server"),
    ("coder", "blink"),
    ("coder", "boundary"),
    ("coder", "agentapi"),
    ("coder", "aibridge"),
]
# ============================================================================

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

def get_repo_total(owner, repo):
    query = f'''
    {{
      repository(owner: "{owner}", name: "{repo}") {{
        stargazerCount
      }}
    }}
    '''
    data = run_graphql(query)
    return data["data"]["repository"]["stargazerCount"]

def main():
    since_date = sys.argv[1] if len(sys.argv) > 1 else "2025-01-01"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "github_stars.csv"
    
    print(f"Fetching stars since {since_date}")
    print(f"Tracking {len(REPOSITORIES)} repositories")
    
    # Fetch star data for all repos
    all_stars = []
    for owner, repo in REPOSITORIES:
        all_stars.extend(fetch_stars_since(owner, repo, since_date))
    
    # Aggregate by month and repo
    monthly = defaultdict(lambda: defaultdict(int))
    for star in all_stars:
        month = star["starred_at"][:7]
        repo = star["repo"]
        monthly[month][repo] += 1
    
    # Get current totals for all repos
    repo_totals = {}
    print("\nCurrent totals:")
    for owner, repo in REPOSITORIES:
        repo_key = f"{owner}/{repo}"
        total = get_repo_total(owner, repo)
        repo_totals[repo_key] = total
        print(f"  {repo_key}: {total:,}")
    
    # Calculate all-time by working backwards from current total
    months = sorted(monthly.keys(), reverse=True)
    cumulative = {repo_key: {} for repo_key in repo_totals.keys()}
    running = dict(repo_totals)  # Copy current totals
    
    for month in months:
        for repo_key in repo_totals.keys():
            cumulative[repo_key][month] = running[repo_key]
            running[repo_key] -= monthly[month].get(repo_key, 0)
    
    # Build column names
    repo_names = [f"{owner}/{repo}" for owner, repo in REPOSITORIES]
    monthly_cols = repo_names
    alltime_cols = [f"{name} All-Time" for name in repo_names]
    
    # Write CSV
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Month'] + monthly_cols + alltime_cols)
        for month in sorted(monthly.keys()):
            row = [month]
            # Monthly counts
            for repo_key in repo_names:
                row.append(monthly[month].get(repo_key, 0))
            # All-time totals
            for repo_key in repo_names:
                row.append(cumulative[repo_key].get(month, ''))
            writer.writerow(row)
    
    print(f"\nWritten to {output_file}")
    
    # Print summary table to console
    print("\n" + "="*120)
    header = f"{'Month':<10}"
    for name in repo_names:
        short_name = name.split('/')[1][:12]
        header += f" {short_name:>12}"
    header += " |"
    for name in repo_names:
        short_name = name.split('/')[1][:10] + " Tot"
        header += f" {short_name:>14}"
    print(header)
    print("-"*120)
    
    for month in sorted(monthly.keys()):
        row = f"{month:<10}"
        for repo_key in repo_names:
            row += f" {monthly[month].get(repo_key, 0):>12,}"
        row += " |"
        for repo_key in repo_names:
            row += f" {cumulative[repo_key].get(month, 0):>14,}"
        print(row)
    print("-"*120)

if __name__ == "__main__":
    main()
