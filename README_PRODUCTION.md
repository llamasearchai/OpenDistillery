# OpenDistillery - Production Deployment Guide

## Overview

OpenDistillery is an enterprise-grade compound AI system designed for Fortune 500 companies and large-scale production deployments. This guide covers production deployment, configuration, and operational best practices.

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │    │   API Gateway   │    │  Authentication │
│     (NGINX)     │────│   (FastAPI)     │────│    (JWT/MFA)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Agent Orchestra │    │ Compound AI     │    │   Monitoring    │
│   (Multi-Agent) │────│   Systems       │────│ (Prometheus)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │     Redis       │    │  Elasticsearch  │
│   (Database)    │    │    (Cache)      │    │   (Logging)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Enterprise Features

### Security & Compliance
- **Multi-Factor Authentication (MFA)** with TOTP support
- **Role-Based Access Control (RBAC)** with granular permissions
- **API Key Management** with expiration and rate limiting
- **Audit Logging** with correlation tracking
- **Data Encryption** at rest and in transit
- **SOC2, ISO27001, GDPR, HIPAA** compliance ready

### Monitoring & Observability
- **Structured Logging** with correlation IDs
- **Prometheus Metrics** with custom dashboards
- **Distributed Tracing** with Jaeger
- **Health Checks** and alerting
- **Performance Analytics** and insights
- **Real-time Dashboards** with Grafana

### Performance & Scaling
- **Horizontal Auto-scaling** based on load
- **Intelligent Load Balancing** across agents
- **Advanced Caching** with Redis
- **Circuit Breakers** for fault tolerance
- **Resource Pool Management**
- **Performance Optimization Engine**

### Enterprise Integrations
- **Salesforce CRM** with AI-powered insights
- **Microsoft 365** integration
- **SAP** enterprise systems
- **Custom API** integrations
- **Webhook** support for real-time events

## Quick Start (Production)

### 1. Prerequisites

```bash
# System Requirements
- Docker 24.0+ and Docker Compose 2.0+
- 16GB+ RAM, 8+ CPU cores
- 100GB+ SSD storage
- PostgreSQL 15+
- Redis 7+

# Network Requirements
- Ports 80, 443 (HTTPS)
- Port 8000 (API)
- Port 9090 (Prometheus)
- Port 3000 (Grafana)
```

### 2. Environment Configuration

```bash
# Copy and configure environment
cp config/production.env.example .env

# Edit configuration (CRITICAL: Change all passwords and secrets!)
nano .env
```

### 3. Production Deployment

```bash
# Deploy with Docker Compose
docker-compose -f docker-compose.production.yml up -d

# Verify deployment
docker-compose -f docker-compose.production.yml ps
curl http://localhost:8000/health
```

### 4. Initial Setup

```bash
# Create admin user
curl -X POST http://localhost:8000/admin/users \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@yourcompany.com",
    "password": "secure_password_123",
    "role": "admin"
  }'

# Generate API keys
curl -X POST http://localhost:8000/auth/api-keys \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production API Key",
    "permissions": ["read", "write", "admin"],
    "expires_in_days": 90
  }'
```

## Configuration

### Security Configuration

For production deployments, ensure that sensitive information such as API keys and database credentials are not hardcoded in the codebase. Use environment variables to manage these settings:

- **SECRET_KEY**: Used for JWT token generation. Set a strong, unique key.
- **DATABASE_URL**: Connection string for your database.
- **REDIS_URL**: Connection string for Redis.
- **OPENAI_API_KEY**: Your OpenAI API key for AI services.
- **ANTHROPIC_API_KEY**: Your Anthropic API key if applicable.

You can set these variables in your deployment environment or use a `.env` file (not included in version control) for local development. Refer to the `.env.example` file for a template (if available).

```yaml
# config/security.yml
security:
  secret_key: "your-256-bit-secret-key"
  jwt_expiry_hours: 24
  mfa_required: true
  rate_limiting:
    enabled: true
    requests_per_minute: 100
  encryption:
    algorithm: "AES-256-GCM"
    key_rotation_days: 90
```

### Database Configuration

```yaml
# config/database.yml
database:
  host: "postgres-cluster.internal"
  port: 5432
  name: "opendistillery_prod"
  user: "opendistillery"
  password: "${DATABASE_PASSWORD}"
  ssl_mode: "require"
  pool_size: 20
  max_overflow: 30
  pool_timeout: 30
```

### AI Model Configuration

```yaml
# config/models.yml
models:
  openai:
    api_key: "${OPENAI_API_KEY}"
    default_model: "gpt-4"
    max_tokens: 4096
    temperature: 0.1
  
  anthropic:
    api_key: "${ANTHROPIC_API_KEY}"
    default_model: "claude-3-opus-20240229"
    max_tokens: 4096
    temperature: 0.0
```

## Deployment Options

### Docker Compose (Recommended for Single Server)

```bash
# Production deployment
docker-compose -f docker-compose.production.yml up -d

# Scale workers
docker-compose -f docker-compose.production.yml up -d --scale opendistillery-worker=5

# Update deployment
docker-compose -f docker-compose.production.yml pull
docker-compose -f docker-compose.production.yml up -d
```

### Kubernetes (Recommended for Enterprise)

```bash
# Deploy to Kubernetes
kubectl apply -f k8s/namespace.yml
kubectl apply -f k8s/configmap.yml
kubectl apply -f k8s/secrets.yml
kubectl apply -f k8s/deployment.yml
kubectl apply -f k8s/service.yml
kubectl apply -f k8s/ingress.yml

# Scale deployment
kubectl scale deployment opendistillery-api --replicas=5

# Rolling update
kubectl set image deployment/opendistillery-api \
  opendistillery=opendistillery:v1.1.0
```

### Cloud Deployments

#### AWS ECS/Fargate
```bash
# Deploy to AWS ECS
aws ecs create-cluster --cluster-name opendistillery-prod
aws ecs register-task-definition --cli-input-json file://aws/task-definition.json
aws ecs create-service --cluster opendistillery-prod --service-name opendistillery-api
```

#### Azure Container Instances
```bash
# Deploy to Azure
az container create \
  --resource-group opendistillery-rg \
  --name opendistillery-prod \
  --image opendistillery:latest \
  --cpu 4 --memory 8
```

#### Google Cloud Run
```bash
# Deploy to Google Cloud Run
gcloud run deploy opendistillery \
  --image gcr.io/your-project/opendistillery:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

## Monitoring & Operations

### Health Monitoring

```bash
# Health check endpoint
curl http://localhost:8000/health

# Detailed system status
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/metrics

# Prometheus metrics
curl http://localhost:9090/metrics
```

### Log Management

```bash
# View application logs
docker-compose logs -f opendistillery-api

# Search logs in Elasticsearch
curl -X GET "localhost:9200/opendistillery-logs/_search" \
  -H "Content-Type: application/json" \
  -d '{"query": {"match": {"level": "ERROR"}}}'

# Structured log analysis
grep "correlation_id" /app/logs/opendistillery.log | jq .
```

### Performance Monitoring

```bash
# View Grafana dashboards
open http://localhost:3000

# Prometheus queries
curl -G http://localhost:9090/api/v1/query \
  --data-urlencode 'query=opendistillery_requests_total'

# Jaeger tracing
open http://localhost:16686
```

## Security Best Practices

### 1. Authentication & Authorization

```python
# Enable MFA for all admin users
OPENDISTILLERY_REQUIRE_MFA=true

# Use strong API keys
API_KEY_LENGTH=32
API_KEY_EXPIRY_DAYS=90

# Implement RBAC
ROLES=["admin", "operator", "analyst", "viewer"]
```

### 2. Network Security

```bash
# Use HTTPS only
FORCE_HTTPS=true
HSTS_MAX_AGE=31536000

# Restrict network access
ALLOWED_IPS="10.0.0.0/8,172.16.0.0/12,192.168.0.0/16"

# Enable firewall
ufw enable
ufw allow 80/tcp
ufw allow 443/tcp
ufw deny 8000/tcp  # Only internal access
```

### 3. Data Protection

```yaml
# Encryption configuration
encryption:
  at_rest: true
  in_transit: true
  key_rotation: 90  # days
  algorithm: "AES-256-GCM"

# Data retention
retention:
  logs: 90  # days
  audit_logs: 2555  # 7 years
  user_data: 2555  # 7 years
```

## Backup & Disaster Recovery

### Database Backup

```bash
# Automated daily backups
pg_dump -h postgres -U opendistillery opendistillery_prod | \
  gzip > backup_$(date +%Y%m%d).sql.gz

# Upload to S3
aws s3 cp backup_$(date +%Y%m%d).sql.gz \
  s3://opendistillery-backups/database/
```

### Application Backup

```bash
# Backup configuration
tar -czf config_backup_$(date +%Y%m%d).tar.gz config/

# Backup logs
tar -czf logs_backup_$(date +%Y%m%d).tar.gz logs/

# Upload to cloud storage
aws s3 sync ./backups s3://opendistillery-backups/
```

### Disaster Recovery

```bash
# Restore from backup
gunzip -c backup_20241201.sql.gz | \
  psql -h postgres-new -U opendistillery opendistillery_prod

# Restore configuration
tar -xzf config_backup_20241201.tar.gz

# Restart services
docker-compose -f docker-compose.production.yml restart
```

## Troubleshooting

### Common Issues

#### 1. High Memory Usage
```bash
# Check memory usage
docker stats

# Scale down workers
docker-compose -f docker-compose.production.yml \
  up -d --scale opendistillery-worker=2

# Optimize cache settings
CACHE_MAX_SIZE_MB=256
```

#### 2. Database Connection Issues
```bash
# Check database connectivity
pg_isready -h postgres -p 5432

# Check connection pool
curl http://localhost:8000/health | jq .database

# Restart database
docker-compose restart postgres
```

#### 3. API Performance Issues
```bash
# Check API metrics
curl http://localhost:8000/metrics | grep response_time

# Enable caching
CACHE_ENABLED=true
CACHE_TTL_SECONDS=3600

# Scale API instances
kubectl scale deployment opendistillery-api --replicas=5
```

### Log Analysis

```bash
# Error analysis
grep "ERROR" /app/logs/opendistillery.log | \
  jq -r '.timestamp + " " + .message'

# Performance analysis
grep "duration_ms" /app/logs/opendistillery.log | \
  jq '.duration_ms' | sort -n | tail -10

# Security analysis
grep "security_event" /app/logs/opendistillery.log | \
  jq -r '.details'
```

## API Documentation

### Authentication

```bash
# Login and get token
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'

# Use token in requests
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/systems
```

### Task Submission

```bash
# Submit a task
curl -X POST http://localhost:8000/tasks \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "financial_analysis",
    "description": "Analyze Q4 financial performance",
    "input_data": {"revenue": 1000000, "expenses": 800000},
    "priority": "high"
  }'

# Check task status
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/tasks/task_123
```

### System Management

```bash
# Create new AI system
curl -X POST http://localhost:8000/systems \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "system_id": "financial_system",
    "domain": "finance",
    "use_case": "risk_analysis",
    "architecture": "hybrid"
  }'

# List all systems
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/systems
```

## Support & Maintenance

### Regular Maintenance

```bash
# Weekly tasks
- Review security logs
- Update dependencies
- Rotate API keys
- Check backup integrity
- Performance optimization

# Monthly tasks
- Security audit
- Capacity planning
- Cost optimization
- Disaster recovery testing
- Documentation updates
```

### Support Channels

- **Enterprise Support**: nikjois@llamasearch.ai
- **Documentation**: https://docs.opendistillery.ai
- **Status Page**: https://status.opendistillery.ai
- **Security Issues**: nikjois@llamasearch.ai

### SLA & Performance Targets

- **Uptime**: 99.9% (8.76 hours downtime/year)
- **Response Time**: < 500ms (95th percentile)
- **Throughput**: 1000+ requests/second
- **Recovery Time**: < 1 hour (RTO)
- **Data Loss**: < 15 minutes (RPO)

## License & Compliance

OpenDistillery Enterprise is licensed under a commercial license for production use. The system is designed to meet enterprise compliance requirements including:

- **SOC 2 Type II** compliance
- **ISO 27001** certification
- **GDPR** compliance for EU operations
- **HIPAA** compliance for healthcare
- **PCI DSS** for payment processing

For licensing information, contact: nikjois@llamasearch.ai

---

**OpenDistillery Contact**  
Nik Jois  
Email: nikjois@llamasearch.ai  
Website: https://opendistillery.ai  
Documentation: https://docs.opendistillery.ai 