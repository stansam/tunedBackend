# Redis and Celery Setup Instructions

## Prerequisites

Before running the Flask application with the new auth system, you need to install and configure Redis.

## Installing Redis

### Ubuntu/Debian
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

### macOS (using Homebrew)
```bash
brew install redis
brew services start redis
```

### Windows
Download and install Redis from: https://github.com/microsoftarchive/redis/releases
Or use WSL2 and follow Ubuntu instructions.

### Verify Redis Installation
```bash
redis-cli ping
# Should return: PONG
```

## Configuration

### Development Environment

The default configuration works out of the box with Redis running on `localhost:6379`.

**No `.env` changes needed for basic local development**.

### Production Environment

Add these variables to your `.env` file:

```bash
# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Celery Configuration (uses Redis)
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# SocketIO (optional, for multi-server deployments)
SOCKETIO_MESSAGE_QUEUE=redis://localhost:6379/3
```

**For cloud Redis (e.g., Redis Cloud, AWS ElastiCache):**
```bash
REDIS_URL=redis://:password@your-redis-host:port/0
CELERY_BROKER_URL=redis://:password@your-redis-host:port/1
CELERY_RESULT_BACKEND=redis://:password@your-redis-host:port/2
```

## Installing Python Dependencies

```bash
cd /home/vault/Documents/tunedBundle/backend
pip install -r requirements.txt
```

## Running the Application

### 1. Start Redis (if not already running)
```bash
# Linux
sudo systemctl start redis-server

# macOS
brew services start redis

# Or manually
redis-server
```

### 2. Start Flask Application
```bash
python run.py
```

### 3. Start Celery Worker (in a new terminal)
```bash
cd /home/vault/Documents/tunedBundle/backend
celery -A tuned.celery_app worker --loglevel=info
```

**For Windows:**
```bash
celery -A tuned.celery_app worker --pool=solo --loglevel=info
```

### 4. Start Celery Beat (optional, for scheduled tasks)
```bash
cd /home/vault/Documents/tunedBundle/backend
celery -A tuned.celery_app beat --loglevel=info
```

## Testing Redis Connection

### Python Shell Test
```bash
python
>>> from tuned.redis_client import redis_client
>>> redis_client.set('test', 'hello')
>>> redis_client.get('test')
'hello'
>>> redis_client.delete('test')
>>>exit()
```

### Redis CLI Test
```bash
redis-cli
127.0.0.1:6379> PING
PONG
127.0.0.1:6379> SET test "Hello Redis"
OK
127.0.0.1:6379> GET test
"Hello Redis"
127.0.0.1:6379> DEL test
(integer) 1
127.0.0.1:6379> exit
```

## Production Deployment

### Using Supervisor (recommended for production)

Create `/etc/supervisor/conf.d/tunedessays.conf`:

```ini
[program:tuned_flask]
command=/path/to/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 "tuned:create_app()"
directory=/path/to/tunedBundle/backend
user=www-data
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/tuned/flask_err.log
stdout_logfile=/var/log/tuned/flask_out.log

[program:tuned_celery_worker]
command=/path/to/venv/bin/celery -A tuned.celery_app worker --loglevel=info
directory=/path/to/tunedBundle/backend
user=www-data
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/tuned/celery_worker_err.log
stdout_logfile=/var/log/tuned/celery_worker_out.log

[program:tuned_celery_beat]
command=/path/to/venv/bin/celery -A tuned.celery_app beat --loglevel=info
directory=/path/to/tunedBundle/backend
user=www-data
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/tuned/celery_beat_err.log
stdout_logfile=/var/log/tuned/celery_beat_out.log
```

Then:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl status
```

### Using systemd

Create service files for Flask, Celery worker, and Celery beat similar to supervisor configuration.

## Troubleshooting

### Redis Connection Refused
- Check if Redis is running: `sudo systemctl status redis-server`
- Check Redis port: `sudo netstat -tulpn | grep 6379`
- Check firewall rules

### Celery Not Starting
- Verify Redis is accessible: `redis-cli ping`
- Check CELERY_BROKER_URL in .env
- For Windows, use `--pool=solo` flag

### JWT Blacklist Not Working
- Verify Redis client is initialized: Check `tuned/redis_client.py`
- Check JWT_BLACKLIST_ENABLED=True in config
- Test Redis connection manually

## Database Migration Note

Since we removed `email_verification_token` and `password_reset_token` fields from the User model, you'll need to create a migration:

```bash
cd /home/vault/Documents/tunedBundle/backend
flask db migrate -m "Remove token fields from User model"
flask db upgrade
```

**Or if using Alembic directly:**
```bash
alembic revision --autogenerate -m "Remove token fields from User model"
alembic upgrade head
```

## Next Steps

After completing this setup:
1. Verify Redis is running
2. Install dependencies from requirements.txt
3. Run database migrations
4. Start Flask application
5. Start Celery worker
6. Test authentication endpoints

All background tasks (email sending, token blacklisting) will now work correctly.
