import pandas as pd
import numpy as np

# Load your data
df = pd.read_csv('../csv/bills_119_processed.csv')

# Convert dates to datetime
date_cols = ['date_introduced', 'date_passedHouse', 'date_passedSenate', 
             'date_sentToPresident', 'date_becameLaw']
for col in date_cols:
    df[col] = pd.to_datetime(df[col], errors='coerce')

# ============================================================================
# ADD HELPFUL COLUMNS FOR TABLEAU
# ============================================================================

# 1. Bill status category
def categorize_status(row):
    if row['becameLaw']:
        return 'Became Law'
    elif pd.notna(row['daysSecondChamberToPresident']):
        return 'Passed Both Chambers'
    elif pd.notna(row['daysFirstChamberToSecondChamber']):
        return 'Passed Origin Chamber Only'
    else:
        return 'Introduced Only'

df['status'] = df.apply(categorize_status, axis=1)

# 2. Bill type full name
bill_type_map = {
    'HR': 'House Bill',
    'S': 'Senate Bill',
    'HRES': 'House Resolution',
    'SRES': 'Senate Resolution',
    'HJRES': 'House Joint Resolution',
    'SJRES': 'Senate Joint Resolution'
}
df['billTypeFull'] = df['type'].map(bill_type_map).fillna(df['type'])

# 5. Month/Year for time series
df['introMonth'] = df['date_introduced'].dt.to_period('M').astype(str)
df['introYear'] = df['date_introduced'].dt.year
df['introQuarter'] = df['date_introduced'].dt.to_period('Q').astype(str)

# 6. Bottleneck stage (where most time was spent)
duration_cols = ['daysIntroToFirstChamber', 'daysFirstChamberToSecondChamber', 'daysSecondChamberToPresident', 'daysPresidentToLaw']
df['bottleneckStage'] = df[duration_cols].idxmax(axis=1).map({
    'daysIntroToFirstChamber': 'Introduction to Passing First Chamber',
    'daysFirstChamberToSecondChamber': 'First Chamber to Passing Second Chamber',
    'daysSecondChamberToPresident': 'Second Chamber to Passing President',
    'daysPresidentToLaw': 'President to Law'
})

# 7. Success rate helper (for aggregations)
df['successCount'] = df['becameLaw'].astype(int)

# 8. Duration category
def categorize_duration(days):
    if pd.isna(days):
        return 'Unknown'
    elif days < 100:
        return 'Fast (<100 days)'
    elif days < 365:
        return 'Moderate (100-365 days)'
    else:
        return 'Slow (>365 days)'

df['duration'] = df['daysTotalToLaw'].apply(categorize_duration)

# 9. Sponsor party full name
party_map = {'D': 'Democrat', 'R': 'Republican', 'I': 'Independent'}
df['sponsorPartyFull'] = df['sponsorParty'].map(party_map).fillna(df['sponsorParty'])

# 10. Clean up any text fields for Tableau
df['title'] = df['title'].str.replace('"', '', regex=False)

# ============================================================================
# SAVE TABLEAU-READY FILE
# ============================================================================

# Reorder columns for better Tableau experience
column_order = [
    'billId', 'type', 'billTypeFull', 'originatingChamber', 'title', 'policyArea', 
    'sponsor', 'sponsorParty', 'sponsorPartyFull', 'sponsorState', 'status', 'becameLaw',
    'date_introduced', 'date_passedHouse', 'date_passedSenate', 'date_sentToPresident', 'date_becameLaw',
    'introMonth', 'introYear', 'introQuarter',
    'daysIntroToFirstChamber', 'daysFirstChamberToSecondChamber', 'daysSecondChamberToPresident', 'daysPresidentToLaw', 'daysTotalToLaw',
    'duration', 'bottleneckStage', 'successCount'
]

df_tableau = df[column_order]

# Save
df_tableau.to_csv('../csv/bills_119_tableau.csv', index=False)

print("✅ Tableau-ready file created: bills_118_tableau.csv")
print(f"\nTotal bills: {len(df_tableau)}")
print(f"Columns added: {len(column_order) - len(df.columns) + len(column_order)}")
print("\nNew columns for Tableau:")
print("  • status - Bill progression stage")
print("  • billTypeFull - Human-readable bill type")
print("  • introMonth/Year/Quarter - Time aggregations")
print("  • bottleneckStage - Where most time was spent")
print("  • duration - Fast/Moderate/Slow bins")
print("  • sponsorPartyFull - Full party names")
print("  • successCount - For success rate calculations")

# Print sample for verification
print("\n" + "="*60)
print("Sample data (first 3 rows):")
print("="*60)
print(df_tableau[['billId', 'status', 'duration', 'bottleneckStage']].head(3))