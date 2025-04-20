import os
import sys
import json
import requests
import numpy as np
from datetime import datetime

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

def create_animated_racetrack(contributions, output_path):
    """Create an animated race track SVG with car based on contribution data"""
    # Determine the dimensions
    width = 800
    height = 400
    
    # Calculate contribution stats
    recent_contributions = contributions[-364:] if len(contributions) > 364 else contributions
    total_contribs = sum(c['count'] for c in recent_contributions)
    
    # Track dimensions
    track_width = width - 100
    track_height = height - 100
    cx = width / 2
    cy = height / 2
    
    # Create SVG with SMIL animation
    svg_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
    <!-- Background -->
    <rect width="{width}" height="{height}" fill="#0d1117"/>
    
    <!-- Track -->
    <ellipse cx="{cx}" cy="{cy}" rx="{track_width/2}" ry="{track_height/2}" fill="#333333"/>
    <ellipse cx="{cx}" cy="{cy}" rx="{track_width/2 - 30}" ry="{track_height/2 - 30}" fill="#264026"/>
    
    <!-- Finish line -->
    <line x1="{cx + track_width/2 - 20}" y1="{cy - 15}" x2="{cx + track_width/2 - 20}" y2="{cy + 15}" stroke="#ffffff" stroke-width="4"/>
    
    <!-- Car with animation -->
    <g>
        <!-- Car body -->
        <rect width="30" height="15" rx="3" fill="#ff3300">
            <!-- Animation along elliptical path -->
            <animateTransform
                attributeName="transform"
                type="rotate"
                from="0 {cx} {cy}"
                to="360 {cx} {cy}"
                dur="8s"
                repeatCount="indefinite"/>
            <animateTransform
                attributeName="transform"
                type="translate"
                values="{cx + track_width/2 - 40},{cy}; {cx},{cy - track_height/2 + 40}; {cx - track_width/2 + 40},{cy}; {cx},{cy + track_height/2 - 40}; {cx + track_width/2 - 40},{cy}"
                dur="8s"
                repeatCount="indefinite"
                additive="sum"/>
        </rect>
    </g>
    
    <!-- Stats -->
    <text x="{cx}" y="{height-30}" fill="#ffffff" font-size="16px" text-anchor="middle">
        Total Contributions: {total_contribs}
    </text>
    
    <!-- Title -->
    <text x="{cx}" y="30" fill="#ffffff" font-size="18px" font-weight="bold" text-anchor="middle">
        @{GITHUB_USERNAME}'s Racing Contributions
    </text>
    
    <!-- Date -->
    <text x="{width-20}" y="{height-10}" fill="#aaaaaa" font-size="10px" text-anchor="end">
        Generated: {datetime.now().strftime("%Y-%m-%d")}
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
    dark_mode_svg = dark_mode_svg.replace('#333333', '#222222')  # Darker track
    dark_mode_svg = dark_mode_svg.replace('#264026', '#1a2a1a')  # Darker grass
    
    with open(output_path, 'w') as f:
        f.write(dark_mode_svg)

def main():
    """Main function to generate animated race car"""
    print(f"Generating animated race car for GitHub user: {GITHUB_USERNAME}")
    
    # Get contribution data
    contributions = get_contributions()
    
    # Create animated race track SVG
    svg_path = os.path.join(OUTPUT_DIR, 'github-race-car.svg')
    create_animated_racetrack(contributions, svg_path)
    
    # Create dark mode version
    dark_svg_path = os.path.join(OUTPUT_DIR, 'github-race-car-dark.svg')
    create_dark_mode_version(svg_path, dark_svg_path)
    
    print(f"Generated animated race car at {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
