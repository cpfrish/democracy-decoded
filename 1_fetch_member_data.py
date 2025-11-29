#!/usr/bin/env python3
"""
Step 1: Fetch Congressional Data
Fetches all member data from Congress.gov API and saves to CSV files
"""

import os
import sys

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

from congress_api_client import fetch_congress_members_json
from congress_photo_fetcher import CongressPhotoFetcher
import pandas as pd


def main():
    """Fetch all congressional data from API"""
    
    # Check for API key
    API_KEY = os.environ.get("CONGRESS_API_KEY")
    if not API_KEY:
        print("ERROR: CONGRESS_API_KEY environment variable not set")
        print("Set it with: export CONGRESS_API_KEY='your_key_here'")
        sys.exit(1)
    
    print("=" * 70)
    print("STEP 1: Fetching Congressional Data from Congress.gov API")
    print("=" * 70)
    print()
    
    # Fetch base member data
    print("Fetching member data (this takes ~2 minutes due to API rate limits)...")
    data = fetch_congress_members_json(detailed_analysis=False)
    
    # Save summary data
    members_df = pd.DataFrame(data['members'])
    summary_df = pd.DataFrame(data['summary'])
    
    members_df.to_csv('data/congress_individual_members.csv', index=False)
    summary_df.to_csv('data/congress_generational_summary.csv', index=False)
    
    print(f"✓ Saved {len(members_df)} members to data/congress_individual_members.csv")
    print(f"✓ Saved generation summary to data/congress_generational_summary.csv")
    print()
    
    # Fetch photos
    print("Fetching member photos...")
    fetcher = CongressPhotoFetcher(api_key=API_KEY)
    
    # Normalize column names for photo fetcher (expects capitalized names)
    members_normalized = members_df.rename(columns={
        'bioguide_id': 'BioguideID',
        'name': 'Name',
        'party': 'Party',
        'birth_year': 'BirthYear',
        'generation': 'Generation',
        'bill_count': 'BillCount'
    })
    
    members_with_photos_df = fetcher.process_dataframe(members_normalized)
    members_with_photos_df.to_csv('data/congress_members_with_photos.csv', index=False)
    print(f"✓ Saved {len(members_with_photos_df)} members with photos to data/congress_members_with_photos.csv")
    print()
    
    print("=" * 70)
    print("✓ Data fetching complete!")
    print("=" * 70)
    print()
    print("Next steps:")
    print("  1. Run: python 2_fetch_location_data.py")
    print("  2. Run: python 3_create_visualizations.py")
    print()


if __name__ == "__main__":
    main()
