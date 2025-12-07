"""
Generates an interactive US Congress map visualization from existing CSV files.
Python 3 must be installed to run this file.

Setup instructions:
1. Place your CSV files in the same directory or update CSV_PATHS
2. Install required packages: pip install pandas

How to run: Run 'python generate_congress_map.py' in terminal.
"""

import pandas as pd
import json
from pathlib import Path
from collections import defaultdict

# CSV file paths - update these to match your file locations
CSV_PATHS = {
    'congress_members_all_chambers': '../data/congress_members_all_chambers.csv'
}

# State abbreviation to full name mapping
STATE_ABBR_TO_NAME = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho",
    "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
    "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
    "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
    "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
    "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming"
}

def load_congress_data():
    """Load congressional data from CSV files."""
    print("Loading congressional data from CSV files...\n")
    
    try:
        # Load the main members data with chamber info
        members_df = pd.read_csv(CSV_PATHS['congress_members_all_chambers'])
        
        print(f"✓ Loaded {len(members_df)} members from CSV")
        
        # Build congress data structure
        congress_data = defaultdict(lambda: {"senators": [], "representatives": []})
        
        for _, member in members_df.iterrows():
            state = member['State']
            
            member_info = {
                "name": member['Name'],
                "party": member['Party'],
                "bioguideId": member['BioguideID'],
                "photoUrl": member['PhotoURL'] if pd.notna(member['PhotoURL']) else '',
                "billCount": int(member['BillCount']) if pd.notna(member['BillCount']) else 0,
                "congressUrl": f"https://www.congress.gov/member/{member['Name'].split()[0]}-{member['Name'].split()[-1]}/{member['BioguideID']}" if pd.notna(member['BioguideID']) else ''
            }
            
            if member['Chamber'] == 'Senate':
                congress_data[state]["senators"].append(member_info)
            elif member['Chamber'] == 'House':
                district = member['District']
                if pd.isna(district) or district == '' or district == '0':
                    district = 'At-Large'
                else:
                    district = int(float(district))
                
                member_info['district'] = district
                congress_data[state]["representatives"].append(member_info)
        
        # Sort representatives by district
        for state in congress_data:
            congress_data[state]["representatives"].sort(
                key=lambda x: x['district'] if isinstance(x['district'], int) else 999
            )
        
        return dict(congress_data)
        
    except FileNotFoundError as e:
        print(f"ERROR: Could not find CSV file - {e}")
        print("Please update CSV_PATHS in the script to match your file locations")
        return {}
    except Exception as e:
        print(f"ERROR: {e}")
        return {}

# HTML template
html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>US Congress Map</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/topojson/3.0.2/topojson.min.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #f8f9fa;
        }}
        
        #container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            padding: 30px;
        }}
        
        h1 {{
            color: #1a1a2e;
            margin: 0 0 10px 0;
            font-size: 28px;
        }}
        
        .subtitle {{
            color: #666;
            margin: 0 0 15px 0;
            font-size: 14px;
        }}
        
        .controls {{
            gap: 20px;
            display: flex;
            gap: 15px;
            margin-top: 15px;
            margin-bottom: 20px;
            flex-wrap: wrap;
            align-items: center;
        }}
        
        .control-group {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .control-group label {{
            font-size: 14px;
            font-weight: 500;
            color: #666;
        }}
        
        .control-group select {{
            padding: 6px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
            background: white;
            cursor: pointer;
        }}
        
        .zoom-controls {{
            display: flex;
            gap: 8px;
            margin-left: auto;
        }}
        
        .zoom-btn {{
            padding: 6px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            background: white;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            color: #666;
            transition: all 0.2s;
        }}
        
        .zoom-btn:hover {{
            background: #f5f5f5;
            border-color: #999;
        }}
        
        #map-container {{
            position: relative;
            width: 100%;
            height: 600px;
        }}
        
        .state {{
            fill: #e8eaf6;
            stroke: #fff;
            stroke-width: 1.5;
            cursor: pointer;
            transition: fill 0.2s;
        }}
        
        .state:hover {{
            fill: #5c6bc0;
        }}
        
        .state.selected {{
            fill: #3949ab;
        }}

        .territory rect.selected {{
            fill: #3949ab;
        }}
        
        #info-panel {{
            margin-top: 30px;
            padding: 20px;
            background: #f5f7fa;
            border-radius: 8px;
            min-height: 150px;
        }}
        
        .info-header {{
            font-size: 20px;
            font-weight: 600;
            color: #1a1a2e;
            margin-bottom: 15px;
        }}
        
        .rep-section {{
            margin-bottom: 20px;
        }}
        
        .rep-section h3 {{
            font-size: 14px;
            font-weight: 600;
            color: #666;
            margin: 0 0 10px 0;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .rep-list {{
            display: grid;
            gap: 10px;
        }}
        
        .rep-item {{
            padding: 12px;
            background: white;
            border-radius: 6px;
            border-left: 4px solid #5c6bc0;
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        
        .rep-item.d {{
            border-left-color: #2e86ab;
        }}
        
        .rep-item.r {{
            border-left-color: #c23b22;
        }}
        
        .rep-item.i {{
            border-left-color: #9966cc;
        }}
        
        .rep-photo {{
            width: 50px;
            height: 50px;
            border-radius: 50%;
            object-fit: cover;
            background: #e0e0e0;
            flex-shrink: 0;
        }}
        
        .rep-info {{
            flex: 1;
        }}
        
        .rep-name {{
            font-weight: 600;
            color: #1a1a2e;
            margin-bottom: 4px;
        }}

        .rep-name a {{
            color: #1a1a2e;
            text-decoration: none;
            transition: color 0.2s;
        }}

        .rep-name a:hover {{
            color: #5c6bc0;
            text-decoration: underline;
        }}
        
        .rep-details {{
            font-size: 14px;
            color: #666;
        }}
        
        .placeholder {{
            color: #999;
            font-style: italic;
            text-align: center;
            padding: 40px 20px;
        }}
        
        .legend {{
            margin-top: 15px;
            display: flex;
            gap: 20px;
            justify-content: center;
            font-size: 13px;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .legend-color {{
            width: 20px;
            height: 12px;
            border-radius: 2px;
        }}
        
        .data-info {{
            margin-top: 20px;
            text-align: center;
            font-size: 12px;
            color: #999;
        }}

        .data-info a {{
            color: #999;
            text-decoration: none;
        }}

        .data-info a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div id="container">
        <h1>US Congressional Representatives Map</h1>
        <p class="subtitle">Click on any state to view its senators and representatives</p>
        
        <div id="map-container">
            <svg id="map"></svg>
        </div>

        <div class="controls">
            <div class="control-group">
                <label for="party-filter">Filter by Party:</label>
                <select id="party-filter">
                    <option value="all">All Parties</option>
                    <option value="Democrat">Democrat</option>
                    <option value="Republican">Republican</option>
                    <option value="Independent">Independent</option>
                </select>
            </div>
            
            <div class="control-group">
                <label for="sort-by">Sort by:</label>
                <select id="sort-by">
                    <option value="district">District</option>
                    <option value="name">Name</option>
                    <option value="billCount">Bill Count</option>
                </select>
            </div>
            
            <div class="zoom-controls">
                <button class="zoom-btn" id="zoom-in">Zoom In</button>
                <button class="zoom-btn" id="zoom-out">Zoom Out</button>
                <button class="zoom-btn" id="zoom-reset">Reset</button>
            </div>
        </div>
        
        <div class="legend">
            <div class="legend-item">
                <div class="legend-color" style="background: #2e86ab;"></div>
                <span>Democrat</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #c23b22;"></div>
                <span>Republican</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #9966cc;"></div>
                <span>Independent</span>
            </div>
        </div>
        
        <div id="info-panel">
            <div class="placeholder">Click on a state to view its congressional delegation</div>
        </div>
        
        <div class="data-info">
            Data from Congress.gov API • 
            <a href="https://www.congress.gov/help/linking-to-congress-gov" target="_blank" rel="noopener noreferrer">Learn more about Congress.gov here</a>
        </div>
    </div>

    <script>
        const congressData = {congress_data_json};
        let currentState = null;
        let currentPartyFilter = 'all';
        let currentSortBy = 'district';

        const width = document.getElementById('map-container').clientWidth;
        const height = 600;

        const svg = d3.select("#map")
            .attr("width", width)
            .attr("height", height);

        const g = svg.append("g");

        const projection = d3.geoAlbersUsa()
            .scale(width)
            .translate([width / 2, height / 2]);

        const path = d3.geoPath().projection(projection);
        
        // Zoom behavior
        const zoom = d3.zoom()
            .scaleExtent([0.5, 8])
            .on("zoom", (event) => {{
                g.attr("transform", event.transform);
            }});
        
        svg.call(zoom);
        
        // Zoom controls
        document.getElementById('zoom-in').addEventListener('click', () => {{
            svg.transition().call(zoom.scaleBy, 1.5);
        }});
        
        document.getElementById('zoom-out').addEventListener('click', () => {{
            svg.transition().call(zoom.scaleBy, 0.67);
        }});
        
        document.getElementById('zoom-reset').addEventListener('click', () => {{
            svg.transition().call(zoom.transform, d3.zoomIdentity);
        }});
        
        // Filter and sort controls
        document.getElementById('party-filter').addEventListener('change', (e) => {{
            currentPartyFilter = e.target.value;
            if (currentState) {{
                showStateInfo(currentState);
            }}
        }});
        
        document.getElementById('sort-by').addEventListener('change', (e) => {{
            currentSortBy = e.target.value;
            if (currentState) {{
                showStateInfo(currentState);
            }}
        }});

        d3.json("https://cdn.jsdelivr.net/npm/us-atlas@3/states-10m.json").then(us => {{
            const states = topojson.feature(us, us.objects.states);
            
            g.selectAll(".state")
                .data(states.features)
                .enter().append("path")
                .attr("class", "state")
                .attr("d", path)
                .on("click", function(event, d) {{
                    g.selectAll(".state").classed("selected", false);
                    g.selectAll(".territory rect").classed("selected", false);
                    g.selectAll(".territory rect").attr("fill", "#e8eaf6");
                    d3.select(this).classed("selected", true);
                    currentState = d.properties.name;
                    showStateInfo(d.properties.name);
                }});
            
            g.selectAll(".state-label")
                .data(states.features)
                .enter().append("text")
                .attr("class", "state-label")
                .attr("transform", d => `translate(${{path.centroid(d)}})`)
                .attr("text-anchor", "middle")
                .attr("font-size", "10px")
                .attr("fill", "#666")
                .attr("pointer-events", "none")
                .text(d => {{
                    const abbr = getStateAbbr(d.properties.name);
                    return abbr;
                }});
        }});

        const territories = [
            {{ name: "Puerto Rico", x: width - 160, y: height - 180, abbr: "PR" }},
            {{ name: "District of Columbia", x: width - 160, y: height - 150, abbr: "DC" }},
            {{ name: "Guam", x: width - 160, y: height - 120, abbr: "GU" }},
            {{ name: "Virgin Islands", x: width - 160, y: height - 90, abbr: "VI" }},
            {{ name: "American Samoa", x: width - 160, y: height - 60, abbr: "AS" }},
            {{ name: "Northern Mariana Islands", x: width - 160, y: height - 30, abbr: "MP" }}
        ];

        territories.forEach(territory => {{
            const territoryGroup = g.append("g")
                .attr("class", "territory")
                .attr("transform", `translate(${{territory.x}},${{territory.y}})`);
            
            territoryGroup.append("rect")
                .attr("width", 150)
                .attr("height", 25)
                .attr("rx", 4)
                .attr("fill", "#e8eaf6")
                .attr("stroke", "#fff")
                .attr("stroke-width", 1.5)
                .attr("cursor", "pointer")
                .on("click", function() {{
                    g.selectAll(".state").classed("selected", false);
                    g.selectAll(".territory rect").classed("selected", false);
                    g.selectAll(".territory rect").attr("fill", "#e8eaf6");
                    d3.select(this).classed("selected", true);
                    currentState = territory.name;
                    showStateInfo(territory.name);
                }})
                .on("mouseover", function() {{
                    if (!d3.select(this).classed("selected")) {{
                        d3.select(this).attr("fill", "#5c6bc0");
                    }}
                }})
                .on("mouseout", function() {{
                    if (!d3.select(this).classed("selected")) {{
                        d3.select(this).attr("fill", "#e8eaf6");
                    }}
                }});
            
            territoryGroup.append("text")
                .attr("x", 75)
                .attr("y", 16)
                .attr("text-anchor", "middle")
                .attr("font-size", "9px")
                .attr("fill", "#666")
                .attr("pointer-events", "none")
                .text(territory.name + " (" + territory.abbr + ")");
        }});

        function filterMembers(members) {{
            if (currentPartyFilter === 'all') {{
                return members;
            }}
            const partyMap = {{
                'Democrat': 'D',
                'Republican': 'R',
                'Independent': 'I'
            }};
            return members.filter(m => m.party === partyMap[currentPartyFilter]);
        }}
        
        function sortMembers(members, isRepresentatives) {{
            const sorted = [...members];
            
            if (currentSortBy === 'name') {{
                sorted.sort((a, b) => a.name.localeCompare(b.name));
            }} else if (currentSortBy === 'billCount') {{
                sorted.sort((a, b) => b.billCount - a.billCount);
            }} else if (currentSortBy === 'district' && isRepresentatives) {{
                sorted.sort((a, b) => {{
                    const aVal = a.district === 'At-Large' ? 999 : a.district;
                    const bVal = b.district === 'At-Large' ? 999 : b.district;
                    return aVal - bVal;
                }});
            }}
            
            return sorted;
        }}

        function showStateInfo(stateName) {{
            const panel = document.getElementById('info-panel');
            const data = congressData[stateName];
            
            if (!data) {{
                panel.innerHTML = `
                    <div class="info-header">${{stateName}}</div>
                    <div class="placeholder">No congressional data available for this state.</div>
                `;
                return;
            }}
            
            let html = `<div class="info-header">${{stateName}}</div>`;
            
            // Filter and sort senators
            let senators = filterMembers(data.senators);
            senators = sortMembers(senators, false);
            
            html += `<div class="rep-section">
                <h3>Senators (${{senators.length}})</h3>
                <div class="rep-list">`;
            
            if (senators.length === 0) {{
                html += `<div class="placeholder">No senators match the current filter.</div>`;
            }} else {{
                senators.forEach(senator => {{
                    const partyClass = senator.party.toLowerCase();
                    const photoHtml = senator.photoUrl ? 
                        `<img src="${{senator.photoUrl}}" alt="${{senator.name}}" class="rep-photo">` :
                        `<div class="rep-photo"></div>`;
                    
                    html += `
                        <div class="rep-item ${{partyClass}}">
                            ${{photoHtml}}
                            <div class="rep-info">
                                <div class="rep-name">
                                    <a href="${{senator.congressUrl}}" target="_blank" rel="noopener noreferrer">${{senator.name}}</a>
                                </div>
                                <div class="rep-details">${{senator.party}} • ${{senator.billCount}} bills</div>
                            </div>
                        </div>
                    `;
                }});
            }}
            
            html += `</div></div>`;
            
            // Filter and sort representatives
            let representatives = filterMembers(data.representatives);
            representatives = sortMembers(representatives, true);
            
            html += `<div class="rep-section">
                <h3>Representatives (${{representatives.length}})</h3>
                <div class="rep-list">`;
            
            if (representatives.length === 0) {{
                html += `<div class="placeholder">No representatives match the current filter.</div>`;
            }} else {{
                representatives.forEach(rep => {{
                    const partyClass = rep.party.toLowerCase();
                    const districtLabel = rep.district === 'At-Large' ? 'At-Large' : `District ${{rep.district}}`;
                    const photoHtml = rep.photoUrl ? 
                        `<img src="${{rep.photoUrl}}" alt="${{rep.name}}" class="rep-photo">` :
                        `<div class="rep-photo"></div>`;
                    
                    html += `
                        <div class="rep-item ${{partyClass}}">
                            ${{photoHtml}}
                            <div class="rep-info">
                                <div class="rep-name">
                                    <a href="${{rep.congressUrl}}" target="_blank" rel="noopener noreferrer">${{rep.name}}</a>
                                </div>
                                <div class="rep-details">${{rep.party}} • ${{districtLabel}} • ${{rep.billCount}} bills</div>
                            </div>
                        </div>
                    `;
                }});
            }}
            
            html += `</div></div>`;
            
            panel.innerHTML = html;
        }}

        function getStateAbbr(name) {{
            const abbrs = {{
                "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR",
                "California": "CA", "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE",
                "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID",
                "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS",
                "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
                "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS",
                "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV",
                "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY",
                "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK",
                "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
                "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT",
                "Vermont": "VT", "Virginia": "VA", "Washington": "WA", "West Virginia": "WV",
                "Wisconsin": "WI", "Wyoming": "WY"
            }};
            return abbrs[name] || "";
        }}
    </script>
</body>
</html>"""

def generate_html(output_file="congress_map.html"):
    """Generate the HTML file with congressional data from CSV files."""
    
    # Load data from CSV
    congress_data = load_congress_data()
    
    if not congress_data:
        print("ERROR: Failed to load congressional data from CSV")
        return
    
    print(f'✓ Processed data for {len(congress_data)} states')
    
    # Count total members
    total_senators = sum(len(data['senators']) for data in congress_data.values())
    total_reps = sum(len(data['representatives']) for data in congress_data.values())
    print(f'✓ Total senators: {total_senators}')
    print(f'✓ Total representatives: {total_reps}')
    
    # Convert to JSON
    congress_data_json = json.dumps(congress_data, indent=4)
    
    # Generate HTML
    html_content = html_template.format(congress_data_json=congress_data_json)
    
    # Create visualizations directory if it doesn't exist
    Path('visualizations').mkdir(exist_ok=True)
    output_path = f'../visualizations/{output_file}'
    
    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f'\n✓ Generated {output_path}')
    print(f'✓ Open the file in your browser to view the visualization\n')

if __name__ == "__main__":
    generate_html()