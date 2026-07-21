# WORKFLOW.md - Project Workflow

## Overview

This repository provides a clean workflow for generating congressional data visualizations and bill tracking dashboards.

## Structure

```
congress_project/
├── 1_fetch_member_data.py         # Step 1: Fetch members from API
├── 2_fetch_location_data.py       # Step 2: Fetch state/district info
├── 3_create_visualizations.py     # Step 3: Generate HTML visualizations
├── 4_create_bill_tracker.py       # Step 4: Generate bill tracker visualization
├── run_all.py                     # Run all 3 steps at once
├── README.md                      # Full documentation
├── requirements.txt               # Python dependencies
│
├── data/                          # Generated CSV files (git-ignored)
│   ├── congress_individual_members.csv
│   ├── congress_generational_summary.csv
│   ├── congress_members_with_photos.csv
│   ├── congress_members_all_chambers.csv
│   ├── congress_members_districts.csv
│   └── congress_119_bills_2.csv
│
├── visualizations/                # Generated HTML files
│   ├── member_activity_scatter_interactive.html
│   ├── congress_map_dual_chamber.html
│   └── congress_bill_tracker.html
│
├── scripts/                       # Helper modules (don't run directly)
│   ├── congress_api_client.py
│   ├── congress_photo_fetcher.py
│   ├── congress_bill_fetcher_bulk.py
│   └── create_dual_chamber_map.py
│
└── notebooks/                     # Jupyter notebooks for exploration
    ├── congress_eda.ipynb
    └── congress_graphs.ipynb
```

## Usage

### Option 1: Run Everything at Once

```bash
export CONGRESS_API_KEY='your_key_here'
python run_all.py
```

### Option 2: Run Steps Individually

```bash
# Set API key
export CONGRESS_API_KEY='your_key_here'

# Step 1: Fetch member data (~2 minutes)
python 1_fetch_member_data.py

# Step 2: Fetch location data (~2 minutes)  
python 2_fetch_location_data.py

# Step 3: Create visualizations (instant)
python 3_create_visualizations.py

# Step 4 (Optional): Fetch bill data & create tracker (~5m - 3hrs)
python scripts/congress_bill_fetcher_bulk.py 
python 4_create_bill_tracker.py
```

## What Each Step Does

### Step 1: Fetch Member Data
- Calls Congress.gov API for all current members
- Gets: name, party, birth year, bills sponsored, generation
- Fetches official photo URLs from bioguide
- **Output**: 
  - `data/congress_individual_members.csv`
  - `data/congress_generational_summary.csv`
  - `data/congress_members_with_photos.csv`

### Step 2: Fetch Location Data
- Fetches state, district, and chamber for each member
- Separates House (district-level) from Senate (state-level)
- **Output**:
  - `data/congress_members_all_chambers.csv` (all 538 members)
  - `data/congress_members_districts.csv` (House only, ~435 members)

### Step 3: Create Visualizations
- Generates interactive D3.js visualizations
- **Output**:
  - `member_activity_scatter_interactive.html` - Bills vs birth year
  - `congress_map_dual_chamber.html` - House/Senate choropleth map

### Step 4: Bill Tracker (Optional)
- Fetches bill metadata from Congress.gov API
- Gets: title, status, summary, sponsor, policy area
- Determines tracker status (Introduced, Passed House/Senate, Became Law, etc.)
- Creates interactive dashboard similar to congress.gov tracker
- **Output**:
  - `data/congress_119_bills_2.csv` (bill data with tracker status; filename is `congress_{congress}_bills_2.csv`)
  - `congress_bill_tracker.html` (interactive dashboard)

## Visualization Features

### Member Activity Scatter Plot
- X-axis: Birth year
- Y-axis: Bills sponsored
- **Interactive**: Hover to see photo tooltips
- **Toggle**: Switch between Generation and Party coloring
- **Details**: Name, party, generation, bills, photo

### Dual-Chamber Map
- **House View**: 435 congressional districts
- **Senate View**: 50 states (both senators shown)
- **Interactive**: Hover to see photo tooltips
- **Toggle**: Switch between House and Senate
- **Colors**: Democrat (blue), Republican (red), Independent (purple)
- **Live Stats**: Member counts, party breakdown, bill totals

## Data Freshness

All data comes directly from Congress.gov API. To refresh:

```bash
# Delete cached data
rm data/*.csv

# Re-run scripts
python run_all.py
```

## Requirements

- Python 3.8+
- pandas
- requests
- altair (for notebooks)
- Congress.gov API key

Install with:
```bash
pip install -r requirements.txt
```

## Pushing to GitHub

The repository is configured to ignore generated data files. Only code and documentation are tracked:

```bash
# Add all changes
git add .

# Commit
git commit -m "Update visualizations"

# Push
git push origin dev_colin / git push origin main 
```

## Helper Modules (scripts/)

These are imported by the main scripts - don't run directly (except bill fetcher):

- **congress_api_client.py**: Core API functions
- **congress_photo_fetcher.py**: Photo URL fetching and processing
- **congress_bill_fetcher_bulk.py**: Bill data fetching (run for Step 4)
- **create_dual_chamber_map.py**: Map generation logic

## Notebooks (notebooks/)

Jupyter notebooks for data exploration:

- **congress_eda.ipynb**: Exploratory data analysis
- **congress_graphs.ipynb**: Chart prototyping

Run with:
```bash
jupyter notebook notebooks/congress_eda.ipynb
```

## Troubleshooting

### "API key not set"
```bash
export CONGRESS_API_KEY='your_key_here'
```

### "File not found" errors
Run steps in order: 1 → 2 → 3

### API rate limits
Scripts include automatic 0.25s delays - no action needed

### Photos not loading
Some members may not have official photos - this is normal

## Clean Repository Summary

✅ **3 main scripts** - Simple, numbered workflow  
✅ **1 run-all script** - Complete automation  
✅ **2 visualizations** - Interactive HTML with photos  
✅ **Helper modules** - Organized in scripts/  
✅ **Data caching** - Fast re-runs after initial fetch  
✅ **Git-friendly** - Data files ignored, only code tracked  

This structure makes it easy to:
1. Pull fresh data anytime
2. Generate visualizations instantly
3. Push clean code to GitHub
