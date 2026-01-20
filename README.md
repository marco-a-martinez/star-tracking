# GitHub Star Tracking

Track star counts for coder/coder and coder/code-server repositories.

## Files

- `github_star_history.py` - Script to fetch fresh star data
- `github_stars_2025.csv` - Current data snapshot

## Usage

To refresh the data:

```bash
# Fetch 2025 data (default)
python3 github_star_history.py

# Fetch from a specific date
python3 github_star_history.py 2024-01-01

# Specify output file
python3 github_star_history.py 2025-01-01 my_output.csv
```

## Requirements

- Python 3
- GitHub CLI (`gh`) authenticated

## Data Columns

| Column | Description |
|--------|-------------|
| Month | YYYY-MM format |
| coder/coder | New stars that month |
| code-server | New stars that month |
| coder/coder All-Time | Total stars at end of month |
| code-server All-Time | Total stars at end of month |
