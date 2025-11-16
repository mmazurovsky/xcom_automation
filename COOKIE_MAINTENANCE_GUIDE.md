# Cookie Maintenance Guide

## How Often Should You Refresh Cookies?

### Normal Usage
- **Cookies last**: 30-60+ days typically
- **Check frequency**: Once per week
- **Refresh**: Only when expired or showing errors

### Production Best Practices
- **Proactive check**: Every 3-7 days
- **Automated monitoring**: Set up health checks (see below)
- **Alert threshold**: Refresh if cookies are >45 days old

---

## Cookie Lifespan Factors

Cookies stay valid longer if:
- ✅ Account is actively used (API calls count as activity)
- ✅ Using consistent IP addresses (proxy helps here)
- ✅ No suspicious behavior detected
- ✅ Account in good standing

Cookies expire faster if:
- ❌ Long periods of inactivity
- ❌ IP address changes frequently
- ❌ Rate limit violations
- ❌ Account flagged by Twitter

---

## Monitoring Setup

### Option 1: Manual Check (Weekly)

Run this command once per week:

```bash
python check_cookie_health.py
```

Expected output if healthy:
```
✅ Cookies are valid!
💚 Cookie Health: HEALTHY
```

Expected output if expired:
```
❌ Cookie Health: EXPIRED or INVALID
⚠️  AUTHENTICATION FAILED
📋 Action Required: [steps to refresh]
```

### Option 2: API Endpoint (Automated)

You now have a cookie health endpoint! Test it:

```bash
curl http://localhost:8000/cookie-health/applyfirst_app
```

Response when healthy:
```json
{
  "username": "applyfirst_app",
  "cookie_status": "healthy",
  "authenticated": true,
  "account_name": "Your Account Name",
  "message": "Cookies are valid and working"
}
```

Response when expired (401 status):
```json
{
  "username": "applyfirst_app",
  "cookie_status": "expired",
  "authenticated": false,
  "message": "Cookies have expired - please refresh"
}
```

### Option 3: Cron Job (Production)

Set up weekly automated checks:

**On Mac/Linux:**
```bash
# Edit crontab
crontab -e

# Add this line (runs every Monday at 9 AM)
0 9 * * 1 cd /Users/mmazurovsky/Code/MyProjects/xcom_automation && /usr/bin/python3 check_cookie_health.py >> cookie_check.log 2>&1

# Add this line (sends email if check fails)
0 9 * * 1 cd /Users/mmazurovsky/Code/MyProjects/xcom_automation && /usr/bin/python3 check_cookie_health.py || echo "Cookie check failed for Twitter automation" | mail -s "Action Required: Refresh Twitter Cookies" your@email.com
```

**Via Monitoring Service (Better for Production):**

Use something like UptimeRobot, Cronitor, or Healthchecks.io to ping:
```
https://your-deployed-service.com/cookie-health/applyfirst_app
```

Set up alerts for:
- HTTP 401 responses (cookies expired)
- HTTP 500 errors (service issues)
- No response (service down)

---

## When to Refresh Cookies

### Immediate Refresh Required:
1. **Tweet posting fails** with authentication errors
2. **Cookie health check** returns "expired"
3. **Service logs** show 401/authentication errors
4. **After 45+ days** of same cookies (proactive refresh)

### How to Refresh:

```bash
# 1. Export fresh cookies from browser
# 2. Save as cookies.json
# 3. Import to MongoDB
python manual_cookie_setup.py

# 4. Restart service
# Ctrl+C to stop, then:
python -m app.main
```

---

## Production Recommendations

### Weekly Routine:
```bash
# Monday morning - check cookie health
python check_cookie_health.py

# If healthy: do nothing
# If expired: refresh cookies (5 minutes)
```

### Monthly Routine:
- Review service logs for any auth errors
- Proactive cookie refresh (even if not expired)
- Test tweet posting to verify everything works

### Quarterly:
- Update dependencies (`pip install -U -r requirements.txt`)
- Review Twitter account status on web
- Verify proxy is still working well

---

## Signs Cookies Need Refresh

Watch for these in your logs:

```
❌ 401 Unauthorized
❌ Could not authenticate you
❌ Invalid or expired token
❌ Authentication credentials were missing or incorrect
```

If you see any of these → refresh cookies immediately!

---

## Quick Reference

| Task | Command |
|------|---------|
| Check cookie health | `python check_cookie_health.py` |
| Check via API | `curl localhost:8000/cookie-health/applyfirst_app` |
| Export new cookies | Use Cookie-Editor extension on https://x.com |
| Import cookies | `python manual_cookie_setup.py` |
| Restart service | `python -m app.main` |
| Test posting | `python test_tweet.py` |

---

## Summary

**Short answer**: Check weekly, refresh when expired (usually 30-60 days)

**Best practice**:
- Set up automated weekly health checks
- Refresh cookies proactively every 4-6 weeks
- Keep spare cookies exported for quick replacement
- Monitor service logs for authentication errors

Your cookies should last at least a month with normal usage! 🎉
