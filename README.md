# Congressional Generational Analysis - Serverless Architecture

This project analyzes U.S. Congressional members using a serverless API architecture deployed on Vercel, with visualizations hosted on GitHub Pages and embedded in WordPress.

## 🏗️ Architecture Overview

```
Congress.gov API → Vercel Serverless Functions (Python)
                 ↓
               JSON API Endpoints (/api/congress-data, /api/member-photos)
                 ↓
               Altair Charts (load from API URLs)
                 ↓
               GitHub Pages (static HTML hosting)
                 ↓
               WordPress (iframe embeds)
```

## 🚀 Quick Start

### 1. Deploy to Vercel

```bash
# Install Vercel CLI
npm i -g vercel

# Login to Vercel
vercel login

# Deploy (from project root)
vercel

# Add your API key as environment variable
vercel env add CONGRESS_API_KEY
```

After deployment, you'll get a URL like: `https://your-project.vercel.app`

### 2. Generate Visualizations

```bash
# Update generate_api_charts.py with your Vercel URL
# Then run:
python generate_api_charts.py
```

This creates HTML files in `visualizations/` that load from your API.

### 3. Push to GitHub Pages

```bash
# Commit visualizations
git add visualizations/*.html
git commit -m "Add API-powered visualizations"

# Push to gh-pages branch (or configure docs/ folder in Settings)
git push origin main
```

### 4. Embed in WordPress

```html
<iframe 
  src="https://your-username.github.io/final-project-209-congress/visualizations/generation_overview.html" 
  width="800" 
  height="600" 
  frameborder="0">
</iframe>
```

## 📁 Project Structure

### API Endpoints (`/api/`)

- **`/api/congress-data.py`** - Main congressional data endpoint
  - Returns: member list, generational summary, optional topic analysis
  - Query params: `?detailed=true` for bill topics (slower)
  - Cache: 1 hour

- **`/api/member-photos.py`** - Member data with official photos
  - Returns: all members with bioguide IDs and photo URLs
  - Cache: 6 hours (photos rarely change)

### Core Libraries

- **`congress_api_client.py`** - Congress.gov API wrapper (no CSV output)
- **`congress_photo_api.py`** - Photo fetching from unitedstates/images
- **`generate_api_charts.py`** - Creates Altair charts that load from API

### Configuration

- **`vercel.json`** - Vercel deployment config
- **`requirements.txt`** - Python dependencies for serverless functions

## 🔑 Environment Variables

**Required:**
- `CONGRESS_API_KEY` - Get from https://api.congress.gov/sign-up/

**Setup in Vercel:**
```bash
vercel env add CONGRESS_API_KEY production
```

## 📊 API Endpoints Usage

### Get Congressional Data (Basic)
```
GET https://your-app.vercel.app/api/congress-data
```

Response:
```json
{
  "data": {
    "members": [...],
    "summary": [
      {
        "generation": "Baby Boomer",
        "member_count": 245,
        "total_bills": 12450,
        "avg_bills_per_member": 50.82
      }
    ]
  },
  "metadata": {
    "timestamp": "2025-11-27T10:30:00Z",
    "cache_ttl": 3600
  }
}
```

### Get Congressional Data (With Topics)
```
GET https://your-app.vercel.app/api/congress-data?detailed=true
```

Adds `topics` array with bill categorizations (slower, use sparingly).

### Get Member Photos
```
GET https://your-app.vercel.app/api/member-photos
```

Response includes `photo_url` (official or fallback) for each member.

## 🎨 Visualization Patterns

### Loading Data from API in Altair

```python
import altair as alt

# Load from your API
data = alt.Data(
    url='https://your-app.vercel.app/api/congress-data',
    format=alt.DataFormat(property='data.summary', type='json')
)

chart = alt.Chart(data).mark_bar().encode(
    x='generation:N',
    y='member_count:Q'
)
```

### Party Color Standards
- Democrat: `#2E86AB` (blue)
- Republican: `#C23B22` (red)
- Independent: `#9966CC` (purple)

### Generation Classification (Birth Years)
- Silent Generation: 1928-1945
- Baby Boomer: 1946-1964
- Gen X: 1965-1980
- Millennial: 1981-1996
- Gen Z: 1997+

## ⚡ Performance Optimization

### API Caching Strategy
- **Congress data**: 1 hour cache (members change infrequently)
- **Photos**: 6 hour cache (photos almost never change)
- **Browser cache**: Respects `Cache-Control` headers

### Rate Limiting
- Built-in `time.sleep()` delays in API client:
  - 0.25s between member detail requests
  - 0.05s during photo fetching
- Vercel function timeout: 10 seconds (configurable)

### Photo URL Priority
1. GitHub unitedstates/images (225x275) - fastest
2. theunitedstates.io mirror
3. GitHub original size
4. Bioguide.gov subdirectory
5. Bioguide.gov direct
6. Fallback: placeholder with initials

## 🔄 Development Workflow

### Local Testing
```bash
# Install Vercel CLI dev server
vercel dev

# Your API will be at:
# http://localhost:3000/api/congress-data
# http://localhost:3000/api/member-photos
```

### Testing API Locally
```bash
# Set environment variable
export CONGRESS_API_KEY="your_key_here"

# Test the core functions
python -c "from congress_api_client import fetch_congress_members_json; print(fetch_congress_members_json())"
```

### Adding New Bill Topics

Edit `categorize_bill_topic()` in `congress_api_client.py`:

```python
topic_keywords = {
    'YourNewTopic': ['keyword1', 'keyword2', 'keyword3'],
    # ... existing topics
}
```

## ⚠️ Common Issues

1. **CORS errors in WordPress iframe**
   - APIs include `Access-Control-Allow-Origin: *` headers
   - If issues persist, check WordPress CSP settings

2. **Slow API responses**
   - Use `?detailed=false` (default) for faster responses
   - Consider increasing Vercel function memory/timeout

3. **API key not found**
   - Verify in Vercel dashboard: Settings → Environment Variables
   - Redeploy after adding env vars: `vercel --prod`

4. **Charts not updating**
   - Check browser cache (Ctrl+Shift+R to hard refresh)
   - Verify API returns fresh `timestamp` in metadata

## 🚫 What NOT to Do

- ❌ Don't commit CSV files to git anymore
- ❌ Don't run `python_analyzer.py` manually for production
- ❌ Don't use `detailed=true` in WordPress embeds (too slow)
- ❌ Don't store API keys in code (use Vercel env vars)

## 👥 Team Collaboration

### Branch Strategy
- `main` - production code, auto-deploys to Vercel
- `dev_*` - feature branches for team members
- `gh-pages` - static HTML visualizations (auto-generated)

### Making Changes
1. Create feature branch: `git checkout -b dev_yourname`
2. Test locally: `vercel dev`
3. Push to GitHub: `git push origin dev_yourname`
4. Merge to main after review
5. Vercel auto-deploys on main branch push

### Updating Visualizations
1. Update `generate_api_charts.py`
2. Run: `python generate_api_charts.py`
3. Commit HTML files
4. Push to trigger GitHub Pages update

## 📚 Key Dependencies

- **requests** - HTTP client for Congress.gov API
- **pandas** - Data manipulation (minimal use now)
- **altair** - Declarative visualizations
- **numpy** - Numerical operations

## 🔗 External Services

- **Congress.gov API** - Primary data source
- **GitHub unitedstates/images** - Official photos
- **Vercel** - Serverless function hosting
- **GitHub Pages** - Static HTML hosting
- **WordPress** - Final iframe presentation

## 📖 Further Reading

- [Vercel Python Runtime Docs](https://vercel.com/docs/functions/runtimes/python)
- [Altair Data from URLs](https://altair-viz.github.io/user_guide/data.html#data-from-url)
- [Congress.gov API Docs](https://api.congress.gov/)
