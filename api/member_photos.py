from http.server import BaseHTTPRequestHandler
import json
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from congress_photo_api import fetch_members_with_photos_json
except ImportError as e:
    print(f"Import error: {e}")
    print(f"sys.path: {sys.path}")
    raise


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Fetch members with photos
            data = fetch_members_with_photos_json()
            
            # Add metadata
            response_data = {
                'data': data,
                'metadata': {
                    'timestamp': datetime.utcnow().isoformat() + 'Z',
                    'cache_ttl': 21600
                }
            }
            
            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Cache-Control', 'public, max-age=21600')
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
                'message': 'Failed to fetch member photos'
            }
            self.wfile.write(json.dumps(error_response).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
