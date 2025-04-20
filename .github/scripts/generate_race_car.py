import os
import sys
import json
import requests
import numpy as np
import svgwrite
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import random

# Configuration
GITHUB_USERNAME = os.environ.get('GITHUB_USERNAME')
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
    width = 1000
    height = 400
    
    # Calculate contribution stats
    recent_contributions = contributions[-364:] if len(contributions) > 364 else contributions
    total_contribs = sum(c['count'] for c in recent_contributions)
    
    # Create SVG manually (bypassing svgwrite's animation limitations)
    # Start with the SVG header
    svg_content = f'''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
    <rect x="0" y="0" width="{width}" height="{height}" fill="#0d1117"/>
    
    <!-- Track outline -->
    <ellipse cx="{width/2}" cy="{height/2}" rx="{(width-200)/2}" ry="{(height-200)/2}" fill="#333333"/>
    
    <!-- Inner track -->
    <ellipse cx="{width/2}" cy="{height/2}" rx="{(width-200)/2 - 40}" ry="{(height-200)/2 - 40}" fill="#264026"/>
    
    <!-- Start/finish line -->
    <line x1="{width/2 + (width-200)/2 - 35}" y1="{height/2 - 10}" x2="{width/2 + (width-200)/2 - 5}" y2="{height/2 + 10}" stroke="#ffffff" stroke-width="3"/>
    <line x1="{width/2 + (width-200)/2 - 5}" y1="{height/2 - 10}" x2="{width/2 + (width-200)/2 - 35}" y2="{height/2 + 10}" stroke="#ffffff" stroke-width="3"/>
    
    <!-- Path for car to follow (invisible) -->
    <path id="carPath" d="M {width/2 + (width-200)/2 - 20} {height/2} 
                A {(width-200)/2 - 20} {(height-200)/2 - 20} 0 1 1 {width/2 - (width-200)/2 + 20} {height/2}
                A {(width-200)/2 - 20} {(height-200)/2 - 20} 0 1 1 {width/2 + (width-200)/2 - 20} {height/2}"
          fill="none" stroke="none"/>
    
    <!-- Race car -->
    <g id="raceCar">
        <!-- Car body -->
        <rect x="-12" y="-6" width="24" height="12" rx="3" fill="#ff3300"/>
        <!-- Wheels -->
        <rect x="-10" y="-8" width="4" height="4" fill="#111111"/>
        <rect x="6" y="-8" width="4" height="4" fill="#111111"/>
        <rect x="-10" y="4" width="4" height="4" fill="#111111"/>
        <rect x="6" y="4" width="4" height="4" fill="#111111"/>
        <!-- Windshield -->
        <polygon points="0,-6 6,-3 6,3 0,6" fill="#66ccff"/>
        
        <!-- Animation -->
        <animateMotion dur="10s" repeatCount="indefinite" rotate="auto">
            <mpath xlink:href="#carPath"/>
        </animateMotion>
    </g>
    
    <!-- Stats text -->
    <text x="{width/2}" y="{height-40}" fill="#ffffff" font-size="14px" text-anchor="middle">Total Contributions: {total_contribs}</text>
    
    <!-- Watermark -->
    <text x="{width/2}" y="30" fill="#ffffff" font-size="18px" font-weight="bold" text-anchor="middle">@{GITHUB_USERNAME}'s Racing Contributions</text>
    
    <!-- Generation date -->
    <text x="{width-20}" y="{height-20}" fill="#aaaaaa" font-size="10px" text-anchor="end">Generated: {datetime.now().strftime("%Y-%m-%d")}</text>
</svg>'''
    
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
