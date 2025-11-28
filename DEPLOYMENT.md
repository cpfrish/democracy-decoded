# Deployment Guide

## Prerequisites

1. **Vercel Account**: Sign up at https://vercel.com
2. **Congress.gov API Key**: Get from https://api.congress.gov/sign-up/
3. **GitHub Repository**: Your code should be pushed to GitHub

## Step-by-Step Deployment

### 1. Install Vercel CLI

```bash
npm install -g vercel
```

### 2. Login to Vercel

```bash
vercel login
```

This will open your browser for authentication.

### 3. Link Your Project

```bash
cd /path/to/final-project-209-congress
vercel
```

Answer the prompts:
- **Set up and deploy**: Yes
- **Which scope**: Choose your account/team
- **Link to existing project**: No (first time)
- **What's your project's name**: `congress-analysis` (or your choice)
- **In which directory is your code located**: `./` (current directory)
- **Want to override settings**: No

Vercel will deploy to a preview URL.

### 4. Add Environment Variable

```bash
vercel env add CONGRESS_API_KEY
```

When prompted:
- **What's the value**: Paste your Congress.gov API key
- **Which environment**: Production (select using arrow keys)

### 5. Deploy to Production

```bash
vercel --prod
```

You'll get a production URL like: `https://congress-analysis.vercel.app`

### 6. Test Your API Endpoints

```bash
# Test basic data endpoint
curl https://your-app.vercel.app/api/congress-data

# Test photos endpoint
curl https://your-app.vercel.app/api/member-photos

# Test detailed analysis (slower)
curl "https://your-app.vercel.app/api/congress-data?detailed=true"
```

### 7. Generate Visualizations

Update `generate_api_charts.py` with your Vercel URL:

```python
API_BASE_URL = "https://your-app.vercel.app"
```

Then run:

```bash
python generate_api_charts.py
```

### 8. Push Visualizations to GitHub Pages

```bash
# Commit generated HTML files
git add visualizations/*.html
git commit -m "Add API-powered visualizations"
git push origin main
```

### 9. Configure GitHub Pages

1. Go to repository Settings → Pages
2. Source: Deploy from branch
3. Branch: `main` → `/docs` or `/` (depends on your setup)
4. Save

Your visualizations will be at:
`https://your-username.github.io/final-project-209-congress/visualizations/`

### 10. Embed in WordPress

```html
<iframe 
  src="https://your-username.github.io/final-project-209-congress/visualizations/generation_overview.html" 
  width="100%" 
  height="600" 
  frameborder="0"
  style="border: none;">
</iframe>
```

## Continuous Deployment

Vercel automatically redeploys when you push to `main` branch:

```bash
git checkout main
git pull
# Make changes...
git add .
git commit -m "Update API logic"
git push origin main
```

Vercel will detect the push and redeploy automatically.

## Updating Environment Variables

```bash
# Update existing variable
vercel env rm CONGRESS_API_KEY production
vercel env add CONGRESS_API_KEY production

# Redeploy to apply changes
vercel --prod
```

## Monitoring

View logs and analytics:
```bash
vercel logs https://your-app.vercel.app/api/congress-data
```

Or visit: https://vercel.com/dashboard

## Troubleshooting

### API Returns 500 Error
- Check logs: `vercel logs`
- Verify `CONGRESS_API_KEY` is set
- Test locally: `vercel dev`

### CORS Issues in WordPress
- Verify API responses include CORS headers
- Check WordPress security plugins aren't blocking iframes

### Charts Not Loading
- Verify GitHub Pages is published
- Check browser console for errors
- Hard refresh: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)

### Slow API Response
- Use `?detailed=false` parameter
- Consider upgrading Vercel plan for more function duration
- Check Congress.gov API status

## Cost Optimization

Vercel Free Tier includes:
- 100GB bandwidth/month
- 100 hours serverless function execution/month
- No credit card required

For your use case (academic project), free tier should be sufficient.

To monitor usage:
1. Go to Vercel Dashboard
2. Click your project
3. Analytics → Usage

## Team Collaboration

### Adding Team Members to Vercel

1. Go to Vercel Dashboard → Settings → Members
2. Invite team members by email
3. They can deploy using `vercel --prod`

### Shared Environment Variables

All team members with access can view/edit env vars in dashboard.

## Next Steps

1. ✅ Deploy API to Vercel
2. ✅ Generate visualizations
3. ✅ Push to GitHub Pages
4. ✅ Embed in WordPress
5. 🎉 Share your live site!
