#!/usr/bin/env python3
"""
Create a state-level congressional map that works with both House and Senate data.
Since congressional district TopoJSON is not available, we aggregate House members by state.
"""

import pandas as pd
import json

def create_state_level_congress_map():
    """Create an interactive state-level map showing both House and Senate"""
    
    # Load member data
    df = pd.read_csv('data/congress_members_all_chambers.csv')
    
    # Split into House and Senate
    house_df = df[df['Chamber'] == 'House'].copy()
    senate_df = df[df['Chamber'] == 'Senate'].copy()
    
    # Aggregate House members by state
    house_by_state = house_df.groupby('State').agg({
        'BioguideID': 'count',  # Number of representatives
        'BillCount': 'sum',      # Total bills
        'Party': lambda x: x.mode()[0] if len(x.mode()) > 0 else 'Unknown'  # Majority party
    }).reset_index()
    house_by_state.columns = ['State', 'MemberCount', 'TotalBills', 'MajorityParty']
    
    # Calculate party breakdown by state for House
    house_party_counts = house_df.groupby(['State', 'Party']).size().unstack(fill_value=0).reset_index()
    house_by_state = house_by_state.merge(house_party_counts, on='State', how='left')
    
    # Get Senate data by state
    senate_by_state = senate_df.groupby('State').agg({
        'BioguideID': 'count',
        'BillCount': 'sum',
        'Party': list  # Keep all parties as list
    }).reset_index()
    senate_by_state.columns = ['State', 'MemberCount', 'TotalBills', 'Parties']
    
    # Calculate Senate majority by state
    senate_party_counts = senate_df.groupby(['State', 'Party']).size().unstack(fill_value=0).reset_index()
    senate_by_state = senate_by_state.merge(senate_party_counts, on='State', how='left')
    
    # Get individual members for tooltips
    house_members = house_df.to_dict('records')
    senate_members = senate_df.to_dict('records')
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>US Congress State-Level Map</title>
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
            margin-bottom: 20px;
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
        
        .state {{
            stroke: #fff;
            stroke-width: 1;
            cursor: pointer;
            transition: opacity 0.2s;
        }}
        
        .state:hover {{
            opacity: 0.8;
            stroke-width: 2;
        }}
        
        .tooltip {{
            position: absolute;
            padding: 12px;
            background: rgba(0, 0, 0, 0.9);
            color: white;
            border-radius: 6px;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.2s;
            max-width: 350px;
            font-size: 13px;
            line-height: 1.6;
            z-index: 1000;
        }}
        
        .tooltip.show {{
            opacity: 1;
        }}
        
        .tooltip-header {{
            font-size: 15px;
            font-weight: bold;
            margin-bottom: 8px;
            padding-bottom: 8px;
            border-bottom: 1px solid rgba(255,255,255,0.3);
        }}
        
        .tooltip-row {{
            margin: 4px 0;
        }}
        
        .member-list {{
            margin-top: 8px;
            padding-top: 8px;
            border-top: 1px solid rgba(255,255,255,0.2);
        }}
        
        .member-item {{
            margin: 3px 0;
            font-size: 12px;
        }}
        
        .party-badge {{
            display: inline-block;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 11px;
            font-weight: bold;
            margin-left: 5px;
        }}
        
        .party-D {{
            background-color: #4472C4;
            color: white;
        }}
        
        .party-R {{
            background-color: #C94444;
            color: white;
        }}
        
        .party-I {{
            background-color: #70AD47;
            color: white;
        }}
        
        #stats {{
            text-align: center;
            padding: 15px;
            background: #f8f8f8;
            border-radius: 6px;
            margin-top: 20px;
            font-size: 14px;
        }}
        
        .legend {{
            margin: 20px 0;
            padding: 15px;
            background: #f8f8f8;
            border-radius: 6px;
        }}
        
        .legend-title {{
            font-weight: bold;
            margin-bottom: 10px;
            text-align: center;
        }}
        
        .legend-items {{
            display: flex;
            justify-content: center;
            gap: 20px;
            flex-wrap: wrap;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .legend-color {{
            width: 30px;
            height: 20px;
            border-radius: 3px;
            border: 1px solid #ccc;
        }}
        
        .loading {{
            text-align: center;
            padding: 50px;
            color: #666;
        }}
        
        .fade-in {{
            animation: fadeIn 0.5s;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}
    </style>
</head>
<body>
    <div id="container">
        <h1>🏛️ US Congress State-Level Map</h1>
        <p class="subtitle">Interactive visualization of House and Senate representation by state</p>
        
        <div class="controls">
            <div class="toggle-container">
                <button class="toggle-btn active" id="houseBtn" onclick="switchChamber('house')">
                    🏛️ House
                </button>
                <button class="toggle-btn" id="senateBtn" onclick="switchChamber('senate')">
                    🏛️ Senate
                </button>
            </div>
        </div>
        
        <div class="legend">
            <div class="legend-title">Party Control by State</div>
            <div class="legend-items">
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #4472C4;"></div>
                    <span>Democratic</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #C94444;"></div>
                    <span>Republican</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #9966CC;"></div>
                    <span>Split/Mixed</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #70AD47;"></div>
                    <span>Independent</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #cccccc;"></div>
                    <span>No Data</span>
                </div>
            </div>
        </div>
        
        <div id="map"></div>
        
        <div id="stats"></div>
    </div>
    
    <script>
        // Data
        const houseMembers = {json.dumps(house_members)};
        const senateMembers = {json.dumps(senate_members)};
        
        // State name to abbreviation
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
            'District of Columbia': 'DC', 'Puerto Rico': 'PR'
        }};
        
        // Party colors
        const partyColors = {{
            'D': '#4472C4',
            'R': '#C94444',
            'I': '#70AD47'
        }};
        
        // Create lookups by state
        const houseLookup = {{}};
        houseMembers.forEach(m => {{
            if (!houseLookup[m.State]) houseLookup[m.State] = [];
            houseLookup[m.State].push(m);
        }});
        
        const senateLookup = {{}};
        senateMembers.forEach(m => {{
            if (!senateLookup[m.State]) senateLookup[m.State] = [];
            senateLookup[m.State].push(m);
        }});
        
        // Map setup
        const width = 960;
        const height = 600;
        const projection = d3.geoAlbersUsa().scale(1300).translate([width / 2, height / 2]);
        const path = d3.geoPath().projection(projection);
        
        let svg;
        let currentChamber = 'house';
        
        // Tooltip
        const tooltip = d3.select("body")
            .append("div")
            .attr("class", "tooltip");
        
        // Switch chamber
        function switchChamber(chamber) {{
            currentChamber = chamber;
            
            // Update button states
            d3.selectAll('.toggle-btn').classed('active', false);
            d3.select(`#${{chamber}}Btn`).classed('active', true);
            
            // Redraw map
            drawMap();
        }}
        
        // Get state color
        function getStateColor(stateName, chamber) {{
            const abbr = stateAbbr[stateName];
            if (!abbr) return '#cccccc';
            
            const members = chamber === 'house' ? houseLookup[abbr] : senateLookup[abbr];
            if (!members || members.length === 0) return '#cccccc';
            
            // Count parties
            const dems = members.filter(m => m.Party === 'D').length;
            const reps = members.filter(m => m.Party === 'R').length;
            const inds = members.filter(m => m.Party === 'I').length;
            
            // Determine color
            if (chamber === 'senate') {{
                // For Senate, show if both are same party or split
                if (dems === 2) return partyColors['D'];
                if (reps === 2) return partyColors['R'];
                if (inds > 0 && dems === 0 && reps === 0) return partyColors['I'];
                return '#9966CC'; // Split
            }} else {{
                // For House, show majority party
                const total = members.length;
                if (dems > total / 2) return partyColors['D'];
                if (reps > total / 2) return partyColors['R'];
                if (inds > total / 2) return partyColors['I'];
                
                // If close, show largest party
                if (dems > reps && dems > inds) return partyColors['D'];
                if (reps > dems && reps > inds) return partyColors['R'];
                if (inds > dems && inds > reps) return partyColors['I'];
                
                return '#9966CC'; // Very close/mixed
            }}
        }}
        
        // Show tooltip
        function showTooltip(event, stateName) {{
            const abbr = stateAbbr[stateName];
            if (!abbr) return;
            
            const members = currentChamber === 'house' ? houseLookup[abbr] : senateLookup[abbr];
            if (!members || members.length === 0) return;
            
            const dems = members.filter(m => m.Party === 'D').length;
            const reps = members.filter(m => m.Party === 'R').length;
            const inds = members.filter(m => m.Party === 'I').length;
            const totalBills = members.reduce((sum, m) => sum + m.BillCount, 0);
            
            const chamberName = currentChamber === 'house' ? 'House' : 'Senate';
            
            let html = `
                <div class="tooltip-header">${{stateName}} (${{abbr}})</div>
                <div class="tooltip-row"><strong>${{chamberName}} Members:</strong> ${{members.length}}</div>
                <div class="tooltip-row">
                    Democrats: ${{dems}} | Republicans: ${{reps}} | Independents: ${{inds}}
                </div>
                <div class="tooltip-row"><strong>Total Bills Sponsored:</strong> ${{totalBills}}</div>
                <div class="member-list">
            `;
            
            // Add member list
            members.slice(0, 10).forEach(m => {{
                const district = m.District ? ` (District ${{m.District}})` : '';
                html += `
                    <div class="member-item">
                        ${{m.Name}}${{district}}
                        <span class="party-badge party-${{m.Party}}">${{m.Party}}</span>
                        - ${{m.BillCount}} bills
                    </div>
                `;
            }});
            
            if (members.length > 10) {{
                html += `<div class="member-item" style="font-style: italic;">... and ${{members.length - 10}} more</div>`;
            }}
            
            html += '</div>';
            
            tooltip
                .html(html)
                .style("left", (event.pageX + 15) + "px")
                .style("top", (event.pageY - 50) + "px")
                .classed("show", true);
        }}
        
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
        
        // Draw map
        function drawMap() {{
            d3.select("#map").html('<div class="loading">Loading map...</div>');
            
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
                    
                    svg.selectAll(".state")
                        .data(states.features)
                        .enter()
                        .append("path")
                        .attr("class", "state")
                        .attr("d", path)
                        .attr("fill", d => getStateColor(d.properties.name, currentChamber))
                        .on("mouseover", function(event, d) {{
                            showTooltip(event, d.properties.name);
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
                    d3.select("#map").html('<div class="loading">Error loading map data. Please refresh the page.</div>');
                }});
        }}
        
        // Initialize
        drawMap();
    </script>
</body>
</html>"""
    
    # Write the file
    with open('visualizations/congress_state_map_dual_chamber.html', 'w') as f:
        f.write(html_content)
    
    print("✅ Created congress_state_map_dual_chamber.html")
    print("   - House view: Shows majority party by state")
    print("   - Senate view: Shows whether state has 2D, 2R, or split")
    print("   - Tooltip shows all members and their bill counts")

if __name__ == '__main__':
    create_state_level_congress_map()
