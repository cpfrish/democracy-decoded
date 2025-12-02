"""
Processes CSV of raw bill details and extracts temporal milestones (introduction, 
House passage, Senate passage, presidential action) to calculate durations between 
each legislative stage. Returns this as another CSV file.

Setup instructions:
1. Replace the parameter in pd.read_csv('') with the CSV file generated from 
fetchSimpleBill.js
2. Replace output_file variable with name of CSV file you want to write to.

How to run: Run 'python process_bills.py' in terminal. Must be run after the raw CSV
file has already been generated.

Todo: Add functions for specific bill cleaning as per required by different 
visualizations. Currently only supports data for visualizations in Legistlative Timeline tab.
"""

import pandas as pd
import json
from datetime import datetime

print("\nLoading csv...")
df = pd.read_csv('../csv/bills_119_raw.csv')
print(f"Loaded {len(df)} bills\n")

# function to extract milestones from actions JSON
def extract_milestones(actions_json):
    milestones = {
        'introduced': None,
        'passedHouse': None,
        'passedSenate': None,
        'sentToPresident': None,
        'becameLaw': None,
        'vetoed': None
    }
    
    if pd.isna(actions_json) or actions_json == '':
        return milestones
    
    try:
        actions = json.loads(actions_json)
        actions.sort(key=lambda x: x.get('actionDate', ''))
        
        for action in actions:
            text = action.get('text', '').lower()
            date = action.get('actionDate', '')
            
            if not milestones['introduced'] and 'introduced' in text:
                milestones['introduced'] = date
            
            if not milestones['passedHouse'] and ('passed house' in text or 'passed/agreed to in house' in text):
                milestones['passedHouse'] = date
            
            if not milestones['passedSenate'] and ('passed senate' in text or 'passed/agreed to in senate' in text):
                milestones['passedSenate'] = date
            
            if not milestones['sentToPresident'] and 'presented to president' in text:
                milestones['sentToPresident'] = date
            
            if not milestones['becameLaw'] and ('became public law' in text or 'signed by president' in text):
                milestones['becameLaw'] = date
            
            if not milestones['vetoed'] and 'vetoed' in text:
                milestones['vetoed'] = date
                
    except (json.JSONDecodeError, TypeError):
        pass
    
    return milestones

# extract milestones for each bill
print("Extracting milestones from actions...")
milestones_list = []

for idx, row in df.iterrows():
    if (idx + 1) % 50 == 0:
        print(f"  Processed {idx + 1}/{len(df)} bills...")
    
    milestones = extract_milestones(row['actions'])
    milestones_list.append(milestones)

# milestone columns
milestone_df = pd.DataFrame(milestones_list)
for col in milestone_df.columns:
    df[f'date_{col}'] = milestone_df[col]

# becameLaw boolean and originating chamber
df['becameLaw'] = df['date_becameLaw'].notna()
df['originatingChamber'] = df['type'].apply(lambda x: 'House' if x.startswith('H') else 'Senate')

# calculate durations
def calculate_duration(start_date, end_date):
    if pd.isna(start_date) or pd.isna(end_date) or start_date == '' or end_date == '':
        return None
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        return (end - start).days
    except:
        return None
    
# calculate durations for all bills
def calculate_chamber_durations(row):
    if row['originatingChamber'] == 'House':
        intro_to_first = calculate_duration(row['date_introduced'], row['date_passedHouse'])
        first_to_second = calculate_duration(row['date_passedHouse'], row['date_passedSenate'])
        second_to_pres = calculate_duration(row['date_passedSenate'], row['date_sentToPresident'])
    elif row['originatingChamber'] == 'Senate':
        intro_to_first = calculate_duration(row['date_introduced'], row['date_passedSenate'])
        first_to_second = calculate_duration(row['date_passedSenate'], row['date_passedHouse'])
        second_to_pres = calculate_duration(row['date_passedHouse'], row['date_sentToPresident'])
    else:
        intro_to_first = None
        first_to_second = None
        second_to_pres = None
    
    return pd.Series({
        'daysIntroToFirstChamber': intro_to_first,
        'daysFirstChamberToSecondChamber': first_to_second,
        'daysSecondChamberToPresident': second_to_pres
    })

chamber_durations = df.apply(calculate_chamber_durations, axis=1)
df[['daysIntroToFirstChamber', 'daysFirstChamberToSecondChamber', 'daysSecondChamberToPresident']] = chamber_durations
df['daysPresidentToLaw'] = df.apply(lambda x: calculate_duration(x['date_sentToPresident'], x['date_becameLaw']), axis=1)
df['daysTotalToLaw'] = df.apply(lambda x: calculate_duration(x['date_introduced'], x['date_becameLaw']), axis=1)

output_cols = [
    'billId', 'congress', 'type', 'originatingChamber', 'number', 'title', 'policyArea',
    'sponsor', 'sponsorParty', 'sponsorState',
    'latestActionText', 'latestActionDate',
    'becameLaw',
    'date_introduced', 'date_passedHouse', 'date_passedSenate',
    'date_sentToPresident', 'date_becameLaw', 'date_vetoed',
    'daysIntroToFirstChamber', 'daysFirstChamberToSecondChamber',
    'daysSecondChamberToPresident', 'daysPresidentToLaw', 'daysTotalToLaw'
]

df_clean = df[output_cols].copy()

# save processed data
output_file = '../csv/bills_119_processed.csv'
df_clean.to_csv(output_file, index=False)

print(f"\nTotal bills processed: {len(df_clean)}")
print(f"Bills that became law: {df_clean['becameLaw'].sum()} ({df_clean['becameLaw'].mean()*100:.1f}%)")
print(f"\nMilestone coverage:")
print(f"  - Has introduction date: {df_clean['date_introduced'].notna().sum()}")
print(f"  - Passed House: {df_clean['date_passedHouse'].notna().sum()}")
print(f"  - Passed Senate: {df_clean['date_passedSenate'].notna().sum()}")
print(f"  - Became law: {df_clean['date_becameLaw'].notna().sum()}")

print(f"\nProcessed data saved to: {output_file}")