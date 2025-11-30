#!/usr/bin/env python3
"""
Congress Bill Fetcher - Bulk Download
Fetches bill metadata, summaries, and status tracking information from Congress.gov API
Generates CSV data and interactive tracker status visualization
"""

import requests
import os
import sys
import pandas as pd
import time
from collections import defaultdict
from typing import Dict, List, Optional


def fetch_bills_list(congress: int = 119, limit: int = 250, max_bills: int = None) -> List[Dict]:
    """
    Fetch list of all bills for a given congress.
    
    Args:
        congress: Congress number (e.g., 119 for 119th Congress 2025-2026)
        limit: Number of bills per API request
        max_bills: Maximum number of bills to fetch (None for all)
        
    Returns:
        List of bill dictionaries with basic info
    """
    API_KEY = os.environ.get("CONGRESS_API_KEY")
    if not API_KEY:
        raise ValueError("CONGRESS_API_KEY environment variable not set")
    
    headers = {"X-Api-Key": API_KEY}
    all_bills = []
    url = f"https://api.congress.gov/v3/bill/{congress}"
    
    print(f"Fetching bill list for Congress {congress}...")
    print("This may take several minutes due to API rate limits...")
    
    offset = 0
    batch_count = 0
    
    while True:
        params = {
            "limit": limit,
            "offset": offset,
            "format": "json"
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            bills = data.get("bills", [])
            if not bills:
                break
                
            all_bills.extend(bills)
            batch_count += 1
            
            # Progress indicator
            if batch_count % 10 == 0:
                print(f"  Fetched {len(all_bills)} bills so far...")
            
            # Check if we've reached max_bills limit
            if max_bills and len(all_bills) >= max_bills:
                all_bills = all_bills[:max_bills]
                print(f"✓ Reached limit of {max_bills} bills")
                break
            
            # Check if there are more results
            pagination = data.get("pagination", {})
            if not pagination.get("next"):
                break
                
            offset += limit
            time.sleep(0.2)  # Rate limiting
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching bills: {e}")
            break
    
    print(f"✓ Fetched {len(all_bills)} total bills")
    return all_bills


def fetch_bill_details(congress: int, bill_type: str, bill_number: str) -> Optional[Dict]:
    """
    Fetch detailed information for a specific bill.
    
    Args:
        congress: Congress number
        bill_type: Bill type (hr, s, hjres, sjres, hconres, sconres, hres, sres)
        bill_number: Bill number
        
    Returns:
        Dictionary with detailed bill information or None if error
    """
    API_KEY = os.environ.get("CONGRESS_API_KEY")
    headers = {"X-Api-Key": API_KEY}
    
    url = f"https://api.congress.gov/v3/bill/{congress}/{bill_type}/{bill_number}"
    
    try:
        response = requests.get(url, headers=headers, params={"format": "json"}, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("bill", {})
    except requests.exceptions.RequestException:
        return None


def fetch_bill_summary(congress: int, bill_type: str, bill_number: str) -> Optional[str]:
    """
    Fetch bill summary text.
    
    Args:
        congress: Congress number
        bill_type: Bill type
        bill_number: Bill number
        
    Returns:
        Summary text or None
    """
    API_KEY = os.environ.get("CONGRESS_API_KEY")
    headers = {"X-Api-Key": API_KEY}
    
    url = f"https://api.congress.gov/v3/bill/{congress}/{bill_type}/{bill_number}/summaries"
    
    try:
        response = requests.get(url, headers=headers, params={"format": "json"}, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        summaries = data.get("summaries", [])
        if summaries:
            # Get most recent summary
            latest = summaries[-1]
            return latest.get("text", "")
        return None
    except requests.exceptions.RequestException:
        return None


def determine_tracker_status(bill: Dict) -> str:
    """
    Determine the tracker status of a bill based on its latest action.
    
    Status categories match congress.gov tracker:
    - Introduced
    - Passed House
    - Passed Senate
    - Resolved
    - To President
    - Became Law
    - Failed
    
    Args:
        bill: Bill dictionary with action information
        
    Returns:
        Tracker status string
    """
    latest_action = bill.get("latestAction", {}).get("text", "").lower()
    
    # Check for became law
    if "became public law" in latest_action or "signed by president" in latest_action:
        return "Became Law"
    
    # Check for to president
    if "presented to president" in latest_action or "sent to president" in latest_action:
        return "To President"
    
    # Check for passed both chambers
    if "passed senate" in latest_action and bill.get("originChamber") == "House":
        return "Passed Senate"
    if "passed house" in latest_action and bill.get("originChamber") == "Senate":
        return "Passed House"
    
    # Check for passed origin chamber
    if bill.get("originChamber") == "House" and "passed house" in latest_action:
        return "Passed House"
    if bill.get("originChamber") == "Senate" and "passed senate" in latest_action:
        return "Passed Senate"
    
    # Check for failed
    if any(word in latest_action for word in ["failed", "rejected", "defeated", "withdrawn"]):
        return "Failed"
    
    # Check for resolved (for resolutions)
    bill_type = bill.get("type", "").lower()
    if bill_type in ["hres", "sres", "hconres", "sconres"]:
        if "agreed to" in latest_action or "adopted" in latest_action:
            return "Resolved"
    
    # Default to introduced
    return "Introduced"


def fetch_bills_data_bulk(congress: int = 119, max_bills: int = 500) -> Dict:
    """
    Fetch congressional bills with metadata, summaries, and tracker status.
    
    Args:
        congress: Congress number to fetch (default: 119)
        max_bills: Maximum number of bills to fetch (default: 500, None for all)
        
    Returns:
        Dictionary with bills list and summary statistics
    """
    # Fetch bills list
    all_bills = fetch_bills_list(congress=congress, max_bills=max_bills)
    
    if not all_bills:
        return {"bills": [], "congress": congress, "total_count": 0}
    
    print(f"\nFetching detailed info for {len(all_bills)} bills...")
    
    # Fetch detailed information for each bill
    processed_bills = []
    tracker_counts = defaultdict(int)
    
    for i, bill_info in enumerate(all_bills, 1):
        # Extract bill identifiers
        bill_type = bill_info.get("type", "").lower()
        bill_number = bill_info.get("number", "")
        
        if not bill_type or not bill_number:
            continue
        
        # Get detailed info
        details = fetch_bill_details(congress, bill_type, bill_number)
        
        if details:
            # Determine tracker status
            tracker_status = determine_tracker_status(details)
            tracker_counts[tracker_status] += 1
            
            # Build processed bill record
            processed_bill = {
                "congress": congress,
                "bill_type": bill_info.get("type"),
                "bill_number": bill_number,
                "bill_id": f"{bill_info.get('type')}{bill_number}",
                "title": details.get("title", ""),
                "introduced_date": details.get("introducedDate", ""),
                "latest_action_date": details.get("latestAction", {}).get("actionDate", ""),
                "latest_action_text": details.get("latestAction", {}).get("text", ""),
                "tracker_status": tracker_status,
                "origin_chamber": details.get("originChamber", ""),
                "policy_area": details.get("policyArea", {}).get("name", ""),
                "sponsor": "",
                "cosponsors_count": details.get("cosponsors", {}).get("count", 0),
                "congress_url": details.get("legislationUrl", ""),
                "summary": ""
            }
            
            # Get sponsor info
            sponsors = details.get("sponsors", [])
            if sponsors:
                sponsor = sponsors[0]
                processed_bill["sponsor"] = sponsor.get("fullName", "")
            
            processed_bills.append(processed_bill)
        
        # Progress indicator
        if i % 50 == 0:
            print(f"  Processed {i}/{len(all_bills)} bills...")
        
        # Rate limiting
        time.sleep(0.2)
    
    print(f"✓ Processed {len(processed_bills)} bills with details")
    print("\nTracker Status Summary:")
    for status, count in sorted(tracker_counts.items(), key=lambda x: -x[1]):
        print(f"  {status}: {count}")
    
    return {
        "bills": processed_bills,
        "congress": congress,
        "total_count": len(all_bills),
        "detailed_count": len(processed_bills),
        "tracker_counts": dict(tracker_counts)
    }


def save_bills_data(bills_data: Dict, output_dir: str = "data") -> str:
    """
    Save bills data to CSV file.
    
    Args:
        bills_data: Dictionary from fetch_bills_data_bulk
        output_dir: Directory to save files
        
    Returns:
        Path to saved CSV file
    """
    os.makedirs(output_dir, exist_ok=True)
    
    congress = bills_data["congress"]
    output_path = os.path.join(output_dir, f"congress_{congress}_bills.csv")
    
    df = pd.DataFrame(bills_data["bills"])
    df.to_csv(output_path, index=False)
    
    print(f"\n✓ Saved bills data to {output_path}")
    return output_path


def main():
    """Main execution function"""
    
    # Check for API key
    if not os.environ.get("CONGRESS_API_KEY"):
        print("ERROR: CONGRESS_API_KEY environment variable not set")
        print("Set it with: export CONGRESS_API_KEY='your_key_here'")
        sys.exit(1)
    
    print("=" * 70)
    print("Congress Bill Fetcher - Bulk Download")
    print("=" * 70)
    print()
    print("Note: Fetching 500 most recent bills by default.")
    print("To fetch all bills (~8000+), edit max_bills=None in the script.")
    print()
    
    # Fetch bills data (default 500 bills, set max_bills=None for all ~8000+)
    bills_data = fetch_bills_data_bulk(congress=119, max_bills=500)
    
    # Save to CSV
    csv_path = save_bills_data(bills_data)
    
    print()
    print("=" * 70)
    print("✓ Bill fetching complete!")
    print("=" * 70)
    print()
    print(f"Total bills fetched from Congress 119: {bills_data['total_count']}")
    print(f"Bills with detailed info: {bills_data['detailed_count']}")
    print()
    print("Next step: Run visualization script to create tracker dashboard")
    

if __name__ == "__main__":
    main()