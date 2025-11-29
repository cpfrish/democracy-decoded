"""
Fast Congress API - Returns basic member data without expensive API calls
This is optimized for serverless functions with strict timeouts
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import requests
from datetime import datetime


def get_generation(birth_year):
    """Classify generation from birth year"""
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
        return "Pre-Silent"


def fetch_basic_members():
    """
    Fetch ONLY the basic member list - no additional API calls per member.
    This is fast enough for serverless (< 2 seconds total).
    """
    API_KEY = os.environ.get("CONGRESS_API_KEY")
    if not API_KEY:
        return {"error": "CONGRESS_API_KEY not configured"}
    
    headers = {"X-Api-Key": API_KEY}
    url = "https://api.congress.gov/v3/member"
    params = {"limit": 250, "currentMember": "true"}
    
    all_members = []
    generation_counts = {}
    
    try:
        # Fetch first page
        response = requests.get(url, headers=headers, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        members = data.get("members", [])
        
        # Process members
        for member in members:
            # Get basic info from the member list API (no extra calls needed)
            terms = member.get("terms", {})
            if isinstance(terms, dict):
                latest_term = terms.get("item", [{}])[-1] if terms.get("item") else {}
            else:
                latest_term = terms[-1] if terms else {}
            
            # Try to extract party from latest term
            party = latest_term.get("memberType", "Unknown")[0] if latest_term else "Unknown"
            
            member_info = {
                "bioguide_id": member.get("bioguideId"),
                "name": member.get("name"),
                "state": member.get("state"),
                "party": party,
                "district": member.get("district"),
                "url": member.get("url")
            }
            
            all_members.append(member_info)
        
        # Try to fetch second page if exists
        next_url = data.get("pagination", {}).get("next")
        if next_url:
            response = requests.get(next_url, headers=headers, timeout=5)
            response.raise_for_status()
            data = response.json()
            members.extend(data.get("members", []))
        
        return {
            "members": all_members,
            "count": len(all_members),
            "note": "Basic member data only. For detailed analysis with bill counts, run locally with python_analyzer.py"
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to fetch congressional data"
        }


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            data = fetch_basic_members()
            
            response_data = {
                'data': data,
                'metadata': {
                    'timestamp': datetime.utcnow().isoformat() + 'Z',
                    'cache_ttl': 3600
                }
            }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Cache-Control', 'public, max-age=3600')
            self.end_headers()
            
            self.wfile.write(json.dumps(response_data, indent=2).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            error_response = {
                'error': str(e),
                'type': type(e).__name__,
                'message': 'Failed to fetch congressional data'
            }
            self.wfile.write(json.dumps(error_response).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
