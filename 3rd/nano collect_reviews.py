import googlemaps
import pandas as pd
import time

# API 키 입력
API_KEY = 'AIzaSyC2J_U42ZYFyMqrAp04VCJdVZrGbDF_XPs'
gmaps = googlemaps.Client(key=API_KEY)

# 벤치 데이터 로드
benches = pd.read_csv('Seating_Locations_20251017.csv')
benches = benches[benches['BoroName'] == 'Manhattan']

results = []

for idx, bench in benches.iterrows():
    print(f"Processing {idx+1}/{len(benches)}...")
    
    lat = bench['Latitude']
    lon = bench['Longitude']
    
    try:
        nearby = gmaps.places_nearby(
            location=(lat, lon),
            radius=200,
            type=['library', 'cafe', 'community_center', 'park']
        )
        
        reviews_text = []
        
        for place in nearby['results'][:20]:
            details = gmaps.place(place['place_id'], fields=['review'])
            
            if 'reviews' in details['result']:
                for r in details['result']['reviews']:
                    reviews_text.append(r['text'])
            
            time.sleep(0.3)
        
        # 수정된 키워드
        positive = [
            # 분위기
            'great atmosphere', 'great vibe', 'love this', 'amazing', 
            'perfect spot', 'favorite', 'always busy', 'bustling', 
            'lively', 'vibrant', 'energy', 'fun',
            # 추천
            'recommend', 'must visit', 'come back', 'worth it',
            'definitely', 'enjoyed', 'awesome', 'wonderful',
            # 사람들
            'crowded', 'packed', 'lots of people', 'popular',
            'full', 'busy', 'everyone', 'gathering',
            # 머무름
            'stayed for', 'sat for', 'spent time', 'hang out',
            'relaxing', 'chill', 'comfortable', 'cozy',
            # 활동
            'people watching', 'watched people', 'great for',
            'nice place to sit', 'good spot', 'loved it'
        ]
        
        negative = [
            # 회피
            'nothing here', 'nothing special', 'not much', 
            'pass by', 'passing through', 'just walked', 
            'keep walking', "wouldn't stop", "didn't stay",
            # 실망
            'disappointed', 'expected more', 'overhyped',
            'not worth', 'waste', 'skip', 'avoid',
            'better places', 'meh', 'okay at best',
            # 비어있음
            'empty', 'dead', 'quiet', 'nobody', 'deserted',
            'no one', 'closed', 'abandoned',
            # 불편함
            'uncomfortable', 'sketchy', 'unsafe', 'dirty',
            'smelly', 'run down', 'needs work', 'neglected',
            # 부정
            'boring', 'dull', 'nothing to do', 'bland'
        ]
        
        pos = sum(any(k in t.lower() for k in positive) for t in reviews_text)
        neg = sum(any(k in t.lower() for k in negative) for t in reviews_text)
        
        score = ((pos - neg) / len(reviews_text) * 10) if reviews_text else 0
        
        results.append({
            'bench_id': idx,
            'lat': lat,
            'lon': lon,
            'score': score,
            'reviews': len(reviews_text),
            'positive_count': pos,
            'negative_count': neg
        })
        
    except Exception as e:
        print(f"Error: {e}")

pd.DataFrame(results).to_csv('bench_scores_v2.csv', index=False)
print(f"완료! {len(results)}개 벤치 분석됨")