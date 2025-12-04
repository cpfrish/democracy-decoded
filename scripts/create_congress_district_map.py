"""
Generates an interactive US Congress map visualization at district level from existing CSV files.
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
    """Load congressional data from CSV files organized by district."""
    print("Loading congressional data from CSV files...\n")
    
    try:
        # Load the main members data with chamber info
        members_df = pd.read_csv(CSV_PATHS['congress_members_all_chambers'])
        
        print(f"✓ Loaded {len(members_df)} members from CSV")
        
        # Build district-level data structure
        district_data = {}
        
        # First, collect senators by state
        senators_by_state = defaultdict(list)
        for _, member in members_df[members_df['Chamber'] == 'Senate'].iterrows():
            state = member['State']
            senators_by_state[state].append({
                "name": member['Name'],
                "party": member['Party'],
                "bioguideId": member['BioguideID'],
                "photoUrl": member['PhotoURL'] if pd.notna(member['PhotoURL']) else '',
                "billCount": int(member['BillCount']) if pd.notna(member['BillCount']) else 0
            })
        
        # Collect all representatives by state
        reps_by_state = defaultdict(list)
        for _, member in members_df[members_df['Chamber'] == 'House'].iterrows():
            state = member['State']
            district = member['District']
            
            if pd.isna(district) or district == '' or district == '0':
                district = 0  # At-Large
            else:
                district = int(float(district))
            
            rep_info = {
                "name": member['Name'],
                "party": member['Party'],
                "bioguideId": member['BioguideID'],
                "photoUrl": member['PhotoURL'] if pd.notna(member['PhotoURL']) else '',
                "billCount": int(member['BillCount']) if pd.notna(member['BillCount']) else 0,
                "district": district
            }
            
            reps_by_state[state].append(rep_info)
            
            # Create district key (e.g., "CA-12")
            district_key = f"{state}-{district:02d}" if district > 0 else f"{state}-AL"
            
            district_data[district_key] = {
                "state": state,
                "stateName": STATE_ABBR_TO_NAME.get(state, state),
                "district": district,
                "representative": rep_info,
                "senators": senators_by_state[state],
                "allStateReps": []  # Will be filled next
            }
        
        # Fill in allStateReps for each district
        for district_key in district_data:
            state = district_data[district_key]["state"]
            all_reps = sorted(reps_by_state[state], key=lambda x: x['district'])
            district_data[district_key]["allStateReps"] = all_reps
        
        print(f"✓ Created {len(district_data)} district entries")
        
        return district_data
        
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
    <title>US Congress District Map</title>
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
            max-width: 1400px;
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
        
        #map-container {{
            position: relative;
            width: 100%;
            height: 700px;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            overflow: hidden;
        }}
        
        .district {{
            fill: #e8eaf6;
            stroke: #fff;
            stroke-width: 0.5;
            cursor: pointer;
            transition: fill 0.2s;
        }}
        
        .district:hover {{
            fill: #5c6bc0;
        }}
        
        .district.selected {{
            fill: #3949ab;
            stroke: #1a237e;
            stroke-width: 1.5;
        }}
        
        .controls {{
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
            margin-top: 20px;
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
        
        .district-header {{
            font-size: 16px;
            color: #666;
            margin-bottom: 20px;
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
            border-left-color: #2196F3;
        }}
        
        .rep-item.r {{
            border-left-color: #f44336;
        }}
        
        .rep-item.i {{
            border-left-color: #9E9E9E;
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
        
        .loading {{
            text-align: center;
            padding: 50px;
            color: #666;
        }}
    </style>
</head>
<body>
    <div id="container">
        <h1>US Congressional Districts Map</h1>
        <p class="subtitle">Click on any congressional district to view its representative and senators</p>
        
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
                <div class="legend-color" style="background: #2196F3;"></div>
                <span>Democrat</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #f44336;"></div>
                <span>Republican</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #9E9E9E;"></div>
                <span>Independent</span>
            </div>
        </div>
        
        <div id="info-panel">
            <div class="placeholder">Click on a congressional district to view its representative and senators</div>
        </div>
        
        <div class="data-info">
            Data from Congress.gov API • Congressional District Boundaries from US Census Bureau
        </div>
    </div>

    <script>
        const districtData = {district_data_json};
        let currentDistrict = null;
        let currentPartyFilter = 'all';
        let currentSortBy = 'district';

        const width = document.getElementById('map-container').clientWidth;
        const height = 700;

        const svg = d3.select("#map")
            .attr("width", width)
            .attr("height", height)

        const g = svg.append("g");
        
        // Zoom behavior
        const zoom = d3.zoom()
            .scaleExtent([1, 8])
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
            if (currentDistrict) {{
                showDistrictInfo(currentDistrict);
            }}
        }});
        
        document.getElementById('sort-by').addEventListener('change', (e) => {{
            currentSortBy = e.target.value;
            if (currentDistrict) {{
                showDistrictInfo(currentDistrict);
            }}
        }});

        // Load embedded congressional district boundaries
        const districtsGeoJSON = {district_geojson};

        console.log('District GeoJSON loaded:', districtsGeoJSON);
        console.log('Number of features:', districtsGeoJSON.features ? districtsGeoJSON.features.length : 'undefined');

        // Hide loading and render map immediately
        document.addEventListener('DOMContentLoaded', function() {{
            console.log('DOM loaded, rendering map...');

            // State FIPS to abbreviation mapping
            const fipsToState = {{
                '01': 'AL', '02': 'AK', '04': 'AZ', '05': 'AR', '06': 'CA', '08': 'CO', 
                '09': 'CT', '10': 'DE', '12': 'FL', '13': 'GA', '15': 'HI', '16': 'ID', 
                '17': 'IL', '18': 'IN', '19': 'IA', '20': 'KS', '21': 'KY', '22': 'LA', 
                '23': 'ME', '24': 'MD', '25': 'MA', '26': 'MI', '27': 'MN', '28': 'MS', 
                '29': 'MO', '30': 'MT', '31': 'NE', '32': 'NV', '33': 'NH', '34': 'NJ', 
                '35': 'NM', '36': 'NY', '37': 'NC', '38': 'ND', '39': 'OH', '40': 'OK', 
                '41': 'OR', '42': 'PA', '44': 'RI', '45': 'SC', '46': 'SD', '47': 'TN', 
                '48': 'TX', '49': 'UT', '50': 'VT', '51': 'VA', '53': 'WA', '54': 'WV', 
                '55': 'WI', '56': 'WY'
            }};

            // Filter out territories
            const continentalFeatures = districtsGeoJSON.features.filter(d => {{
                const state = d.properties.STATEFP;
                return !['72', '78', '66', '60', '69'].includes(state);
            }});
            
            const continentalGeoJSON = {{
                type: 'FeatureCollection',
                features: continentalFeatures
            }};
            
            const projection = d3.geoAlbersUsa()
                .fitSize([width, height], continentalGeoJSON);

            const path = d3.geoPath().projection(projection);
            
            console.log('Rendering', continentalFeatures.length, 'continental districts');
            
            g.selectAll(".district")
                .data(continentalFeatures)
                .enter().append("path")
                .attr("class", "district")
                .attr("d", path)
                .on("click", function(event, d) {{
                    const stateFIPS = d.properties.STATEFP;
                    const state = fipsToState[stateFIPS];
                    const districtNum = d.properties.CD119FP;
                    const districtName = d.properties.NAMELSAD;
                    
                    console.log(`Clicked: ${{districtName}} (${{state}}-${{districtNum}})`);
                    
                    const districtKey = districtNum === '00' ? 
                        `${{state}}-AL` : 
                        `${{state}}-${{districtNum}}`;
                    
                    console.log('Looking for district key:', districtKey);
                    
                    g.selectAll(".district").classed("selected", false);
                    d3.select(this).classed("selected", true);
                    currentDistrict = districtKey;
                    showDistrictInfo(districtKey);
                }});
                    
            console.log('Map rendering complete');
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
                    const aVal = a.district === 0 ? 999 : a.district;
                    const bVal = b.district === 0 ? 999 : b.district;
                    return aVal - bVal;
                }});
            }}
            
            return sorted;
        }}
        
        function getPartyName(abbr) {{
            const map = {{ 'D': 'Democrat', 'R': 'Republican', 'I': 'Independent' }};
            return map[abbr] || abbr;
        }}

        function showDistrictInfo(districtKey) {{
            const panel = document.getElementById('info-panel');
            const data = districtData[districtKey];
            
            if (!data) {{
                panel.innerHTML = `
                    <div class="info-header">District ${{districtKey}}</div>
                    <div class="placeholder">No congressional data available for this district.</div>
                `;
                return;
            }}
            
            const districtLabel = data.district === 0 ? 'At-Large' : `District ${{data.district}}`;
            
            let html = `
                <div class="info-header">${{data.stateName}}</div>
                <div class="district-header">${{districtLabel}}</div>
            `;
            
            // Show the representative for this district
            html += `<div class="rep-section">
                <h3>Representative for this District</h3>
                <div class="rep-list">`;
            
            const rep = data.representative;
            const partyClass = rep.party.toLowerCase();
            const photoHtml = rep.photoUrl ? 
                `<img src="${{rep.photoUrl}}" alt="${{rep.name}}" class="rep-photo">` :
                `<div class="rep-photo"></div>`;
            
            html += `
                <div class="rep-item ${{partyClass}}">
                    ${{photoHtml}}
                    <div class="rep-info">
                        <div class="rep-name">${{rep.name}}</div>
                        <div class="rep-details">${{getPartyName(rep.party)}} • ${{districtLabel}} • ${{rep.billCount}} bills</div>
                    </div>
                </div>
            `;
            
            html += `</div></div>`;
            
            // Filter and sort senators
            let senators = filterMembers(data.senators);
            senators = sortMembers(senators, false);
            
            html += `<div class="rep-section">
                <h3>Senators for ${{data.stateName}} (${{senators.length}})</h3>
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
                                <div class="rep-name">${{senator.name}}</div>
                                <div class="rep-details">${{getPartyName(senator.party)}} • ${{senator.billCount}} bills</div>
                            </div>
                        </div>
                    `;
                }});
            }}
            
            html += `</div></div>`;
            
            // Filter and sort all state representatives
            let allReps = filterMembers(data.allStateReps);
            allReps = sortMembers(allReps, true);
            
            html += `<div class="rep-section">
                <h3>All Representatives for ${{data.stateName}} (${{allReps.length}})</h3>
                <div class="rep-list">`;
            
            if (allReps.length === 0) {{
                html += `<div class="placeholder">No representatives match the current filter.</div>`;
            }} else {{
                allReps.forEach(rep => {{
                    const partyClass = rep.party.toLowerCase();
                    const districtLabel = rep.district === 0 ? 'At-Large' : `District ${{rep.district}}`;
                    const photoHtml = rep.photoUrl ? 
                        `<img src="${{rep.photoUrl}}" alt="${{rep.name}}" class="rep-photo">` :
                        `<div class="rep-photo"></div>`;
                    
                    html += `
                        <div class="rep-item ${{partyClass}}">
                            ${{photoHtml}}
                            <div class="rep-info">
                                <div class="rep-name">${{rep.name}}</div>
                                <div class="rep-details">${{getPartyName(rep.party)}} • ${{districtLabel}} • ${{rep.billCount}} bills</div>
                            </div>
                        </div>
                    `;
                }});
            }}
            
            html += `</div></div>`;
            
            panel.innerHTML = html;
        }}
    </script>
</body>
</html>"""

def generate_html(output_file="congress_district_map.html"):
    """Generate the HTML file with congressional data from CSV files."""
    
    # Load data from CSV
    district_data = load_congress_data()
    
    if not district_data:
        print("ERROR: Failed to load congressional data from CSV")
        return
    
    # Load the district GeoJSON file
    json_path = Path('../data/cb_2024_us_cd119_20m.json')
    try:
        with open(json_path, 'r') as f:
            district_geojson = json.load(f)
        district_geojson_str = json.dumps(district_geojson)
        print(f'✓ Loaded district boundaries from {json_path}')
    except FileNotFoundError:
        print(f"ERROR: Could not find {json_path}")
        return
    except Exception as e:
        print(f"ERROR loading GeoJSON: {e}")
        return
    
    print(f'✓ Processed data for {len(district_data)} districts')
    
    # Convert to JSON
    district_data_json = json.dumps(district_data, indent=4)
    
    # Generate HTML
    html_content = html_template.format(
        district_data_json=district_data_json,
        district_geojson=district_geojson_str
    )
    
    output_path = f'../visualizations/{output_file}'
    
    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f'\n✓ Generated {output_path}')
    print(f'✓ Open the file in your browser to view the visualization')
    print(f'\nNote: The map loads congressional district boundaries from an external source.')
    print(f'      An internet connection is required to view the map.\n')

if __name__ == "__main__":
    generate_html()