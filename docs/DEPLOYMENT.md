# PyForest Deployment Guide

Guide for deploying PyForest in various environments.

## Table of Contents

1. [Development](#development)
2. [Production](#production)
3. [Configuration](#configuration)
4. [Monitoring](#monitoring)
5. [Scaling](#scaling)
6. [Security](#security)
7. [Backup](#backup)

## Development

### Local Development

**Install**:
```bash
pip install -e ".[dev]"
```

**Run Server**:
```bash
python run_server.py
```

Or with uvicorn directly:
```bash
uvicorn py_forest.api.main:app --reload --host 0.0.0.0 --port 8000
```

**Access**:
- API: `http://localhost:8000`
- Docs: `http://localhost:8000/docs`

### Development Tools

**CLI**:
```bash
pyforest config --api-url http://localhost:8000
pyforest tree list
```

**Testing**:
```bash
pytest tests/
pytest tests/test_integration.py -v
```

**Linting**:
```bash
black src/ tests/
ruff check src/ tests/
mypy src/
```

## Production

### Requirements

- Python 3.10+
- Linux/Unix server
- Systemd (for service management)
- Reverse proxy (Nginx/Apache)

### Installation

```bash
# Create dedicated user
sudo useradd -r -s /bin/false pyforest

# Create directories
sudo mkdir -p /opt/pyforest
sudo mkdir -p /var/lib/pyforest/trees
sudo mkdir -p /var/lib/pyforest/templates
sudo mkdir -p /var/log/pyforest

# Set ownership
sudo chown -R pyforest:pyforest /opt/pyforest
sudo chown -R pyforest:pyforest /var/lib/pyforest
sudo chown -R pyforest:pyforest /var/log/pyforest

# Clone and install
sudo -u pyforest git clone https://github.com/yourusername/py_forest.git /opt/pyforest
cd /opt/pyforest
sudo -u pyforest python -m venv venv
sudo -u pyforest venv/bin/pip install .
```

### Systemd Service

Create `/etc/systemd/system/pyforest.service`:

```ini
[Unit]
Description=PyForest Behavior Tree Service
After=network.target

[Service]
Type=simple
User=pyforest
Group=pyforest
WorkingDirectory=/opt/pyforest
Environment="PATH=/opt/pyforest/venv/bin"
ExecStart=/opt/pyforest/venv/bin/uvicorn py_forest.api.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --log-config /opt/pyforest/logging.yaml

Restart=always
RestartSec=10

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/lib/pyforest /var/log/pyforest

[Install]
WantedBy=multi-user.target
```

**Enable and start**:
```bash
sudo systemctl daemon-reload
sudo systemctl enable pyforest
sudo systemctl start pyforest
sudo systemctl status pyforest
```

### Nginx Reverse Proxy

Create `/etc/nginx/sites-available/pyforest`:

```nginx
upstream pyforest {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name pyforest.example.com;

    client_max_body_size 10M;

    location / {
        proxy_pass http://pyforest;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws/ {
        proxy_pass http://pyforest;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }
}
```

**Enable**:
```bash
sudo ln -s /etc/nginx/sites-available/pyforest /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### SSL/TLS (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d pyforest.example.com
```

Nginx config with SSL:
```nginx
server {
    listen 443 ssl http2;
    server_name pyforest.example.com;

    ssl_certificate /etc/letsencrypt/live/pyforest.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/pyforest.example.com/privkey.pem;

    # ... rest of config
}

server {
    listen 80;
    server_name pyforest.example.com;
    return 301 https://$server_name$request_uri;
}
```

## Configuration

### Environment Variables

Create `/opt/pyforest/.env`:

```bash
# API Configuration
PYFOREST_HOST=0.0.0.0
PYFOREST_PORT=8000
PYFOREST_WORKERS=4

# Storage
PYFOREST_TREE_PATH=/var/lib/pyforest/trees
PYFOREST_TEMPLATE_PATH=/var/lib/pyforest/templates

# Logging
PYFOREST_LOG_LEVEL=INFO
PYFOREST_LOG_FILE=/var/log/pyforest/app.log

# Performance
PYFOREST_MAX_EXECUTIONS=100
PYFOREST_HISTORY_SIZE=1000
```

### Logging Configuration

Create `/opt/pyforest/logging.yaml`:

```yaml
version: 1
disable_existing_loggers: false

formatters:
  standard:
    format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
  json:
    format: '{"time": "%(asctime)s", "name": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}'

handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: standard
    stream: ext://sys.stdout

  file:
    class: logging.handlers.RotatingFileHandler
    level: INFO
    formatter: json
    filename: /var/log/pyforest/app.log
    maxBytes: 10485760  # 10MB
    backupCount: 10

  error_file:
    class: logging.handlers.RotatingFileHandler
    level: ERROR
    formatter: json
    filename: /var/log/pyforest/error.log
    maxBytes: 10485760
    backupCount: 10

loggers:
  py_forest:
    level: INFO
    handlers: [console, file, error_file]
    propagate: false

  uvicorn:
    level: INFO
    handlers: [console, file]
    propagate: false

root:
  level: INFO
  handlers: [console, file]
```

## Monitoring

### Health Check Endpoint

Add health check to API:

```python
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "executions": len(execution_service.list_executions())
    }
```

### Prometheus Metrics

Install prometheus client:
```bash
pip install prometheus-fastapi-instrumentator
```

Add to `main.py`:
```python
from prometheus_fastapi_instrumentator import Instrumentator

@app.on_event("startup")
async def startup():
    Instrumentator().instrument(app).expose(app)
```

Metrics available at `/metrics`.

### Log Monitoring

Use log aggregation:
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Loki + Grafana
- CloudWatch Logs (AWS)

**Example logrotate** (`/etc/logrotate.d/pyforest`):
```
/var/log/pyforest/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 pyforest pyforest
    sharedscripts
    postrotate
        systemctl reload pyforest > /dev/null 2>&1 || true
    endscript
}
```

### Systemd Monitoring

```bash
# Service status
sudo systemctl status pyforest

# Logs
sudo journalctl -u pyforest -f

# Resource usage
sudo systemctl show pyforest --property=MemoryCurrent
sudo systemctl show pyforest --property=CPUUsageNSec
```

## Scaling

### Horizontal Scaling

Run multiple API instances behind load balancer.

**HAProxy config**:
```
frontend pyforest_front
    bind *:80
    default_backend pyforest_back

backend pyforest_back
    balance roundrobin
    server pyforest1 192.168.1.10:8000 check
    server pyforest2 192.168.1.11:8000 check
    server pyforest3 192.168.1.12:8000 check
```

**Shared Storage**: Use network filesystem (NFS, GlusterFS) for tree library.

**Considerations**:
- Executions are in-memory (not shared between instances)
- WebSocket connections sticky to instance
- Consider external execution service

### Vertical Scaling

Increase resources:

```bash
# More workers
ExecStart=.../uvicorn ... --workers 8

# More memory
[Service]
MemoryLimit=4G

# Process priority
Nice=-5
```

### Database Backend

For high scale, implement database storage:

```python
class PostgreSQLTreeLibrary(TreeLibrary):
    def __init__(self, connection_string):
        self.engine = create_engine(connection_string)

    def save(self, tree: TreeDefinition):
        # Save to PostgreSQL
        pass
```

## Security

### Authentication

Add API key authentication:

```python
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME)

def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key not in valid_api_keys:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return api_key

@app.get("/trees/", dependencies=[Depends(verify_api_key)])
def list_trees():
    # Protected endpoint
    pass
```

### Rate Limiting

Use slowapi:

```bash
pip install slowapi
```

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/trees/")
@limiter.limit("100/minute")
def list_trees(request: Request):
    pass
```

### Firewall

Configure UFW:

```bash
sudo ufw allow 22/tcp  # SSH
sudo ufw allow 80/tcp  # HTTP
sudo ufw allow 443/tcp # HTTPS
sudo ufw enable
```

### Security Headers

Add security headers in Nginx:

```nginx
add_header X-Content-Type-Options "nosniff" always;
add_header X-Frame-Options "DENY" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "no-referrer-when-downgrade" always;
add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
```

## Backup

### Tree Library Backup

**Simple backup**:
```bash
#!/bin/bash
BACKUP_DIR=/backup/pyforest/$(date +%Y%m%d)
mkdir -p $BACKUP_DIR
rsync -av /var/lib/pyforest/trees/ $BACKUP_DIR/trees/
rsync -av /var/lib/pyforest/templates/ $BACKUP_DIR/templates/
```

**Automated backup** (cron):
```cron
# Daily backup at 2 AM
0 2 * * * /opt/pyforest/scripts/backup.sh
```

### Export All Trees

Using CLI:
```bash
pyforest export batch --output /backup/trees --format json
```

### Restore

```bash
# Restore trees
rsync -av /backup/pyforest/20240101/trees/ /var/lib/pyforest/trees/

# Or use CLI
pyforest export batch-import /backup/trees --format json
```

### Database Backup

If using PostgreSQL:
```bash
pg_dump pyforest > backup_$(date +%Y%m%d).sql
```

## Performance Tuning

### Uvicorn Workers

Adjust based on CPU cores:
```bash
# Rule: (2 x CPU cores) + 1
--workers 9  # For 4-core system
```

### Database Connection Pool

```python
engine = create_engine(
    connection_string,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True
)
```

### Execution Limits

Limit concurrent executions:
```python
MAX_EXECUTIONS = 100

def create_execution(config):
    if len(execution_service.list_executions()) >= MAX_EXECUTIONS:
        raise HTTPException(status_code=429, detail="Too many executions")
    return execution_service.create_execution(config)
```

### History Management

Tune history size:
```python
history = ExecutionHistory(max_size=500)  # Reduce memory usage
```

## Troubleshooting

### Service Won't Start

```bash
# Check logs
sudo journalctl -u pyforest -n 50

# Check port
sudo lsof -i :8000

# Check permissions
ls -la /var/lib/pyforest
```

### High Memory Usage

```bash
# Check memory
free -h

# Check process
ps aux | grep uvicorn

# Reduce workers or history size
```

### Slow Response Times

```bash
# Check CPU
top

# Check disk I/O
iostat -x 1

# Profile execution
pyforest profile TREE_ID --ticks 1000
```

### WebSocket Connection Drops

Check Nginx timeout:
```nginx
proxy_read_timeout 86400;
proxy_send_timeout 86400;
```

## Summary

For production deployment:
1. Use systemd for service management
2. Configure Nginx reverse proxy with SSL
3. Implement authentication and rate limiting
4. Set up monitoring and logging
5. Configure automated backups
6. Tune performance based on load

For support:
- GitHub Issues: Bug reports and features
- Documentation: Full guides in `docs/`
