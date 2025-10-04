#!/usr/bin/env python3

import urllib.request
import json
import os
from datetime import datetime, timedelta

CHESS_USERNAME = "AnishTheAnnihilator"
API_URL = f"https://api.chess.com/pub/player/{CHESS_USERNAME}/stats"
HISTORY_FILE = "rating_history.json"
GRAPH_FILE = "rating_trend.svg"

def fetch_current_rating():
    try:
        with urllib.request.urlopen(API_URL, timeout=10) as response:
            data = json.loads(response.read().decode())
            if 'chess_rapid' in data and 'last' in data['chess_rapid']:
                return data['chess_rapid']['last']['rating']
    except Exception as e:
        print(f"Error fetching rating: {e}")
    return None

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    return []

def save_history(history):
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

def add_today_rating(history, rating):
    if rating is None:
        return history
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    for entry in history:
        if entry['date'] == today:
            entry['rating'] = rating
            entry['updated'] = datetime.now().isoformat()
            break
    else:
        history.append({
            'date': today,
            'rating': rating,
            'updated': datetime.now().isoformat()
        })
    
    history.sort(key=lambda x: x['date'])
    
    cutoff_date = datetime.now() - timedelta(days=30)
    cutoff_str = cutoff_date.strftime('%Y-%m-%d')
    history = [entry for entry in history if entry['date'] >= cutoff_str]
    
    if len(history) > 30:
        history = history[-30:]
    
    return history

def create_svg_graph(history):
    if len(history) < 1:
        return False
    
    dates = [datetime.strptime(entry['date'], '%Y-%m-%d') for entry in history]
    ratings = [entry['rating'] for entry in history]
    
    width = 1000
    height = 500
    margin = 60
    
    min_rating = min(ratings) - 50
    max_rating = max(ratings) + 50
    rating_range = max_rating - min_rating
    
    svg_content = f'''<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
  <rect width="{width}" height="{height}" fill="#1e1e1e"/>
  <text x="{width//2}" y="30" text-anchor="middle" fill="white" font-family="Arial" font-size="18" font-weight="bold">
    Chess.com Rapid Rating - {CHESS_USERNAME}
  </text>
  <text x="{width//2}" y="55" text-anchor="middle" fill="#888" font-family="Arial" font-size="12">
    Last 30 Days ({len(history)} days tracked)
  </text>
'''
    
    for i in range(6):
        y = margin + (i * (height - 2*margin) // 5)
        rating_val = max_rating - (i * rating_range // 5)
        svg_content += f'  <line x1="{margin}" y1="{y}" x2="{width-margin}" y2="{y}" stroke="#333" stroke-width="1"/>\n'
        svg_content += f'  <text x="{margin-10}" y="{y+5}" text-anchor="end" fill="#888" font-family="Arial" font-size="12">{int(rating_val)}</text>\n'
    
    if len(ratings) > 1:
        points = []
        for i, (date, rating) in enumerate(zip(dates, ratings)):
            x = margin + (i * (width - 2*margin) // (len(dates) - 1))
            y = margin + ((max_rating - rating) * (height - 2*margin) // rating_range)
            points.append(f"{x},{y}")
        
        area_points = f"{margin},{height-margin} " + " ".join(points) + f" {width-margin},{height-margin}"
        svg_content += f'  <polygon points="{area_points}" fill="#00ff88" fill-opacity="0.2"/>\n'
        svg_content += f'  <polyline points="{" ".join(points)}" fill="none" stroke="#00ff88" stroke-width="3"/>\n'
        
        for point in points:
            x, y = point.split(',')
            svg_content += f'  <circle cx="{x}" cy="{y}" r="4" fill="#00ff88"/>\n'
    else:
        x = width // 2
        y = margin + ((max_rating - ratings[0]) * (height - 2*margin) // rating_range)
        svg_content += f'  <circle cx="{x}" cy="{y}" r="6" fill="#00ff88"/>\n'
        svg_content += f'  <text x="{x}" y="{y-15}" text-anchor="middle" fill="#00ff88" font-family="Arial" font-size="14" font-weight="bold">{ratings[0]}</text>\n'
    
    current_rating = ratings[-1]
    if len(ratings) > 1:
        highest = max(ratings)
        lowest = min(ratings)
        change = current_rating - ratings[0]
        change_text = f"+{change}" if change >= 0 else str(change)
        change_color = "#00ff88" if change >= 0 else "#ff4444"
        
        svg_content += f'  <text x="{width-10}" y="{height-80}" text-anchor="end" fill="#00ff88" font-family="Arial" font-size="16" font-weight="bold">Current: {current_rating}</text>\n'
        svg_content += f'  <text x="{width-10}" y="{height-60}" text-anchor="end" fill="#888" font-family="Arial" font-size="12">High: {highest}</text>\n'
        svg_content += f'  <text x="{width-10}" y="{height-45}" text-anchor="end" fill="#888" font-family="Arial" font-size="12">Low: {lowest}</text>\n'
        svg_content += f'  <text x="{width-10}" y="{height-25}" text-anchor="end" fill="{change_color}" font-family="Arial" font-size="12" font-weight="bold">Change: {change_text}</text>\n'
    else:
        svg_content += f'  <text x="{width-10}" y="{height-25}" text-anchor="end" fill="#00ff88" font-family="Arial" font-size="16" font-weight="bold">Current: {current_rating}</text>\n'
    
    svg_content += '</svg>'
    
    with open(GRAPH_FILE, 'w') as f:
        f.write(svg_content)
    
    return True

def update_readme(rating, history):
    if not history:
        return
    
    current = history[-1]['rating']
    days_tracked = len(history)
    
    readme_content = f"""# Chess Rating Tracker

## Rapid Rating: {current}

![Rating Trend]({GRAPH_FILE})

**Days Tracked:** {days_tracked}  
**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

*This graph shows only real rating data. Run daily to build up your historical trend!*
"""
    
    with open('README.md', 'w') as f:
        f.write(readme_content)

def cleanup_old_data():
    if os.path.exists(HISTORY_FILE):
        history = load_history()
        cutoff_date = datetime.now() - timedelta(days=30)
        cutoff_str = cutoff_date.strftime('%Y-%m-%d')
        
        cleaned_history = [entry for entry in history if entry['date'] >= cutoff_str]
        
        if len(cleaned_history) != len(history):
            print(f"Cleaned up {len(history) - len(cleaned_history)} old entries")
            save_history(cleaned_history)
            return cleaned_history
    
    return load_history()

def main():
    print(f"Fetching rating data for {CHESS_USERNAME}...")
    
    current_rating = fetch_current_rating()
    if current_rating is None:
        print("Could not fetch current rating")
        return
    
    print(f"Current rating: {current_rating}")
    
    history = cleanup_old_data()
    print(f"Existing data points: {len(history)}")
    
    history = add_today_rating(history, current_rating)
    save_history(history)
    
    print(f"Total data points: {len(history)}")
    
    if create_svg_graph(history):
        update_readme(current_rating, history)
        print(f"Graph created with {len(history)} data points!")
        print(f"Files updated: {GRAPH_FILE}, rating_history.json, README.md")
        
        if len(history) > 1:
            highest = max(entry['rating'] for entry in history)
            lowest = min(entry['rating'] for entry in history)
            change = current_rating - history[0]['rating']
            print(f"Stats: High {highest}, Low {lowest}, Change {change:+d}")
        else:
            print("Run this script daily to build up your rating history!")
    else:
        print("Could not create graph")

if __name__ == "__main__":
    main()
