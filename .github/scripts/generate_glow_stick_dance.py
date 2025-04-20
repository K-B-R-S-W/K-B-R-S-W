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

def create_glow_stick_dance(contributions, output_path):
    """Create a glow stick dance SVG based on contribution data"""
    # Determine the dimensions
    width = 1000
    height = 400
    
    # Create SVG
    dwg = svgwrite.Drawing(output_path, size=(width, height), profile='full')
    
    # Create background (black for glow stick effect)
    dwg.add(dwg.rect(insert=(0, 0), size=(width, height), fill='#000000'))
    
    # Get dates for last 30 days
    recent_contributions = contributions[-30:] if len(contributions) > 30 else contributions
    
    # Calculate max contributions for scaling
    max_contributions = max(contrib['count'] for contrib in contributions) if contributions else 1
    
    # Function to create a glow stick figure
    def create_glow_figure(x, y, size, color, dab_phase):
        """Create a glowing stick figure with dab pose based on phase"""
        figure = dwg.g()
        
        # Add glow effect
        filter_id = f"glow_{color.replace('#', '')}"
        glow_filter = dwg.defs.add(dwg.filter(id=filter_id))
        glow_filter.feGaussianBlur(in_="SourceGraphic", stdDeviation="3")
        glow_filter.feComposite(in2="SourceGraphic", operator="over")
        
        # Stick figure dimensions
        head_radius = size * 0.2
        body_length = size * 0.6
        limb_length = size * 0.4
        
        # Head
        head = dwg.circle(center=(x, y), r=head_radius, fill="none", 
                        stroke=color, stroke_width=size/10)
        head.attribs["filter"] = f"url(#{filter_id})"
        figure.add(head)
        
        # Different poses based on dab_phase (0-1)
        if dab_phase < 0.5:  # Preparing for dab
            dab_progress = dab_phase * 2  # 0 to 1
            
            # Body (vertical line)
            body = dwg.line(start=(x, y + head_radius), 
                          end=(x, y + head_radius + body_length),
                          stroke=color, stroke_width=size/10)
            body.attribs["filter"] = f"url(#{filter_id})"
            figure.add(body)
            
            # Left arm (going up as dab progresses)
            left_arm_angle = -np.pi/4 - (np.pi/4 * dab_progress)  # Moving upward
            left_arm_x = x + limb_length * np.cos(left_arm_angle)
            left_arm_y = y + head_radius + limb_length * np.sin(left_arm_angle)
            left_arm = dwg.line(start=(x, y + head_radius + size * 0.15),
                              end=(left_arm_x, left_arm_y),
                              stroke=color, stroke_width=size/10)
            left_arm.attribs["filter"] = f"url(#{filter_id})"
            figure.add(left_arm)
            
            # Right arm (going down and across as dab progresses)
            right_arm_angle = np.pi/4 + (np.pi/4 * dab_progress)  # Moving across body
            right_arm_x = x + limb_length * np.cos(right_arm_angle)
            right_arm_y = y + head_radius + limb_length * np.sin(right_arm_angle)
            right_arm = dwg.line(start=(x, y + head_radius + size * 0.15),
                               end=(right_arm_x, right_arm_y),
                               stroke=color, stroke_width=size/10)
            right_arm.attribs["filter"] = f"url(#{filter_id})"
            figure.add(right_arm)
            
            # Left leg
            left_leg = dwg.line(start=(x, y + head_radius + body_length),
                              end=(x - limb_length * 0.7, y + head_radius + body_length + limb_length),
                              stroke=color, stroke_width=size/10)
            left_leg.attribs["filter"] = f"url(#{filter_id})"
            figure.add(left_leg)
            
            # Right leg
            right_leg = dwg.line(start=(x, y + head_radius + body_length),
                               end=(x + limb_length * 0.7, y + head_radius + body_length + limb_length),
                               stroke=color, stroke_width=size/10)
            right_leg.attribs["filter"] = f"url(#{filter_id})"
            figure.add(right_leg)
            
        else:  # Full dab
            dab_progress = (dab_phase - 0.5) * 2  # 0 to 1 (for oscillation)
            
            # For dab pose, tilt the body slightly
            body_angle = np.pi/12 * np.sin(dab_progress * np.pi)  # Small tilt
            body_end_x = x + body_length * np.sin(body_angle)
            body_end_y = y + head_radius + body_length * np.cos(body_angle)
            
            body = dwg.line(start=(x, y + head_radius),
                          end=(body_end_x, body_end_y),
                          stroke=color, stroke_width=size/10)
            body.attribs["filter"] = f"url(#{filter_id})"
            figure.add(body)
            
            # Dab position - one arm up across face, one arm out to side
            # Head slightly tucked into raised arm
            
            # Left arm (down to side in dab)
            left_arm = dwg.line(start=(x, y + head_radius + size * 0.15),
                              end=(x - limb_length * 0.8, y + head_radius + limb_length * 0.8),
                              stroke=color, stroke_width=size/10)
            left_arm.attribs["filter"] = f"url(#{filter_id})"
            figure.add(left_arm)
            
            # Right arm (up across face in dab)
            right_arm = dwg.line(start=(x, y + head_radius + size * 0.15),
                               end=(x + limb_length * 0.5, y - limb_length * 0.5),
                               stroke=color, stroke_width=size/10)
            right_arm.attribs["filter"] = f"url(#{filter_id})"
            figure.add(right_arm)
            
            # Left leg
            left_leg = dwg.line(start=(body_end_x, body_end_y),
                              end=(body_end_x - limb_length * 0.7, body_end_y + limb_length),
                              stroke=color, stroke_width=size/10)
            left_leg.attribs["filter"] = f"url(#{filter_id})"
            figure.add(left_leg)
            
            # Right leg
            right_leg = dwg.line(start=(body_end_x, body_end_y),
                               end=(body_end_x + limb_length * 0.7, body_end_y + limb_length),
                               stroke=color, stroke_width=size/10)
            right_leg.attribs["filter"] = f"url(#{filter_id})"
            figure.add(right_leg)
        
        return figure
    
    # Create multiple dancing figures based on contribution data
    glow_colors = ['#00FFFF', '#00FF00', '#FF00FF', '#0099FF', '#FFFF00']
    
    # Get number of figures based on contributions
    num_figures = min(5, max(2, sum(1 for c in recent_contributions if c['count'] > 0) // 6))
    
    for i in range(num_figures):
        # Distribute figures evenly
        x_pos = width * (i + 1) / (num_figures + 1)
        y_pos = height / 2.5
        
        # Size based on recent activity
        base_size = 80
        size_boost = sum(c['count'] for c in recent_contributions[-7:]) / max(1, max_contributions) * 20
        figure_size = base_size + size_boost
        
        # Different phase for each figure
        dab_phase = (i / num_figures + 0.2) % 1.0
        
        # Create figure with random glow color
        color = random.choice(glow_colors)
        figure = create_glow_figure(x_pos, y_pos, figure_size, color, dab_phase)
        dwg.add(figure)
    
    # Add contribution stats
    stats_text = f"Total Contributions: {sum(c['count'] for c in recent_contributions)}"
    stats = dwg.text(stats_text, insert=(width/2, height-40), 
                     fill='#FFFFFF', font_size='14px', 
                     text_anchor='middle')
    stats.attribs["filter"] = "url(#glow_FFFFFF)"
    dwg.add(stats)
    
    # Add watermark with username
    title_filter = dwg.defs.add(dwg.filter(id="glow_title"))
    title_filter.feGaussianBlur(in_="SourceGraphic", stdDeviation="2")
    title_filter.feComposite(in2="SourceGraphic", operator="over")
    
    title = dwg.text(f"@{GITHUB_USERNAME}'s Glow Stick Dance", 
                    insert=(width/2, 30), 
                    fill='#FFFFFF', 
                    font_size='18px', 
                    font_weight='bold',
                    text_anchor='middle')
    title.attribs["filter"] = "url(#glow_title)"
    dwg.add(title)
    
    # Add current date
    today = datetime.now().strftime("%Y-%m-%d")
    date_text = dwg.text(f"Generated: {today}", 
                    insert=(width-20, height-20), 
                    fill='#AAAAAA', 
                    font_size='10px',
                    text_anchor='end')
    dwg.add(date_text)
    
    # Save the drawing
    dwg.save()

def create_light_mode_version(input_path, output_path):
    """Create a light mode version of the SVG"""
    with open(input_path, 'r') as f:
        svg_content = f.read()
    
    # Replace colors for light mode (keep dark background for glow effect)
    light_mode_svg = svg_content
    
    with open(output_path, 'w') as f:
        f.write(light_mode_svg)

def main():
    """Main function to generate glow stick dance animation"""
    print(f"Generating glow stick dance animation for GitHub user: {GITHUB_USERNAME}")
    
    # Get contribution data
    contributions = get_contributions()
    
    # Create glow stick dance SVG
    svg_path = os.path.join(OUTPUT_DIR, 'github-glow-dance.svg')
    create_glow_stick_dance(contributions, svg_path)
    
    # Create light mode version (same as dark for glow effect)
    light_svg_path = os.path.join(OUTPUT_DIR, 'github-glow-dance-light.svg')
    create_light_mode_version(svg_path, light_svg_path)
    
    print(f"Generated glow stick dance animations at {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
