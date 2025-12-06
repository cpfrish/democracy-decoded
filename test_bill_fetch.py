#!/usr/bin/env python3
"""
Quick test to fetch a small sample of bills
"""

import os
import sys

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

from congress_bill_fetcher_bulk import fetch_bills_data_bulk, save_bills_data


def main():
    """Test bill fetching with small sample"""
    
    # Check for API key
    if not os.environ.get("CONGRESS_API_KEY"):
        print("ERROR: CONGRESS_API_KEY environment variable not set")
        sys.exit(1)
    
    print("Testing bill fetch with 50 bills from Congress 119...")
    print()
    
    # Fetch just 50 bills to test
    bills_data = fetch_bills_data_bulk(congress=119, max_bills=50)
    
    # Save to CSV
    csv_path = save_bills_data(bills_data)
    
    print()
    print(f"✓ Test complete! Fetched {bills_data['total_count']} bills")
    print(f"✓ Data saved to {csv_path}")
    print()
    print("To fetch full 500 bills, run: python scripts/congress_bill_fetcher_bulk.py")


if __name__ == "__main__":
    main()
