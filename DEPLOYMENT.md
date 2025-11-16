# Deployment Guide - Twitter Automation Service

This guide covers deploying the Twitter automation FastAPI service to Digital Ocean App Platform using Docker containers.

## Prerequisites

Before deploying, ensure you have:

1. **Digital Ocean Account** with:
   - Container Registry created (`mmazurovsky-registry`)
   - MongoDB cluster running (DigitalOcean Managed MongoDB)
   - App Platform access

2. **Local Tools Installed**:
   - Docker Desktop
   - `doctl` (DigitalOcean CLI) - [Install Guide](https://docs.digitalocean.com/reference/doctl/how-to/install/)

3. **Authentication**:
   - Twitter account credentials
   - Geonode proxy credentials
   - MongoDB connection details

---

## One-Time Setup

### 1. Install DigitalOcean CLI (doctl)

**macOS:**
```bash
brew install doctl
```

**Linux:**
```bash
cd ~
wget https://github.com/digitalocean/doctl/releases/download/v1.94.0/doctl-1.94.0-linux-amd64.tar.gz
tar xf ~/doctl-1.94.0-linux-amd64.tar.gz
sudo mv ~/doctl /usr/local/bin
```

### 2. Authenticate with Digital Ocean

```bash
# Get API token from: https://cloud.digitalocean.com/account/api/tokens
doctl auth init

# Verify authentication
doctl account get
```

### 3. Login to Container Registry

```bash
doctl registry login
```

This authenticates Docker to push images to your Digital Ocean Container Registry.

---

## Deployment Process

### Step 1: Prepare Environment Variables

Review your local `.env` file to see all required environment variables. You'll configure these same variables in Digital Ocean App Platform at the OS level.

**Required variables (same as your .env file):**
- `MONGO_USER`, `MONGO_PASSWORD`, `MONGO_HOST`, `MONGO_PORT`, `MONGO_DB`
- `API_KEY`
- `TWITTER_ACCOUNTS` (JSON array string)
- `PROXY_SERVER`, `PROXY_USERNAME`, `PROXY_PASSWORD`, `PROXY_PORTS`
- `APP_HOST`, `APP_PORT`, `LOG_LEVEL`

**Note:** In Digital Ocean, these will be provided at the OS level (not from an .env file).

### Step 2: Build and Push Docker Image

```bash
# Make sure you're in the project directory
cd /Users/mmazurovsky/Code/MyProjects/xcom_automation

# Run the deployment script
./deploy.sh
```

**What this does:**
1. Enables Docker BuildKit for optimized builds
2. Builds multi-stage Docker image
3. Tags as: `registry.digitalocean.com/mmazurovsky-registry/xcom-automation`
4. Pushes to Digital Ocean Container Registry

**Expected output:**
```
Building and pushing xcom-automation to Digital Ocean Container Registry...
[+] Building 45.2s (15/15) FINISHED
...
✅ Build and push completed successfully!
📦 Image: registry.digitalocean.com/mmazurovsky-registry/xcom-automation
```

### Step 3: Create App in Digital Ocean

#### Option A: Using Web Console

1. Go to [Digital Ocean App Platform](https://cloud.digitalocean.com/apps)
2. Click **"Create App"**
3. Choose **"DigitalOcean Container Registry"**
4. Select repository: `mmazurovsky-registry/xcom-automation`
5. Click **"Next"**

**Configure App:**
- **Name**: `xcom-automation`
- **Region**: Choose closest to your users (e.g., `fra1` for Europe)
- **Instance Type**: Basic ($5/month) or Professional based on needs
- **HTTP Port**: `8000`

**Environment Variables:**
Add all variables from your local `.env` file (with your actual production values):

```
MONGO_USER=doadmin
MONGO_PASSWORD=your_mongodb_password
MONGO_HOST=your-mongodb-host.mongo.ondigitalocean.com
MONGO_PORT=25060
MONGO_DB=xcom_automation
API_KEY=your_secure_api_key
TWITTER_ACCOUNTS=[{"username":"applyfirst_app","email":"email@example.com","password":"password"}]
PROXY_SERVER=proxy.geonode.io
PROXY_USERNAME=geonode_xxx
PROXY_PASSWORD=xxx
PROXY_PORTS=9001
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=info
```

**Health Check:**
- **HTTP Path**: `/health`
- **HTTP Port**: `8000`
- **Initial Delay**: 40 seconds
- **Period**: 30 seconds
- **Timeout**: 10 seconds
- **Success Threshold**: 1
- **Failure Threshold**: 3

6. Click **"Next"** → **"Create Resources"**

#### Option B: Using doctl CLI

Create `app.yaml`:

```yaml
name: xcom-automation
region: fra1
services:
  - name: xcom-automation
    image:
      registry_type: DOCR
      repository: xcom-automation
      tag: latest
    instance_count: 1
    instance_size_slug: basic-xxs
    http_port: 8000
    health_check:
      http_path: /health
      initial_delay_seconds: 40
      period_seconds: 30
      timeout_seconds: 10
      success_threshold: 1
      failure_threshold: 3
    envs:
      - key: MONGO_USER
        value: doadmin
      - key: MONGO_PASSWORD
        value: your_password
        type: SECRET
      - key: MONGO_HOST
        value: your-host.mongo.ondigitalocean.com
      # ... add all other env vars
```

Deploy:
```bash
doctl apps create --spec app.yaml
```

### Step 4: Import Twitter Cookies

Since automated login is blocked by Cloudflare, you need to manually export cookies:

1. **On your local machine**:
   - Open https://x.com and login as your Twitter account
   - Use [Cookie-Editor](https://chrome.google.com/webstore/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm) extension
   - Export cookies as JSON
   - Save as `cookies.json`

2. **Import to MongoDB**:
   ```bash
   # Connect to your production MongoDB and import cookies
   python manual_cookie_setup.py
   ```

   Or use MongoDB Compass/CLI to insert cookies directly into your production MongoDB.

### Step 5: Verify Deployment

1. **Check app status**:
   ```bash
   doctl apps list
   doctl apps get <app-id>
   ```

2. **View logs**:
   ```bash
   doctl apps logs <app-id> --type=run
   ```

3. **Test health endpoint**:
   ```bash
   curl https://xcom-automation-xxxxx.ondigitalocean.app/health
   ```

   Expected response:
   ```json
   {
     "status": "healthy",
     "database": "connected",
     "accounts": ["applyfirst_app"]
   }
   ```

4. **Test tweet posting**:
   ```bash
   curl -X POST https://xcom-automation-xxxxx.ondigitalocean.app/tweet \
     -H "Content-Type: application/json" \
     -H "X-API-Key: your_api_key" \
     -d '{
       "username": "applyfirst_app",
       "text": "Hello from Digital Ocean! 🚀"
     }'
   ```

---

## Updating the Deployment

### When you make code changes:

```bash
# 1. Build and push new image
./deploy.sh

# 2. Trigger redeployment in Digital Ocean
doctl apps create-deployment <app-id>

# Or use the web console:
# - Go to your app in DO dashboard
# - Click "Actions" → "Force Rebuild and Deploy"
```

### When you update environment variables:

```bash
# Update via web console or:
doctl apps update <app-id> --spec app.yaml
```

### When cookies expire:

1. Export fresh cookies from browser
2. Import to production MongoDB
3. Restart the app (or it will auto-retry on next API call)

---

## Monitoring

### Check Application Status

**Digital Ocean Dashboard:**
- Go to App Platform → Your App
- View: Metrics, Logs, Runtime Logs

**Using doctl:**
```bash
# App info
doctl apps get <app-id>

# Recent logs
doctl apps logs <app-id> --type=run --follow

# Deployments
doctl apps list-deployments <app-id>
```

### Health Monitoring

Set up external monitoring with:
- [UptimeRobot](https://uptimerobot.com/)
- [Pingdom](https://www.pingdom.com/)
- [Healthchecks.io](https://healthchecks.io/)

Monitor endpoint: `https://your-app.ondigitalocean.app/health`

Alert on:
- HTTP 500 errors (service issues)
- HTTP 401 errors (cookie expiration)
- No response (service down)

### Cookie Health

Check cookie status:
```bash
curl https://your-app.ondigitalocean.app/cookie-health/applyfirst_app
```

Response indicates if cookies need refresh.

---

## Troubleshooting

### Build fails

```bash
# Check Docker is running
docker ps

# Try cleaning Docker cache
docker system prune -a

# Rebuild without cache
docker compose build --no-cache xcom-automation
```

### Push fails

```bash
# Re-authenticate with registry
doctl registry login

# Check registry exists
doctl registry get
```

### App won't start

1. Check logs in DO dashboard
2. Verify all environment variables are set
3. Check MongoDB is accessible from DO network
4. Verify health check endpoint is responding

### Tweet posting fails

1. Check cookies are imported to MongoDB
2. Verify proxy credentials are correct
3. Check Twitter account credentials
4. Review app logs for errors

### Database connection fails

1. Verify MongoDB connection string
2. Check MongoDB cluster is running
3. Ensure app is in same region (or VPC configured)
4. Check firewall rules allow connection

---

## Architecture

```
┌─────────────────────────────────────────────┐
│   Digital Ocean App Platform                │
│   ┌─────────────────────────────────────┐   │
│   │  Container: xcom-automation         │   │
│   │  Image: registry.digitalocean.com/  │   │
│   │         mmazurovsky-registry/       │   │
│   │         xcom-automation:latest      │   │
│   │                                     │   │
│   │  Port: 8000                         │   │
│   │  Health: /health                    │   │
│   └─────────────────────────────────────┘   │
│                    │                         │
│                    ▼                         │
│   ┌─────────────────────────────────────┐   │
│   │  Environment Variables              │   │
│   │  (Injected at runtime)              │   │
│   └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│   DigitalOcean Managed MongoDB              │
│   (Session/Cookie Storage)                  │
└─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│   Geonode Proxy (proxy.geonode.io:9001)    │
│   (All Twitter API requests)                │
└─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│   Twitter/X API                             │
└─────────────────────────────────────────────┘
```

---

## Cost Estimate

| Service | Plan | Cost/Month |
|---------|------|------------|
| App Platform | Basic (512MB RAM, 1 vCPU) | $5 |
| Container Registry | Basic (500MB storage) | Free |
| MongoDB | Basic (1GB RAM) | $15 |
| Bandwidth | 1TB included | Free |
| **Total** | | **~$20/month** |

Plus Geonode proxy costs (separate subscription).

---

## Security Checklist

- ✅ Environment variables stored securely in DO (encrypted)
- ✅ No credentials in Docker image or git repo
- ✅ API key required for all write endpoints
- ✅ MongoDB uses TLS/SSL
- ✅ Proxy used for all Twitter requests (masks server IP)
- ✅ Container runs as non-root user
- ✅ Health checks don't expose sensitive data
- ✅ Logs don't contain passwords or tokens

---

## Support

- **Digital Ocean Docs**: https://docs.digitalocean.com/products/app-platform/
- **Docker Docs**: https://docs.docker.com/
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Twikit Docs**: https://twikit.readthedocs.io/

---

## Quick Reference

| Task | Command |
|------|---------|
| Deploy new version | `./deploy.sh && doctl apps create-deployment <app-id>` |
| View logs | `doctl apps logs <app-id> --type=run --follow` |
| List apps | `doctl apps list` |
| Get app info | `doctl apps get <app-id>` |
| Test health | `curl https://your-app.ondigitalocean.app/health` |
| Check cookies | `curl https://your-app.ondigitalocean.app/cookie-health/applyfirst_app` |
| Force rebuild | Web console → Actions → Force Rebuild and Deploy |

---

**Last Updated**: 2025-11-16
