"""
Vercel Serverless Function: Fetch Congressional Data
Endpoint: /api/congress-data

Returns fresh congressional member data with generation analysis.
Cached for 1 hour to avoid excessive API calls.
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import sys
from datetime import datetime
from urllib.parse import parse_qs, urlparse

# Add parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from congress_api_client import fetch_congress_members_json


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Parse query parameters
            parsed_path = urlparse(self.path)
            query_params = parse_qs(parsed_path.query)
            
            # Get detailed analysis flag (default: false for speed)
            detailed = query_params.get('detailed', ['false'])[0].lower() == 'true'
            
            # Fetch data from Congress.gov API
            data = fetch_congress_members_json(detailed_analysis=detailed)
            
            # Add metadata
            response_data = {
                'data': data,
                'metadata': {
                    'timestamp': datetime.utcnow().isoformat() + 'Z',
                    'detailed_analysis': detailed,
                    'cache_ttl': 3600
                }
            }
            
            # Send response
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
                'message': 'Failed to fetch congressional data'
            }
            self.wfile.write(json.dumps(error_response).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
