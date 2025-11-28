"""
Altair Visualization Generator for API-based data
Creates standalone HTML charts that load from Vercel endpoints
"""

import altair as alt
import json


def create_generation_overview_chart(api_url):
    """
    Create generation overview bar chart that loads from API.
    
    Args:
        api_url: URL of your Vercel API endpoint (e.g., https://your-app.vercel.app/api/congress-data)
    
    Returns:
        Altair chart configured to load from API
    """
    
    # Create data source from API with transformation
    data_source = alt.Data(
        url=api_url,
        format=alt.DataFormat(property='data.summary', type='json')
    )
    
    chart = alt.Chart(data_source).mark_bar().encode(
        x=alt.X('generation:N', 
                sort=alt.EncodingSortField(field='member_count', op='sum', order='descending'),
                title='Generation'),
        y=alt.Y('member_count:Q', title='Number of Members'),
        color=alt.Color('generation:N', 
                       scale=alt.Scale(scheme='category10'),
                       legend=alt.Legend(title='Generation')),
        tooltip=[
            alt.Tooltip('generation:N', title='Generation'),
            alt.Tooltip('member_count:Q', title='Members'),
            alt.Tooltip('total_bills:Q', title='Total Bills'),
            alt.Tooltip('avg_bills_per_member:Q', title='Avg Bills/Member')
        ]
    ).properties(
        title='Congressional Members by Generation',
        width=500,
        height=350
    ).configure_axis(
        labelFontSize=12,
        titleFontSize=14,
        grid=False
    )
    
    return chart


def create_party_distribution_chart(api_url):
    """
    Create party distribution chart grouped by generation.
    Loads from API and aggregates on client side.
    """
    
    data_source = alt.Data(
        url=api_url,
        format=alt.DataFormat(property='data.members', type='json')
    )
    
    # Map party codes to full names
    chart = alt.Chart(data_source).transform_filter(
        alt.datum.generation != 'Unknown'
    ).transform_aggregate(
        count='count()',
        groupby=['generation', 'party']
    ).transform_calculate(
        party_full="datum.party == 'D' ? 'Democrat' : datum.party == 'R' ? 'Republican' : datum.party == 'I' ? 'Independent' : 'Other'"
    ).mark_bar(size=40).encode(
        y=alt.Y('generation:N', 
                sort=alt.EncodingSortField(field='count', op='sum', order='descending'),
                axis=alt.Axis(labelAngle=0),
                title='Generation'),
        x=alt.X('count:Q', title='Number of Members'),
        color=alt.Color('party_full:N',
                       scale=alt.Scale(
                           domain=['Democrat', 'Republican', 'Independent', 'Other'],
                           range=['#2E86AB', '#C23B22', '#9966CC', '#888888']
                       ),
                       legend=alt.Legend(title='Political Party')),
        tooltip=['generation:N', 'party_full:N', 'count:Q']
    ).properties(
        title='Congressional Members by Generation and Party',
        width=500,
        height=350
    ).configure_axis(
        labelFontSize=12,
        titleFontSize=14,
        grid=False
    )
    
    return chart


def create_member_activity_scatter(api_url):
    """
    Create scatter plot of member activity by birth year.
    Loads directly from member photos API.
    """
    
    data_source = alt.Data(
        url=api_url,
        format=alt.DataFormat(property='data', type='json')
    )
    
    chart = alt.Chart(data_source).mark_circle(
        opacity=0.8,
        stroke='white',
        strokeWidth=1.5
    ).transform_filter(
        alt.datum.generation != 'Unknown'
    ).encode(
        x=alt.X('birth_year:Q',
               title='Birth Year',
               scale=alt.Scale(domain=[1935, 2005]),
               axis=alt.Axis(format='d')),
        y=alt.Y('bill_count:Q',
               title='Number of Bills Sponsored',
               scale=alt.Scale(type='sqrt')),
        color=alt.Color('party:N',
                       scale=alt.Scale(
                           domain=['D', 'R', 'I'],
                           range=['#2E86AB', '#C23B22', '#9966CC']
                       ),
                       legend=alt.Legend(title='Political Party')),
        size=alt.Size('bill_count:Q',
                     scale=alt.Scale(range=[50, 300], type='sqrt'),
                     legend=alt.Legend(title='Bills Sponsored')),
        tooltip=[
            alt.Tooltip('name:N', title='Representative'),
            alt.Tooltip('party:N', title='Party'),
            alt.Tooltip('generation:N', title='Generation'),
            alt.Tooltip('birth_year:Q', title='Birth Year'),
            alt.Tooltip('bill_count:Q', title='Bills Sponsored'),
            alt.Tooltip('photo_url:N', title='Photo')
        ]
    ).properties(
        title=alt.TitleParams(
            text='Congressional Members: Legislative Activity by Birth Year',
            subtitle='Circle size represents bills sponsored. Data updates hourly.',
            fontSize=16,
            subtitleFontSize=12
        ),
        width=700,
        height=500
    ).configure_axis(
        labelFontSize=11,
        titleFontSize=13,
        grid=True,
        gridOpacity=0.3
    ).interactive()
    
    return chart


def create_topic_heatmap(api_url):
    """
    Create topic focus heatmap by generation.
    Note: Requires detailed_analysis=true API parameter.
    """
    
    data_source = alt.Data(
        url=f"{api_url}?detailed=true",
        format=alt.DataFormat(property='data.topics', type='json')
    )
    
    chart = alt.Chart(data_source).transform_aggregate(
        total_count='sum(count)',
        groupby=['generation', 'topic']
    ).transform_joinaggregate(
        generation_total='sum(total_count)',
        groupby=['generation']
    ).transform_calculate(
        proportion='datum.total_count / datum.generation_total'
    ).mark_rect().encode(
        x=alt.X('topic:N', title='Topic Area'),
        y=alt.Y('generation:N', title='Generation'),
        color=alt.Color('proportion:Q',
                       scale=alt.Scale(scheme='blues'),
                       title='Proportion of Bills'),
        stroke=alt.value('white'),
        strokeWidth=alt.value(2),
        tooltip=[
            'generation:N',
            'topic:N',
            alt.Tooltip('total_count:Q', title='Count'),
            alt.Tooltip('proportion:Q', format='.2%', title='Proportion')
        ]
    ).properties(
        title='Topic Focus by Generation (Proportion of Bills)',
        width=600,
        height=300
    )
    
    return chart


def generate_all_charts(api_base_url, output_dir='visualizations'):
    """
    Generate all charts and save as standalone HTML files.
    
    Args:
        api_base_url: Base URL for your Vercel deployment (e.g., https://your-app.vercel.app)
        output_dir: Directory to save HTML files
    """
    import os
    
    os.makedirs(output_dir, exist_ok=True)
    
    congress_api = f"{api_base_url}/api/congress-data"
    photos_api = f"{api_base_url}/api/member-photos"
    
    # Generate charts
    charts = {
        'generation_overview': create_generation_overview_chart(congress_api),
        'party_distribution': create_party_distribution_chart(congress_api),
        'member_activity': create_member_activity_scatter(photos_api),
        'topic_heatmap': create_topic_heatmap(congress_api)
    }
    
    # Save each chart
    for name, chart in charts.items():
        filepath = os.path.join(output_dir, f'{name}.html')
        chart.save(filepath)
        print(f"✅ Saved {filepath}")
    
    print(f"\n🎉 All charts generated in {output_dir}/")
    print(f"📊 These charts load live data from: {api_base_url}")
    print(f"💡 Embed in WordPress using iframe:")
    print(f'   <iframe src="https://your-github-pages.io/{output_dir}/{name}.html" width="800" height="600"></iframe>')


if __name__ == '__main__':
    # Example usage - update with your actual Vercel URL after deployment
    API_BASE_URL = "https://your-app-name.vercel.app"
    
    print("⚠️  Update API_BASE_URL with your actual Vercel deployment URL")
    print(f"Current URL: {API_BASE_URL}\n")
    
    # Uncomment after deploying to Vercel:
    # generate_all_charts(API_BASE_URL)
