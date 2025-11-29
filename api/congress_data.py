"""
Vercel Serverless Function: Fetch Congressional Data
Endpoint: /api/congress-data

Returns fresh congressional member data with generation analysis.
Cached for 1 hour to avoid excessive API calls.
"""

import json
import os
import sys
from datetime import datetime

# Add parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from congress_api_client import fetch_congress_members_json


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
        # Get detailed analysis flag (default: false for speed)
        detailed = request.args.get('detailed', 'false').lower() == 'true'
        
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
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Cache-Control': 'public, max-age=3600'
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
                'message': 'Failed to fetch congressional data'
            })
        }
