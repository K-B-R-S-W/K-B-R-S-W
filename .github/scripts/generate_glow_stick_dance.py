import os
import sys
import json
import requests
import numpy as np
import svgwrite
from datetime import datetime, timedelta
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
    
    # Use GitHub GraphQL API to fetch contribution data - kept for workflow compatibility
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

def create_animated_glow_stick_dance(output_path):
    """Create an animated glow stick dance SVG with continuous dabbing motion"""
    # Determine the dimensions
    width = 1000
    height = 400
    
    # Create SVG with namespace for animations
    dwg = svgwrite.Drawing(output_path, size=(width, height), profile='full')
    
    # Add SVG animation namespace
    dwg.attribs['xmlns:xlink'] = 'http://www.w3.org/1999/xlink'
    
    # Create background (black for glow stick effect)
    dwg.add(dwg.rect(insert=(0, 0), size=(width, height), fill='#000000'))
    
    # Define glow filters
    glow_colors = ['#00FFFF', '#00FF00', '#FF00FF', '#0099FF', '#FFFF00']
    
    for color in glow_colors:
        color_code = color.replace('#', '')
        filter_id = f"glow_{color_code}"
        glow_filter = dwg.defs.add(dwg.filter(id=filter_id))
        glow_filter.feGaussianBlur(in_="SourceGraphic", stdDeviation="3")
        glow_filter.feComposite(in2="SourceGraphic", operator="over")
    
    # Function to create animated glow stick figure
    def create_animated_dab_figure(x, y, size, color, delay):
        """Create a glowing stick figure with animated dab movements"""
        color_code = color.replace('#', '')
        group_id = f"figure_{color_code}_{int(x)}_{int(y)}"
        figure = dwg.g(id=group_id)
        
        # Stick figure dimensions
        head_radius = size * 0.2
        body_length = size * 0.6
        limb_length = size * 0.4
        
        # Head
        head = dwg.circle(center=(x, y), r=head_radius, fill="none", 
                          stroke=color, stroke_width=size/10,
                          filter=f"url(#glow_{color_code})")
        figure.add(head)
        
        # Body (using path instead of line for animation)
        body_path = dwg.path(
            d=f"M{x},{y + head_radius} L{x},{y + head_radius + body_length}",
            stroke=color, stroke_width=size/10,
            filter=f"url(#glow_{color_code})"
        )
        
        # Add animation to body path with plain animate
        body_anim = dwg.animate(
            attributeName="d",
            values=(
                f"M{x},{y + head_radius} L{x},{y + head_radius + body_length}; "
                f"M{x-5},{y + head_radius} L{x-3},{y + head_radius + body_length}; "
                f"M{x},{y + head_radius} L{x},{y + head_radius + body_length}; "
                f"M{x+5},{y + head_radius} L{x+3},{y + head_radius + body_length}; "
                f"M{x},{y + head_radius} L{x},{y + head_radius + body_length}"
            ),
            dur="3s",
            repeatCount="indefinite",
            begin=f"{delay}s"
        )
        body_path.add(body_anim)
        figure.add(body_path)
        
        # Left arm
        left_arm_path = dwg.path(
            d=f"M{x},{y + head_radius + size * 0.15} L{x - limb_length * 0.7},{y + head_radius + limb_length * 0.5}",
            stroke=color, stroke_width=size/10,
            filter=f"url(#glow_{color_code})"
        )
        
        # Left arm animation - for dabbing motion
        left_arm_anim = dwg.animate(
            attributeName="d",
            values=(
                f"M{x},{y + head_radius + size * 0.15} "
                f"L{x - limb_length * 0.7},{y + head_radius + limb_length * 0.5}; "
                
                f"M{x},{y + head_radius + size * 0.15} "
                f"L{x - limb_length * 0.8},{y + head_radius + limb_length * 0.8}; "
                
                f"M{x},{y + head_radius + size * 0.15} "
                f"L{x - limb_length * 0.7},{y + head_radius + limb_length * 0.5}"
            ),
            dur="3s",
            repeatCount="indefinite",
            begin=f"{delay}s"
        )
        
        left_arm_path.add(left_arm_anim)
        figure.add(left_arm_path)
        
        # Right arm - for dabbing position
        right_arm_path = dwg.path(
            d=f"M{x},{y + head_radius + size * 0.15} L{x + limb_length * 0.5},{y + head_radius - limb_length * 0.2}",
            stroke=color, stroke_width=size/10,
            filter=f"url(#glow_{color_code})"
        )
        
        # Right arm animation - dab motion
        right_arm_anim = dwg.animate(
            attributeName="d",
            values=(
                # Regular position
                f"M{x},{y + head_radius + size * 0.15} "
                f"L{x + limb_length * 0.5},{y + head_radius - limb_length * 0.2}; "
                
                # Dab position - arm across face
                f"M{x},{y + head_radius + size * 0.15} "
                f"L{x + limb_length * 0.5},{y - limb_length * 0.5}; "
                
                # Back to slightly different position
                f"M{x},{y + head_radius + size * 0.15} "
                f"L{x + limb_length * 0.6},{y + head_radius - limb_length * 0.1}; "
                
                # Regular position again
                f"M{x},{y + head_radius + size * 0.15} "
                f"L{x + limb_length * 0.5},{y + head_radius - limb_length * 0.2}"
            ),
            dur="3s",
            repeatCount="indefinite",
            begin=f"{delay}s"
        )
        
        right_arm_path.add(right_arm_anim)
        figure.add(right_arm_path)
        
        # Left leg (using path instead of line for animation)
        left_leg_path = dwg.path(
            d=f"M{x},{y + head_radius + body_length} L{x - limb_length * 0.7},{y + head_radius + body_length + limb_length}",
            stroke=color, stroke_width=size/10,
            filter=f"url(#glow_{color_code})"
        )
        
        # Add animation to left leg path
        left_leg_anim = dwg.animate(
            attributeName="d",
            values=(
                f"M{x},{y + head_radius + body_length} "
                f"L{x - limb_length * 0.7},{y + head_radius + body_length + limb_length}; "
                
                f"M{x},{y + head_radius + body_length} "
                f"L{x - limb_length * 0.7},{y + head_radius + body_length + limb_length - 5}; "
                
                f"M{x},{y + head_radius + body_length} "
                f"L{x - limb_length * 0.7},{y + head_radius + body_length + limb_length}"
            ),
            dur="3s",
            repeatCount="indefinite",
            begin=f"{delay}s"
        )
        left_leg_path.add(left_leg_anim)
        figure.add(left_leg_path)
        
        # Right leg (using path instead of line for animation)
        right_leg_path = dwg.path(
            d=f"M{x},{y + head_radius + body_length} L{x + limb_length * 0.7},{y + head_radius + body_length + limb_length}",
            stroke=color, stroke_width=size/10,
            filter=f"url(#glow_{color_code})"
        )
        
        # Add animation to right leg path
        right_leg_anim = dwg.animate(
            attributeName="d",
            values=(
                f"M{x},{y + head_radius + body_length} "
                f"L{x + limb_length * 0.7},{y + head_radius + body_length + limb_length}; "
                
                f"M{x},{y + head_radius + body_length} "
                f"L{x + limb_length * 0.7},{y + head_radius + body_length + limb_length - 10}; "
                
                f"M{x},{y + head_radius + body_length} "
                f"L{x + limb_length * 0.7},{y + head_radius + body_length + limb_length}"
            ),
            dur="3s",
            repeatCount="indefinite",
            begin=f"{delay}s"
        )
        right_leg_path.add(right_leg_anim)
        figure.add(right_leg_path)
        
        return figure
    
    # Create 2 dancing figures
    num_figures = 2
    
    for i in range(num_figures):
        # Distribute figures evenly
        x_pos = width * (i + 1) / (num_figures + 1)
        y_pos = height / 2.5
        
        # Size for figures
        figure_size = 80
        
        # Different animation delay for each figure to create varied motion
        delay = i * 0.5
        
        # Create figure with random glow color
        color = random.choice(glow_colors)
        figure = create_animated_dab_figure(x_pos, y_pos, figure_size, color, delay)
        dwg.add(figure)
    
    # Save the drawing
    dwg.save()

def create_light_mode_version(input_path, output_path):
    """Create a light mode version of the SVG"""
    with open(input_path, 'r') as f:
        svg_content = f.read()
    
    # Keep dark background for glow effect in both modes
    light_mode_svg = svg_content
    
    with open(output_path, 'w') as f:
        f.write(light_mode_svg)

def main():
    """Main function to generate animated glow stick dance"""
    print("Generating animated glow stick dab dance")
    
    # Get contribution data (for workflow compatibility only)
    try:
        get_contributions()
    except Exception as e:
        print(f"Warning: Could not fetch contributions data: {e}")
        print("Continuing without contributions data...")
    
    # Create animated glow stick dance SVG
    svg_path = os.path.join(OUTPUT_DIR, 'github-glow-dance.svg')
    create_animated_glow_stick_dance(svg_path)
    
    # Create light mode version (same as dark for glow effect)
    light_svg_path = os.path.join(OUTPUT_DIR, 'github-glow-dance-light.svg')
    create_light_mode_version(svg_path, light_svg_path)
    
    print(f"Generated animated glow stick dance at {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
