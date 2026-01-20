# Product Requirements Document (PRD): GitHub Star Tracking System

## Document Information

| Field | Value |
|-------|-------|
| Product Name | GitHub Star Tracking System |
| Version | 1.0 |
| Author | Marco Martinez (Community Manager, Coder) |
| Last Updated | January 2026 |
| Status | In Production |

---

## Executive Summary

The GitHub Star Tracking System is an automated tool that collects and aggregates star history data for Coder's GitHub repositories. It produces monthly breakdowns with cumulative all-time totals, enabling the marketing team to report on repository growth as a quarterly metric. The system runs monthly in a Coder cloud workspace and outputs CSV files for easy analysis and reporting.

---

## Problem Statement

### Current Pain Points

1. **No Historical Visibility**: GitHub only shows current star counts, not historical trends. Understanding growth patterns requires manual tracking over time.

2. **Manual Data Collection**: Gathering star data across multiple repositories requires navigating to each repo individually and recording numbers in spreadsheets.

3. **API Complexity**: GitHub's stargazers API has pagination limits (40,000 stars max via REST) and requires authentication, making ad-hoc queries difficult for non-technical team members.

4. **Quarterly Reporting Burden**: Each quarter, someone must manually compile star metrics, which is time-consuming and error-prone.

### Impact

- Marketing team lacks visibility into repository growth trends
- Quarterly reports are delayed or incomplete
- Cannot correlate star growth with marketing campaigns or product launches
- No standardized metrics across repositories

---

## Goals & Success Metrics

### Primary Goals

1. Automate monthly collection of star data for all tracked repositories
2. Provide both monthly new stars and cumulative all-time totals
3. Output data in a format easily consumable by non-technical users
4. Support adding new repositories without code changes

### Success Metrics

| Metric | Target |
|--------|--------|
| Data Accuracy | 100% match with GitHub's reported totals |
| Collection Reliability | Successful monthly run with no manual intervention |
| Time Savings | Reduce quarterly reporting prep from hours to minutes |
| Repository Coverage | All major Coder repositories tracked |

### Non-Goals

- Real-time star tracking (daily or more frequent)
- Automated report generation (PDFs, slides)
- Competitor repository tracking
- Star/unstar event notifications
- Integration with BI tools (Phase 1)

---

## User Personas

### Primary User: Marketing Team

**Role**: Prepares quarterly metrics and reports for leadership

**Pain Points**:
- Needs historical data that GitHub doesn't surface
- Limited technical skills for API queries
- Time-constrained during quarterly reporting periods

**Needs**:
- Simple CSV files they can open in Excel/Google Sheets
- Clear column headers (no ambiguous data)
- Both monthly increments and running totals
- Data ready before quarterly deadlines

**Technical Proficiency**: Business user; comfortable with spreadsheets

### Secondary User: Community Manager (Marco)

**Role**: Maintains the system and adds new repositories

**Pain Points**:
- Limited software development experience
- Needs system to "just work" without constant maintenance

**Needs**:
- Simple commands to run or update the system
- Clear documentation for common tasks
- Easy process to add new repositories

**Technical Proficiency**: Non-developer; comfortable with terminal basics

### Tertiary User: Leadership (CMO, Executives)

**Role**: Consumes quarterly reports containing star metrics

**Pain Points**:
- Wants high-level trends, not raw data
- Needs context (month-over-month, year-over-year)

**Needs**:
- Summary data that can be dropped into presentations
- Consistent format quarter over quarter

**Technical Proficiency**: Business user; receives processed reports

---

## Solution Overview

### Architecture Overview

The system consists of a Python script that:

1. **Authenticates** with GitHub using the `gh` CLI
2. **Queries** the GitHub GraphQL API for stargazer data with timestamps
3. **Aggregates** data by month and repository
4. **Calculates** cumulative all-time totals
5. **Outputs** CSV files for analysis

### Technology Stack

| Component | Technology |
|-----------|------------|
| Runtime | Python 3.x |
| API | GitHub GraphQL API |
| Authentication | GitHub CLI (`gh`) |
| Infrastructure | Coder cloud workspace |
| Output Format | CSV |
| Version Control | GitHub (private repo) |

### Data Flow

```
1. Script starts
   ↓
2. Authenticate via gh CLI
   ↓
3. For each repository:
   a. Query GraphQL API (paginated, newest first)
   b. Collect stars until reaching start date
   ↓
4. Aggregate by month
   ↓
5. Calculate cumulative totals (working backwards from current)
   ↓
6. Output CSV file
   ↓
7. Print summary to console
```

---

## Functional Requirements

### Core Features

#### FR1: Star Data Collection

**Description**: Collect star history for configured repositories using GitHub GraphQL API.

**Requirements**:
- Must authenticate using GitHub CLI token
- Must use GraphQL API to bypass REST API's 40,000 star limit
- Must collect `starred_at` timestamp for each star
- Must handle pagination (100 stars per page)
- Must stop collection when reaching configured start date
- Must handle API errors gracefully with retry logic

#### FR2: Monthly Aggregation

**Description**: Aggregate raw star data into monthly buckets.

**Requirements**:
- Must group stars by YYYY-MM format
- Must count stars per repository per month
- Must handle months with zero stars (show as 0, not omit)
- Must sort output chronologically

#### FR3: Cumulative Totals

**Description**: Calculate all-time cumulative star counts at each month's end.

**Requirements**:
- Must show total stars each repository has ever received as of that month
- Must calculate by working backwards from current GitHub total
- Must match GitHub's displayed star count for the current month

#### FR4: CSV Output

**Description**: Generate CSV files suitable for spreadsheet analysis.

**Requirements**:
- Must include headers: Month, [repo1], [repo2], ..., [repo1] All-Time, [repo2] All-Time, ...
- Must use comma separation
- Must be openable in Excel and Google Sheets without import issues
- Must name file with date range (e.g., `github_stars_2025.csv`)

#### FR5: Configurable Repositories

**Description**: Support adding/removing repositories without code changes.

**Requirements**:
- Repository list defined at top of script or in config file
- Adding a repository requires only editing one location
- Script handles arbitrary number of repositories

#### FR6: Console Output

**Description**: Display summary table when script runs.

**Requirements**:
- Must show formatted table with monthly data
- Must show progress during collection (page counts)
- Must show total stars collected
- Must indicate when CSV is written

### Configuration

#### Script Configuration

```python
# Repositories to track (edit this list to add more)
REPOSITORIES = [
    ("coder", "coder"),
    ("coder", "code-server"),
    # Add more: ("owner", "repo"),
]

# Default start date for data collection
DEFAULT_START_DATE = "2025-01-01"

# Output file name
OUTPUT_FILE = "github_stars.csv"
```

---

## Non-Functional Requirements

### Performance

| Requirement | Target |
|-------------|--------|
| Collection Speed | < 5 minutes for 2 repos, 1 year of data |
| API Efficiency | Minimize requests via pagination (100/page) |
| Memory Usage | < 500MB RAM |

### Reliability

| Requirement | Target |
|-------------|--------|
| Error Handling | Graceful failure with clear error messages |
| Retry Logic | Automatic retry on transient API failures |
| Data Integrity | Output matches GitHub's reported totals |

### Security

| Requirement | Implementation |
|-------------|----------------|
| Authentication | Uses `gh` CLI (no tokens in code) |
| Repository Access | Works with public repos; private repos require appropriate `gh` auth |
| Code Storage | Private GitHub repository |

### Maintainability

| Requirement | Implementation |
|-------------|----------------|
| Code Simplicity | Single Python file, well-commented |
| Dependencies | Minimal (just `gh` CLI and Python stdlib) |
| Documentation | README with usage instructions |

### Usability

| Requirement | Implementation |
|-------------|----------------|
| Execution | Single command: `python3 github_star_history.py` |
| Output | Human-readable console output + CSV file |
| Error Messages | Clear, actionable error messages |

---

## Technical Specifications

### Code Structure

```
star-tracking/
├── README.md                    # Usage instructions
├── github_star_history.py       # Main script
└── github_stars_2025.csv        # Output (generated)
```

### Key Code Components

#### 1. GitHub GraphQL Query

Uses the `stargazers` connection with `orderBy: STARRED_AT` to fetch stars newest-first, enabling early termination when reaching the start date.

#### 2. Pagination Handling

Uses cursor-based pagination (`before` parameter) to walk backwards through star history.

#### 3. Cumulative Calculation

Works backwards from current total (fetched via GraphQL) subtracting each month's stars to determine historical totals.

### Dependencies

#### System Requirements

| Dependency | Version | Purpose |
|------------|---------|----------|
| Python | 3.8+ | Runtime |
| GitHub CLI (`gh`) | Latest | Authentication |

#### Python Standard Library (no pip install needed)

- `subprocess` - Run `gh` commands
- `json` - Parse API responses
- `csv` - Write output files
- `collections.defaultdict` - Data aggregation

---

## Deployment

### Infrastructure

| Component | Details |
|-----------|----------|
| Platform | Coder cloud workspace |
| Persistence | Files stored in workspace home directory |
| Schedule | Manual run monthly (future: cron automation) |

### Initial Setup

1. **Create/access Coder workspace**
   ```bash
   # Navigate to workspace on dev.coder.com
   ```

2. **Authenticate GitHub CLI**
   ```bash
   gh auth login
   ```

3. **Clone repository**
   ```bash
   git clone https://github.com/marco-a-martinez/star-tracking.git
   cd star-tracking
   ```

4. **Run script**
   ```bash
   python3 github_star_history.py
   ```

### Monthly Run Process

1. Open Coder workspace
2. Navigate to `star-tracking` directory
3. Run: `python3 github_star_history.py`
4. Retrieve `github_stars.csv` for reporting

### Adding New Repositories

1. Edit `github_star_history.py`
2. Add repository to `REPOSITORIES` list:
   ```python
   REPOSITORIES = [
       ("coder", "coder"),
       ("coder", "code-server"),
       ("coder", "new-repo"),  # Add this line
   ]
   ```
3. Save and run script

---

## Testing

### Manual Testing Checklist

#### Pre-Launch

- [ ] Script runs without errors
- [ ] GitHub CLI authentication works
- [ ] All configured repositories are queried
- [ ] CSV file is created
- [ ] CSV opens correctly in Excel
- [ ] CSV opens correctly in Google Sheets
- [ ] Monthly totals are accurate (spot-check)
- [ ] Cumulative totals match GitHub's current count
- [ ] Console output is readable

#### Post-Launch (Monthly)

- [ ] Script completes successfully
- [ ] New month's data appears in output
- [ ] No unexpected errors in output
- [ ] CSV delivered to marketing team

### Validation

| Check | Method |
|-------|--------|
| Current Total Accuracy | Compare last row's cumulative to GitHub repo page |
| Monthly Accuracy | Spot-check a month against GitHub Insights (if available) |
| CSV Format | Open in Excel and Google Sheets, verify no parsing issues |

---

## Error Scenarios

| Scenario | Expected Behavior | Recovery |
|----------|-------------------|----------|
| `gh` not authenticated | Error message: "Please run `gh auth login`" | Run `gh auth login` |
| Repository not found | Error message with repo name | Check repository name spelling |
| API rate limit | Pause and retry after reset | Automatic; may take time |
| Network error | Retry with exponential backoff | Automatic |
| Invalid start date | Error message with format hint | Fix date format (YYYY-MM-DD) |

---

## Risks & Mitigations

### Technical Risks

#### Risk 1: GitHub API Changes

| Aspect | Details |
|--------|----------|
| Impact | Script stops working |
| Likelihood | Low (GraphQL API is stable) |
| Mitigation | Monitor for deprecation notices; script is simple to update |

#### Risk 2: Large Repository Growth

| Aspect | Details |
|--------|----------|
| Impact | Script takes longer to run |
| Likelihood | Medium (code-server has 75k+ stars) |
| Mitigation | Script only fetches new data since start date; historical data cached in CSV |

#### Risk 3: Authentication Token Expiry

| Aspect | Details |
|--------|----------|
| Impact | Script fails to authenticate |
| Likelihood | Medium |
| Mitigation | Re-run `gh auth login`; document in troubleshooting |

### Operational Risks

#### Risk 1: Forgotten Monthly Run

| Aspect | Details |
|--------|----------|
| Impact | Missing month's data in quarterly report |
| Likelihood | Medium |
| Mitigation | Calendar reminder; future: automate via cron |

#### Risk 2: Workspace Unavailable

| Aspect | Details |
|--------|----------|
| Impact | Cannot run script |
| Likelihood | Low |
| Mitigation | Script can run on any machine with Python and `gh` CLI |

---

## Future Enhancements

### Phase 2 (Next 3-6 months)

#### Automated Monthly Runs
- Cron job or scheduled task to run on 1st of each month
- Email or Slack notification with results
- Auto-commit updated CSV to repository

#### Google Sheets Integration
- Direct export to Google Sheets
- Automatic chart updates
- Shared access for marketing team

#### Additional Metrics
- Fork counts
- Watch counts
- Contributor counts
- Issue/PR activity

### Phase 3 (6+ months)

#### Dashboard
- Web-based visualization
- Interactive charts
- Trend analysis
- Comparison between repositories

#### Alerting
- Notify on unusual star activity (viral moments)
- Weekly digest of star growth

#### Historical Backfill
- Collect complete history for repositories under 40k stars
- Merge with GraphQL data for complete picture

---

## Appendix

### A. Usage Reference

#### Basic Usage
```bash
# Run with defaults (2025-01-01 start date)
python3 github_star_history.py

# Run with custom start date
python3 github_star_history.py 2024-01-01

# Run with custom start date and output file
python3 github_star_history.py 2024-01-01 custom_output.csv
```

#### Output Format
```csv
Month,coder/coder,code-server,coder/coder All-Time,code-server All-Time
2025-01,302,515,8752,68692
2025-02,199,488,8951,69180
...
```

### B. Troubleshooting Guide

#### Problem: "gh: command not found"
```bash
# Install GitHub CLI
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update
sudo apt install gh
```

#### Problem: "Not authenticated"
```bash
gh auth login
# Follow prompts to authenticate
```

#### Problem: "Repository not found"
- Verify repository exists and is spelled correctly
- For private repos, ensure `gh` has appropriate permissions

#### Problem: Script runs slowly
- This is normal for repositories with many stars
- code-server (75k+ stars) may take several minutes
- Progress is shown in console output

### C. GitHub API Notes

#### Why GraphQL Instead of REST?

The REST API endpoint (`GET /repos/{owner}/{repo}/stargazers`) has a hard limit of 40,000 results. The GraphQL API can access the full star history by paginating from newest to oldest.

#### Rate Limits

| API | Limit |
|-----|-------|
| GraphQL | 5,000 points/hour |
| Cost per stargazers query | ~1 point |
| Practical limit | ~5,000 pages/hour (500,000 stars) |

### D. Glossary

| Term | Definition |
|------|------------|
| Star | GitHub's "like" or "bookmark" feature for repositories |
| Stargazer | A GitHub user who has starred a repository |
| GraphQL | Query language for APIs; GitHub's modern API |
| Cumulative Total | Running sum of all stars ever received |
| `gh` CLI | GitHub's official command-line tool |

### E. References

- GitHub Repository: https://github.com/marco-a-martinez/star-tracking (private)
- GitHub GraphQL API: https://docs.github.com/en/graphql
- GitHub CLI: https://cli.github.com/
- Coder Documentation: https://coder.com/docs

---

## Sign-Off

| Role | Name | Approval | Date |
|------|------|----------|------|
| Product Owner | Marco Martinez | Yes | January 2026 |
| Technical Advisor | Blink AI | Yes | January 2026 |
| Stakeholder (Marketing) | [Name] | Pending | |

---

## Document Version History

| Version | Date | Changes |
|---------|------|----------|
| 1.0 | January 2026 | Initial PRD creation |
