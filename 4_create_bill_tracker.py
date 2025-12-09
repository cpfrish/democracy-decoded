#!/usr/bin/env python3
"""
Step 4: Create Bill Tracker Visualization
Generates interactive tracker status visualization from bills data
"""

import os
import sys
import pandas as pd
import json


def create_bill_tracker_visualization(csv_path: str = "data/congress_119_bills_2.csv"):
    """
    Create interactive bill tracker visualization showing status breakdown.
    
    Args:
        csv_path: Path to bills CSV file
    """
    
    # Load bills data
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        print(f"ERROR: {csv_path} not found")
        print("Run: python scripts/congress_bill_fetcher_bulk.py first")
        sys.exit(1)
    
    print(f"Loaded {len(df)} bills from {csv_path}")
    
    # Fill empty policy areas with "Uncategorized"
    df['policy_area'] = df['policy_area'].fillna('Uncategorized')
    df['policy_area'] = df['policy_area'].replace('', 'Uncategorized')
    
    # Calculate tracker status counts
    tracker_counts = df['tracker_status'].value_counts().to_dict()
    
    # Calculate by bill type
    bill_type_counts = df.groupby(['bill_type', 'tracker_status']).size().reset_index(name='count')
    
    # Calculate by policy area (top 20, excluding Uncategorized)
    policy_counts = df[df['policy_area'] != 'Uncategorized']['policy_area'].value_counts().head(20).to_dict()
    
    # Prepare data for visualization
    bills_json = df.to_json(orient='records')
    tracker_counts_json = json.dumps(tracker_counts)
    policy_counts_json = json.dumps(policy_counts)
    
    # Color scheme for tracker statuses
    status_colors = {
        'Introduced': '#94a3b8',
        'Passed House': '#3b82f6',
        'Passed Senate': '#8b5cf6',
        'Resolved': '#10b981',
        'To President': '#f59e0b',
        'Became Law': '#22c55e',
        'Failed': '#ef4444'
    }
    
    # Bill type colors
    bill_type_colors = {
        'HR': '#3b82f6',
        'S': '#8b5cf6',
        'HJRES': '#06b6d4',
        'SJRES': '#a855f7',
        'HCONRES': '#14b8a6',
        'SCONRES': '#d946ef',
        'HRES': '#0ea5e9',
        'SRES': '#c026d3'
    }
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Congressional Bills Tracker - 119th Congress</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        
        #container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        
        header {{
            background: linear-gradient(135deg, #1e3a8a 0%, #312e81 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 700;
        }}
        
        .subtitle {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8fafc;
            border-bottom: 2px solid #e2e8f0;
        }}
        
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        
        .stat-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}
        
        .stat-number {{
            font-size: 2.5em;
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 5px;
        }}
        
        .stat-label {{
            font-size: 0.9em;
            color: #64748b;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .charts-container {{
            padding: 40px;
        }}
        
        .chart-section {{
            margin-bottom: 60px;
        }}
        
        .chart-title {{
            font-size: 1.5em;
            font-weight: 600;
            color: #1e293b;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #e2e8f0;
        }}
        
        .chart {{
            background: white;
            border-radius: 8px;
            padding: 20px;
        }}
        
        .bar {{
            transition: all 0.3s;
            cursor: pointer;
        }}
        
        .bar:hover {{
            opacity: 0.8;
        }}
        
        .axis text {{
            font-size: 12px;
            fill: #475569;
        }}
        
        .axis-label {{
            font-size: 13px;
            font-weight: 600;
            fill: #334155;
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
            font-size: 13px;
            line-height: 1.5;
            max-width: 300px;
            z-index: 1000;
        }}
        
        .tooltip.show {{
            opacity: 1;
        }}
        
        .tooltip-title {{
            font-weight: 700;
            margin-bottom: 8px;
            font-size: 14px;
            border-bottom: 1px solid rgba(255,255,255,0.3);
            padding-bottom: 4px;
        }}
        
        .bills-table {{
            margin-top: 40px;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        .table-controls {{
            padding: 20px;
            background: #f8fafc;
            border-bottom: 2px solid #e2e8f0;
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            align-items: center;
        }}
        
        .table-controls label {{
            font-weight: 600;
            color: #475569;
        }}
        
        .table-controls select,
        .table-controls input {{
            padding: 8px 12px;
            border: 1px solid #cbd5e1;
            border-radius: 6px;
            font-size: 14px;
            background: white;
        }}
        
        .table-controls input {{
            flex: 1;
            min-width: 200px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        thead {{
            background: #1e293b;
            color: white;
        }}
        
        th {{
            padding: 15px;
            text-align: left;
            font-weight: 600;
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        td {{
            padding: 12px 15px;
            border-bottom: 1px solid #e2e8f0;
            font-size: 14px;
        }}
        
        tbody tr.bill-row {{
            cursor: pointer;
            transition: background-color 0.2s;
        }}
        
        tbody tr.bill-row:hover {{
            background: #f8fafc;
        }}
        
        tbody tr.bill-row.expanded {{
            background: #eff6ff;
        }}
        
        .expand-icon {{
            display: inline-block;
            margin-right: 8px;
            transition: transform 0.2s;
            font-weight: bold;
            color: #3b82f6;
        }}
        
        .expanded .expand-icon {{
            transform: rotate(90deg);
        }}
        
        .expanded-content {{
            display: none;
            padding: 20px;
            background: #f8fafc;
            border-left: 4px solid #3b82f6;
            margin: 10px 15px;
            border-radius: 6px;
        }}
        
        .expanded-content.show {{
            display: block;
        }}
        
        .expanded-section {{
            margin-bottom: 15px;
        }}
        
        .expanded-section:last-child {{
            margin-bottom: 0;
        }}
        
        .expanded-label {{
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 5px;
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .expanded-text {{
            color: #475569;
            line-height: 1.6;
            font-size: 14px;
        }}
        
        .status-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .bill-link {{
            color: #3b82f6;
            text-decoration: none;
            font-weight: 600;
        }}
        
        .bill-link:hover {{
            text-decoration: underline;
        }}
        
        .bill-type-legend {{
            margin-top: 25px;
            padding: 20px;
            background: #f8fafc;
            border-radius: 8px;
            border-left: 4px solid #3b82f6;
        }}
        
        .legend-title {{
            font-size: 14px;
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .legend-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 12px;
        }}
        
        .legend-item {{
            display: flex;
            align-items: flex-start;
            gap: 8px;
        }}
        
        .legend-color {{
            width: 16px;
            height: 16px;
            border-radius: 3px;
            flex-shrink: 0;
            margin-top: 2px;
        }}
        
        .legend-content {{
            flex: 1;
        }}
        
        .legend-type {{
            font-weight: 700;
            font-size: 13px;
            color: #1e293b;
            margin-bottom: 2px;
        }}
        
        .legend-description {{
            font-size: 12px;
            color: #64748b;
            line-height: 1.4;
        }}
        
        .legend {{
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            margin-top: 15px;
            padding: 15px;
            background: #f8fafc;
            border-radius: 6px;
        }}
        
        .truncated {{
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            max-width: 300px;
        }}
    </style>
</head>
<body>
    <div id="container">
        <header>
            <h1>📊 Congressional Bills Tracker</h1>
            <div class="subtitle">119th United States Congress (2025-2027)</div>
        </header>
        
        <div class="stats-grid" id="stats-grid">
            <!-- Stats will be populated by JavaScript -->
        </div>
        
        <div class="charts-container">
            <div class="chart-section">
                <div class="chart-title">Bills by Tracker Status</div>
                <div id="status-chart" class="chart"></div>
            </div>
            
            <div class="chart-section">
                <div class="chart-title">Bills by Type</div>
                <div id="type-chart" class="chart"></div>
                <div class="bill-type-legend">
                    <div class="legend-title">Bill Type Definitions</div>
                    <div class="legend-grid">
                        <div class="legend-item">
                            <div class="legend-color" style="background-color: #3b82f6;"></div>
                            <div class="legend-content">
                                <div class="legend-type">HR</div>
                                <div class="legend-description">House Bill - Legislation originating in the House of Representatives</div>
                            </div>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color" style="background-color: #8b5cf6;"></div>
                            <div class="legend-content">
                                <div class="legend-type">S</div>
                                <div class="legend-description">Senate Bill - Legislation originating in the Senate</div>
                            </div>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color" style="background-color: #06b6d4;"></div>
                            <div class="legend-content">
                                <div class="legend-type">HJRES</div>
                                <div class="legend-description">House Joint Resolution - Proposes amendments to Constitution or deals with limited matters</div>
                            </div>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color" style="background-color: #14b8a6;"></div>
                            <div class="legend-content">
                                <div class="legend-type">SJRES</div>
                                <div class="legend-description">Senate Joint Resolution - Similar to HJRES but originates in Senate</div>
                            </div>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color" style="background-color: #f59e0b;"></div>
                            <div class="legend-content">
                                <div class="legend-type">HCONRES</div>
                                <div class="legend-description">House Concurrent Resolution - Matters affecting both chambers, no force of law</div>
                            </div>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color" style="background-color: #f97316;"></div>
                            <div class="legend-content">
                                <div class="legend-type">SCONRES</div>
                                <div class="legend-description">Senate Concurrent Resolution - Similar to HCONRES but originates in Senate</div>
                            </div>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color" style="background-color: #10b981;"></div>
                            <div class="legend-content">
                                <div class="legend-type">HRES</div>
                                <div class="legend-description">House Simple Resolution - Matters concerning House only, no force of law</div>
                            </div>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color" style="background-color: #22c55e;"></div>
                            <div class="legend-content">
                                <div class="legend-type">SRES</div>
                                <div class="legend-description">Senate Simple Resolution - Matters concerning Senate only, no force of law</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="chart-section">
                <div class="chart-title">Top 20 Policy Areas</div>
                <div id="policy-chart" class="chart"></div>
            </div>
            
            <div class="chart-section">
                <div class="chart-title">All Bills <span style="font-size: 0.7em; color: #64748b; font-weight: normal;">(Click rows to expand)</span></div>
                <div class="bills-table">
                    <div class="table-controls">
                        <label for="status-filter">Status:</label>
                        <select id="status-filter">
                            <option value="">All Statuses</option>
                        </select>
                        
                        <label for="type-filter">Type:</label>
                        <select id="type-filter">
                            <option value="">All Types</option>
                        </select>
                        
                        <input type="text" id="search-input" placeholder="Search bills by title, sponsor, or policy area...">
                    </div>
                    <div style="overflow-x: auto;">
                        <table id="bills-table">
                            <thead>
                                <tr>
                                    <th>Bill</th>
                                    <th>Title</th>
                                    <th>Status</th>
                                    <th>Sponsor</th>
                                    <th>Policy Area</th>
                                    <th>Latest Action</th>
                                </tr>
                            </thead>
                            <tbody id="table-body">
                                <!-- Table rows will be populated by JavaScript -->
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="tooltip" id="tooltip"></div>
    
    <script>
        // Data
        const billsData = {bills_json};
        const trackerCounts = {tracker_counts_json};
        const policyCounts = {policy_counts_json};
        
        const statusColors = {json.dumps(status_colors)};
        const billTypeColors = {json.dumps(bill_type_colors)};
        
        // Populate stats grid
        function populateStats() {{
            const statsGrid = document.getElementById('stats-grid');
            
            const totalBills = billsData.length;
            const becameLaw = billsData.filter(b => b.tracker_status === 'Became Law').length;
            const passedHouse = billsData.filter(b => b.tracker_status === 'Passed House').length;
            const passedSenate = billsData.filter(b => b.tracker_status === 'Passed Senate').length;
            const toPresident = billsData.filter(b => b.tracker_status === 'To President').length;
            const failed = billsData.filter(b => b.tracker_status === 'Failed').length;
            
            const stats = [
                {{ label: 'Total Bills', value: totalBills, color: '#3b82f6' }},
                {{ label: 'Became Law', value: becameLaw, color: '#22c55e' }},
                {{ label: 'Passed House', value: passedHouse, color: '#3b82f6' }},
                {{ label: 'Passed Senate', value: passedSenate, color: '#8b5cf6' }},
                {{ label: 'To President', value: toPresident, color: '#f59e0b' }},
                {{ label: 'Failed', value: failed, color: '#ef4444' }}
            ];
            
            stats.forEach(stat => {{
                const card = document.createElement('div');
                card.className = 'stat-card';
                card.innerHTML = `
                    <div class="stat-number" style="color: ${{stat.color}}">${{stat.value.toLocaleString()}}</div>
                    <div class="stat-label">${{stat.label}}</div>
                `;
                statsGrid.appendChild(card);
            }});
        }}
        
        // Create tracker status chart
        function createStatusChart() {{
            const data = Object.entries(trackerCounts).map(([status, count]) => ({{
                status, count
            }}));
            
            data.sort((a, b) => b.count - a.count);
            
            const margin = {{top: 20, right: 30, bottom: 60, left: 100}};
            const width = 800 - margin.left - margin.right;
            const height = 400 - margin.top - margin.bottom;
            
            const svg = d3.select('#status-chart')
                .append('svg')
                .attr('width', width + margin.left + margin.right)
                .attr('height', height + margin.top + margin.bottom)
                .append('g')
                .attr('transform', `translate(${{margin.left}},${{margin.top}})`);
            
            const x = d3.scaleLinear()
                .domain([0, d3.max(data, d => d.count)])
                .range([0, width]);
            
            const y = d3.scaleBand()
                .domain(data.map(d => d.status))
                .range([0, height])
                .padding(0.2);
            
            // Bars
            svg.selectAll('.bar')
                .data(data)
                .enter()
                .append('rect')
                .attr('class', 'bar')
                .attr('x', 0)
                .attr('y', d => y(d.status))
                .attr('width', d => x(d.count))
                .attr('height', y.bandwidth())
                .attr('fill', d => statusColors[d.status] || '#94a3b8')
                .on('mouseover', function(event, d) {{
                    showTooltip(event, `
                        <div class="tooltip-title">${{d.status}}</div>
                        <div>Count: <strong>${{d.count.toLocaleString()}}</strong></div>
                        <div>Percentage: <strong>${{(d.count / billsData.length * 100).toFixed(1)}}%</strong></div>
                    `);
                }})
                .on('mouseout', hideTooltip);
            
            // Value labels
            svg.selectAll('.value-label')
                .data(data)
                .enter()
                .append('text')
                .attr('x', d => x(d.count) + 5)
                .attr('y', d => y(d.status) + y.bandwidth() / 2)
                .attr('dy', '0.35em')
                .attr('font-size', '12px')
                .attr('font-weight', 'bold')
                .attr('fill', '#1e293b')
                .text(d => d.count.toLocaleString());
            
            // Axes
            svg.append('g')
                .attr('transform', `translate(0,${{height}})`)
                .call(d3.axisBottom(x).ticks(5).tickFormat(d => d.toLocaleString()))
                .attr('class', 'axis');
            
            svg.append('g')
                .call(d3.axisLeft(y))
                .attr('class', 'axis');
        }}
        
        // Create bill type chart
        function createTypeChart() {{
            const typeCounts = {{}};
            billsData.forEach(bill => {{
                const type = bill.bill_type;
                typeCounts[type] = (typeCounts[type] || 0) + 1;
            }});
            
            const data = Object.entries(typeCounts).map(([type, count]) => ({{
                type, count
            }}));
            
            data.sort((a, b) => b.count - a.count);
            
            const margin = {{top: 20, right: 30, bottom: 60, left: 80}};
            const width = 800 - margin.left - margin.right;
            const height = 400 - margin.top - margin.bottom;
            
            const svg = d3.select('#type-chart')
                .append('svg')
                .attr('width', width + margin.left + margin.right)
                .attr('height', height + margin.top + margin.bottom)
                .append('g')
                .attr('transform', `translate(${{margin.left}},${{margin.top}})`);
            
            const x = d3.scaleBand()
                .domain(data.map(d => d.type))
                .range([0, width])
                .padding(0.3);
            
            const y = d3.scaleLinear()
                .domain([0, d3.max(data, d => d.count)])
                .range([height, 0]);
            
            // Bars
            svg.selectAll('.bar')
                .data(data)
                .enter()
                .append('rect')
                .attr('class', 'bar')
                .attr('x', d => x(d.type))
                .attr('y', d => y(d.count))
                .attr('width', x.bandwidth())
                .attr('height', d => height - y(d.count))
                .attr('fill', d => billTypeColors[d.type] || '#3b82f6')
                .on('mouseover', function(event, d) {{
                    showTooltip(event, `
                        <div class="tooltip-title">${{d.type}}</div>
                        <div>Count: <strong>${{d.count.toLocaleString()}}</strong></div>
                        <div>Percentage: <strong>${{(d.count / billsData.length * 100).toFixed(1)}}%</strong></div>
                    `);
                }})
                .on('mouseout', hideTooltip);
            
            // Value labels
            svg.selectAll('.value-label')
                .data(data)
                .enter()
                .append('text')
                .attr('x', d => x(d.type) + x.bandwidth() / 2)
                .attr('y', d => y(d.count) - 5)
                .attr('text-anchor', 'middle')
                .attr('font-size', '12px')
                .attr('font-weight', 'bold')
                .attr('fill', '#1e293b')
                .text(d => d.count.toLocaleString());
            
            // Axes
            svg.append('g')
                .attr('transform', `translate(0,${{height}})`)
                .call(d3.axisBottom(x))
                .attr('class', 'axis');
            
            svg.append('g')
                .call(d3.axisLeft(y).ticks(5).tickFormat(d => d.toLocaleString()))
                .attr('class', 'axis');
        }}
        
        // Create policy area chart
        function createPolicyChart() {{
            const data = Object.entries(policyCounts).map(([policy, count]) => ({{
                policy: policy || 'Unknown',
                count
            }}));
            
            const margin = {{top: 20, right: 30, bottom: 60, left: 250}};
            const width = 900 - margin.left - margin.right;
            const height = 600 - margin.top - margin.bottom;
            
            const svg = d3.select('#policy-chart')
                .append('svg')
                .attr('width', width + margin.left + margin.right)
                .attr('height', height + margin.top + margin.bottom)
                .append('g')
                .attr('transform', `translate(${{margin.left}},${{margin.top}})`);
            
            const x = d3.scaleLinear()
                .domain([0, d3.max(data, d => d.count)])
                .range([0, width]);
            
            const y = d3.scaleBand()
                .domain(data.map(d => d.policy))
                .range([0, height])
                .padding(0.2);
            
            const colorScale = d3.scaleSequential()
                .domain([0, d3.max(data, d => d.count)])
                .interpolator(d3.interpolateBlues);
            
            // Bars
            svg.selectAll('.bar')
                .data(data)
                .enter()
                .append('rect')
                .attr('class', 'bar')
                .attr('x', 0)
                .attr('y', d => y(d.policy))
                .attr('width', d => x(d.count))
                .attr('height', y.bandwidth())
                .attr('fill', d => colorScale(d.count))
                .on('mouseover', function(event, d) {{
                    showTooltip(event, `
                        <div class="tooltip-title">${{d.policy}}</div>
                        <div>Count: <strong>${{d.count.toLocaleString()}}</strong></div>
                    `);
                }})
                .on('mouseout', hideTooltip);
            
            // Value labels
            svg.selectAll('.value-label')
                .data(data)
                .enter()
                .append('text')
                .attr('x', d => x(d.count) + 5)
                .attr('y', d => y(d.policy) + y.bandwidth() / 2)
                .attr('dy', '0.35em')
                .attr('font-size', '11px')
                .attr('font-weight', 'bold')
                .attr('fill', '#1e293b')
                .text(d => d.count.toLocaleString());
            
            // Axes
            svg.append('g')
                .attr('transform', `translate(0,${{height}})`)
                .call(d3.axisBottom(x).ticks(5).tickFormat(d => d.toLocaleString()))
                .attr('class', 'axis');
            
            svg.append('g')
                .call(d3.axisLeft(y))
                .attr('class', 'axis')
                .selectAll('text')
                .attr('font-size', '11px');
        }}
        
        // Populate bills table
        function populateTable(filteredData = billsData) {{
            const tbody = document.getElementById('table-body');
            tbody.innerHTML = '';
            
            filteredData.slice(0, 100).forEach((bill, index) => {{
                const statusColor = statusColors[bill.tracker_status] || '#94a3b8';
                const billId = `bill-${{index}}`;
                
                // Main row
                const row = document.createElement('tr');
                row.className = 'bill-row';
                row.setAttribute('data-bill-id', billId);
                
                row.innerHTML = `
                    <td><span class="expand-icon">▶</span><a href="${{bill.congress_url}}" target="_blank" class="bill-link" onclick="event.stopPropagation()">${{bill.bill_id}}</a></td>
                    <td><div class="truncated">${{bill.title}}</div></td>
                    <td><span class="status-badge" style="background: ${{statusColor}}; color: white;">${{bill.tracker_status}}</span></td>
                    <td>${{bill.sponsor || 'N/A'}}</td>
                    <td>${{bill.policy_area || 'N/A'}}</td>
                    <td><div class="truncated" style="max-width: 250px; font-size: 12px;">${{bill.latest_action_text}}</div></td>
                `;
                
                row.addEventListener('click', function() {{
                    toggleRow(billId);
                }});
                
                tbody.appendChild(row);
                
                // Expanded content row
                const expandedRow = document.createElement('tr');
                expandedRow.setAttribute('data-expanded-for', billId);
                expandedRow.style.display = 'none';
                
                expandedRow.innerHTML = `
                    <td colspan="6">
                        <div class="expanded-content" id="expanded-${{billId}}">
                            <div class="expanded-section">
                                <div class="expanded-label">Full Title</div>
                                <div class="expanded-text">${{bill.title}}</div>
                            </div>
                            <div class="expanded-section">
                                <div class="expanded-label">Latest Action</div>
                                <div class="expanded-text">${{bill.latest_action_text}}</div>
                            </div>
                            <div class="expanded-section">
                                <div class="expanded-label">Latest Action Date</div>
                                <div class="expanded-text">${{bill.latest_action_date || 'N/A'}}</div>
                            </div>
                        </div>
                    </td>
                `;
                
                tbody.appendChild(expandedRow);
            }});
            
            if (filteredData.length > 100) {{
                const row = document.createElement('tr');
                row.innerHTML = `<td colspan="6" style="text-align: center; padding: 20px; color: #64748b;">Showing first 100 of ${{filteredData.length.toLocaleString()}} bills. Use filters to narrow results.</td>`;
                tbody.appendChild(row);
            }}
        }}
        
        // Toggle row expansion
        function toggleRow(billId) {{
            const mainRow = document.querySelector(`tr[data-bill-id="${{billId}}"]`);
            const expandedRow = document.querySelector(`tr[data-expanded-for="${{billId}}"]`);
            const expandedContent = document.getElementById(`expanded-${{billId}}`);
            
            if (mainRow.classList.contains('expanded')) {{
                mainRow.classList.remove('expanded');
                expandedRow.style.display = 'none';
                expandedContent.classList.remove('show');
            }} else {{
                mainRow.classList.add('expanded');
                expandedRow.style.display = 'table-row';
                expandedContent.classList.add('show');
            }}
        }}
        
        // Populate filter dropdowns
        function populateFilters() {{
            const statusFilter = document.getElementById('status-filter');
            const typeFilter = document.getElementById('type-filter');
            
            // Status options
            Object.keys(trackerCounts).sort().forEach(status => {{
                const option = document.createElement('option');
                option.value = status;
                option.textContent = status;
                statusFilter.appendChild(option);
            }});
            
            // Type options
            const types = [...new Set(billsData.map(b => b.bill_type))].sort();
            types.forEach(type => {{
                const option = document.createElement('option');
                option.value = type;
                option.textContent = type;
                typeFilter.appendChild(option);
            }});
        }}
        
        // Filter table
        function filterTable() {{
            const statusFilter = document.getElementById('status-filter').value;
            const typeFilter = document.getElementById('type-filter').value;
            const searchInput = document.getElementById('search-input').value.toLowerCase();
            
            let filtered = billsData;
            
            if (statusFilter) {{
                filtered = filtered.filter(b => b.tracker_status === statusFilter);
            }}
            
            if (typeFilter) {{
                filtered = filtered.filter(b => b.bill_type === typeFilter);
            }}
            
            if (searchInput) {{
                filtered = filtered.filter(b => 
                    b.title.toLowerCase().includes(searchInput) ||
                    (b.sponsor && b.sponsor.toLowerCase().includes(searchInput)) ||
                    (b.policy_area && b.policy_area.toLowerCase().includes(searchInput))
                );
            }}
            
            populateTable(filtered);
        }}
        
        // Tooltip functions
        function showTooltip(event, content) {{
            const tooltip = document.getElementById('tooltip');
            tooltip.innerHTML = content;
            tooltip.className = 'tooltip show';
            tooltip.style.left = event.pageX + 10 + 'px';
            tooltip.style.top = event.pageY - 10 + 'px';
        }}
        
        function hideTooltip() {{
            document.getElementById('tooltip').className = 'tooltip';
        }}
        
        // Initialize
        populateStats();
        createStatusChart();
        createTypeChart();
        createPolicyChart();
        populateFilters();
        populateTable();
        
        // Event listeners
        document.getElementById('status-filter').addEventListener('change', filterTable);
        document.getElementById('type-filter').addEventListener('change', filterTable);
        document.getElementById('search-input').addEventListener('input', filterTable);
    </script>
</body>
</html>"""
    
    # Save visualization
    output_path = 'visualizations/congress_bill_tracker.html'
    os.makedirs('visualizations', exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✓ Saved visualization to {output_path}")
    print()
    print("Open the file in your browser to view the interactive tracker!")


def main():
    """Main execution function"""
    
    print("=" * 70)
    print("Creating Bill Tracker Visualization")
    print("=" * 70)
    print()
    
    create_bill_tracker_visualization()
    
    print()
    print("=" * 70)
    print("✓ Visualization complete!")
    print("=" * 70)
    

if __name__ == "__main__":
    main()
