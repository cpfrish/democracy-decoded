"""
Vercel Serverless Function: Fetch Member Photos
Endpoint: /api/member-photos

Returns congressional member data enriched with official photos.
Cached for 6 hours since photos rarely change.
"""

import json
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from congress_photo_api import fetch_members_with_photos_json


def handler(request):
    # Handle OPTIONS for CORS preflight
    if request.method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': ''
        }
    
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
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Cache-Control': 'public, max-age=21600'
            },
            'body': json.dumps(response_data, indent=2)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': str(e),
                'message': 'Failed to fetch member photos'
            })
        }
