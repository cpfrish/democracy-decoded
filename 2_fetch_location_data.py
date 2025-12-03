#!/usr/bin/env python3
"""
Step 2: Fetch Location Data (State/District/Chamber)
Fetches geographic and chamber information for all members
"""

import os
import sys
import pandas as pd
import requests
import time


def fetch_all_members_location_data():
    """Fetch state, district, and chamber for all members"""
    
    API_KEY = os.environ.get("CONGRESS_API_KEY")
    if not API_KEY:
        print("ERROR: CONGRESS_API_KEY environment variable not set")
        sys.exit(1)
    
    headers = {"X-Api-Key": API_KEY}
    
    # Load base member data
    try:
        df = pd.read_csv('data/congress_members_with_photos.csv')
    except FileNotFoundError:
        print("ERROR: congress_members_with_photos.csv not found")
        print("Run: python 1_fetch_member_data.py first")
        sys.exit(1)
    
    print("=" * 70)
    print("STEP 2: Fetching Location Data (State/District/Chamber)")
    print("=" * 70)
    print()
    print(f"Processing {len(df)} members...")
    print("This will take ~2 minutes due to API rate limits...")
    print()
    
    members_data = []
    
    for idx, row in df.iterrows():
        bioguide_id = row['BioguideID']
        
        url = f"https://api.congress.gov/v3/member/{bioguide_id}"
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            member_data = data.get("member", {})
            
            # Extract state from top-level
            state = member_data.get("state")
            
            # Extract district and chamber from terms
            terms_data = member_data.get("terms", {})
            if isinstance(terms_data, dict):
                terms = terms_data.get("item", [])
            else:
                terms = terms_data if isinstance(terms_data, list) else []
            
            district = None
            chamber = None
            if terms:
                latest_term = terms[-1]
                district = latest_term.get("district")
                chamber = latest_term.get("chamber")
            
            if terms:
                member_info = {
                    'Name': row['Name'],
                    'Party': row['Party'],
                    'BirthYear': row['BirthYear'],
                    'BillCount': row['BillCount'],
                    'BioguideID': bioguide_id,
                    'PhotoURL': row['PhotoURL'],
                    'State': state,
                    'District': int(district) if district else None,
                    'Chamber': 'House' if chamber and 'house' in chamber.lower() else 'Senate',
                    'Generation': row['Generation']
                }
                members_data.append(member_info)
            
            if (idx + 1) % 50 == 0:
                print(f"  Processed {idx + 1}/{len(df)} members...")
            
            time.sleep(0.25)  # Rate limiting
            
        except Exception as e:
            print(f"  Warning: Error fetching {row['Name']}: {e}")
            continue
    
    # Save data
    all_df = pd.DataFrame(members_data)
    all_df.to_csv('data/congress_members_all_chambers.csv', index=False)
    
    # Save House-only data
    house_df = all_df[all_df['Chamber'] == 'House'].copy()
    house_df.to_csv('data/congress_members_districts.csv', index=False)
    
    print()
    print("=" * 70)
    print("✓ Location data fetching complete!")
    print("=" * 70)
    print()
    print(f"✓ Total members: {len(all_df)}")
    print(f"✓ House members: {len(house_df)}")
    print(f"✓ Senate members: {len(all_df[all_df['Chamber'] == 'Senate'])}")
    print()
    print("Files saved:")
    print("  - data/congress_members_all_chambers.csv")
    print("  - data/congress_members_districts.csv")
    print()
    print("Next step:")
    print("  Run: python 3_create_visualizations.py")
    print()


if __name__ == "__main__":
    fetch_all_members_location_data()
