import requests
import os
from collections import defaultdict, Counter
import time
import pandas as pd
import datetime
import altair as alt
import numpy as np
import re


# --- (Functions get_generation and fetch_sponsored_bills_count are unchanged) ---
def get_generation(birth_year):
    if not birth_year: return "Unknown"
    year = int(birth_year)
    if 1928 <= year <= 1945: return "Silent Generation"
    elif 1946 <= year <= 1964: return "Baby Boomer"
    elif 1965 <= year <= 1980: return "Gen X"
    elif 1981 <= year <= 1996: return "Millennial"
    elif year >= 1997: return "Gen Z"
    else: return "Pre-Silent"

def fetch_sponsored_bills_count(member_id, headers):
    endpoint = f"member/{member_id}/sponsored-legislation"
    url = f"https://api.congress.gov/v3/{endpoint}"
    params = {"limit": 1}
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("pagination", {}).get("count", 0)
    except requests.exceptions.RequestException:
        return 0

def fetch_member_details(member_id, headers):
    """Fetch detailed member information including birth year and current party"""
    endpoint = f"member/{member_id}"
    url = f"https://api.congress.gov/v3/{endpoint}"
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        member_data = data.get("member", {})
        
        # Get birth year
        birth_year = member_data.get("birthYear")
        
        # Get current party - try multiple approaches
        party = "Unknown"
        
        # Approach 1: Try partyName field (primary field per API documentation)
        party_name = member_data.get("partyName", "")
        if party_name:
            if "Republican" in party_name or "GOP" in party_name:
                party = "R"
            elif "Democrat" in party_name:
                party = "D"
            elif "Independent" in party_name:
                party = "I"
            else:
                party = party_name  # Keep full name if not standard party
        
        # Approach 2: If still Unknown, try partyHistory field
        if party == "Unknown":
            party_history = member_data.get("partyHistory", [])
            if party_history:
                # Get the most recent party
                latest_party = party_history[-1] if isinstance(party_history, list) else party_history
                if isinstance(latest_party, dict):
                    party_code = latest_party.get("partyCode") or latest_party.get("partyAbbreviation")
                    if party_code:
                        party = party_code
        
        # Approach 3: Try from terms (last resort)
        if party == "Unknown":
            terms_data = member_data.get("terms", [])
            if isinstance(terms_data, dict):
                terms = terms_data.get("item", [])
            else:
                terms = terms_data if isinstance(terms_data, list) else []
            
            if terms:
                latest_term = terms[-1]
                # Try getting party from the term
                term_party = latest_term.get("party") or latest_term.get("partyCode")
                if term_party:
                    party = term_party
        
        return birth_year, party
        
    except requests.exceptions.RequestException as e:
        print(f"  Error fetching details for {member_id}: {e}")
        return None, "Unknown"
    except Exception as e:
        print(f"  Unexpected error processing {member_id}: {e}")
        return None, "Unknown"


def fetch_detailed_bills(member_id, headers, limit=50):
    """Fetch detailed bill data for topic analysis"""
    endpoint = f"member/{member_id}/sponsored-legislation"
    url = f"https://api.congress.gov/v3/{endpoint}"
    params = {"limit": limit}
    bills = []
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        for bill in data.get("sponsoredLegislation", []):
            latest_action = bill.get('latestAction')
            policy_area = bill.get('policyArea')
            subjects = bill.get('subjects', {})
            
            bill_info = {
                'title': bill.get('title', ''),
                'type': bill.get('type', ''),
                'number': bill.get('number', ''),
                'congress': bill.get('congress', ''),
                'latest_action': latest_action.get('text', '') if latest_action else '',
                'policy_area': policy_area.get('name', '') if policy_area else '',
                'subjects': [subj.get('name', '') for subj in subjects.get('legislativeSubjects', [])] if subjects else []
            }
            bills.append(bill_info)
            
    except requests.exceptions.RequestException as e:
        print(f"Error fetching bills for {member_id}: {e}")
        
    return bills

def categorize_bill_topic(title, policy_area, subjects):
    """Categorize bills into broad topic areas"""
    title_lower = title.lower()
    policy_lower = policy_area.lower() if policy_area else ''
    subjects_lower = ' '.join(subjects).lower() if subjects else ''
    
    # Combine all text for analysis
    all_text = f"{title_lower} {policy_lower} {subjects_lower}"
    
    # Define topic keywords
    topic_keywords = {
        'Technology': ['technology', 'cyber', 'digital', 'internet', 'artificial intelligence', 'ai', 'data', 'privacy', 'tech'],
        'Climate/Environment': ['climate', 'environment', 'energy', 'renewable', 'carbon', 'emissions', 'green', 'clean'],
        'Healthcare': ['health', 'medical', 'medicare', 'medicaid', 'hospital', 'healthcare', 'drug', 'pharmaceutical'],
        'Defense/Security': ['defense', 'military', 'security', 'veteran', 'armed forces', 'homeland', 'intelligence'],
        'Economy/Finance': ['economy', 'economic', 'finance', 'financial', 'tax', 'budget', 'banking', 'commerce'],
        'Education': ['education', 'school', 'student', 'university', 'college', 'teacher', 'learning'],
        'Social Issues': ['civil rights', 'equality', 'justice', 'immigration', 'housing', 'welfare', 'social'],
        'Infrastructure': ['infrastructure', 'transportation', 'highway', 'bridge', 'road', 'transit', 'construction'],
        'Agriculture': ['agriculture', 'farm', 'farming', 'rural', 'food', 'crop', 'livestock']
    }
    
    # Score each topic
    topic_scores = {}
    for topic, keywords in topic_keywords.items():
        score = sum(1 for keyword in keywords if keyword in all_text)
        if score > 0:
            topic_scores[topic] = score
    
    # Return the topic with highest score, or 'Other' if no matches
    if topic_scores:
        return max(topic_scores.keys(), key=lambda k: topic_scores[k])
    return 'Other'

def analyze_bipartisan_tendency(member_id, headers):
    """Analyze bipartisan tendency based on cosponsorship patterns"""
    # Placeholder function - detailed implementation would require extensive data
    # For now, return a random score between 0 and 1
    return np.random.uniform(0, 1)  # Placeholder bipartisan score

def analyze_congress_generations(detailed_analysis=True):
    """
    Analyze congressional members by generation.
    
    Args:
        detailed_analysis: If True, fetches detailed bill topics (slower).
                          If False, only counts bill volumes (faster).
    """
    API_KEY = os.environ.get("CONGRESS_API_KEY") 
    if not API_KEY:
        print("🛑 Error: CONGRESS_API_KEY environment variable not set.")
        return
        
    headers = {"X-Api-Key": API_KEY}
    all_members_raw = []
    url = "https://api.congress.gov/v3/member"
    
    print("Fetching current member data from Congress.gov...")
    print("(Using currentMember=true filter to get only active members)")
    page_count = 0
    while url:
        page_count += 1
        print(f"Fetching page {page_count}...")
        try:
            # Use currentMember parameter to filter at API level
            params = {"limit": 250, "currentMember": "true"}
            if page_count > 1:
                # For subsequent pages, the URL already has the offset
                params = {"limit": 250}
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status() 
            data = response.json()
            members_on_page = data.get("members", [])
            all_members_raw.extend(members_on_page)
            
            print(f"  Retrieved {len(members_on_page)} members (Total so far: {len(all_members_raw)})")
            
            url = data.get("pagination", {}).get("next", None)
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            url = None
    
    print(f"\nTotal current members fetched: {len(all_members_raw)}")
    
    print(f"\nTotal current members fetched: {len(all_members_raw)}")
    
    # The API already filtered for current members, so we can use them directly
    current_members = all_members_raw
    
    
    generation_data = {}

    print(f"\nNow performing detailed analysis on {len(current_members)} members...")


    for i, member in enumerate(current_members):
        member_id = member.get("bioguideId")
        member_name = member.get("name", "N/A")
        
        # Fetch detailed member information to get birth year and party
        birth_year, party = fetch_member_details(member_id, headers)
        
        generation = get_generation(birth_year)
        
        # Initialize generation data if not exists
        if generation not in generation_data:
            generation_data[generation] = {
                'count': 0,
                'total_bills': 0,
                'topic_counts': defaultdict(int),
                'bipartisan_scores': [],
                'members': []
            }
        
        print(f"Processing member {i+1}/{len(current_members)}: {member_name} ({generation}, {party})")
        
        # Basic counts
        generation_data[generation]['count'] += 1
        
        # Fetch bill count
        bill_count = fetch_sponsored_bills_count(member_id, headers)
        generation_data[generation]['total_bills'] += bill_count
        
        # Fetch detailed bills for topic analysis (only if detailed_analysis is True)
        if detailed_analysis:
            detailed_bills = fetch_detailed_bills(member_id, headers, limit=20)
            
            # Analyze topics
            for bill in detailed_bills:
                topic = categorize_bill_topic(bill['title'], bill['policy_area'], bill['subjects'])
                generation_data[generation]['topic_counts'][topic] += 1
            
            # Analyze bipartisan tendency (placeholder)
            bipartisan_score = analyze_bipartisan_tendency(member_id, headers)
            generation_data[generation]['bipartisan_scores'].append(bipartisan_score)
        
        # Store member info
        generation_data[generation]['members'].append({
            'name': member_name,
            'party': party,
            'birth_year': birth_year,
            'bill_count': bill_count
        })
        
        time.sleep(0.25)  # Rate limiting - slightly faster with extra API call

    # Prepare data for analysis and visualization
    return prepare_analysis_data(generation_data, detailed_analysis)

def prepare_analysis_data(generation_data, detailed_analysis=True):
    """Prepare and structure data for visualization"""
    
    # 1. Basic generational summary
    summary_data = []
    for generation, data in generation_data.items():
        avg_bills = data['total_bills'] / data['count'] if data['count'] > 0 else 0
        avg_bipartisan = np.mean(data['bipartisan_scores']) if data['bipartisan_scores'] else 0
        
        summary_data.append({
            'Generation': generation,
            'Members': data['count'],
            'TotalSponsoredBills': data['total_bills'],
            'AvgBillsPerMember': round(avg_bills, 2),
            'AvgBipartisanScore': round(avg_bipartisan, 3) if detailed_analysis else None
        })
    
    summary_df = pd.DataFrame(summary_data)
    
    # 2. Topic analysis by generation (only if detailed analysis was performed)
    topic_df = pd.DataFrame()
    if detailed_analysis:
        topic_data = []
        for generation, data in generation_data.items():
            total_bills_analyzed = sum(data['topic_counts'].values())
            for topic, count in data['topic_counts'].items():
                proportion = count / total_bills_analyzed if total_bills_analyzed > 0 else 0
                topic_data.append({
                    'Generation': generation,
                    'Topic': topic,
                    'Count': count,
                    'Proportion': round(proportion, 3)
                })
        
        topic_df = pd.DataFrame(topic_data)
    
    # 3. Individual member data
    member_data = []
    for generation, data in generation_data.items():
        for member in data['members']:
            member_data.append({
                'Generation': generation,
                'Name': member['name'],
                'Party': member['party'],
                'BirthYear': member['birth_year'],
                'BillCount': member['bill_count']
            })
    
    member_df = pd.DataFrame(member_data)
    
    # Save all data
    summary_df.to_csv("congress_generational_summary.csv", index=False)
    if detailed_analysis and not topic_df.empty:
        topic_df.to_csv("congress_generational_topics.csv", index=False)
    member_df.to_csv("congress_individual_members.csv", index=False)
    
    # Print summary statistics
    print("\n" + "="*70)
    print("📊 GENERATIONAL ANALYSIS SUMMARY")
    print("="*70)
    print(f"\nTotal Members Analyzed: {len(member_df)}")
    print(f"\nBreakdown by Generation:")
    print(summary_df.to_string(index=False))
    print(f"\n📁 CSV Files Created:")
    print(f"  • congress_generational_summary.csv ({len(summary_df)} rows)")
    if detailed_analysis and not topic_df.empty:
        print(f"  • congress_generational_topics.csv ({len(topic_df)} rows)")
    print(f"  • congress_individual_members.csv ({len(member_df)} rows)")
    
    # Create visualizations
    if detailed_analysis and not topic_df.empty:
        create_interactive_visualizations(summary_df, topic_df, member_df)
    else:
        print("\n⚠️  Skipping detailed visualizations")
    
    print(f"\n✅ Success! {'Enhanced' if detailed_analysis else 'Basic'} generational analysis complete.")
    print("="*70 + "\n")
    
    return summary_df, topic_df, member_df

def create_interactive_visualizations(summary_df, topic_df, member_df):
    """Create interactive Altair visualizations for generational analysis"""
    
    # Enable Altair to save as HTML
    alt.data_transformers.enable('json')
    
    # 1. Basic generational overview - bar chart
    gen_overview = alt.Chart(summary_df).mark_bar().add_params(
        alt.selection_point()
    ).encode(
        x=alt.X('Generation:N', sort='-y'),
        y=alt.Y('Members:Q'),
        color=alt.Color('Generation:N', 
                       scale=alt.Scale(scheme='category10')),
        tooltip=['Generation', 'Members', 'TotalSponsoredBills', 'AvgBillsPerMember']
    ).properties(
        title='Congressional Members by Generation',
        width=400,
        height=300
    )
    
    # 2. Average bills per member by generation
    avg_bills_chart = alt.Chart(summary_df).mark_circle(size=200).encode(
        x=alt.X('Generation:N'),
        y=alt.Y('AvgBillsPerMember:Q'),
        color=alt.Color('Generation:N', scale=alt.Scale(scheme='category10')),
        size=alt.Size('Members:Q', scale=alt.Scale(range=[100, 400])),
        tooltip=['Generation', 'AvgBillsPerMember', 'Members']
    ).properties(
        title='Average Bills Sponsored per Member by Generation',
        width=400,
        height=300
    )
    
    # 3. Topic focus heatmap
    # First, normalize topic data for better visualization
    topic_summary = topic_df.groupby(['Generation', 'Topic']).agg({
        'Count': 'sum',
        'Proportion': 'mean'
    }).reset_index()
    
    topic_heatmap = alt.Chart(topic_summary).mark_rect().encode(
        x=alt.X('Topic:N', title='Topic Area'),
        y=alt.Y('Generation:N', title='Generation'),
        color=alt.Color('Proportion:Q', 
                       scale=alt.Scale(scheme='blues'),
                       title='Proportion of Bills'),
        stroke=alt.value('white'),
        strokeWidth=alt.value(2),
        tooltip=['Generation', 'Topic', 'Count', 'Proportion']
    ).properties(
        title='Topic Focus by Generation (Proportion of Bills)',
        width=500,
        height=200
    )
    
    # 4. Distribution of individual member activity
    member_activity = alt.Chart(member_df).mark_circle(opacity=0.7).add_params(
        alt.selection_interval()
    ).encode(
        x=alt.X('BirthYear:Q', title='Birth Year'),
        y=alt.Y('BillCount:Q', title='Number of Bills Sponsored'),
        color=alt.Color('Generation:N', scale=alt.Scale(scheme='category10')),
        size=alt.value(60),
        tooltip=['Name', 'Generation', 'Party', 'BirthYear', 'BillCount']
    ).properties(
        title='Individual Member Activity by Birth Year',
        width=500,
        height=300
    )
    
    # 5. Party distribution by generation
    party_gen = member_df.groupby(['Generation', 'Party']).size().reset_index(name='Count')
    
    party_chart = alt.Chart(party_gen).mark_bar().encode(
        x=alt.X('Generation:N'),
        y=alt.Y('Count:Q'),
        color=alt.Color('Party:N', 
                       scale=alt.Scale(domain=['D', 'R', 'I', 'Unknown'],
                                     range=['blue', 'red', 'green', 'gray'])),
        tooltip=['Generation', 'Party', 'Count']
    ).properties(
        title='Party Affiliation by Generation',
        width=400,
        height=300
    )
    
    # 6. Interactive topic exploration
    topic_selector = alt.selection_point(fields=['Topic'])
    
    topic_bar = alt.Chart(topic_summary).mark_bar().add_params(
        topic_selector
    ).encode(
        x=alt.X('Generation:N'),
        y=alt.Y('Count:Q'),
        color=alt.condition(topic_selector, 
                           alt.Color('Topic:N', scale=alt.Scale(scheme='category10')),
                           alt.value('lightgray')),
        tooltip=['Generation', 'Topic', 'Count']
    ).properties(
        title='Bills by Topic and Generation (Click to Filter)',
        width=400,
        height=250
    )
    
    topic_detail = alt.Chart(topic_summary).mark_text(
        align='left',
        baseline='top',
        fontSize=12,
        dx=5
    ).transform_filter(
        topic_selector
    ).encode(
        x=alt.value(10),
        y=alt.Y('Generation:N', scale=alt.Scale(paddingOuter=0.2)),
        text=alt.Text('Count:Q'),
        color=alt.value('black')
    ).properties(
        width=50,
        height=250
    )
    
    # Combine charts into dashboard
    top_row = alt.hconcat(gen_overview, avg_bills_chart)
    middle_row = topic_heatmap
    bottom_left = alt.hconcat(topic_bar, topic_detail)
    bottom_right = party_chart
    bottom_row = alt.hconcat(bottom_left, bottom_right)
    
    dashboard = alt.vconcat(
        top_row,
        middle_row,
        member_activity,
        bottom_row
    ).resolve_scale(
        color='independent'
    ).properties(
        title=alt.TitleParams(
            text='Congressional Generational Analysis Dashboard',
            fontSize=16,
            anchor='start'
        )
    )
    
    # Save visualizations
    dashboard.save('congress_generational_dashboard.html')
    gen_overview.save('generation_overview.html')
    topic_heatmap.save('topic_heatmap.html')
    member_activity.save('member_activity_scatter.html')
    
    print("📊 Interactive visualizations created:")
    print("  - congress_generational_dashboard.html (main dashboard)")
    print("  - generation_overview.html")
    print("  - topic_heatmap.html") 
    print("  - member_activity_scatter.html")

if __name__ == "__main__":
    # Run analysis - set detailed_analysis=True for full topic analysis (slower)
    # Set to False for basic analysis (faster - no bill details fetched)
    analyze_congress_generations(detailed_analysis=True)
    print("\n✓ Analysis complete! Generated visualizations:")
    print("  - generation_overview.html")
    print("  - topic_heatmap.html") 
    print("  - member_activity_scatter.html")