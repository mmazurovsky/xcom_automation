# Twitter Automation API

A FastAPI-based service for automated tweet posting using the [Twikit](https://github.com/d60/twikit) library. This service allows you to post tweets on behalf of pre-configured Twitter accounts through a simple REST API with API key authentication.

## Features

- **Multiple Account Support**: Manage multiple Twitter accounts from a single service
- **Persistent Sessions**: Store Twitter session cookies in MongoDB for faster authentication
- **API Key Authentication**: Secure your endpoints with API key authentication
- **Retry Logic**: Automatic retry with exponential backoff for failed requests
- **Session Management**: Automatic session refresh when authentication expires
- **Health Monitoring**: Health check endpoint to monitor service status

## Prerequisites

- Python 3.10 or higher
- MongoDB instance (local or remote)
- Twitter/X accounts with username, email, and password

## Installation

1. Clone the repository:
```bash
cd xcom_automation
```

2. Install dependencies using pip:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
```

4. Edit `.env` file with your configuration:
```bash
# MongoDB Configuration (DigitalOcean)
MONGO_USER=doadmin
MONGO_PASSWORD=your_mongo_password
MONGO_HOST=db-mongodb-fra1-53189-e46f01e8.mongo.ondigitalocean.com
MONGO_PORT=25060
MONGO_DB=xcom_automation

# API Security - Change this to a secure random key!
API_KEY=your-secret-api-key-here

# Twitter Accounts Configuration
TWITTER_ACCOUNTS=[{"username": "your_username", "email": "your_email@example.com", "password": "your_password"}]

# Optional: Application Settings
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=info
```

## Configuration

### Twitter Accounts

Configure your Twitter accounts in the `TWITTER_ACCOUNTS` environment variable as a JSON array:

```json
[
  {
    "username": "username1",
    "email": "email1@example.com",
    "password": "password1"
  },
  {
    "username": "username2",
    "email": "email2@example.com",
    "password": "password2"
  }
]
```

Each account must have:
- `username`: Twitter username (also used as the identifier in API requests)
- `email`: Email address (used for 2FA verification)
- `password`: Account password

### MongoDB Setup

The service requires a MongoDB instance to store Twitter session cookies. You can use:

- **DigitalOcean MongoDB** (Recommended): Managed MongoDB cluster with automatic replica sets and TLS encryption
  - The service is pre-configured to use DigitalOcean MongoDB with the `mongodb+srv://` protocol
  - Update the `.env` file with your DigitalOcean MongoDB credentials
- **MongoDB Atlas**: Create a free cluster at [mongodb.com/atlas](https://www.mongodb.com/atlas) and use the connection string
- **Local MongoDB**: Install MongoDB locally (for development only)
- **Docker MongoDB**: Run MongoDB in Docker:
  ```bash
  docker run -d -p 27017:27017 --name mongodb mongo:latest
  ```

The connection URI is automatically constructed using the format:
```
mongodb+srv://{user}:{password}@{host}/{database}?authSource=admin&replicaSet=db-mongodb-fra1-53189&tls=true
```

## Running the Service

### Development Mode

Run with auto-reload enabled:

```bash
python -m app.main
```

Or using uvicorn directly:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

The service will:
1. Connect to MongoDB
2. Initialize all configured Twitter accounts
3. Load existing sessions or authenticate if needed
4. Start the FastAPI server

## API Usage

### Base URL

```
http://localhost:8000
```

### Authentication

All protected endpoints require the `X-API-Key` header:

```bash
X-API-Key: your-secret-api-key-here
```

### Endpoints

#### 1. Health Check

```bash
GET /health
```

Response:
```json
{
  "status": "healthy",
  "database": "connected",
  "accounts": ["main", "backup"]
}
```

#### 2. Post Tweet

```bash
POST /tweet
Headers:
  X-API-Key: your-secret-api-key-here
  Content-Type: application/json

Body:
{
  "username": "applyfirst_app",
  "text": "Check out this awesome article! https://example.com/article",
  "media_ids": null
}
```

**Note**: URLs in the text will be automatically detected and linkified by Twitter/X. You can include links directly in the tweet text.

Response:
```json
{
  "success": true,
  "message": "Tweet posted successfully",
  "tweet_id": "1234567890123456789",
  "username": "applyfirst_app"
}
```

#### 3. Refresh Session

Force re-authentication for a specific account:

```bash
POST /refresh-session/{username}
Headers:
  X-API-Key: your-secret-api-key-here
```

Response:
```json
{
  "success": true,
  "message": "Session refreshed successfully",
  "username": "applyfirst_app"
}
```

### Example Usage with curl

```bash
# Post a tweet with URL
curl -X POST http://localhost:8000/tweet \
  -H "X-API-Key: your-secret-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "applyfirst_app",
    "text": "Check out this cool project! https://github.com/example/project"
  }'

# Post a simple tweet
curl -X POST http://localhost:8000/tweet \
  -H "X-API-Key: your-secret-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "applyfirst_app",
    "text": "Hello from curl!"
  }'

# Health check
curl http://localhost:8000/health

# Refresh session
curl -X POST http://localhost:8000/refresh-session/applyfirst_app \
  -H "X-API-Key: your-secret-api-key-here"
```

### Example Usage with Python

```python
import requests

API_URL = "http://localhost:8000"
API_KEY = "your-secret-api-key-here"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# Post a tweet with URL
response = requests.post(
    f"{API_URL}/tweet",
    headers=headers,
    json={
        "username": "applyfirst_app",
        "text": "Check out this awesome article! https://example.com/article"
    }
)

print(response.json())

# Post a simple tweet
response = requests.post(
    f"{API_URL}/tweet",
    headers=headers,
    json={
        "username": "applyfirst_app",
        "text": "Hello from Python!"
    }
)

print(response.json())
```

## API Documentation

Once the service is running, you can access:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These provide interactive API documentation and testing interfaces.

## Project Structure

```
xcom_automation/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Environment variables & settings
│   ├── auth.py              # API key authentication
│   ├── database.py          # MongoDB operations
│   ├── twitter_service.py   # Twikit integration
│   └── models.py            # Pydantic models
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
├── .env                    # Your configuration (gitignored)
└── README.md               # This file
```

## How It Works

1. **Initialization**: On startup, the service connects to MongoDB and initializes Twitter clients for all configured accounts
2. **Session Management**: Twitter session cookies are stored in MongoDB to avoid repeated authentication
3. **Tweet Posting**: When you POST to `/tweet`, the service uses the appropriate Twitter client to post the tweet
4. **Retry Logic**: Failed requests are automatically retried with exponential backoff
5. **Session Refresh**: If authentication expires, the service automatically re-authenticates

## Security Considerations

- **API Key**: Change the default API key in `.env` to a strong random value
- **Environment Variables**: Never commit `.env` file to version control
- **MongoDB**: Secure your MongoDB instance with authentication
- **Rate Limits**: Be mindful of Twitter's rate limits to avoid account suspension
- **Account Safety**: Avoid posting inappropriate content that could lead to account bans

## Troubleshooting

### MongoDB Connection Issues

```
Failed to connect to MongoDB: ...
```

**Solution**: Verify your `MONGODB_URI` is correct and MongoDB is running

### Authentication Failed

```
Failed to initialize account main: ...
```

**Solution**:
- Verify credentials in `TWITTER_ACCOUNTS` are correct
- Check if the account requires 2FA (email must be provided)
- Try refreshing the session using `/refresh-session/{username}`

### Account Not Found

```
Account not initialized: applyfirst_app
```

**Solution**: Check that the `username` exists in `TWITTER_ACCOUNTS` environment variable

### API Key Invalid

```
Invalid or missing API key
```

**Solution**: Ensure you're sending the `X-API-Key` header with the correct value

## Rate Limits

Twitter has rate limits for various operations. The service includes retry logic, but be aware:

- **Tweet Creation**: Generally unrestricted, but excessive posting may trigger anti-spam measures
- **Authentication**: Minimize login attempts by using persistent sessions

## License

This project is for educational purposes. Use responsibly and in accordance with Twitter's Terms of Service.

## Contributing

Contributions are welcome! Please ensure your code follows the existing style and includes appropriate error handling.

## Support

For issues related to:
- **This service**: Open an issue in this repository
- **Twikit library**: Visit [twikit GitHub](https://github.com/d60/twikit)
- **FastAPI**: Visit [FastAPI documentation](https://fastapi.tiangolo.com/)
