# How to Export Twitter Cookies (Bypass Cloudflare 403)

Since automated login is blocked by Cloudflare, we'll use cookies from a manual login session.

## Method 1: Using Cookie-Editor Extension (Recommended)

### Step 1: Install Extension
- Chrome: https://chrome.google.com/webstore/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm
- Firefox: https://addons.mozilla.org/firefox/addon/cookie-editor/

### Step 2: Login to Twitter
1. Open https://x.com in your browser
2. Log in with your account: **applyfirst_app**
3. Make sure you're fully logged in (see your feed)

### Step 3: Export Cookies
1. Click the Cookie-Editor extension icon
2. Click "Export" button (bottom right)
3. Choose "JSON" format
4. Save the file as `cookies.json` in your project directory:
   `/Users/mmazurovsky/Code/MyProjects/xcom_automation/cookies.json`

### Step 4: Import to MongoDB
```bash
cd /Users/mmazurovsky/Code/MyProjects/xcom_automation
python manual_cookie_setup.py
```

### Step 5: Restart Service
```bash
# Ctrl+C to stop the service if running
python -m app.main
```

You should now see:
```
INFO - Loaded session from database for: applyfirst_app
```

Instead of:
```
WARNING - No cookies found for account: applyfirst_app
```

---

## Method 2: Using Browser DevTools (Manual)

### Step 1: Login to Twitter
1. Open https://x.com
2. Login as **applyfirst_app**

### Step 2: Open DevTools
1. Press `F12` or `Cmd+Option+I` (Mac)
2. Go to **Application** tab (Chrome) or **Storage** tab (Firefox)
3. Click **Cookies** → **https://x.com**

### Step 3: Copy Important Cookies
Look for these cookies and copy their values:
- `auth_token` (most important!)
- `ct0`
- `kdt`
- `twid`

### Step 4: Create cookies.json manually
Create a file with this format:

```json
{
  "auth_token": "your_auth_token_value_here",
  "ct0": "your_ct0_value_here",
  "kdt": "your_kdt_value_here",
  "twid": "your_twid_value_here"
}
```

### Step 5: Import
```bash
python manual_cookie_setup.py
```

---

## Verification

After importing cookies, test with:
```bash
python test_tweet.py
```

You should see a successful tweet post!

---

## Why This Works

- ✅ Bypasses Cloudflare's anti-bot detection (cookies from real browser session)
- ✅ No automated login needed (uses existing authenticated session)
- ✅ Cookies stored in MongoDB (persist across restarts)
- ✅ Proxy will be used for all API calls after authentication

## Troubleshooting

**Cookies expired?**
- Cookies typically last 30+ days
- Just export fresh cookies and import again
- Set up the `/refresh-session` endpoint to handle this

**Service still failing?**
- Make sure you exported ALL cookies, not just a few
- Verify cookies.json is valid JSON format
- Check MongoDB connection is working
