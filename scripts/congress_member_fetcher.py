"""
Congress Member Fetcher - Refactored for JSON output
Extracts core logic from python_analyzer.py for serverless use
"""

import requests
import os
from collections import defaultdict
import time
import numpy as np


def get_generation(birth_year):
    """Consistent generation classification"""
    if not birth_year:
        return "Unknown"
    year = int(birth_year)
    if 1928 <= year <= 1945:
        return "Silent Generation"
    elif 1946 <= year <= 1964:
        return "Baby Boomer"
    elif 1965 <= year <= 1980:
        return "Gen X"
    elif 1981 <= year <= 1996:
        return "Millennial"
    elif year >= 1997:
        return "Gen Z"
    else:
        return "Unknown"


def fetch_sponsored_bills_count(member_id, headers):
    """Get total bill count for a member"""
    endpoint = f"member/{member_id}/sponsored-legislation"
    url = f"https://api.congress.gov/v3/{endpoint}"
    params = {"limit": 1}
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("pagination", {}).get("count", 0)
    except requests.exceptions.RequestException:
        return 0


def fetch_member_details(member_id, headers):
    """Fetch detailed member information including birth year and party"""
    endpoint = f"member/{member_id}"
    url = f"https://api.congress.gov/v3/{endpoint}"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        member_data = data.get("member", {})
        
        # Get birth year
        birth_year = member_data.get("birthYear")
        
        # Get current party - try multiple approaches
        party = "Unknown"
        
        # Try partyName field first
        party_name = member_data.get("partyName", "")
        if party_name:
            if "Republican" in party_name or "GOP" in party_name:
                party = "R"
            elif "Democrat" in party_name:
                party = "D"
            elif "Independent" in party_name:
                party = "I"
            else:
                party = party_name
        
        # Try partyHistory if still Unknown
        if party == "Unknown":
            party_history = member_data.get("partyHistory", [])
            if party_history:
                latest_party = party_history[-1] if isinstance(party_history, list) else party_history
                if isinstance(latest_party, dict):
                    party_code = latest_party.get("partyCode") or latest_party.get("partyAbbreviation")
                    if party_code:
                        party = party_code
        
        # Last resort: check terms
        if party == "Unknown":
            terms_data = member_data.get("terms", [])
            if isinstance(terms_data, dict):
                terms = terms_data.get("item", [])
            else:
                terms = terms_data if isinstance(terms_data, list) else []
            
            if terms:
                latest_term = terms[-1]
                term_party = latest_term.get("party") or latest_term.get("partyCode")
                if term_party:
                    party = term_party
        
        return birth_year, party
        
    except requests.exceptions.RequestException:
        return None, "Unknown"



def fetch_congress_members_json() -> dict:
    """
    Fetch congressional members and return as JSON-friendly dict.
    No CSV output - pure API response.
    
    Returns:
        dict with 'members', 'summary'
    """
    API_KEY = os.environ.get("CONGRESS_API_KEY")
    if not API_KEY:
        raise ValueError("CONGRESS_API_KEY environment variable not set")
    
    # Hardcoded birth years for members missing from API
    BIRTH_YEAR_OVERRIDES = {
        'K000404': 1975,  # Kimberlyn King-Hinds (Delegate, Northern Mariana Islands)
    }
    
    headers = {"X-Api-Key": API_KEY}
    all_members_raw = []
    url = "https://api.congress.gov/v3/member"
    
    # Fetch all current members
    print("Fetching member list from Congress.gov...")
    while url:
        params = {"limit": 250, "currentMember": "true"}
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            all_members_raw.extend(data.get("members", []))
            url = data.get("pagination", {}).get("next", None)
        except requests.exceptions.RequestException:
            break
    
    print(f"Found {len(all_members_raw)} current members")
    
    # Process members by generation
    generation_data = {}
    members_list = []
    
    print(f"\nFetching details for {len(all_members_raw)} members...")
    print("(This takes ~3-4 minutes due to API rate limits)")
    
    for i, member in enumerate(all_members_raw):
        member_id = member.get("bioguideId")
        member_name = member.get("name", "N/A")
        
        # Extract party from initial data (already available)
        party = "Unknown"
        party_name = member.get("partyName", "")
        if party_name:
            if "Republican" in party_name or "GOP" in party_name:
                party = "R"
            elif "Democrat" in party_name:
                party = "D"
            elif "Independent" in party_name:
                party = "I"
        
        # Fetch detailed member info for birth year (required for generation)
        birth_year, fetched_party = fetch_member_details(member_id, headers)
        
        # Check for hardcoded birth year override
        if not birth_year and member_id in BIRTH_YEAR_OVERRIDES:
            birth_year = BIRTH_YEAR_OVERRIDES[member_id]
            print(f"  Using hardcoded birth year for {member_name}: {birth_year}")
        
        # Use fetched party if we didn't get it from initial data
        if party == "Unknown" and fetched_party != "Unknown":
            party = fetched_party
        
        generation = get_generation(birth_year)
        
        # Initialize generation tracking
        if generation not in generation_data:
            generation_data[generation] = {
                'count': 0,
                'total_bills': 0,
                'topic_counts': defaultdict(int),
                'members': []
            }
        
        generation_data[generation]['count'] += 1
        
        # Fetch bill count
        bill_count = fetch_sponsored_bills_count(member_id, headers)
        generation_data[generation]['total_bills'] += bill_count
        
        # Store member info
        member_info = {
            'bioguide_id': member_id,
            'name': member_name,
            'party': party,
            'birth_year': birth_year,
            'generation': generation,
            'bill_count': bill_count
        }
        
        members_list.append(member_info)
        generation_data[generation]['members'].append(member_info)
        
        # Rate limiting - Congress API allows ~5 requests/second, so 0.2s is safe
        time.sleep(0.2)
        
        # Progress indicator every 50 members
        if (i + 1) % 50 == 0:
            elapsed_min = ((i + 1) * 0.2 * 2) / 60  # 2 API calls per member
            remaining = ((len(all_members_raw) - i - 1) * 0.2 * 2) / 60
            print(f"  Progress: {i + 1}/{len(all_members_raw)} members (~{elapsed_min:.1f}m elapsed, ~{remaining:.1f}m remaining)")
    
    # Build summary
    summary = []
    for generation, data in generation_data.items():
        avg_bills = data['total_bills'] / data['count'] if data['count'] > 0 else 0
        summary.append({
            'generation': generation,
            'member_count': data['count'],
            'total_bills': data['total_bills'],
            'avg_bills_per_member': round(avg_bills, 2)
        })
    
    # Build response
    response = {
        'members': members_list,
        'summary': summary
    }

    
    return response
