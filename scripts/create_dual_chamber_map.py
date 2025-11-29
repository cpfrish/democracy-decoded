"""
Enhanced Congressional Map with Photo Tooltips - House and Senate Toggle
Creates an interactive map using D3.js/TopoJSON with chamber toggle
"""

import pandas as pd
import json
import requests
import os
import time


def fetch_all_congress_members():
    """
    Fetch all current Congress members (both House and Senate) with location data
    """
    API_KEY = os.environ.get("CONGRESS_API_KEY")
    if not API_KEY:
        raise ValueError("CONGRESS_API_KEY environment variable required")
    
    headers = {"X-Api-Key": API_KEY}
    
    # Load base member data with photos
    df = pd.read_csv('../data/congress_members_with_photos.csv')
    
    # Fetch chamber, state, and district info for each member
    members_data = []
    
    print(f"Fetching location data for {len(df)} members...")
    
    for idx, row in df.iterrows():
        bioguide_id = row['BioguideID']
        
        # Fetch member details from API
        url = f"https://api.congress.gov/v3/member/{bioguide_id}"
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            member_data = data.get("member", {})
            
            # Extract state from top-level member data
            state = member_data.get("state")
            
            # Extract district and chamber from terms
            terms_data = member_data.get("terms", {})
            if isinstance(terms_data, dict):
                terms = terms_data.get("item", [])
            else:
                terms = terms_data if isinstance(terms_data, list) else []
            
            # Get latest term for district and chamber
            district = None
            chamber = None
            if terms:
                latest_term = terms[-1]
                district = latest_term.get("district")
                chamber = latest_term.get("chamber")
            
            if terms:
                member_info = {
                    'Name': row['Name'],
                    'Party': row['Party'],
                    'BirthYear': row['BirthYear'],
                    'BillCount': row['BillCount'],
                    'BioguideID': bioguide_id,
                    'PhotoURL': row['PhotoURL'],
                    'State': state,
                    'District': int(district) if district else None,
                    'Chamber': 'House' if chamber and 'house' in chamber.lower() else 'Senate',
                    'Generation': row['Generation']
                }
                
                members_data.append(member_info)
                
                if (idx + 1) % 50 == 0:
                    print(f"Processed {idx + 1}/{len(df)} members...")
            
            time.sleep(0.25)  # Rate limiting
            
        except Exception as e:
            print(f"Error fetching data for {row['Name']}: {e}")
            continue
    
    return pd.DataFrame(members_data)


def create_dual_chamber_map():
    """
    Create an HTML file with D3.js visualization showing both House and Senate
    with a toggle to switch between chambers
    """
    
    # Try to load from cache first
    try:
        df = pd.read_csv('../data/congress_members_all_chambers.csv')
        print("Loaded chamber data from cache")
    except FileNotFoundError:
        print("No cached data found. Fetching from Congress API...")
        print("This will take several minutes due to API rate limits...")
        df = fetch_all_congress_members()
        df.to_csv('../data/congress_members_all_chambers.csv', index=False)
        print(f"Saved data for {len(df)} members")
    
    # Separate House and Senate members
    house_df = df[df['Chamber'] == 'House'].copy()
    senate_df = df[df['Chamber'] == 'Senate'].copy()
    
    # Convert to JSON
    house_json = house_df.to_json(orient='records')
    senate_json = senate_df.to_json(orient='records')
    
    html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>US Congress Interactive Map - House & Senate</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <script src="https://d3js.org/topojson.v3.min.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        
        #container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        h1 {{
            text-align: center;
            color: #333;
            margin-bottom: 10px;
        }}
        
        .subtitle {{
            text-align: center;
            color: #666;
            margin-bottom: 10px;
            font-size: 14px;
        }}
        
        .controls {{
            text-align: center;
            margin: 20px 0;
            padding: 15px;
            background: #f8f8f8;
            border-radius: 6px;
        }}
        
        .toggle-container {{
            display: inline-flex;
            background: #e0e0e0;
            border-radius: 25px;
            padding: 4px;
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .toggle-btn {{
            padding: 10px 30px;
            border: none;
            background: transparent;
            color: #666;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            border-radius: 20px;
            transition: all 0.3s;
        }}
        
        .toggle-btn.active {{
            background: white;
            color: #333;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }}
        
        .toggle-btn:hover:not(.active) {{
            color: #333;
        }}
        
        #map {{
            width: 100%;
            height: 600px;
            position: relative;
        }}
        
        #map svg {{
            display: block;
        }}
        
        .district {{
            stroke: white;
            stroke-width: 0.5;
            cursor: pointer;
            transition: opacity 0.2s;
        }}
        
        .district:hover {{
            opacity: 0.8;
            stroke: #333;
            stroke-width: 2;
        }}
        
        .state {{
            stroke: white;
            stroke-width: 1.5;
            cursor: pointer;
            transition: opacity 0.2s;
        }}
        
        .state:hover {{
            opacity: 0.8;
            stroke: #333;
            stroke-width: 3;
        }}
        
        .tooltip {{
            position: absolute;
            padding: 12px;
            background: rgba(255, 255, 255, 0.98);
            border: 2px solid #333;
            border-radius: 8px;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.2s;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            max-width: 320px;
            z-index: 1000;
        }}
        
        .tooltip.show {{
            opacity: 1;
        }}
        
        .tooltip-photo {{
            width: 100px;
            height: 120px;
            object-fit: cover;
            border-radius: 4px;
            margin-bottom: 8px;
            display: block;
            border: 2px solid #ddd;
        }}
        
        .tooltip-name {{
            font-weight: bold;
            font-size: 14px;
            margin-bottom: 4px;
            color: #333;
        }}
        
        .tooltip-info {{
            font-size: 12px;
            color: #666;
            line-height: 1.5;
        }}
        
        .party-badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 3px;
            color: white;
            font-size: 11px;
            font-weight: bold;
            margin-right: 4px;
        }}
        
        .chamber-badge {{
            display: inline-block;
            padding: 3px 10px;
            border-radius: 3px;
            background: #555;
            color: white;
            font-size: 10px;
            font-weight: bold;
            margin-left: 4px;
        }}
        
        .party-D {{ background-color: #2E86AB; }}
        .party-R {{ background-color: #C23B22; }}
        .party-I {{ background-color: #9966CC; }}
        
        .legend {{
            margin-top: 20px;
            text-align: center;
            font-size: 14px;
        }}
        
        .legend-item {{
            display: inline-block;
            margin: 0 15px;
        }}
        
        .legend-color {{
            display: inline-block;
            width: 20px;
            height: 20px;
            border-radius: 3px;
            vertical-align: middle;
            margin-right: 5px;
        }}
        
        .stats {{
            text-align: center;
            margin: 20px 0;
            padding: 15px;
            background: #f0f7ff;
            border-radius: 6px;
            font-size: 13px;
            color: #555;
        }}
        
        .stats strong {{
            color: #333;
        }}
        
        .loading {{
            text-align: center;
            padding: 40px;
            color: #666;
            font-size: 16px;
        }}
        
        .fade-out {{
            opacity: 0;
            transition: opacity 0.3s;
        }}
        
        .fade-in {{
            opacity: 1;
            transition: opacity 0.3s;
        }}
    </style>
</head>
<body>
    <div id="container">
        <h1>United States Congress Interactive Map</h1>
        <div class="subtitle">119th Congress - Legislative Activity by Location</div>
        <div class="subtitle">Hover over districts or states to see representative/senator details and photos</div>
        
        <div class="controls">
            <div class="toggle-container">
                <button class="toggle-btn active" id="btn-house" onclick="switchChamber('house')">
                    House of Representatives
                </button>
                <button class="toggle-btn" id="btn-senate" onclick="switchChamber('senate')">
                    Senate
                </button>
            </div>
        </div>
        
        <div class="stats" id="stats"></div>
        
        <div id="map">
            <div class="loading">Loading map data...</div>
        </div>
        
        <div class="legend">
            <div class="legend-item">
                <span class="legend-color" style="background-color: #2E86AB;"></span>
                Democrat
            </div>
            <div class="legend-item">
                <span class="legend-color" style="background-color: #C23B22;"></span>
                Republican
            </div>
            <div class="legend-item">
                <span class="legend-color" style="background-color: #9966CC;"></span>
                Independent
            </div>
        </div>
    </div>
    
    <div class="tooltip" id="tooltip">
        <img class="tooltip-photo" id="tooltip-photo" src="" alt="">
        <div class="tooltip-name" id="tooltip-name"></div>
        <div class="tooltip-info" id="tooltip-info"></div>
    </div>
    
    <script>
        // Member data
        const houseMembers = {house_json};
        const senateMembers = {senate_json};
        
        let currentChamber = 'house';
        let svg = null;
        
        // Party colors
        const partyColors = {{
            'D': '#2E86AB',
            'R': '#C23B22',
            'I': '#9966CC'
        }};
        
        const partyNames = {{
            'D': 'Democrat',
            'R': 'Republican',
            'I': 'Independent'
        }};
        
        // Create lookups
        const houseLookup = {{}};
        houseMembers.forEach(member => {{
            const districtId = member.State + String(member.District).padStart(2, '0');
            houseLookup[districtId] = member;
        }});
        
        const senateLookup = {{}};
        senateMembers.forEach(member => {{
            if (!senateLookup[member.State]) {{
                senateLookup[member.State] = [];
            }}
            senateLookup[member.State].push(member);
        }});
        
        // Dimensions
        const width = 1200;
        const height = 600;
        
        // Projection
        const projection = d3.geoAlbersUsa()
            .scale(1300)
            .translate([width / 2, height / 2]);
        
        const path = d3.geoPath().projection(projection);
        
        // Tooltip
        const tooltip = d3.select("#tooltip");
        
        // Update stats
        function updateStats() {{
            const members = currentChamber === 'house' ? houseMembers : senateMembers;
            const dems = members.filter(m => m.Party === 'D').length;
            const reps = members.filter(m => m.Party === 'R').length;
            const inds = members.filter(m => m.Party === 'I').length;
            const totalBills = members.reduce((sum, m) => sum + m.BillCount, 0);
            const avgBills = (totalBills / members.length).toFixed(1);
            
            const chamberName = currentChamber === 'house' ? 'House of Representatives' : 'Senate';
            
            d3.select("#stats").html(`
                <strong>${{chamberName}}</strong> | 
                Total Members: <strong>${{members.length}}</strong> | 
                Democrats: <strong>${{dems}}</strong> | 
                Republicans: <strong>${{reps}}</strong> | 
                Independents: <strong>${{inds}}</strong> | 
                Total Bills Sponsored: <strong>${{totalBills}}</strong> | 
                Avg per Member: <strong>${{avgBills}}</strong>
            `);
        }}
        
        // Draw House map
        function drawHouseMap() {{
            d3.select("#map").html('<div class="loading">Loading House districts...</div>');
            
            d3.json("https://cdn.jsdelivr.net/npm/us-atlas@3/districts-10m.json")
                .then(us => {{
                    d3.select("#map").html("");
                    
                    svg = d3.select("#map")
                        .append("svg")
                        .attr("viewBox", [0, 0, width, height])
                        .attr("width", "100%")
                        .attr("height", "100%")
                        .classed("fade-in", true);
                    
                    const districts = topojson.feature(us, us.objects.districts);
                    
                    svg.selectAll(".district")
                        .data(districts.features)
                        .enter()
                        .append("path")
                        .attr("class", "district")
                        .attr("d", path)
                        .attr("fill", d => {{
                            const geoid = d.properties.GEOID;
                            const member = houseLookup[geoid];
                            return member && member.Party ? partyColors[member.Party] || '#cccccc' : '#cccccc';
                        }})
                        .on("mouseover", function(event, d) {{
                            const member = houseLookup[d.properties.GEOID];
                            if (member) {{
                                showTooltip(event, member);
                            }}
                        }})
                        .on("mousemove", function(event) {{
                            tooltip
                                .style("left", (event.pageX + 15) + "px")
                                .style("top", (event.pageY - 50) + "px");
                        }})
                        .on("mouseout", function() {{
                            tooltip.classed("show", false);
                        }});
                    
                    updateStats();
                }})
                .catch(error => {{
                    console.error("Error loading map:", error);
                    d3.select("#map").html('<div class="loading">Error loading map data</div>');
                }});
        }}
        
        // Draw Senate map (state-level)
        function drawSenateMap() {{
            d3.select("#map").html('<div class="loading">Loading Senate map...</div>');
            
            d3.json("https://cdn.jsdelivr.net/npm/us-atlas@3/states-10m.json")
                .then(us => {{
                    d3.select("#map").html("");
                    
                    svg = d3.select("#map")
                        .append("svg")
                        .attr("viewBox", [0, 0, width, height])
                        .attr("width", "100%")
                        .attr("height", "100%")
                        .classed("fade-in", true);
                    
                    const states = topojson.feature(us, us.objects.states);
                    
                    // State name to abbreviation lookup
                    const stateAbbr = {{
                        'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR', 'California': 'CA',
                        'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE', 'Florida': 'FL', 'Georgia': 'GA',
                        'Hawaii': 'HI', 'Idaho': 'ID', 'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA',
                        'Kansas': 'KS', 'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD',
                        'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN', 'Mississippi': 'MS', 'Missouri': 'MO',
                        'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV', 'New Hampshire': 'NH', 'New Jersey': 'NJ',
                        'New Mexico': 'NM', 'New York': 'NY', 'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH',
                        'Oklahoma': 'OK', 'Oregon': 'OR', 'Pennsylvania': 'PA', 'Rhode Island': 'RI', 'South Carolina': 'SC',
                        'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT', 'Vermont': 'VT',
                        'Virginia': 'VA', 'Washington': 'WA', 'West Virginia': 'WV', 'Wisconsin': 'WI', 'Wyoming': 'WY',
                        'District of Columbia': 'DC'
                    }};
                    
                    svg.selectAll(".state")
                        .data(states.features)
                        .enter()
                        .append("path")
                        .attr("class", "state")
                        .attr("d", path)
                        .attr("fill", d => {{
                            const stateName = d.properties.name;
                            const abbr = stateAbbr[stateName];
                            const senators = senateLookup[abbr];
                            
                            if (!senators || senators.length === 0) return '#cccccc';
                            
                            // Color by majority party
                            const dems = senators.filter(s => s.Party === 'D').length;
                            const reps = senators.filter(s => s.Party === 'R').length;
                            
                            if (dems > reps) return partyColors['D'];
                            if (reps > dems) return partyColors['R'];
                            
                            // Mixed or independent - blend
                            return '#9966CC';
                        }})
                        .on("mouseover", function(event, d) {{
                            const stateName = d.properties.name;
                            const abbr = stateAbbr[stateName];
                            const senators = senateLookup[abbr];
                            
                            if (senators && senators.length > 0) {{
                                showSenateTooltip(event, senators, abbr);
                            }}
                        }})
                        .on("mousemove", function(event) {{
                            tooltip
                                .style("left", (event.pageX + 15) + "px")
                                .style("top", (event.pageY - 50) + "px");
                        }})
                        .on("mouseout", function() {{
                            tooltip.classed("show", false);
                        }});
                    
                    updateStats();
                }})
                .catch(error => {{
                    console.error("Error loading map:", error);
                    d3.select("#map").html('<div class="loading">Error loading map data</div>');
                }});
        }}
        
        // Show tooltip for single member (House)
        function showTooltip(event, member) {{
            d3.select("#tooltip-photo")
                .attr("src", member.PhotoURL)
                .style("display", member.PhotoURL ? "block" : "none");
            
            d3.select("#tooltip-name")
                .html(`
                    <span class="party-badge party-${{member.Party}}">
                        ${{member.Party}}
                    </span>
                    ${{member.Name}}
                    <span class="chamber-badge">HOUSE</span>
                `);
            
            d3.select("#tooltip-info")
                .html(`
                    <strong>${{member.State}}-${{member.District}}</strong><br>
                    Party: ${{partyNames[member.Party] || member.Party}}<br>
                    Born: ${{member.BirthYear}}<br>
                    Generation: ${{member.Generation}}<br>
                    Bills Sponsored: ${{member.BillCount}}
                `);
            
            tooltip
                .style("left", (event.pageX + 15) + "px")
                .style("top", (event.pageY - 50) + "px")
                .classed("show", true);
        }}
        
        // Show tooltip for senators (multiple per state)
        function showSenateTooltip(event, senators, state) {{
            // Show first senator's photo
            d3.select("#tooltip-photo")
                .attr("src", senators[0].PhotoURL)
                .style("display", senators[0].PhotoURL ? "block" : "none");
            
            // Build senator list
            let senatorInfo = senators.map(s => `
                <div style="margin: 8px 0; padding: 8px; background: #f8f8f8; border-radius: 4px;">
                    <span class="party-badge party-${{s.Party}}">${{s.Party}}</span>
                    <strong>${{s.Name}}</strong><br>
                    <small>Born: ${{s.BirthYear}} | ${{s.Generation}}<br>
                    Bills Sponsored: ${{s.BillCount}}</small>
                </div>
            `).join('');
            
            d3.select("#tooltip-name")
                .html(`
                    <strong>${{state}} Senators</strong>
                    <span class="chamber-badge">SENATE</span>
                `);
            
            d3.select("#tooltip-info")
                .html(senatorInfo);
            
            tooltip
                .style("left", (event.pageX + 15) + "px")
                .style("top", (event.pageY - 50) + "px")
                .classed("show", true);
        }}
        
        // Switch chamber
        function switchChamber(chamber) {{
            if (chamber === currentChamber) return;
            
            currentChamber = chamber;
            
            // Update buttons
            document.getElementById('btn-house').classList.toggle('active');
            document.getElementById('btn-senate').classList.toggle('active');
            
            // Hide tooltip
            tooltip.classed("show", false);
            
            // Fade out and redraw
            if (svg) {{
                svg.classed("fade-out", true);
                setTimeout(() => {{
                    if (chamber === 'house') {{
                        drawHouseMap();
                    }} else {{
                        drawSenateMap();
                    }}
                }}, 300);
            }} else {{
                if (chamber === 'house') {{
                    drawHouseMap();
                }} else {{
                    drawSenateMap();
                }}
            }}
        }}
        
        // Initial load
        drawHouseMap();
    </script>
</body>
</html>
    """
    
    # Save HTML file
    output_path = '../visualizations/congress_map_dual_chamber.html'
    with open(output_path, 'w') as f:
        f.write(html_template)
    
    print(f"\nCreated dual-chamber interactive map: {output_path}")
    print(f"\nStatistics:")
    print(f"  House Members: {len(house_df)}")
    print(f"  Senate Members: {len(senate_df)}")
    print(f"  Total: {len(df)}")
    print("\nFeatures:")
    print("  - Toggle between House (districts) and Senate (states)")
    print("  - Photo thumbnails on hover")
    print("  - Party color coding")
    print("  - Live statistics for each chamber")
    print("  - Senate view shows both senators per state")
    print("\nOpen this file in a web browser to see the interactive map!")


if __name__ == "__main__":
    import sys
    
    # Check if API key is set
    if not os.environ.get("CONGRESS_API_KEY"):
        print("\nError: CONGRESS_API_KEY environment variable not set")
        print("Please set it with: export CONGRESS_API_KEY='your_key_here'")
        sys.exit(1)
    
    create_dual_chamber_map()
