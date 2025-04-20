import os
import sys
import json
import requests
import numpy as np
from datetime import datetime
import calendar

# Configuration
GITHUB_USERNAME = os.environ.get('GITHUB_USERNAME', 'K-B-R-S-W')  # Default value for testing
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
OUTPUT_DIR = 'dist'

# Create output directory if it doesn't exist
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def get_contributions():
    """Fetch GitHub contribution data for the user"""
    headers = {}
    if GITHUB_TOKEN:
        headers['Authorization'] = f'token {GITHUB_TOKEN}'
    
    # Use GitHub GraphQL API to fetch contribution data
    query = """
    query($username: String!) {
      user(login: $username) {
        contributionsCollection {
          contributionCalendar {
            weeks {
              contributionDays {
                date
                contributionCount
              }
            }
          }
        }
      }
    }
    """
    
    variables = {
        "username": GITHUB_USERNAME
    }
    
    url = 'https://api.github.com/graphql'
    r = requests.post(url, json={"query": query, "variables": variables}, headers=headers)
    
    if r.status_code != 200:
        print(f"Error fetching contribution data: {r.status_code}")
        print(r.text)
        sys.exit(1)
    
    result = r.json()
    
    # Parse contribution data
    contributions = []
    weeks = result['data']['user']['contributionsCollection']['contributionCalendar']['weeks']
    for week in weeks:
        for day in week['contributionDays']:
            contributions.append({
                'date': day['date'],
                'count': day['contributionCount']
            })
    
    return contributions

def group_contributions_by_month(contributions, recent_months=6):
    """Group contributions by month for the last N months"""
    # Sort contributions by date
    contributions.sort(key=lambda x: x['date'])
    
    # Group by month
    monthly_contribs = {}
    for contrib in contributions:
        date = datetime.strptime(contrib['date'], '%Y-%m-%d')
        month_key = f"{date.year}-{date.month:02d}"
        
        if month_key not in monthly_contribs:
            monthly_contribs[month_key] = {
                'year': date.year,
                'month': date.month,
                'name': calendar.month_name[date.month],
                'count': 0
            }
        
        monthly_contribs[month_key]['count'] += contrib['count']
    
    # Get the last N months
    sorted_months = sorted(monthly_contribs.items(), key=lambda x: f"{x[1]['year']}-{x[1]['month']:02d}")
    recent_data = sorted_months[-recent_months:] if len(sorted_months) > recent_months else sorted_months
    
    return [item[1] for item in recent_data]

def create_contribution_graph(contributions, output_path):
    """Create a dynamic bar graph SVG of GitHub contributions"""
    # Get monthly contributions
    monthly_data = group_contributions_by_month(contributions)
    
    # SVG dimensions
    width = 800
    height = 400
    padding = 50
    graph_width = width - (padding * 2)
    graph_height = height - (padding * 2)
    
    # Calculate max value for scaling
    max_count = max([month['count'] for month in monthly_data]) if monthly_data else 1
    # Ensure minimum scale
    max_count = max(max_count, 10)
    
    # Calculate bar width based on number of months
    bar_width = graph_width / len(monthly_data) if monthly_data else graph_width
    bar_padding = bar_width * 0.2  # 20% padding between bars
    bar_width = bar_width - bar_padding
    
    # Generate SVG
    svg_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
    <!-- Background -->
    <rect width="{width}" height="{height}" fill="#0d1117"/>
    
    <!-- Title -->
    <text x="{width/2}" y="30" font-family="Arial, sans-serif" font-size="20" font-weight="bold" fill="#ffffff" text-anchor="middle">
        @{GITHUB_USERNAME}'s Contribution Activity
    </text>
    
    <!-- Y-axis -->
    <line x1="{padding}" y1="{padding}" x2="{padding}" y2="{height-padding}" stroke="#555" stroke-width="1"/>
    
    <!-- X-axis -->
    <line x1="{padding}" y1="{height-padding}" x2="{width-padding}" y2="{height-padding}" stroke="#555" stroke-width="1"/>
    
    <!-- Y-axis labels -->
    <text x="{padding-10}" y="{padding}" font-family="Arial, sans-serif" font-size="12" fill="#888" text-anchor="end">{max_count}</text>
    <text x="{padding-10}" y="{padding+graph_height/2}" font-family="Arial, sans-serif" font-size="12" fill="#888" text-anchor="end">{int(max_count/2)}</text>
    <text x="{padding-10}" y="{height-padding}" font-family="Arial, sans-serif" font-size="12" fill="#888" text-anchor="end">0</text>
    
    <!-- Horizontal grid lines -->
    <line x1="{padding}" y1="{padding}" x2="{width-padding}" y2="{padding}" stroke="#333" stroke-width="1" stroke-dasharray="5,5"/>
    <line x1="{padding}" y1="{padding+graph_height/2}" x2="{width-padding}" y2="{padding+graph_height/2}" stroke="#333" stroke-width="1" stroke-dasharray="5,5"/>
    <line x1="{padding}" y1="{height-padding}" x2="{width-padding}" y2="{height-padding}" stroke="#333" stroke-width="1"/>
    
    <!-- Bars with animations -->"""
    
    # Add bars for each month
    for i, month in enumerate(monthly_data):
        # Calculate bar position and height
        bar_height = (month['count'] / max_count) * graph_height
        bar_x = padding + (i * (bar_width + bar_padding))
        bar_y = height - padding - bar_height
        
        # Calculate color based on contribution count (green intensity)
        intensity = min(0.5 + (month['count'] / max_count) * 0.5, 1.0)
        color = f"rgb(0, {int(100 + intensity * 155)}, 0)"
        
        # Add bar with grow animation
        svg_content += f"""
    <rect x="{bar_x}" y="{height-padding}" width="{bar_width}" height="0" fill="{color}">
        <animate attributeName="height" from="0" to="{bar_height}" dur="1s" begin="0s" fill="freeze" />
        <animate attributeName="y" from="{height-padding}" to="{bar_y}" dur="1s" begin="0s" fill="freeze" />
    </rect>"""
        
        # Add month label
        svg_content += f"""
    <text x="{bar_x + bar_width/2}" y="{height-padding+20}" font-family="Arial, sans-serif" font-size="12" fill="#ffffff" text-anchor="middle">
        {month['name'][:3]}
    </text>
    <text x="{bar_x + bar_width/2}" y="{bar_y-10}" font-family="Arial, sans-serif" font-size="12" fill="#ffffff" text-anchor="middle" opacity="0">
        {month['count']}
        <animate attributeName="opacity" from="0" to="1" dur="1.5s" begin="1s" fill="freeze" />
    </text>"""
    
    # Add total count
    total_contributions = sum(month['count'] for month in monthly_data)
    svg_content += f"""
    <!-- Total count -->
    <text x="{width-padding}" y="{height-10}" font-family="Arial, sans-serif" font-size="14" fill="#aaaaaa" text-anchor="end">
        Total: {total_contributions} contributions in the last {len(monthly_data)} months
    </text>
    
    <!-- Generation date -->
    <text x="{width-padding}" y="20" font-family="Arial, sans-serif" font-size="10" fill="#666666" text-anchor="end">
        Generated: {datetime.now().strftime('%Y-%m-%d')}
    </text>
</svg>"""
    
    # Write the SVG file
    with open(output_path, 'w') as f:
        f.write(svg_content)

def create_dark_mode_version(input_path, output_path):
    """Create a dark mode version of the SVG"""
    with open(input_path, 'r') as f:
        svg_content = f.read()
    
    # Replace colors for dark mode
    dark_mode_svg = svg_content.replace('#0d1117', '#000000')  # Darker background
    dark_mode_svg = dark_mode_svg.replace('#333333', '#222222')  # Darker elements
    
    with open(output_path, 'w') as f:
        f.write(dark_mode_svg)

def main():
    """Main function to generate contribution visualization"""
    print(f"Generating contribution graph for GitHub user: {GITHUB_USERNAME}")
    
    # Get contribution data
    contributions = get_contributions()
    
    # Create animated bar graph SVG
    svg_path = os.path.join(OUTPUT_DIR, 'github-race-car.svg')
    create_contribution_graph(contributions, svg_path)
    
    # Create dark mode version
    dark_svg_path = os.path.join(OUTPUT_DIR, 'github-race-car-dark.svg')
    create_dark_mode_version(svg_path, dark_svg_path)
    
    print(f"Generated contribution graph at {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
