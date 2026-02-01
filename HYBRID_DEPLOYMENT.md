# Hybrid Deployment Guide: Static Site + API Backend

This guide covers deploying your trivia card generator as a split architecture:
- **Static HTML on Awebsolutions** (your existing cPanel hosting)
- **API Backend on Render** (free Python hosting)

## Benefits
✅ Use your existing paid hosting
✅ Free Python backend (Render free tier)
✅ No server management needed
✅ Simple deployment process

---

## Part 1: Deploy API Backend to Render (5 minutes)

### Step 1: Push Code to GitHub
Your code is already in a git repository. Push it to GitHub:

```bash
# If you haven't set a remote yet
git remote add origin https://github.com/YOUR-USERNAME/trivia-card-generator.git

# Push your code
git push -u origin main
```

### Step 2: Create Render Account
1. Go to https://render.com
2. Sign up with GitHub (free account)
3. Authorize Render to access your repositories

### Step 3: Deploy the API
1. Click **"New +"** → **"Web Service"**
2. Select your `trivia-card-generator` repository
3. Render will auto-detect settings from your `Procfile`:
   - **Build Command**: `pip install -r requirements-web.txt`
   - **Start Command**: `gunicorn app:app` (from Procfile)
4. Click **"Create Web Service"**

### Step 4: Wait for Deployment
- First deployment takes 2-3 minutes
- Render will show build logs in real-time
- When complete, you'll get a URL like: `https://trivia-card-generator-xyz.onrender.com`

### Step 5: Test the API
```bash
# Test with curl (replace with your actual URL)
curl https://YOUR-APP-NAME.onrender.com/

# You should see: "Trivia Card Generator API is running!"
```

**⚠️ Important**: Free tier apps sleep after 15 minutes of inactivity. First request after sleep takes ~30 seconds to wake up.

---

## Part 2: Upload Static Site to Awebsolutions

### Step 1: Update API URL
1. Open `static-site/index.html` in a text editor
2. Find this line (around line 263):
   ```javascript
   const API_URL = 'https://YOUR-APP-NAME.onrender.com/api/generate';
   ```
3. Replace `YOUR-APP-NAME` with your actual Render app URL
4. Save the file

### Step 2: Upload to cPanel
1. Log into your Awebsolutions cPanel
2. Click **"File Manager"**
3. Navigate to `public_html` (or your site's root directory)
4. Create a folder called `trivia-cards`
5. Upload `index.html` to `public_html/trivia-cards/`
6. Set file permissions to **644** (right-click → Permissions)

### Step 3: Test Your Site
Visit: `https://yourdomain.com/trivia-cards/`

You should see the trivia card generator interface.

---

## Testing the Complete System

1. **Upload a CSV file** through the web interface
2. **Click "Generate Cards"**
3. The browser calls your Render API
4. Render generates the PDF
5. PDF downloads to your computer

**First request may take 30 seconds** if the Render app was sleeping.

---

## Troubleshooting

### Error: "Network error. Please check the API URL"
- ✅ Check the `API_URL` in `index.html` matches your Render URL
- ✅ Test API directly: visit `https://YOUR-APP.onrender.com/`
- ✅ Check browser console (F12) for CORS errors

### Error: "Failed to generate cards"
- ✅ Check CSV format (6 unique subjects per card)
- ✅ Check Render logs: Dashboard → Your Service → Logs

### Slow First Request
- This is normal for free tier (apps sleep after 15 min)
- Paid tier ($7/month) keeps apps always-on

### CORS Errors
Your Flask app already has CORS enabled:
```python
CORS(app, resources={r"/api/*": {"origins": "*"}})
```

---

## Updating Your App

### Update API Backend (Render)
```bash
git add .
git commit -m "Update feature X"
git push

# Render auto-deploys on every push
```

### Update Static Site (Awebsolutions)
1. Edit `static-site/index.html` locally
2. Upload to cPanel File Manager
3. Overwrite existing file

---

## Cost Breakdown

| Service | Tier | Cost |
|---------|------|------|
| Awebsolutions | Your current plan | £2.50-£10/month |
| Render API | Free tier | £0/month |
| **Total** | | **Your existing hosting cost only** |

### Render Free Tier Limits
- ✅ 750 hours/month (plenty for personal use)
- ✅ Auto-sleep after 15 min inactivity
- ✅ 100GB bandwidth/month
- ❌ Slower cold starts (30 sec wake up)

**Upgrade to Render paid ($7/month) if you need**:
- Always-on (no sleep)
- Faster response times
- Custom domain

---

## Security Notes

Your setup is secure:
✅ HTTPS on both Render and Awebsolutions (free SSL)
✅ CORS properly configured
✅ File upload validation (10MB limit, CSV only)
✅ Secure filename handling
✅ Temporary file cleanup
✅ No sensitive data stored

---

## Alternative: Custom Domain on Render

If you want `cards.yourdomain.com` pointing to Render:

1. In Render Dashboard → Custom Domains
2. Add `cards.yourdomain.com`
3. Add CNAME record in Awebsolutions DNS:
   ```
   Type: CNAME
   Name: cards
   Value: YOUR-APP.onrender.com
   ```
4. Update `API_URL` in `index.html` to use your custom domain

---

## Support

- **Render Docs**: https://render.com/docs
- **Render Status**: https://status.render.com
- **Awebsolutions Support**: https://awebsolutions.uk/client/submitticket.php

---

## Quick Reference

**Your API Endpoints**:
- Health check: `GET https://YOUR-APP.onrender.com/`
- Generate cards: `POST https://YOUR-APP.onrender.com/api/generate`

**Your Static Site**:
- URL: `https://yourdomain.com/trivia-cards/`
- File location: `public_html/trivia-cards/index.html`

**GitHub Repository**:
- Push updates: `git push`
- Render auto-deploys: ~2 minutes
