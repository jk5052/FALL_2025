# NYC Reddit Emotion Collector - Quick Start

## Setup (10분)

### 1. Install Dependencies
```bash
pip install praw openai python-dotenv geopy
```

### 2. Get Reddit API Keys
1. Go to https://www.reddit.com/prefs/apps
2. Scroll down, click "create another app..."
3. Fill in:
   - name: "NYC Emotion Mapper"
   - type: select "script"
   - description: "Collecting NYC emotions"
   - redirect uri: http://localhost:8080
4. Click "create app"
5. Copy:
   - **client_id** (under app name)
   - **client_secret** (next to "secret")

### 3. Get OpenAI API Key
1. Go to https://platform.openai.com/api-keys
2. Create new secret key
3. Copy the key

### 4. Create .env File
```bash
cp .env.template .env
nano .env  # or use any text editor
```

Paste your keys:
```
REDDIT_CLIENT_ID=abc123xyz
REDDIT_CLIENT_SECRET=def456uvw
OPENAI_API_KEY=sk-proj-...
```

### 5. Run Collection
```bash
python collect_reddit_emotions.py
```

This will:
- Search r/nyc, r/AskNYC, r/newyorkcity, etc.
- Extract locations from posts (using OpenAI)
- Analyze emotions
- Save to GeoJSON

**Expected time:** 20-40 minutes (depending on posts found)

## Output Files

- `reddit_emotions.geojson` - For map visualization
- `reddit_emotions_raw.json` - All collected data
- `reddit_emotions_by_date.json` - Grouped by date

## Troubleshooting

**"No data collected"**
- Increase `limit_per_sub` (line 181)
- Increase `days_back` (line 181)
- Check if subreddits are active

**"Rate limit"**
- OpenAI: Increase `time.sleep(2)` to `time.sleep(5)`
- Reddit: Already has built-in rate limiting

**"Location not found"**
- Add more locations to `NYC_LOCATIONS` dict (line 18)
- Check OpenAI output in console

## Quick Test

If you want to test quickly:
```python
# In collect_reddit_emotions.py, change line 181:
data = collect_reddit_data(days_back=30, limit_per_sub=20)
```

This will be faster but collect less data.

## Cost Estimate

**OpenAI API:**
- ~$0.002 per post analyzed
- 100 posts = ~$0.20
- 500 posts = ~$1.00

**Reddit API:**
- Free

## Next Steps

After collection:
1. Check `reddit_emotions.geojson` has data
2. Load into Mapbox visualization
3. Add temporal slider
4. Show emotion changes over time
