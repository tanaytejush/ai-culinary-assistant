# API Setup Guide

## Current Status: API Key Required

Your AI Culinary Assistant is **functional but needs a valid API key** to work properly. The current API key in the `.env` file is invalid/expired.

## Quick Start

### 1. Get a FREE Spoonacular API Key

1. Visit: https://spoonacular.com/food-api
2. Click **"Get Access"** or **"Start Now"**
3. Create a free account (takes 2 minutes)
4. Go to your dashboard: https://spoonacular.com/food-api/console#Dashboard
5. Copy your API key

**Free Tier Benefits:**
- 150 API calls per day
- No credit card required
- Perfect for development and testing

### 2. Update Your .env File

Open `.env` file and replace the placeholder:

```bash
SPOONACULAR_API_KEY=YOUR_ACTUAL_API_KEY_HERE
```

### 3. Start the Application

```bash
python3 app.py
```

The app will automatically validate your API key on startup!

## API Health Check

Once the server is running, check API health:

```bash
# Visit in browser:
http://localhost:5000/api/health

# Or use curl:
curl http://localhost:5000/api/health
```

### Expected Health Check Response

**With Valid API Key:**
```json
{
  "status": "healthy",
  "api_key_configured": true,
  "spoonacular_api": "connected",
  "api_quota_left": "150"
}
```

**Without Valid API Key:**
```json
{
  "status": "degraded",
  "api_key_configured": false,
  "spoonacular_api": "invalid_key"
}
```

## Features & Error Handling

### ✓ What Works Now

1. **Automatic Retry Logic**: API calls retry up to 3 times on failure
2. **Graceful Fallback**: Uses default recipes if API is unavailable
3. **Startup Validation**: Checks API key when server starts
4. **Health Monitoring**: `/api/health` endpoint for status checks
5. **Better Error Messages**: Clear error reporting in UI
6. **Timeout Protection**: 10-second timeout on all API calls
7. **Quota Tracking**: Shows remaining API calls in health check

### ✓ App Works Without API Key

Even without a valid API key, the app will:
- Start successfully
- Accept image uploads
- Return random food classifications
- Provide default recipes (Pizza, Butter Chicken, etc.)
- Display clear warnings about API status

## Troubleshooting

### "API Key Invalid" Error

1. Check `.env` file exists
2. Verify API key is copied correctly (no extra spaces)
3. Make sure you're using the key from https://spoonacular.com/food-api/console#Dashboard
4. Restart the server after updating `.env`

### "Quota Exceeded" Error

- Free tier: 150 calls/day
- Quota resets at midnight UTC
- Use fallback recipes until reset
- Consider upgrading plan if needed

### Connection Errors

- Check internet connection
- Verify firewall isn't blocking API requests
- Try health check endpoint to diagnose

## Testing the App

### 1. Test with Fallback Mode (No API Key)

```bash
# Works immediately, uses default recipes
python3 app.py
```

### 2. Test with Valid API Key

```bash
# Update .env first, then:
python3 app.py
# Should see: "✓ API Key Valid! Quota remaining: 150"
```

### 3. Upload a Food Image

1. Open http://localhost:5000
2. Upload a food image
3. See identification and recipe

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web interface |
| `/api/health` | GET | API health check |
| `/api/identify` | POST | Identify food from image |

## Next Steps

1. **Get your API key** (5 minutes)
2. **Update .env file** (30 seconds)
3. **Restart the app** (5 seconds)
4. **Start identifying food!** 🍕🍔🍜

## Support

If you encounter issues:
- Check console output for detailed error messages
- Visit health endpoint for diagnostics
- Review Spoonacular API docs: https://spoonacular.com/food-api/docs
- Check API dashboard: https://spoonacular.com/food-api/console#Dashboard
