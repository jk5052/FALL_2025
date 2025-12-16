import praw
from openai import OpenAI
import json
from datetime import datetime, timedelta
import time
from dotenv import load_dotenv
import os

load_dotenv()

# API Setup
reddit = praw.Reddit(
    client_id=os.getenv('REDDIT_CLIENT_ID'),
    client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
    user_agent='NYC_Emotion_Mapper/1.0'
)

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# NYC Location Database (for mapping)
NYC_LOCATIONS = {
    'central park': {'lat': 40.7829, 'lng': -73.9654},
    'times square': {'lat': 40.7580, 'lng': -73.9855},
    'brooklyn bridge': {'lat': 40.7061, 'lng': -73.9969},
    'union square': {'lat': 40.7359, 'lng': -73.9911},
    'washington square': {'lat': 40.7308, 'lng': -73.9973},
    'high line': {'lat': 40.7480, 'lng': -74.0048},
    'bryant park': {'lat': 40.7536, 'lng': -73.9832},
    'prospect park': {'lat': 40.6602, 'lng': -73.9690},
    'east village': {'lat': 40.7265, 'lng': -73.9815},
    'west village': {'lat': 40.7358, 'lng': -74.0027},
    'soho': {'lat': 40.7233, 'lng': -74.0030},
    'chelsea': {'lat': 40.7465, 'lng': -74.0014},
    'williamsburg': {'lat': 40.7081, 'lng': -73.9571},
    'financial district': {'lat': 40.7074, 'lng': -74.0113},
    'fidi': {'lat': 40.7074, 'lng': -74.0113},
    'upper west side': {'lat': 40.7870, 'lng': -73.9754},
    'uws': {'lat': 40.7870, 'lng': -73.9754},
    'upper east side': {'lat': 40.7736, 'lng': -73.9566},
    'ues': {'lat': 40.7736, 'lng': -73.9566},
    'midtown': {'lat': 40.7549, 'lng': -73.9840},
    'downtown': {'lat': 40.7074, 'lng': -74.0113},
    'battery park': {'lat': 40.7033, 'lng': -74.0170},
    'madison square park': {'lat': 40.7425, 'lng': -73.9881},
    'flatiron': {'lat': 40.7411, 'lng': -73.9897},
    'gramercy': {'lat': 40.7373, 'lng': -73.9851},
    'tribeca': {'lat': 40.7163, 'lng': -74.0086},
    'chinatown': {'lat': 40.7158, 'lng': -73.9970},
    'little italy': {'lat': 40.7193, 'lng': -73.9973},
    'lower east side': {'lat': 40.7177, 'lng': -73.9860},
    'les': {'lat': 40.7177, 'lng': -73.9860},
    'harlem': {'lat': 40.8116, 'lng': -73.9465},
    'morningside heights': {'lat': 40.8108, 'lng': -73.9622},
    'inwood': {'lat': 40.8677, 'lng': -73.9212},
    'washington heights': {'lat': 40.8500, 'lng': -73.9350},
}

# Subreddits to search
NYC_SUBREDDITS = ['nyc', 'AskNYC', 'newyorkcity', 'Brooklyn', 'Manhattan', 'Queens']

def extract_location_and_emotion(text):
    """Use OpenAI to extract location and analyze emotion"""
    try:
        response = client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=[
                {
                    'role': 'system',
                    'content': '''Extract NYC location and emotion from text.
                    Return JSON only:
                    {
                        "location": "specific place name in NYC (or null if none)",
                        "emotion": "joy|anxiety|peace|sadness|neutral",
                        "intensity": 0.0-1.0,
                        "reasoning": "brief why"
                    }
                    
                    Common NYC locations: Central Park, Times Square, Brooklyn Bridge, 
                    Union Square, East Village, Williamsburg, etc.
                    
                    If no specific location mentioned, return location: null'''
                },
                {
                    'role': 'user',
                    'content': text
                }
            ],
            temperature=0.3
        )
        
        result = json.loads(response.choices[0].message.content)
        return result
        
    except Exception as e:
        print(f"OpenAI Error: {e}")
        return None

def map_location_to_coords(location_name):
    """Map location name to coordinates"""
    if not location_name:
        return None
    
    # Normalize
    location_lower = location_name.lower().strip()
    
    # Direct match
    if location_lower in NYC_LOCATIONS:
        return NYC_LOCATIONS[location_lower]
    
    # Partial match
    for key, coords in NYC_LOCATIONS.items():
        if key in location_lower or location_lower in key:
            return coords
    
    return None

def collect_reddit_data(days_back=7, limit_per_sub=100):
    """Collect Reddit posts from NYC subreddits"""
    
    collected = []
    
    for subreddit_name in NYC_SUBREDDITS:
        print(f"\n{'='*50}")
        print(f"Collecting from r/{subreddit_name}...")
        print(f"{'='*50}")
        
        try:
            subreddit = reddit.subreddit(subreddit_name)
            
            # Get recent posts
            for submission in subreddit.new(limit=limit_per_sub):
                # Check if within time range
                post_time = datetime.fromtimestamp(submission.created_utc)
                if datetime.now() - post_time > timedelta(days=days_back):
                    continue
                
                # Combine title and selftext
                text = f"{submission.title}. {submission.selftext}"
                
                if len(text) < 20:  # Skip too short
                    continue
                
                print(f"\nAnalyzing: {submission.title[:60]}...")
                
                # Extract location and emotion
                analysis = extract_location_and_emotion(text)
                
                if not analysis or not analysis.get('location'):
                    print("  ❌ No location found")
                    continue
                
                # Map to coordinates
                coords = map_location_to_coords(analysis['location'])
                
                if not coords:
                    print(f"  ❌ Couldn't map '{analysis['location']}' to coordinates")
                    continue
                
                # Success!
                collected.append({
                    'location_name': analysis['location'],
                    'lat': coords['lat'],
                    'lng': coords['lng'],
                    'emotion': analysis['emotion'],
                    'intensity': analysis['intensity'],
                    'text': text[:200],  # Truncate
                    'reasoning': analysis.get('reasoning', ''),
                    'timestamp': post_time.isoformat(),
                    'subreddit': subreddit_name,
                    'post_id': submission.id,
                    'url': f"https://reddit.com{submission.permalink}"
                })
                
                print(f"  ✅ {analysis['location']} → {analysis['emotion']} ({analysis['intensity']})")
                
                # Rate limit
                time.sleep(2)  # OpenAI rate limit
                
        except Exception as e:
            print(f"Error with r/{subreddit_name}: {e}")
    
    return collected

def group_by_date(data):
    """Group data by date for temporal visualization"""
    from collections import defaultdict
    
    by_date = defaultdict(list)
    
    for item in data:
        date = item['timestamp'][:10]  # YYYY-MM-DD
        by_date[date].append(item)
    
    return dict(by_date)

def to_geojson(data):
    """Convert to GeoJSON"""
    features = []
    
    for item in data:
        features.append({
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [item['lng'], item['lat']]
            },
            'properties': {
                'location': item['location_name'],
                'emotion': item['emotion'],
                'intensity': item['intensity'],
                'text': item['text'],
                'reasoning': item['reasoning'],
                'timestamp': item['timestamp'],
                'subreddit': item['subreddit'],
                'url': item['url']
            }
        })
    
    return {
        'type': 'FeatureCollection',
        'features': features
    }

def main():
    print("🗽 NYC Reddit Emotion Collector")
    print("="*60)
    
    # Collect
    print("\nStarting collection...")
    data = collect_reddit_data(days_back=14, limit_per_sub=50)
    
    print(f"\n{'='*60}")
    print(f"✅ Collected {len(data)} posts with locations and emotions")
    print(f"{'='*60}")
    
    if not data:
        print("⚠️  No data collected. Try:")
        print("  - Increase days_back")
        print("  - Increase limit_per_sub")
        print("  - Check if subreddits have recent posts")
        return
    
    # Save raw data
    with open('reddit_emotions_raw.json', 'w') as f:
        json.dump(data, f, indent=2)
    print("\n💾 Saved raw data to reddit_emotions_raw.json")
    
    # Save as GeoJSON
    geojson = to_geojson(data)
    with open('reddit_emotions.geojson', 'w') as f:
        json.dump(geojson, f, indent=2)
    print("💾 Saved GeoJSON to reddit_emotions.geojson")
    
    # Group by date
    by_date = group_by_date(data)
    with open('reddit_emotions_by_date.json', 'w') as f:
        json.dump(by_date, f, indent=2)
    print("💾 Saved temporal data to reddit_emotions_by_date.json")
    
    # Summary
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    
    emotions_count = {}
    locations_count = {}
    
    for item in data:
        emotions_count[item['emotion']] = emotions_count.get(item['emotion'], 0) + 1
        locations_count[item['location_name']] = locations_count.get(item['location_name'], 0) + 1
    
    print("\nEmotions:")
    for emotion, count in sorted(emotions_count.items(), key=lambda x: -x[1]):
        print(f"  {emotion}: {count}")
    
    print("\nTop Locations:")
    for location, count in sorted(locations_count.items(), key=lambda x: -x[1])[:10]:
        print(f"  {location}: {count}")
    
    print("\nDates covered:")
    for date in sorted(by_date.keys()):
        print(f"  {date}: {len(by_date[date])} posts")
    
    print("\n✨ Done! Ready for visualization.")

if __name__ == '__main__':
    main()