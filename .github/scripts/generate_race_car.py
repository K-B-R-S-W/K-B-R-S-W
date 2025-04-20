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

def create_racetrack(contributions, output_path):
    """Create a race track SVG with car based on contribution data"""
    # Determine the dimensions
    width = 1000
    height = 400
    
    # Create SVG
    dwg = svgwrite.Drawing(output_path, size=(width, height), profile='full')
    
    # Create background
    dwg.add(dwg.rect(insert=(0, 0), size=(width, height), fill='#0d1117'))
    
    # Draw race track (oval shape)
    track_x = 100
    track_y = 100
    track_width = width - 200
    track_height = height - 200
    
    # Track outline - asphalt color
    dwg.add(dwg.ellipse(center=(width/2, height/2), 
                        r=(track_width/2, track_height/2),
                        fill='#333333'))
    
    # Inner track - grass field
    dwg.add(dwg.ellipse(center=(width/2, height/2), 
                        r=(track_width/2 - 40, track_height/2 - 40),
                        fill='#264026'))
    
    # Lane markers on track
    # Calculate contribution heat levels for color intensity
    max_contributions = max(contrib['count'] for contrib in contributions) if contributions else 1
    
    # Get dates for last 52 weeks (364 days)
    recent_contributions = contributions[-364:] if len(contributions) > 364 else contributions
    
    # Create checkpoints around the track
    total_points = len(recent_contributions)
    
    # Car SVG path (simple race car shape)
    def car_path(x, y, size=10, direction=0):
        """Create an SVG path for a race car at the given position and direction"""
        # Car body
        car = dwg.g()
        
        # Rotate the car based on direction (in radians)
        car.rotate(direction * 180 / np.pi, center=(x, y))
        
        # Car body - adjust colors based on contribution level
        car.add(dwg.rect((x-size, y-size/2), (size*2, size), rx=3, fill='#ff3300'))
        
        # Wheels
        wheel_size = size/3
        car.add(dwg.rect((x-size+wheel_size/2, y-size/2-wheel_size/2), (wheel_size, wheel_size), fill='#111'))
        car.add(dwg.rect((x+size-wheel_size*1.5, y-size/2-wheel_size/2), (wheel_size, wheel_size), fill='#111'))
        car.add(dwg.rect((x-size+wheel_size/2, y+size/2-wheel_size/2), (wheel_size, wheel_size), fill='#111'))
        car.add(dwg.rect((x+size-wheel_size*1.5, y+size/2-wheel_size/2), (wheel_size, wheel_size), fill='#111'))
        
        # Windshield
        car.add(dwg.polygon(points=[(x, y-size/2), (x+size/2, y-size/4), (x+size/2, y+size/4), (x, y+size/2)], fill='#66ccff'))
        
        return car
    
    # Create race track checkpoints and place car
    track_points = []
    for i in range(total_points):
        angle = 2 * np.pi * i / total_points
        
        # Elliptical coordinates
        x = width/2 + (track_width/2 - 20) * np.cos(angle)
        y = height/2 + (track_height/2 - 20) * np.sin(angle)
        
        # Store track points
        track_points.append((x, y, angle))
    
    # Draw car positions with "ghost" trail effect
    # Focus on more recent contributions for more prominent display
    display_contribs = recent_contributions[-30:]  # Last 30 days
    
    for i, contrib in enumerate(display_contribs):
        point_index = (len(track_points) - len(display_contribs) + i) % len(track_points)
        x, y, angle = track_points[point_index]
        
        # Scale car size by contribution
        car_size = 6 + (contrib['count'] * 2 if contrib['count'] < 5 else 10)
        
        # Opacity based on recency (more recent = more opaque)
        opacity = 0.3 + (i / len(display_contribs)) * 0.7
        
        # Create car with current position
        if i == len(display_contribs) - 1:  # Most recent contribution = main car
            car = car_path(x, y, car_size, angle + np.pi/2)
            dwg.add(car)
        else:  # Ghost trail
            ghost_car = car_path(x, y, car_size * 0.8, angle + np.pi/2)
            ghost_car.attribs['opacity'] = str(opacity * 0.5)
            dwg.add(ghost_car)
    
    # Add start/finish line
    finish_x = width/2 + (track_width/2 - 20)
    finish_y = height/2
    dwg.add(dwg.line((finish_x-15, finish_y-10), (finish_x+15, finish_y+10), stroke='#ffffff', stroke_width=3))
    dwg.add(dwg.line((finish_x+15, finish_y-10), (finish_x-15, finish_y+10), stroke='#ffffff', stroke_width=3))
    
    # Add contribution stats
    stats_text = f"Total Contributions: {sum(c['count'] for c in recent_contributions)}"
    dwg.add(dwg.text(stats_text, insert=(width/2, height-40), 
                     fill='#ffffff', font_size='14px', 
                     text_anchor='middle'))
    
    # Add watermark with username
    dwg.add(dwg.text(f"@{GITHUB_USERNAME}'s Racing Contributions", 
                    insert=(width/2, 30), 
                    fill='#ffffff', 
                    font_size='18px', 
                    font_weight='bold',
                    text_anchor='middle'))
    
    # Add current date
    today = datetime.now().strftime("%Y-%m-%d")
    dwg.add(dwg.text(f"Generated: {today}", 
                    insert=(width-20, height-20), 
                    fill='#aaaaaa', 
                    font_size='10px',
                    text_anchor='end'))
    
    # Save the drawing
    dwg.save()

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
    """Main function to generate race car animation"""
    print(f"Generating race car animation for GitHub user: {GITHUB_USERNAME}")
    
    # Get contribution data
    contributions = get_contributions()
    
    # Create race track SVG
    svg_path = os.path.join(OUTPUT_DIR, 'github-race-car.svg')
    create_racetrack(contributions, svg_path)
    
    # Create dark mode version
    dark_svg_path = os.path.join(OUTPUT_DIR, 'github-race-car-dark.svg')
    create_dark_mode_version(svg_path, dark_svg_path)
    
    print(f"Generated race car animations at {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
