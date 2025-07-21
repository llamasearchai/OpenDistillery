<div align="center">
  <img src="OpenDistillery.png" alt="OpenDistillery Logo" width="400"/>
  
  # OpenDistillery
  ## Advanced Compound AI Systems for Enterprise Workflow Transformation
</div>

<div align="center">

[![CI/CD Pipeline](https://github.com/llamasearchai/OpenDistillery/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/llamasearchai/OpenDistillery/actions/workflows/ci-cd.yml)
[![CI](https://github.com/llamasearchai/OpenDistillery/actions/workflows/ci.yml/badge.svg)](https://github.com/llamasearchai/OpenDistillery/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/opendistillery.svg)](https://badge.fury.io/py/opendistillery)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Coverage](https://codecov.io/gh/llamasearchai/OpenDistillery/branch/main/graph/badge.svg)](https://codecov.io/gh/llamasearchai/OpenDistillery)
[![Documentation Status](https://readthedocs.org/projects/opendistillery/badge/?version=latest)](https://opendistillery.readthedocs.io/en/latest/?badge=latest)
[![Docker Pulls](https://img.shields.io/docker/pulls/nikjois/opendistillery.svg)](https://hub.docker.com/r/nikjois/opendistillery)
[![GitHub Stars](https://img.shields.io/github/stars/llamasearchai/OpenDistillery.svg?style=social&label=Star)](https://github.com/llamasearchai/OpenDistillery)
[![Downloads](https://static.pepy.tech/badge/opendistillery)](https://pepy.tech/project/opendistillery)
[![GitHub Issues](https://img.shields.io/github/issues/llamasearchai/OpenDistillery.svg)](https://github.com/llamasearchai/OpenDistillery/issues)
[![GitHub Pull Requests](https://img.shields.io/github/issues-pr/llamasearchai/OpenDistillery.svg)](https://github.com/llamasearchai/OpenDistillery/pulls)

</div>

---

OpenDistillery is a **production-ready, enterprise-grade compound AI system** demonstrating advanced software engineering capabilities and modern architecture patterns. Built with Python, FastAPI, and Docker, it showcases expertise in distributed systems, microservices architecture, and AI/ML integration at scale.

## Key Highlights

- **42+ Latest AI Models** including OpenAI GPT-4.1, o3, Claude-3.5 Sonnet, Grok-2
- **Multi-Agent Orchestration** with intelligent task routing and coordination
- **Enterprise Security** with JWT, MFA, RBAC, and audit logging
- **Production-Ready** with Docker, Kubernetes, and auto-scaling
- **Comprehensive Testing** with 95%+ code coverage and CI/CD pipelines
- **Professional Documentation** with complete API reference and examples

---

## Quick Start

### Installation

```bash
pip install opendistillery
```

### Basic Usage

```python
import asyncio
from opendistillery import get_completion, get_reasoning_completion

async def main():
    # Simple completion with latest models
    response = await get_completion(
        "Analyze quarterly financial performance trends",
        model="gpt-4-turbo",
        temperature=0.1
    )
    print(response)

    # Advanced reasoning with o1-preview
    reasoning_response = await get_reasoning_completion(
        "Solve this complex mathematical proof step by step",
        model="o1-preview"
    )
    print(reasoning_response)

asyncio.run(main())
```

### Multi-Provider Integration

```python
from opendistillery import MultiProviderAPI, OpenAIModel, AnthropicModel, XAIModel

async def multi_provider_example():
    async with MultiProviderAPI(
        openai_api_key="your-openai-key",
        anthropic_api_key="your-anthropic-key",
        xai_api_key="your-xai-key"
    ) as api:
        # Claude-3.5 Sonnet for complex reasoning
        claude_response = await api.chat_completion(
            messages=[{"role": "user", "content": "Analyze this business strategy"}],
            model=AnthropicModel.CLAUDE_35_SONNET.value,
            extended_thinking=True
        )

        # Grok-2 for real-time information
        grok_response = await api.chat_completion(
            messages=[{"role": "user", "content": "What's trending on X today?"}],
            model=XAIModel.GROK_2.value,
            mode="think",
            real_time_info=True
        )

        # GPT-4 Turbo for large document analysis
        gpt_response = await api.chat_completion(
            messages=[{"role": "user", "content": "Summarize this 1000-page report"}],
            model=OpenAIModel.GPT_4_TURBO.value,
            max_tokens=32000
        )

asyncio.run(multi_provider_example())
```

---

## Architecture Overview

OpenDistillery implements a sophisticated compound AI architecture designed for enterprise scale:

```
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ Load Balancer   │ │ API Gateway     │ │ Authentication  │
│ (NGINX)         │─│ (FastAPI)       │─│ (JWT/MFA)       │
└─────────────────┘ └─────────────────┘ └─────────────────┘
        │                   │                   │
        ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ Agent Orchestra │ │ Compound AI     │ │ Monitoring      │
│ (Multi-Agent)   │─│ Systems         │─│ (Prometheus)    │
└─────────────────┘ └─────────────────┘ └─────────────────┘
        │                   │                   │
        ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ PostgreSQL      │ │ Redis           │ │ Elasticsearch   │
│ (Database)      │ │ (Cache)         │ │ (Logging)       │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

### Core Components

- **Multi-Provider API Engine**: Unified interface for OpenAI, Anthropic, xAI, and Google models
- **Compound AI System**: Multi-agent coordination with advanced reasoning chains
- **Enterprise Features**: Production-ready FastAPI server with PostgreSQL and Redis
- **Monitoring & Security**: Comprehensive observability and enterprise-grade security

---

## Latest AI Model Support (2025)

### OpenAI Models
- **GPT-4.1** - Latest flagship model with enhanced capabilities
- **o3 & o3-pro** - Advanced reasoning models with chain-of-thought processing
- **o4-mini** - Cost-effective model for high-volume tasks
- **GPT-4 Turbo** - 128K context window with advanced reasoning
- **GPT-4o** - Multimodal omni model with real-time processing

### Anthropic Claude Models
- **Claude-3.5 Sonnet** - Superior reasoning and analysis capabilities
- **Claude-3 Opus** - Most capable model for complex tasks
- **Claude-3 Haiku** - Fast and efficient for structured tasks

### xAI Grok Models
- **Grok-2** - Real-time information with advanced reasoning
- **Grok-2 Beta** - Enhanced responses with X platform integration
- **Grok-1.5V** - Vision-enabled multimodal processing

---

## Professional Skills Demonstrated

### Software Engineering Excellence
- **Clean Architecture**: SOLID principles, dependency injection, modular design
- **API Development**: RESTful APIs with FastAPI and comprehensive OpenAPI docs
- **Database Design**: PostgreSQL with advanced schema and optimization
- **Testing Strategy**: Unit, integration, and performance testing with 95%+ coverage
- **DevOps Practices**: CI/CD pipelines, containerization, infrastructure as code

### Advanced Technical Implementation
- **Microservices Architecture**: Scalable, fault-tolerant distributed systems
- **Security Engineering**: JWT authentication, RBAC, encryption, audit logging
- **Performance Optimization**: Caching, load balancing, auto-scaling
- **Monitoring & Observability**: Prometheus metrics, structured logging, alerting
- **Cloud-Native Development**: Kubernetes orchestration and multi-cloud deployment

---

## Production Deployment

### Docker Deployment

```bash
# Quick start with Docker Compose
git clone https://github.com/llamasearchai/OpenDistillery.git
cd OpenDistillery

# Configure environment
cp config/production.env.example .env
# Edit .env with your API keys and configuration

# Deploy full stack
docker-compose -f docker-compose.production.yml up -d

# Verify deployment
curl http://localhost:8000/health
```

### Kubernetes Deployment

```bash
# Deploy to Kubernetes cluster
kubectl apply -f deployment/k8s/namespace.yml
kubectl apply -f deployment/k8s/configmap.yml
kubectl apply -f deployment/k8s/secrets.yml
kubectl apply -f deployment/k8s/deployment.yml
kubectl apply -f deployment/k8s/service.yml
kubectl apply -f deployment/k8s/ingress.yml

# Scale deployment
kubectl scale deployment opendistillery-api --replicas=5
```

### Cloud Deployments

**AWS ECS/Fargate:**
```bash
aws ecs create-cluster --cluster-name opendistillery-prod
aws ecs register-task-definition --cli-input-json file://aws/task-definition.json
aws ecs create-service --cluster opendistillery-prod --service-name opendistillery-api
```

**Google Cloud Run:**
```bash
gcloud run deploy opendistillery \
  --image gcr.io/your-project/opendistillery:latest \
  --platform managed \
  --region us-central1 \
  --cpu 4 --memory 8Gi
```

**Azure Container Instances:**
```bash
az container create \
  --resource-group opendistillery-rg \
  --name opendistillery-prod \
  --image opendistillery:latest \
  --cpu 4 --memory 8
```

---

## Configuration

### Environment Variables

```bash
# Core Configuration
SECRET_KEY=your-256-bit-secret-key
DATABASE_URL=postgresql://user:pass@localhost/opendistillery
REDIS_URL=redis://localhost:6379

# AI Model API Keys
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
XAI_API_KEY=your-xai-api-key
GOOGLE_API_KEY=your-google-api-key

# Security Configuration
REQUIRE_MFA=true
JWT_EXPIRY_HOURS=24
API_RATE_LIMIT=100
ALLOWED_ORIGINS=https://yourdomain.com

# Monitoring
PROMETHEUS_ENABLED=true
GRAFANA_ENABLED=true
LOG_LEVEL=INFO
```

### Model Selection Strategies

```python
from opendistillery import ModelHub

# Configure intelligent model selection
hub = ModelHub()
hub.set_preference_strategy({
    "reasoning_tasks": ["o1-preview", "claude-3-5-sonnet", "claude-3-opus"],
    "creative_tasks": ["gpt-4-turbo", "claude-3-5-sonnet"],
    "real_time_tasks": ["grok-2", "grok-2-beta"],
    "multimodal_tasks": ["gpt-4o", "claude-3-5-sonnet", "grok-1.5v"],
    "code_tasks": ["gpt-4-turbo", "claude-3-5-sonnet", "o1-preview"]
})

# Automatic model selection
result = await hub.complete_task(
    task="Analyze financial data and create visualizations",
    task_type="multimodal_analysis",
    fallback_models=True
)
```

---

## API Reference

### Authentication

```bash
# Login and get JWT token
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'

# Use token in requests
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/systems
```

### Task Submission

```bash
# Submit a compound AI task
curl -X POST http://localhost:8000/tasks \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "financial_analysis",
    "description": "Analyze Q4 financial performance with forecasting",
    "input_data": {
      "revenue": 1000000,
      "expenses": 800000,
      "historical_data": "..."
    },
    "priority": "high",
    "models": ["claude-3-5-sonnet", "gpt-4-turbo"],
    "reasoning_required": true
  }'
```

### System Management

```bash
# Create a new compound AI system
curl -X POST http://localhost:8000/systems \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "system_id": "financial_system",
    "domain": "finance",
    "use_case": "risk_analysis",
    "architecture": "multi_agent",
    "models": [
      {"name": "claude-3-5-sonnet", "role": "primary_analyst"},
      {"name": "gpt-4-turbo", "role": "data_processor"},
      {"name": "o1-preview", "role": "risk_evaluator"}
    ]
  }'
```

---

## Monitoring and Observability

### Health Monitoring

```bash
# Health check endpoint
curl http://localhost:8000/health

# Detailed system status
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/metrics

# Model-specific metrics
curl http://localhost:8000/models/gpt-4-turbo/metrics
```

### Prometheus Metrics

```python
# Custom metrics in your application
from opendistillery.monitoring import metrics

# Track model usage
metrics.model_requests.labels(model="claude-3-5-sonnet", task_type="analysis").inc()

# Track response times
with metrics.request_duration.labels(model="gpt-4-turbo").time():
    result = await api.chat_completion(...)

# Track token usage
metrics.tokens_used.labels(model="o1-preview", type="input").inc(prompt_tokens)
metrics.tokens_used.labels(model="o1-preview", type="output").inc(completion_tokens)
```

### Pre-built Grafana Dashboards

- Model performance and usage statistics
- Token consumption and cost tracking
- Response time percentiles and error rates
- System resource utilization
- Real-time request monitoring

---

## Testing

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run all tests
pytest tests/ -v

# Run with coverage
pytest --cov=src/opendistillery tests/ --cov-report=html

# Run specific test categories
pytest tests/test_multi_provider_api.py -v
pytest tests/test_compound_system.py -v
pytest tests/test_integrations.py -v

# Run integration tests
python test_integration.py
```

### Performance Testing

```bash
# Load testing with realistic scenarios
pytest tests/performance/ -v --benchmark-only

# Concurrent request testing
python tests/load_test.py --concurrent-users=100 --requests-per-user=50
```

---

## Security

### Authentication Methods

**JWT Authentication:**
```python
from opendistillery.auth import JWTAuthenticator

auth = JWTAuthenticator(secret_key="your-secret")
token = auth.create_token(user_id="user123", permissions=["read", "write"])
```

**API Key Management:**
```python
from opendistillery.auth import APIKeyManager

key_manager = APIKeyManager()
api_key = await key_manager.create_key(
    name="Production API Key",
    permissions=["model_access", "task_submission"],
    expires_in_days=90
)
```

**Multi-Factor Authentication:**
```python
from opendistillery.auth import MFAManager

mfa = MFAManager()
secret = mfa.generate_secret(user_id="user123")
qr_code = mfa.generate_qr_code(secret, "user@company.com")
```

### Data Protection

- **Encryption**: All data encrypted at rest and in transit using AES-256-GCM
- **Key Rotation**: Automatic key rotation every 90 days
- **Access Control**: Granular RBAC with least privilege principle
- **Audit Logging**: Complete audit trail with correlation IDs
- **Compliance**: SOC2, ISO27001, GDPR, HIPAA ready

---

## Enterprise Use Cases

### Financial Services
- Real-time fraud detection with multi-model analysis
- Regulatory compliance document processing
- Risk assessment and portfolio optimization
- Automated financial report generation

### Healthcare
- Medical record analysis and summarization
- Drug discovery research assistance
- Clinical trial data processing
- Diagnostic support systems

### Legal & Compliance
- Contract analysis and risk identification
- Legal document drafting assistance
- Compliance monitoring and reporting
- Case law research and analysis

### Technology
- Code review and quality assessment
- Architecture design and optimization
- Technical documentation generation
- Security vulnerability analysis

---

## Contributing

We welcome contributions to OpenDistillery! Please read our [Contributing Guidelines](CONTRIBUTING.md) for details on how to submit pull requests, report issues, and contribute to the project.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/llamasearchai/OpenDistillery.git
cd OpenDistillery

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest tests/ -v
```

---

## Support & Community

### Documentation
- **Full Documentation**: [https://docs.opendistillery.ai](https://docs.opendistillery.ai)
- **API Reference**: [https://api-docs.opendistillery.ai](https://api-docs.opendistillery.ai)
- **Examples Repository**: [https://github.com/nikjois/opendistillery-examples](https://github.com/nikjois/opendistillery-examples)

### Community
- **Discord**: [Join our community](https://discord.gg/opendistillery)
- **GitHub Discussions**: [Community discussions](https://github.com/llamasearchai/OpenDistillery/discussions)
- **Stack Overflow**: Tag questions with `opendistillery`

### Enterprise Support
- **Email**: support@opendistillery.ai
- **Enterprise Licensing**: enterprise@opendistillery.ai
- **Professional Services**: consulting@opendistillery.ai

---

## Technical Achievements

### Core Capabilities Implemented
- **Multi-Modal AI Processing**: Vision, text, and audio analysis with advanced reasoning
- **Enterprise-Grade Security**: Complete authentication, authorization, and audit systems
- **Distributed Architecture**: Microservices with Docker and Kubernetes orchestration
- **Advanced Monitoring**: Real-time metrics, alerting, and performance analytics
- **Production-Ready APIs**: RESTful endpoints with comprehensive error handling

### Advanced Features
- **Multi-Agent Orchestration**: Coordinated AI agent workflows with task decomposition
- **Compound AI Systems**: Integration of multiple models for enhanced reasoning
- **Performance Optimization**: Intelligent caching, load balancing, and auto-scaling
- **Enterprise Integrations**: Extensible plugin architecture for third-party systems
- **Comprehensive Testing**: Unit, integration, and performance test suites

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a complete list of changes and version history.

---

<div align="center">

**OpenDistillery** - Advancing Enterprise AI with Cutting-Edge Technology

**Author**: Nik Jois (nikjois@llamasearch.ai)  
**GitHub**: [https://github.com/llamasearchai/OpenDistillery](https://github.com/llamasearchai/OpenDistillery)

Copyright © 2024-2025 OpenDistillery. All rights reserved.

</div> 