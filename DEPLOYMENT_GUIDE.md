# SkillPath AI - Deployment & Infrastructure Guide

> **Document Version:** 1.0
> **Last Updated:** November 4, 2025
> **Target Environment:** Production-Ready MVP

---

## Table of Contents

1. [Infrastructure Overview](#infrastructure-overview)
2. [Development Environment Setup](#development-environment-setup)
3. [Production Deployment](#production-deployment)
4. [CI/CD Pipeline](#cicd-pipeline)
5. [Monitoring & Logging](#monitoring--logging)
6. [Backup & Disaster Recovery](#backup--disaster-recovery)
7. [Security Hardening](#security-hardening)

---

## Infrastructure Overview

### MVP Architecture (Single VPS)

**Cost-Effective Setup:**
- Single DigitalOcean Droplet: $24-48/month
- Domain + SSL: $12/year (Namecheap) + Free Let's Encrypt
- **Total Monthly Cost:** ~$25-50

**Server Specifications:**
- **Tier 1 (MVP Launch):** 2 vCPU, 4GB RAM, 80GB SSD
- **Tier 2 (Growth):** 4 vCPU, 8GB RAM, 160GB SSD

**Location:** Choose closest to Egypt:
- Frankfurt, Germany (low latency to Egypt)
- London, UK
- Or: Deploy on Egyptian cloud provider if available

---

## Development Environment Setup

### Prerequisites

**Install Required Software:**
```bash
# Node.js 20+ (LTS)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Docker & Docker Compose
sudo apt-get update
sudo apt-get install docker.io docker-compose -y
sudo usermod -aG docker $USER

# PostgreSQL Client
sudo apt-get install postgresql-client -y

# Git
sudo apt-get install git -y
```

---

### Local Development Setup

**1. Clone Repository**
```bash
git clone https://github.com/yourusername/skillpath-backend.git
cd skillpath-backend
```

**2. Create Environment File**
```bash
cp .env.example .env
```

**.env (Development)**
```env
# Application
NODE_ENV=development
PORT=3000
API_VERSION=v1

# Database
DATABASE_URL=postgresql://skillpath_user:dev_password@localhost:5432/skillpath_dev
DB_HOST=localhost
DB_PORT=5432
DB_NAME=skillpath_dev
DB_USER=skillpath_user
DB_PASSWORD=dev_password

# Redis
REDIS_URL=redis://localhost:6379
REDIS_HOST=localhost
REDIS_PORT=6379

# JWT
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
JWT_EXPIRATION=15m
REFRESH_TOKEN_SECRET=your-refresh-token-secret
REFRESH_TOKEN_EXPIRATION=7d

# OpenAI / Claude
OPENAI_API_KEY=sk-your-openai-api-key
ANTHROPIC_API_KEY=sk-ant-your-claude-api-key
AI_MONTHLY_BUDGET_USD=50

# Email (Development - Use Mailtrap or similar)
SMTP_HOST=smtp.mailtrap.io
SMTP_PORT=2525
SMTP_USER=your_mailtrap_user
SMTP_PASSWORD=your_mailtrap_password
SMTP_FROM=noreply@skillpath-ai.com

# Frontend URL (for CORS)
FRONTEND_URL=http://localhost:5173

# Logging
LOG_LEVEL=debug
```

**3. Start Development Services with Docker Compose**

**docker-compose.dev.yml**
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: skillpath_postgres_dev
    environment:
      POSTGRES_DB: skillpath_dev
      POSTGRES_USER: skillpath_user
      POSTGRES_PASSWORD: dev_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_dev_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U skillpath_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: skillpath_redis_dev
    ports:
      - "6379:6379"
    volumes:
      - redis_dev_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  mailhog:
    image: mailhog/mailhog:latest
    container_name: skillpath_mailhog
    ports:
      - "1025:1025"  # SMTP
      - "8025:8025"  # Web UI
    networks:
      - skillpath_network

volumes:
  postgres_dev_data:
  redis_dev_data:

networks:
  skillpath_network:
    driver: bridge
```

**Start Services:**
```bash
docker-compose -f docker-compose.dev.yml up -d
```

**4. Install Dependencies**
```bash
npm install
```

**5. Run Database Migrations**
```bash
npm run migration:run
```

**6. Seed Database (Optional)**
```bash
npm run seed
```

**7. Start Development Server**
```bash
npm run dev
```

**Access:**
- API: http://localhost:3000/api/v1
- API Docs: http://localhost:3000/api/v1/docs
- Mailhog UI: http://localhost:8025

---

### Project Structure

```
skillpath-backend/
├── src/
│   ├── config/                 # Configuration files
│   │   ├── database.ts
│   │   ├── redis.ts
│   │   ├── jwt.ts
│   │   └── email.ts
│   ├── controllers/            # Request handlers
│   │   ├── auth.controller.ts
│   │   ├── user.controller.ts
│   │   ├── assessment.controller.ts
│   │   ├── learning.controller.ts
│   │   └── job.controller.ts
│   ├── services/               # Business logic
│   │   ├── auth.service.ts
│   │   ├── user.service.ts
│   │   ├── assessment.service.ts
│   │   ├── ai.service.ts
│   │   ├── learning.service.ts
│   │   └── job.service.ts
│   ├── models/                 # Database models (TypeORM entities)
│   │   ├── User.entity.ts
│   │   ├── UserProfile.entity.ts
│   │   ├── Assessment.entity.ts
│   │   └── ...
│   ├── middleware/             # Custom middleware
│   │   ├── auth.middleware.ts
│   │   ├── error.middleware.ts
│   │   ├── validation.middleware.ts
│   │   └── rateLimit.middleware.ts
│   ├── routes/                 # API route definitions
│   │   ├── auth.routes.ts
│   │   ├── user.routes.ts
│   │   ├── assessment.routes.ts
│   │   ├── learning.routes.ts
│   │   └── job.routes.ts
│   ├── utils/                  # Helper functions
│   │   ├── logger.ts
│   │   ├── validator.ts
│   │   ├── crypto.ts
│   │   └── email.ts
│   ├── validators/             # Input validation schemas (Zod/Joi)
│   │   ├── auth.validator.ts
│   │   ├── user.validator.ts
│   │   └── ...
│   ├── types/                  # TypeScript type definitions
│   │   ├── express.d.ts
│   │   ├── api.types.ts
│   │   └── ...
│   ├── jobs/                   # Background job processors
│   │   ├── roadmapGeneration.job.ts
│   │   ├── jobAggregation.job.ts
│   │   └── emailNotification.job.ts
│   ├── migrations/             # Database migrations
│   └── app.ts                  # Express app setup
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── .env.example
├── .env
├── .gitignore
├── docker-compose.dev.yml
├── docker-compose.prod.yml
├── Dockerfile
├── package.json
├── tsconfig.json
└── README.md
```

---

## Production Deployment

### Step 1: Provision Server

**DigitalOcean Droplet Setup:**
```bash
# 1. Create Droplet via DigitalOcean dashboard or CLI
doctl compute droplet create skillpath-prod \
  --region fra1 \
  --size s-2vcpu-4gb \
  --image ubuntu-22-04-x64 \
  --ssh-keys your-ssh-key-id

# 2. SSH into server
ssh root@your-server-ip
```

---

### Step 2: Server Initial Setup

**Secure Server:**
```bash
# Update system
apt update && apt upgrade -y

# Create app user (don't use root)
adduser skillpath
usermod -aG sudo skillpath
su - skillpath

# Configure firewall
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

---

### Step 3: Install Dependencies

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
sudo usermod -aG docker skillpath

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Nginx
sudo apt install nginx -y
```

---

### Step 4: Clone Application

```bash
cd /home/skillpath
git clone https://github.com/yourusername/skillpath-backend.git app
cd app
```

---

### Step 5: Production Environment Configuration

**.env.production**
```env
# Application
NODE_ENV=production
PORT=3000
API_VERSION=v1

# Database
DATABASE_URL=postgresql://skillpath_prod:STRONG_PASSWORD_HERE@localhost:5432/skillpath_prod
DB_HOST=postgres
DB_PORT=5432
DB_NAME=skillpath_prod
DB_USER=skillpath_prod
DB_PASSWORD=STRONG_PASSWORD_HERE

# Redis
REDIS_URL=redis://redis:6379
REDIS_HOST=redis
REDIS_PORT=6379

# JWT (CHANGE THESE!)
JWT_SECRET=generate-strong-random-secret-with-openssl-rand-base64-32
JWT_EXPIRATION=15m
REFRESH_TOKEN_SECRET=another-strong-secret-for-refresh-tokens
REFRESH_TOKEN_EXPIRATION=7d

# OpenAI / Claude
OPENAI_API_KEY=sk-your-production-openai-key
ANTHROPIC_API_KEY=sk-ant-your-production-claude-key
AI_MONTHLY_BUDGET_USD=50

# Email (Production - Use SendGrid or AWS SES)
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=SG.your-sendgrid-api-key
SMTP_FROM=noreply@skillpath-ai.com

# Frontend URL
FRONTEND_URL=https://skillpath-ai.com

# Domain
API_DOMAIN=api.skillpath-ai.com

# Logging
LOG_LEVEL=info
```

**Generate Secrets:**
```bash
# Generate JWT secret
openssl rand -base64 32

# Generate refresh token secret
openssl rand -base64 32
```

---

### Step 6: Docker Compose Production Setup

**docker-compose.prod.yml**
```yaml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    container_name: skillpath_nginx
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - ./nginx/logs:/var/log/nginx
    depends_on:
      - app
    networks:
      - skillpath_network

  app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: skillpath_app
    restart: always
    environment:
      NODE_ENV: production
    env_file:
      - .env.production
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - skillpath_network
    volumes:
      - ./logs:/app/logs

  postgres:
    image: postgres:15-alpine
    container_name: skillpath_postgres
    restart: always
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    networks:
      - skillpath_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: skillpath_redis
    restart: always
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    networks:
      - skillpath_network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

volumes:
  postgres_data:
  redis_data:

networks:
  skillpath_network:
    driver: bridge
```

---

### Step 7: Dockerfile

**Dockerfile**
```dockerfile
# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./
COPY tsconfig.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY src ./src

# Build TypeScript
RUN npm run build

# Production stage
FROM node:20-alpine

WORKDIR /app

# Copy built files and dependencies
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/package*.json ./

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001

USER nodejs

EXPOSE 3000

CMD ["node", "dist/app.js"]
```

---

### Step 8: Nginx Configuration

**nginx/nginx.conf**
```nginx
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript
               application/json application/javascript application/xml+rss;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=auth_limit:10m rate=5r/m;

    upstream backend {
        server app:3000;
    }

    # Redirect HTTP to HTTPS
    server {
        listen 80;
        server_name api.skillpath-ai.com;
        return 301 https://$server_name$request_uri;
    }

    # HTTPS server
    server {
        listen 443 ssl http2;
        server_name api.skillpath-ai.com;

        # SSL configuration
        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        ssl_prefer_server_ciphers on;

        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "strict-origin-when-cross-origin" always;

        # API endpoints
        location /api/ {
            limit_req zone=api_limit burst=20 nodelay;

            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_cache_bypass $http_upgrade;

            # Timeouts
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # Authentication endpoints (stricter rate limiting)
        location /api/v1/auth/ {
            limit_req zone=auth_limit burst=5 nodelay;

            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Health check endpoint (no rate limiting)
        location /health {
            proxy_pass http://backend;
            access_log off;
        }
    }
}
```

---

### Step 9: SSL Certificate Setup

**Using Let's Encrypt (Free SSL):**
```bash
# Install Certbot
sudo apt install certbot -y

# Generate certificate
sudo certbot certonly --standalone -d api.skillpath-ai.com

# Copy certificates to project
sudo mkdir -p /home/skillpath/app/nginx/ssl
sudo cp /etc/letsencrypt/live/api.skillpath-ai.com/fullchain.pem /home/skillpath/app/nginx/ssl/
sudo cp /etc/letsencrypt/live/api.skillpath-ai.com/privkey.pem /home/skillpath/app/nginx/ssl/
sudo chown -R skillpath:skillpath /home/skillpath/app/nginx/ssl

# Auto-renewal (add to crontab)
sudo crontab -e
# Add this line:
0 0 1 * * certbot renew --quiet && docker-compose -f /home/skillpath/app/docker-compose.prod.yml restart nginx
```

---

### Step 10: Deploy Application

```bash
# Build and start containers
docker-compose -f docker-compose.prod.yml up -d --build

# Run migrations
docker-compose -f docker-compose.prod.yml exec app npm run migration:run

# Check logs
docker-compose -f docker-compose.prod.yml logs -f app

# Check status
docker-compose -f docker-compose.prod.yml ps
```

---

### Step 11: Database Backup Setup

**Automated Backup Script**

**/home/skillpath/scripts/backup-db.sh**
```bash
#!/bin/bash

BACKUP_DIR="/home/skillpath/app/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_NAME="skillpath_prod"
DB_USER="skillpath_prod"

# Create backup
docker exec skillpath_postgres pg_dump -U $DB_USER $DB_NAME | gzip > "$BACKUP_DIR/backup_$TIMESTAMP.sql.gz"

# Delete backups older than 30 days
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete

echo "Backup completed: backup_$TIMESTAMP.sql.gz"
```

**Make Executable:**
```bash
chmod +x /home/skillpath/scripts/backup-db.sh
```

**Schedule Daily Backups (Cron):**
```bash
crontab -e

# Add this line (daily at 2 AM)
0 2 * * * /home/skillpath/scripts/backup-db.sh >> /home/skillpath/logs/backup.log 2>&1
```

---

## CI/CD Pipeline

### GitHub Actions Workflow

**.github/workflows/deploy.yml**
```yaml
name: Deploy to Production

on:
  push:
    branches:
      - main

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_DB: skillpath_test
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_pass
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 3s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run linter
        run: npm run lint

      - name: Run tests
        run: npm test
        env:
          DATABASE_URL: postgresql://test_user:test_pass@localhost:5432/skillpath_test
          REDIS_URL: redis://localhost:6379
          NODE_ENV: test

      - name: Build project
        run: npm run build

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
      - name: Deploy to server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /home/skillpath/app
            git pull origin main
            docker-compose -f docker-compose.prod.yml down
            docker-compose -f docker-compose.prod.yml up -d --build
            docker-compose -f docker-compose.prod.yml exec -T app npm run migration:run
            echo "Deployment completed successfully"

      - name: Notify deployment status
        if: always()
        run: |
          echo "Deployment status: ${{ job.status }}"
```

**GitHub Secrets to Add:**
- `SERVER_HOST`: Your server IP
- `SERVER_USER`: `skillpath`
- `SSH_PRIVATE_KEY`: Your SSH private key

---

## Monitoring & Logging

### Application Logging (Winston)

**src/utils/logger.ts**
```typescript
import winston from 'winston';

const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  transports: [
    new winston.transports.File({
      filename: 'logs/error.log',
      level: 'error'
    }),
    new winston.transports.File({
      filename: 'logs/combined.log'
    }),
  ],
});

if (process.env.NODE_ENV !== 'production') {
  logger.add(new winston.transports.Console({
    format: winston.format.combine(
      winston.format.colorize(),
      winston.format.simple()
    ),
  }));
}

export default logger;
```

---

### Health Check Endpoint

**src/routes/health.routes.ts**
```typescript
import { Router } from 'express';
import { AppDataSource } from '../config/database';
import redis from '../config/redis';

const router = Router();

router.get('/health', async (req, res) => {
  try {
    // Check database
    await AppDataSource.query('SELECT 1');

    // Check Redis
    await redis.ping();

    res.json({
      status: 'healthy',
      timestamp: new Date().toISOString(),
      services: {
        database: 'up',
        redis: 'up',
        api: 'up'
      }
    });
  } catch (error) {
    res.status(503).json({
      status: 'unhealthy',
      timestamp: new Date().toISOString(),
      error: error.message
    });
  }
});

export default router;
```

---

### Uptime Monitoring

**Use Free Services:**
- **UptimeRobot:** https://uptimerobot.com (free, 50 monitors)
- **Pingdom:** Free tier available
- **BetterUptime:** Free tier

**Monitor:**
- API health endpoint: https://api.skillpath-ai.com/health
- Frontend: https://skillpath-ai.com

---

## Backup & Disaster Recovery

### Backup Strategy

**What to Backup:**
1. Database (PostgreSQL)
2. Redis persistence files (if critical data)
3. Application logs
4. Environment configuration
5. SSL certificates

**Backup Schedule:**
- **Database:** Daily at 2 AM (30-day retention)
- **Full system:** Weekly
- **Critical data:** Before each deployment

### Restore Procedure

**Restore Database:**
```bash
# Copy backup to server
scp backup_20251104_020000.sql.gz skillpath@your-server:/tmp/

# SSH into server
ssh skillpath@your-server

# Restore
gunzip < /tmp/backup_20251104_020000.sql.gz | \
  docker exec -i skillpath_postgres psql -U skillpath_prod -d skillpath_prod
```

---

## Security Hardening

### Server Security

**SSH Hardening:**
```bash
# Edit SSH config
sudo nano /etc/ssh/sshd_config

# Disable root login
PermitRootLogin no

# Disable password authentication (use SSH keys only)
PasswordAuthentication no

# Restart SSH
sudo systemctl restart sshd
```

**Install Fail2Ban:**
```bash
sudo apt install fail2ban -y
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### Application Security

**Environment Variable Protection:**
```bash
# Secure .env file
chmod 600 .env.production
```

**Docker Security:**
```bash
# Run containers as non-root user (already in Dockerfile)
# Limit container resources in docker-compose.prod.yml

services:
  app:
    # ... other config
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 2G
```

---

## Troubleshooting

### Common Issues

**Container won't start:**
```bash
# Check logs
docker-compose logs app

# Check container status
docker ps -a
```

**Database connection issues:**
```bash
# Test PostgreSQL connection
docker exec skillpath_postgres psql -U skillpath_prod -d skillpath_prod -c "SELECT 1"
```

**High memory usage:**
```bash
# Check Docker stats
docker stats

# Restart containers
docker-compose -f docker-compose.prod.yml restart
```

---

**Deployment Guide Prepared By:** SkillPath AI Development Team
**Version:** 1.0 (MVP)
**Support:** devops@skillpath-ai.com
