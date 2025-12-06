'''
Fetches bills from Congress API and returns a CSV containing raw bill details.
Python 3 must be installed to run this file.

Setup instructions:
1. Set API_KEY variable to your API key
2. Set CONGRESS variable to your Congress number
3. Set NUM_BILLS variable to how many bills you want to fetch
4. Install required packages: pip install requests

How to run: Run 'python fetch_simple_bill.py' in terminal.
'''

import requests
import json
import csv
import time
from pathlib import Path

API_KEY = ''
BASE_URL = 'https://api.congress.gov/v3'
CONGRESS = 119
NUM_BILLS = 1000


def fetch_bills(congress, max_bills):
    
    # fetch bills with pagination
    all_bills = []
    offset = 0
    limit = 250
    
    print(f'Fetching {max_bills} bills from {congress}th Congress...\n')
    
    while len(all_bills) < max_bills:
        url = f'{BASE_URL}/bill/{congress}?api_key={API_KEY}&limit={limit}&offset={offset}&format=json'
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            bills = data.get('bills', [])
            
            if not bills:
                break
            
            all_bills.extend(bills)
            print(f'Fetched {len(all_bills)} bills...')
            
            if len(all_bills) >= max_bills:
                all_bills = all_bills[:max_bills]
                break
            
            offset += limit
            time.sleep(0.2)  # rate limiting
            
        except requests.exceptions.RequestException as error:
            print(f'Error: {error}')
            break
    
    return all_bills


def fetch_bill_details(congress, bill_type, bill_number):
    bill_type_lower = bill_type.lower()
    url = f'{BASE_URL}/bill/{congress}/{bill_type_lower}/{bill_number}?api_key={API_KEY}&format=json'
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get('bill')
    except requests.exceptions.RequestException:
        return None


def fetch_bill_actions(congress, bill_type, bill_number):
    bill_type_lower = bill_type.lower()
    all_actions = []
    offset = 0
    limit = 250
    
    while True:
        url = f'{BASE_URL}/bill/{congress}/{bill_type_lower}/{bill_number}/actions?api_key={API_KEY}&limit={limit}&offset={offset}&format=json'
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            actions = data.get('actions', [])
            
            if not actions:
                break
            
            all_actions.extend(actions)
            offset += limit
            time.sleep(0.1)  # rate limiting
            
        except requests.exceptions.RequestException:
            break
    
    return all_actions


def clean_text(text):
    """clean text for CSV"""
    if not text:
        return ''
    return str(text).replace('\n', ' ').replace('\r', ' ')


def export_to_csv(bills, filename):
    """export to CSV"""
    
    # create csv directory if it doesn't exist
    Path('../csv').mkdir(exist_ok=True)
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        
        # write headers
        writer.writerow([
            'billId',
            'congress',
            'type',
            'number',
            'title',
            'policyArea',
            'sponsor',
            'sponsorParty',
            'sponsorState',
            'latestActionText',
            'latestActionDate',
            'actions'
        ])
        
        # write rows
        for bill in bills:
            actions = bill.get('actions', [])
            actions_json = json.dumps(actions)
            
            writer.writerow([
                f"{bill['type']}{bill['number']}",
                bill.get('congress', CONGRESS),
                bill['type'],
                bill['number'],
                clean_text(bill.get('title', '')),
                clean_text(bill.get('policyArea', '')),
                clean_text(bill.get('sponsor', '')),
                bill.get('sponsorParty', ''),
                bill.get('sponsorState', ''),
                clean_text(bill.get('latestActionText', '')),
                bill.get('latestActionDate', ''),
                actions_json
            ])


def main():
    
    # fetch bill list
    bill_list = fetch_bills(CONGRESS, NUM_BILLS)
    print(f'\nFetched {len(bill_list)} bills\n')
    
    # get details for each bill
    print('Fetching details for each bill...\n')
    bills_with_details = []
    
    for i, bill in enumerate(bill_list):
        print(f"[{i + 1}/{len(bill_list)}] {bill['type']}{bill['number']}")
        
        details = fetch_bill_details(CONGRESS, bill['type'], bill['number'])
        
        if not details:
            print('Skipped - no details')
            continue
        
        # get actions
        actions = fetch_bill_actions(CONGRESS, bill['type'], bill['number'])
        if not actions and details.get('actions'):
            actions = details['actions']
        
        bills_with_details.append({
            'type': bill['type'],
            'number': bill['number'],
            'congress': CONGRESS,
            'title': bill.get('title', ''),
            'policyArea': details.get('policyArea', {}).get('name', ''),
            'sponsor': details.get('sponsors', [{}])[0].get('fullName', '') if details.get('sponsors') else '',
            'sponsorParty': details.get('sponsors', [{}])[0].get('party', '') if details.get('sponsors') else '',
            'sponsorState': details.get('sponsors', [{}])[0].get('state', '') if details.get('sponsors') else '',
            'latestActionText': details.get('latestAction', {}).get('text', ''),
            'latestActionDate': details.get('latestAction', {}).get('actionDate', ''),
            'actions': actions
        })
        
        time.sleep(0.3)  # rate limiting
    
    # export file
    print(f'\nSuccessfully fetched {len(bills_with_details)} bills')
    
    filename = f'../csv/bills_{CONGRESS}_raw.csv'
    export_to_csv(bills_with_details, filename)
    
    print(f'Data exported to {filename}')
    print(f'Total records: {len(bills_with_details)}\n')


if __name__ == '__main__':
    main()