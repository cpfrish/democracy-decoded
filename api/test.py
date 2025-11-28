"""
Simple test endpoint to verify Vercel deployment works
"""

from http.server import BaseHTTPRequestHandler
import json
from datetime import datetime


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {
            'message': 'Vercel serverless function is working!',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
        self.wfile.write(json.dumps(response).encode())
