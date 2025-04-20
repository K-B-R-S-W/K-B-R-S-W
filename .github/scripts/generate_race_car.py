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
    
    # Create SVG with animation support
    dwg = svgwrite.Drawing(output_path, size=(width, height), profile='full')
    
    # Add SVG namespace for SMIL animations
    dwg.attribs['xmlns:xlink'] = "http://www.w3.org/1999/xlink"
    
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
    
    # Calculate contribution heat levels for color intensity
    max_contributions = max(contrib['count'] for contrib in contributions) if contributions else 1
    
    # Get dates for last 52 weeks (364 days)
    recent_contributions = contributions[-364:] if len(contributions) > 364 else contributions
    
    # Create checkpoints around the track
    total_points = len(recent_contributions)
    
    # Car SVG path (race car shape)
    car_size = 10
    
    # Create a group for the car that will be animated
    car_group = dwg.g(id="race-car")
    
    # Car body - adjust colors based on contribution level
    car_body = dwg.rect((-car_size, -car_size/2), (car_size*2, car_size), rx=3, fill='#ff3300')
    car_group.add(car_body)
    
    # Wheels
    wheel_size = car_size/3
    car_group.add(dwg.rect((-car_size+wheel_size/2, -car_size/2-wheel_size/2), (wheel_size, wheel_size), fill='#111'))
    car_group.add(dwg.rect((car_size-wheel_size*1.5, -car_size/2-wheel_size/2), (wheel_size, wheel_size), fill='#111'))
    car_group.add(dwg.rect((-car_size+wheel_size/2, car_size/2-wheel_size/2), (wheel_size, wheel_size), fill='#111'))
    car_group.add(dwg.rect((car_size-wheel_size*1.5, car_size/2-wheel_size/2), (wheel_size, wheel_size), fill='#111'))
    
    # Windshield
    car_group.add(dwg.polygon(points=[(0, -car_size/2), (car_size/2, -car_size/4), 
                                   (car_size/2, car_size/4), (0, car_size/2)], 
                             fill='#66ccff'))
    
    # Add car to SVG
    dwg.add(car_group)
    
    # Create path for animation
    # Define elliptical path for car to follow
    ellipse_cx = width/2
    ellipse_cy = height/2
    ellipse_rx = track_width/2 - 20
    ellipse_ry = track_height/2 - 20
    
    # Create a path for the car to follow
    path = dwg.path(d=f"M {ellipse_cx + ellipse_rx} {ellipse_cy} " + 
                    f"A {ellipse_rx} {ellipse_ry} 0 1 1 {ellipse_cx - ellipse_rx} {ellipse_cy} " +
                    f"A {ellipse_rx} {ellipse_ry} 0 1 1 {ellipse_cx + ellipse_rx} {ellipse_cy}",
                    id="track-path", stroke="none", fill="none")
    dwg.add(path)
    
    # Create animation for car rotation
    # This makes the car face the direction it's moving
    rotate_anim = svgwrite.animate.AnimateTransform(
        'transform', 'rotate',
        from_='0 0 0', to_='360 0 0', 
        dur='20s', repeatCount='indefinite'
    )
    
    # Create animation for car movement along path
    car_anim = svgwrite.animate.AnimateMotion(
        path=f"M {ellipse_rx} 0 " + 
            f"A {ellipse_rx} {ellipse_ry} 0 1 1 {-ellipse_rx} 0 " +
            f"A {ellipse_rx} {ellipse_ry} 0 1 1 {ellipse_rx} 0",
        dur='20s', repeatCount='indefinite',
        rotate='auto-reverse'
    )
    
    # Add animations to car
    car_group.add(car_anim)
    
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
