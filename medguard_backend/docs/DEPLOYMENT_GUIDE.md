# MedGuard SA - HIPAA-Compliant Deployment Guide

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Environment Setup](#environment-setup)
4. [Database Setup](#database-setup)
5. [Application Deployment](#application-deployment)
6. [Security Configuration](#security-configuration)
7. [Monitoring Setup](#monitoring-setup)
8. [Backup Configuration](#backup-configuration)
9. [SSL/TLS Configuration](#ssltls-configuration)
10. [Testing and Validation](#testing-and-validation)
11. [Maintenance Procedures](#maintenance-procedures)
12. [Troubleshooting](#troubleshooting)

## Overview

This guide provides step-by-step instructions for deploying MedGuard SA in a HIPAA-compliant production environment. The deployment process ensures all security requirements are met and the system is properly configured for production use.

### Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Production Environment                   │
├─────────────────────────────────────────────────────────────┤
│  Load Balancer (Nginx)                                      │
│  ├── SSL Termination                                        │
│  ├── Rate Limiting                                          │
│  └── Security Headers                                       │
├─────────────────────────────────────────────────────────────┤
│  Application Servers (2+)                                   │
│  ├── Django Application                                     │
│  ├── Gunicorn WSGI Server                                   │
│  ├── Security Middleware                                    │
│  └── Audit Logging                                          │
├─────────────────────────────────────────────────────────────┤
│  Database Layer                                             │
│  ├── PostgreSQL (Primary)                                   │
│  ├── PostgreSQL (Replica)                                   │
│  └── Redis (Cache/Sessions)                                 │
├─────────────────────────────────────────────────────────────┤
│  Storage Layer                                              │
│  ├── Encrypted File Storage                                 │
│  ├── Backup Storage                                         │
│  └── Log Storage                                            │
├─────────────────────────────────────────────────────────────┤
│  Monitoring Layer                                           │
│  ├── Application Monitoring                                 │
│  ├── Security Monitoring                                    │
│  ├── Performance Monitoring                                 │
│  └── Compliance Monitoring                                  │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

### System Requirements

#### Minimum Requirements
- **CPU**: 4 cores (2.4 GHz or higher)
- **RAM**: 8 GB
- **Storage**: 100 GB SSD
- **Network**: 100 Mbps

#### Recommended Requirements
- **CPU**: 8 cores (3.0 GHz or higher)
- **RAM**: 16 GB
- **Storage**: 500 GB SSD
- **Network**: 1 Gbps

### Software Requirements

#### Operating System
```bash
# Ubuntu 22.04 LTS (Recommended)
sudo apt update
sudo apt upgrade -y

# Or CentOS 8 / RHEL 8
sudo yum update -y
```

#### Required Software
```bash
# Install required packages
sudo apt install -y \
    python3.11 \
    python3.11-dev \
    python3.11-venv \
    postgresql-14 \
    postgresql-contrib-14 \
    redis-server \
    nginx \
    certbot \
    python3-certbot-nginx \
    git \
    curl \
    wget \
    unzip \
    build-essential \
    libpq-dev \
    libssl-dev \
    libffi-dev \
    supervisor \
    logrotate \
    fail2ban \
    ufw
```

#### Python Dependencies
```bash
# Create virtual environment
python3.11 -m venv /opt/medguard-sa/venv
source /opt/medguard-sa/venv/bin/activate

# Install Python packages
pip install --upgrade pip
pip install -r requirements.txt
```

## Environment Setup

### User and Directory Setup

#### Create Application User
```bash
# Create application user
sudo useradd -r -s /bin/bash -d /opt/medguard-sa medguard
sudo usermod -aG sudo medguard

# Set up SSH keys for secure access
sudo mkdir -p /opt/medguard-sa/.ssh
sudo chown medguard:medguard /opt/medguard-sa/.ssh
sudo chmod 700 /opt/medguard-sa/.ssh
```

#### Create Application Directories
```bash
# Create application directories
sudo mkdir -p /opt/medguard-sa/{app,logs,backups,media,static}
sudo mkdir -p /var/log/medguard-sa
sudo mkdir -p /etc/medguard-sa

# Set permissions
sudo chown -R medguard:medguard /opt/medguard-sa
sudo chown -R medguard:medguard /var/log/medguard-sa
sudo chmod 755 /opt/medguard-sa
sudo chmod 755 /var/log/medguard-sa
```

### Environment Configuration

#### Create Environment File
```bash
# Create environment file
sudo -u medguard tee /opt/medguard-sa/.env << EOF
# Django Settings
SECRET_KEY=your-super-secure-secret-key-here-minimum-50-characters
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com,api.your-domain.com

# Database Configuration
DB_NAME=medguard_sa_production
DB_USER=medguard_user
DB_PASSWORD=your-secure-database-password
DB_HOST=localhost
DB_PORT=5432

# HIPAA Compliance Settings
HIPAA_ENCRYPTION_KEY=your-base64-encoded-encryption-key-32-bytes
ANONYMIZATION_SALT=your-anonymization-salt-for-consistent-hashing
AUDIT_LOG_RETENTION_DAYS=2555
COMPLIANCE_REPORTING_ENABLED=True
BREACH_DETECTION_ENABLED=True

# Email Configuration
EMAIL_HOST=smtp.your-provider.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=notifications@your-domain.com
EMAIL_HOST_PASSWORD=your-email-password
DEFAULT_FROM_EMAIL=noreply@your-domain.com

# Redis Configuration
REDIS_URL=redis://localhost:6379/1
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Security Settings
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/medguard-sa/django.log
SECURITY_LOG_FILE=/var/log/medguard-sa/security.log
AUDIT_LOG_FILE=/var/log/medguard-sa/audit.log

# Monitoring
SENTRY_DSN=your-sentry-dsn-for-error-tracking
HEALTH_CHECK_ENABLED=True
EOF

# Set secure permissions
sudo chmod 600 /opt/medguard-sa/.env
```

## Database Setup

### PostgreSQL Configuration

#### Install and Configure PostgreSQL
```bash
# Install PostgreSQL
sudo apt install -y postgresql-14 postgresql-contrib-14

# Start and enable PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Configure PostgreSQL for security
sudo -u postgres psql << EOF
-- Create database user
CREATE USER medguard_user WITH PASSWORD 'your-secure-database-password';

-- Create database
CREATE DATABASE medguard_sa_production OWNER medguard_user;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE medguard_sa_production TO medguard_user;

-- Enable required extensions
\c medguard_sa_production
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Configure security settings
ALTER SYSTEM SET ssl = on;
ALTER SYSTEM SET ssl_ciphers = 'HIGH:MEDIUM:+3DES:!aNULL';
ALTER SYSTEM SET ssl_prefer_server_ciphers = on;
ALTER SYSTEM SET ssl_cert_file = '/etc/ssl/certs/ssl-cert-snakeoil.pem';
ALTER SYSTEM SET ssl_key_file = '/etc/ssl/private/ssl-cert-snakeoil.key';

-- Restart PostgreSQL to apply changes
\q
EOF

sudo systemctl restart postgresql
```

#### Configure PostgreSQL Security
```bash
# Edit PostgreSQL configuration
sudo tee -a /etc/postgresql/14/main/postgresql.conf << EOF

# Security Settings
ssl = on
ssl_ciphers = 'HIGH:MEDIUM:+3DES:!aNULL'
ssl_prefer_server_ciphers = on
ssl_cert_file = '/etc/ssl/certs/ssl-cert-snakeoil.pem'
ssl_key_file = '/etc/ssl/private/ssl-cert-snakeoil.key'

# Connection Settings
max_connections = 100
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB

# Logging Settings
log_destination = 'stderr'
logging_collector = on
log_directory = 'log'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
log_rotation_age = 1d
log_rotation_size = 100MB
log_min_duration_statement = 1000
log_checkpoints = on
log_connections = on
log_disconnections = on
log_lock_waits = on
log_temp_files = -1
log_autovacuum_min_duration = 0
log_error_verbosity = verbose
EOF

# Configure client authentication
sudo tee /etc/postgresql/14/main/pg_hba.conf << EOF
# TYPE  DATABASE        USER            ADDRESS                 METHOD
local   all             postgres                                peer
local   medguard_sa_production medguard_user                    md5
host    medguard_sa_production medguard_user 127.0.0.1/32      md5
host    medguard_sa_production medguard_user ::1/128           md5
host    all             all             0.0.0.0/0               reject
EOF

# Restart PostgreSQL
sudo systemctl restart postgresql
```

### Redis Configuration

#### Configure Redis Security
```bash
# Edit Redis configuration
sudo tee /etc/redis/redis.conf << EOF
# Network
bind 127.0.0.1
port 6379
timeout 300
tcp-keepalive 60

# Security
requirepass your-redis-password

# Memory Management
maxmemory 256mb
maxmemory-policy allkeys-lru

# Persistence
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename dump.rdb
dir /var/lib/redis

# Logging
loglevel notice
logfile /var/log/redis/redis-server.log
syslog-enabled no
databases 16

# Security
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command DEBUG ""
rename-command CONFIG ""
rename-command SHUTDOWN ""
EOF

# Restart Redis
sudo systemctl restart redis-server
sudo systemctl enable redis-server
```

## Application Deployment

### Code Deployment

#### Clone and Setup Application
```bash
# Switch to application user
sudo su - medguard

# Clone application
cd /opt/medguard-sa
git clone https://github.com/your-org/medguard-sa.git app
cd app

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Copy environment file
cp ../.env .

# Set permissions
chmod 600 .env
```

#### Database Migration
```bash
# Activate virtual environment
source venv/bin/activate

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput

# Verify installation
python manage.py check --deploy
```

### Gunicorn Configuration

#### Create Gunicorn Configuration
```bash
# Create Gunicorn configuration
sudo tee /etc/medguard-sa/gunicorn.conf.py << EOF
import multiprocessing
import os

# Server socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "/var/log/medguard-sa/gunicorn-access.log"
errorlog = "/var/log/medguard-sa/gunicorn-error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "medguard-sa"

# User/Group
user = "medguard"
group = "medguard"

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# SSL (if using SSL termination at Gunicorn)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

# Preload app
preload_app = True

def when_ready(server):
    server.log.info("Server is ready. Spawning workers")

def worker_int(worker):
    worker.log.info("worker received INT or QUIT signal")

def pre_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_worker_init(worker):
    worker.log.info("Worker initialized (pid: %s)", worker.pid)

def worker_abort(worker):
    worker.log.info("Worker aborted (pid: %s)", worker.pid)
EOF
```

#### Create Systemd Service
```bash
# Create systemd service file
sudo tee /etc/systemd/system/medguard-sa.service << EOF
[Unit]
Description=MedGuard SA Gunicorn daemon
After=network.target postgresql.service redis-server.service

[Service]
Type=notify
User=medguard
Group=medguard
RuntimeDirectory=medguard-sa
WorkingDirectory=/opt/medguard-sa/app
Environment=PATH=/opt/medguard-sa/venv/bin
Environment=DJANGO_SETTINGS_MODULE=medguard_backend.settings.production
ExecStart=/opt/medguard-sa/venv/bin/gunicorn --config /etc/medguard-sa/gunicorn.conf.py medguard_backend.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable medguard-sa
sudo systemctl start medguard-sa
```

### Celery Configuration

#### Create Celery Configuration
```bash
# Create Celery configuration
sudo tee /etc/medguard-sa/celery.conf << EOF
# Celery Configuration
CELERY_BROKER_URL=redis://:your-redis-password@localhost:6379/0
CELERY_RESULT_BACKEND=redis://:your-redis-password@localhost:6379/0
CELERY_TASK_SERIALIZER=json
CELERY_RESULT_SERIALIZER=json
CELERY_ACCEPT_CONTENT=['json']
CELERY_TIMEZONE=Africa/Johannesburg
CELERY_ENABLE_UTC=True
CELERY_TASK_TRACK_STARTED=True
CELERY_TASK_TIME_LIMIT=30*60
CELERY_WORKER_MAX_TASKS_PER_CHILD=1000
CELERY_WORKER_PREFETCH_MULTIPLIER=1
CELERY_WORKER_DISABLE_RATE_LIMITS=False
CELERY_WORKER_CONCURRENCY=4
CELERY_WORKER_POOL=prefork
CELERY_WORKER_AUTOSCALE=4,8
CELERY_WORKER_MAX_MEMORY_PER_CHILD=200000
EOF
```

#### Create Celery Service
```bash
# Create Celery service file
sudo tee /etc/systemd/system/medguard-sa-celery.service << EOF
[Unit]
Description=MedGuard SA Celery Worker
After=network.target postgresql.service redis-server.service

[Service]
Type=forking
User=medguard
Group=medguard
EnvironmentFile=/etc/medguard-sa/celery.conf
WorkingDirectory=/opt/medguard-sa/app
ExecStart=/opt/medguard-sa/venv/bin/celery multi start worker1 \\
    -A medguard_backend \\
    --pidfile=/var/run/celery/%n.pid \\
    --logfile=/var/log/medguard-sa/celery/%n%I.log \\
    --loglevel=INFO
ExecStop=/opt/medguard-sa/venv/bin/celery multi stopwait worker1 \\
    --pidfile=/var/run/celery/%n.pid
ExecReload=/opt/medguard-sa/venv/bin/celery multi restart worker1 \\
    -A medguard_backend \\
    --pidfile=/var/run/celery/%n.pid \\
    --logfile=/var/log/medguard-sa/celery/%n%I.log \\
    --loglevel=INFO

[Install]
WantedBy=multi-user.target
EOF

# Create Celery Beat service
sudo tee /etc/systemd/system/medguard-sa-celerybeat.service << EOF
[Unit]
Description=MedGuard SA Celery Beat
After=network.target postgresql.service redis-server.service

[Service]
Type=simple
User=medguard
Group=medguard
EnvironmentFile=/etc/medguard-sa/celery.conf
WorkingDirectory=/opt/medguard-sa/app
ExecStart=/opt/medguard-sa/venv/bin/celery -A medguard_backend beat \\
    --loglevel=INFO \\
    --logfile=/var/log/medguard-sa/celery/beat.log
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Create directories
sudo mkdir -p /var/run/celery
sudo mkdir -p /var/log/medguard-sa/celery
sudo chown -R medguard:medguard /var/run/celery
sudo chown -R medguard:medguard /var/log/medguard-sa/celery

# Enable and start services
sudo systemctl daemon-reload
sudo systemctl enable medguard-sa-celery
sudo systemctl enable medguard-sa-celerybeat
sudo systemctl start medguard-sa-celery
sudo systemctl start medguard-sa-celerybeat
```

## Security Configuration

### Firewall Configuration

#### Configure UFW Firewall
```bash
# Reset UFW
sudo ufw --force reset

# Set default policies
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH
sudo ufw allow ssh

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow internal services
sudo ufw allow from 127.0.0.1 to any port 5432  # PostgreSQL
sudo ufw allow from 127.0.0.1 to any port 6379  # Redis

# Enable UFW
sudo ufw --force enable

# Check status
sudo ufw status verbose
```

### Fail2ban Configuration

#### Configure Fail2ban
```bash
# Install Fail2ban
sudo apt install -y fail2ban

# Create local configuration
sudo tee /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3
backend = auto

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 3

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 3

[medguard-sa]
enabled = true
filter = medguard-sa
port = http,https
logpath = /var/log/medguard-sa/django.log
maxretry = 5
bantime = 7200
EOF

# Create custom filter
sudo tee /etc/fail2ban/filter.d/medguard-sa.conf << EOF
[Definition]
failregex = ^.*Failed login attempt for user .* from IP <HOST>.*$
ignoreregex =
EOF

# Start Fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### SSL/TLS Configuration

#### Obtain SSL Certificate
```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com -d api.your-domain.com

# Test automatic renewal
sudo certbot renew --dry-run
```

## Nginx Configuration

### Create Nginx Configuration
```bash
# Create Nginx configuration
sudo tee /etc/nginx/sites-available/medguard-sa << EOF
# Rate limiting
limit_req_zone \$binary_remote_addr zone=api:10m rate=10r/s;
limit_req_zone \$binary_remote_addr zone=login:10m rate=5r/m;

# Upstream configuration
upstream medguard_backend {
    server 127.0.0.1:8000;
    keepalive 32;
}

# HTTP server (redirect to HTTPS)
server {
    listen 80;
    server_name your-domain.com www.your-domain.com api.your-domain.com;
    
    # Security headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Permissions-Policy "geolocation=(), microphone=()" always;
    
    # Redirect to HTTPS
    return 301 https://\$server_name\$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com api.your-domain.com;
    
    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_session_tickets off;
    
    # Modern SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # HSTS
    add_header Strict-Transport-Security "max-age=63072000" always;
    
    # Security headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Permissions-Policy "geolocation=(), microphone=()" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' https:; connect-src 'self' https:; frame-ancestors 'none';" always;
    
    # Client max body size
    client_max_body_size 10M;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;
    
    # Static files
    location /static/ {
        alias /opt/medguard-sa/app/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }
    
    # Media files
    location /media/ {
        alias /opt/medguard-sa/app/media/;
        expires 1y;
        add_header Cache-Control "public";
        access_log off;
    }
    
    # API endpoints
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        
        proxy_pass http://medguard_backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
    
    # Login endpoint (stricter rate limiting)
    location /api/auth/login/ {
        limit_req zone=login burst=5 nodelay;
        
        proxy_pass http://medguard_backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
    }
    
    # Admin interface
    location /admin/ {
        proxy_pass http://medguard_backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
    }
    
    # Health check
    location /health/ {
        proxy_pass http://medguard_backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
        access_log off;
    }
    
    # Main application
    location / {
        proxy_pass http://medguard_backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
    
    # Deny access to sensitive files
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
    
    location ~ ~$ {
        deny all;
        access_log off;
        log_not_found off;
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/medguard-sa /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

## Monitoring Setup

### Application Monitoring

#### Create Monitoring Scripts
```bash
# Create health check script
sudo tee /opt/medguard-sa/scripts/health_check.sh << 'EOF'
#!/bin/bash

# Health check script for MedGuard SA
LOG_FILE="/var/log/medguard-sa/health_check.log"
ALERT_EMAIL="alerts@your-domain.com"

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> $LOG_FILE
}

# Function to send alert
send_alert() {
    echo "$1" | mail -s "MedGuard SA Health Check Alert" $ALERT_EMAIL
}

# Check if services are running
check_service() {
    local service=$1
    if ! systemctl is-active --quiet $service; then
        log_message "ERROR: Service $service is not running"
        send_alert "Service $service is not running"
        return 1
    else
        log_message "INFO: Service $service is running"
    fi
}

# Check database connectivity
check_database() {
    if ! sudo -u medguard psql -h localhost -U medguard_user -d medguard_sa_production -c "SELECT 1;" > /dev/null 2>&1; then
        log_message "ERROR: Database connectivity failed"
        send_alert "Database connectivity failed"
        return 1
    else
        log_message "INFO: Database connectivity OK"
    fi
}

# Check Redis connectivity
check_redis() {
    if ! redis-cli ping > /dev/null 2>&1; then
        log_message "ERROR: Redis connectivity failed"
        send_alert "Redis connectivity failed"
        return 1
    else
        log_message "INFO: Redis connectivity OK"
    fi
}

# Check application health
check_application() {
    local response=$(curl -s -o /dev/null -w "%{http_code}" https://your-domain.com/health/)
    if [ "$response" != "200" ]; then
        log_message "ERROR: Application health check failed (HTTP $response)"
        send_alert "Application health check failed (HTTP $response)"
        return 1
    else
        log_message "INFO: Application health check OK"
    fi
}

# Check disk space
check_disk_space() {
    local usage=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ $usage -gt 85 ]; then
        log_message "WARNING: Disk usage is high ($usage%)"
        send_alert "Disk usage is high ($usage%)"
    else
        log_message "INFO: Disk usage OK ($usage%)"
    fi
}

# Check memory usage
check_memory() {
    local usage=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
    if [ $usage -gt 85 ]; then
        log_message "WARNING: Memory usage is high ($usage%)"
        send_alert "Memory usage is high ($usage%)"
    else
        log_message "INFO: Memory usage OK ($usage%)"
    fi
}

# Main execution
log_message "Starting health check"

check_service medguard-sa
check_service medguard-sa-celery
check_service medguard-sa-celerybeat
check_service postgresql
check_service redis-server
check_service nginx
check_database
check_redis
check_application
check_disk_space
check_memory

log_message "Health check completed"
EOF

# Make script executable
sudo chmod +x /opt/medguard-sa/scripts/health_check.sh

# Add to crontab
sudo crontab -e
# Add this line:
# */5 * * * * /opt/medguard-sa/scripts/health_check.sh
```

### Log Monitoring

#### Configure Log Rotation
```bash
# Configure log rotation
sudo tee /etc/logrotate.d/medguard-sa << EOF
/var/log/medguard-sa/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 medguard medguard
    postrotate
        systemctl reload medguard-sa
    endscript
}

/var/log/medguard-sa/celery/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 medguard medguard
    postrotate
        systemctl reload medguard-sa-celery
    endscript
}
EOF
```

## Backup Configuration

### Automated Backup Script

#### Create Backup Script
```bash
# Create backup script
sudo tee /opt/medguard-sa/scripts/backup.sh << 'EOF'
#!/bin/bash

# Backup script for MedGuard SA
BACKUP_DIR="/opt/medguard-sa/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="medguard_sa_production"
DB_USER="medguard_user"
RETENTION_DAYS=30

# Create backup directory
mkdir -p $BACKUP_DIR/daily
mkdir -p $BACKUP_DIR/weekly

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> /var/log/medguard-sa/backup.log
}

# Database backup
log_message "Starting database backup"
pg_dump -h localhost -U $DB_USER -d $DB_NAME | gzip > $BACKUP_DIR/daily/db_$DATE.sql.gz

if [ $? -eq 0 ]; then
    log_message "Database backup completed successfully"
else
    log_message "ERROR: Database backup failed"
    exit 1
fi

# File backup
log_message "Starting file backup"
tar -czf $BACKUP_DIR/daily/files_$DATE.tar.gz \
    --exclude=$BACKUP_DIR \
    --exclude=/tmp \
    --exclude=/var/log \
    /opt/medguard-sa/app/media/ \
    /opt/medguard-sa/app/staticfiles/

if [ $? -eq 0 ]; then
    log_message "File backup completed successfully"
else
    log_message "ERROR: File backup failed"
    exit 1
fi

# Encrypt backups
log_message "Encrypting backups"
gpg --batch --yes --encrypt --recipient security@your-domain.com $BACKUP_DIR/daily/db_$DATE.sql.gz
gpg --batch --yes --encrypt --recipient security@your-domain.com $BACKUP_DIR/daily/files_$DATE.tar.gz

if [ $? -eq 0 ]; then
    log_message "Backup encryption completed"
else
    log_message "ERROR: Backup encryption failed"
    exit 1
fi

# Remove unencrypted files
rm $BACKUP_DIR/daily/db_$DATE.sql.gz
rm $BACKUP_DIR/daily/files_$DATE.tar.gz

# Weekly backup (on Sundays)
if [ $(date +%u) -eq 7 ]; then
    log_message "Creating weekly backup"
    cp $BACKUP_DIR/daily/db_$DATE.sql.gz.gpg $BACKUP_DIR/weekly/
    cp $BACKUP_DIR/daily/files_$DATE.tar.gz.gpg $BACKUP_DIR/weekly/
    log_message "Weekly backup created"
fi

# Clean old backups
log_message "Cleaning old backups"
find $BACKUP_DIR/daily -name "*.gpg" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR/weekly -name "*.gpg" -mtime +84 -delete

log_message "Backup process completed"
EOF

# Make script executable
sudo chmod +x /opt/medguard-sa/scripts/backup.sh

# Add to crontab
sudo crontab -e
# Add this line:
# 0 2 * * * /opt/medguard-sa/scripts/backup.sh
```

## Testing and Validation

### Security Testing

#### Run Security Tests
```bash
# Switch to application user
sudo su - medguard

# Activate virtual environment
cd /opt/medguard-sa/app
source venv/bin/activate

# Run security tests
python manage.py test security.tests.test_audit
python manage.py test security.tests.test_encryption

# Run compliance checks
python manage.py shell -c "
from security.hipaa_compliance import get_compliance_monitor
monitor = get_compliance_monitor()
report = monitor.generate_compliance_report()
print('Compliance Status:', report['overall_status'])
"
```

### Performance Testing

#### Load Testing
```bash
# Install Apache Bench
sudo apt install -y apache2-utils

# Run load test
ab -n 1000 -c 10 https://your-domain.com/health/

# Test API endpoints
ab -n 500 -c 5 https://your-domain.com/api/medications/
```

### SSL/TLS Testing

#### Test SSL Configuration
```bash
# Test SSL configuration
curl -vI https://your-domain.com

# Test SSL Labs (online)
# Visit: https://www.ssllabs.com/ssltest/analyze.html?d=your-domain.com
```

## Maintenance Procedures

### Regular Maintenance

#### Daily Tasks
```bash
# Check system health
/opt/medguard-sa/scripts/health_check.sh

# Review security logs
sudo tail -n 100 /var/log/medguard-sa/security.log

# Check backup status
ls -la /opt/medguard-sa/backups/daily/
```

#### Weekly Tasks
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Review audit logs
sudo python manage.py shell -c "
from security.audit import AuditLog
from django.utils import timezone
from datetime import timedelta

recent_logs = AuditLog.objects.filter(
    timestamp__gte=timezone.now() - timedelta(days=7)
).count()
print(f'Recent audit logs: {recent_logs}')
"

# Check compliance status
python manage.py shell -c "
from security.hipaa_compliance import get_compliance_monitor
monitor = get_compliance_monitor()
report = monitor.generate_compliance_report()
print('Weekly compliance report generated')
"
```

#### Monthly Tasks
```bash
# Security assessment
sudo python manage.py shell -c "
from security.hipaa_compliance import run_security_assessment
assessment = run_security_assessment()
print('Security assessment completed')
"

# Update SSL certificate
sudo certbot renew

# Review and update documentation
# Update this deployment guide with any changes
```

### Emergency Procedures

#### System Recovery
```bash
# Emergency recovery script
sudo tee /opt/medguard-sa/scripts/emergency_recovery.sh << 'EOF'
#!/bin/bash

echo "Starting emergency recovery..."

# Stop all services
systemctl stop medguard-sa
systemctl stop medguard-sa-celery
systemctl stop medguard-sa-celerybeat
systemctl stop nginx

# Restore from latest backup
LATEST_BACKUP=$(ls -t /opt/medguard-sa/backups/daily/db_*.gpg | head -1)
if [ -n "$LATEST_BACKUP" ]; then
    echo "Restoring from backup: $LATEST_BACKUP"
    gpg --decrypt $LATEST_BACKUP | psql -h localhost -U medguard_user -d medguard_sa_production
fi

# Start services
systemctl start nginx
systemctl start medguard-sa-celery
systemctl start medguard-sa-celerybeat
systemctl start medguard-sa

# Verify recovery
python manage.py check --deploy

echo "Emergency recovery completed"
EOF

sudo chmod +x /opt/medguard-sa/scripts/emergency_recovery.sh
```

## Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check service status
sudo systemctl status medguard-sa

# Check logs
sudo journalctl -u medguard-sa -f

# Check configuration
sudo python manage.py check --deploy
```

#### Database Connection Issues
```bash
# Test database connection
sudo -u medguard psql -h localhost -U medguard_user -d medguard_sa_production

# Check PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-14-main.log

# Restart PostgreSQL
sudo systemctl restart postgresql
```

#### SSL Certificate Issues
```bash
# Check certificate status
sudo certbot certificates

# Renew certificate
sudo certbot renew

# Test SSL
openssl s_client -connect your-domain.com:443 -servername your-domain.com
```

#### Performance Issues
```bash
# Check system resources
htop
df -h
free -h

# Check application logs
sudo tail -f /var/log/medguard-sa/django.log

# Check Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Log Analysis

#### Security Log Analysis
```bash
# Check for security events
sudo grep -i "security\|breach\|unauthorized" /var/log/medguard-sa/security.log

# Check for failed logins
sudo grep "login_failed" /var/log/medguard-sa/audit.log

# Check for access denials
sudo grep "access_denied" /var/log/medguard-sa/audit.log
```

#### Performance Log Analysis
```bash
# Check slow queries
sudo grep "slow_query" /var/log/medguard-sa/django.log

# Check error rates
sudo grep "ERROR" /var/log/medguard-sa/django.log | wc -l

# Check response times
sudo tail -f /var/log/nginx/access.log | awk '{print $10}'
```

---

## Conclusion

This deployment guide provides a comprehensive approach to deploying MedGuard SA in a HIPAA-compliant production environment. Follow all procedures carefully and ensure regular maintenance and monitoring to maintain security and compliance.

### Next Steps

1. **Documentation**: Update this guide with any environment-specific changes
2. **Training**: Train staff on security procedures and incident response
3. **Monitoring**: Set up comprehensive monitoring and alerting
4. **Testing**: Regular security testing and penetration testing
5. **Compliance**: Regular compliance audits and reporting

### Support

For technical support or questions about this deployment:

- **Technical Support**: support@medguard-sa.com
- **Security Team**: security@medguard-sa.com
- **Documentation**: docs.medguard-sa.com

---

**Document Version**: 1.0  
**Last Updated**: December 2024  
**Next Review**: March 2025  
**Approved By**: Security Officer 