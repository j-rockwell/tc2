# Server
FastAPI backend. Built with Python, featuring JWT Authentication, MongoDB storage and Redis caching.

## Install
### Step 1 - Clone project and install dependencies
```bash
git clone git@github.com:j-rockwell/tc2.git
cd server
poetry install
```

### Step 2 - Configure your .env file
```bash
# Generate a secure JWT secret
python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(64))" > .env

# Add other configuration
cat >> .env << EOF
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME="tc2"

REDIS_URI=redis://localhost:6379
REDIS_PASSWORD=

ACCESS_TOKEN_SECRET="passkey123"
REFRESH_TOKEN_SECRET="passkey123"
ACCESS_TOKEN_TTL_MINUTES=30
REFRESH_TOKEN_TTL_MINUTES=1440

ENVIRONMENT=dev
DEBUG=true

HOST=0.0.0.0
PORT=8000

LOG_LEVEL=INFO
EOF
```

### Step 3 - Start a MongoDB Instance
```bash
# Using Docker
docker run -d -p 27017:27017 --name mongodb mongo:latest

# Or install locally on macOS
brew install mongodb-community
brew services start mongodb-community
```

### Step 4 - Start a Redis Instance
```bash
# Using Docker
docker run -d -p 6379:6379 --name redis redis:latest

# Or install locally on macOS
brew install redis
brew services start redis
```

### Step 5 - Run the Server
**Development Mode**
```bash
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Production Mode**
```bash
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

The server will be available at:
* **API**: [http://localhost:8000](http://localhost:8000)
* **Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
