<div align="center">
  <img src="OpenDistillery.png" alt="OpenDistillery Logo" width="400"/>
  
  # OpenDistillery
  
  ## Advanced Compound AI Systems for Enterprise Workflow Transformation
</div>

<div align="center">

[![PyPI version](https://badge.fury.io/py/opendistillery.svg)](https://badge.fury.io/py/opendistillery)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Documentation Status](https://readthedocs.org/projects/opendistillery/badge/?version=latest)](https://opendistillery.readthedocs.io/en/latest/?badge=latest)

</div>

OpenDistillery is a production-ready, enterprise-grade compound AI system designed for Fortune 500 companies and large-scale deployments. It provides seamless integration with the latest AI models from multiple providers, advanced multi-agent orchestration, and sophisticated reasoning capabilities.

## Key Features

### Latest AI Model Support (2025)

**OpenAI Models:**
- **GPT-4.1** (April 2025) - 1M token context, advanced reasoning
- **GPT-o3/o3-mini** (January 2025) - Enhanced reasoning with deliberative alignment
- **GPT-4o** - Multimodal omni model with real-time capabilities
- **o-series** - Specialized reasoning models (o1, o3, o4-mini)

**Anthropic Claude Models:**
- **Claude 4 Opus** (May 2025) - Most capable model with superior reasoning
- **Claude 4 Sonnet** (May 2025) - High-performance enterprise model
- **Claude 3.7 Sonnet** (February 2025) - Extended thinking and hybrid reasoning
- **Claude 3.5** series - Sonnet v2, Haiku with enhanced capabilities

**xAI Grok Models:**
- **Grok 3** (February 2025) - Real-time information with Think and Big Brain modes
- **Grok 2 Beta** - Unfiltered responses with X platform integration
- **Grok 1.5V** - Vision-enabled model

### Enterprise Capabilities

**Multi-Agent Orchestration:**
- Advanced coordination between specialized AI agents
- Compound reasoning with multiple models
- Intelligent task routing and load balancing
- Real-time collaboration and decision-making

**Production-Grade Infrastructure:**
- Horizontal auto-scaling with Docker and Kubernetes
- Enterprise authentication (JWT, MFA, RBAC)
- Comprehensive monitoring with Prometheus and Grafana
- Circuit breakers and fault tolerance
- Structured logging with correlation tracking

**Security & Compliance:**
- SOC2, ISO27001, GDPR, HIPAA compliance ready
- Multi-factor authentication with TOTP
- Role-based access control with granular permissions
- API key management with expiration and rate limiting
- Audit logging with encryption at rest and in transit

## Quick Start

### Installation

```bash
pip install opendistillery
```

### Basic Usage

```python
import asyncio
from opendistillery import get_completion, get_reasoning_completion

# Simple completion with latest models
async def main():
    # Use GPT-4.1 with 1M token context
    response = await get_completion(
        "Analyze the quarterly financial performance trends",
        model="gpt-4.1",
        temperature=0.1
    )
    print(response)
    
    # Advanced reasoning with o3
    reasoning_response = await get_reasoning_completion(
        "Solve this complex mathematical proof step by step",
        model="o3"
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
        
        # Use Claude 4 Opus for complex reasoning
        claude_response = await api.chat_completion(
            messages=[{"role": "user", "content": "Analyze this business strategy"}],
            model=AnthropicModel.CLAUDE_4_OPUS.value,
            extended_thinking=True
        )
        
        # Use Grok 3 for real-time information
        grok_response = await api.chat_completion(
            messages=[{"role": "user", "content": "What's trending on X today?"}],
            model=XAIModel.GROK_3.value,
            mode="think",
            real_time_info=True
        )
        
        # Use GPT-4.1 for large document analysis
        gpt_response = await api.chat_completion(
            messages=[{"role": "user", "content": "Summarize this 1000-page report"}],
            model=OpenAIModel.GPT_4_1.value,
            max_tokens=32000
        )

asyncio.run(multi_provider_example())
```

### Multimodal Capabilities

```python
from opendistillery import get_multimodal_completion

async def vision_example():
    # Analyze images with GPT-4o or Claude 4
    result = await get_multimodal_completion(
        prompt="Analyze the financial charts in these images and provide insights",
        images=["data:image/jpeg;base64,/9j/4AAQ...", "https://example.com/chart.png"],
        model="gpt-4o"
    )
    print(result)

asyncio.run(vision_example())
```

## Architecture Overview

OpenDistillery implements a sophisticated compound AI architecture designed for enterprise scale:

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

### Core Components

**Multi-Provider API Engine:**
- Unified interface for OpenAI, Anthropic, xAI, and Google models
- Intelligent routing and failover capabilities
- Rate limiting and cost optimization
- Automatic model selection based on task requirements

**Compound AI System:**
- Multi-agent coordination and orchestration
- Advanced reasoning chain implementations
- Task decomposition and parallel processing
- Result synthesis and validation

**Enterprise Features:**
- Production-ready FastAPI server
- PostgreSQL database with 9 enterprise tables
- Redis caching and session management
- Celery background task processing
- Comprehensive monitoring and alerting

## Advanced Features

### Latest Model Capabilities

**Reasoning Models (2025):**
```python
# OpenAI o3 with advanced reasoning
result = await get_reasoning_completion(
    "Prove that P vs NP is undecidable",
    model="o3",
    reasoning_effort="high"
)

# Claude 3.7 with extended thinking
result = await api.chat_completion(
    messages=[{"role": "user", "content": "Design a quantum algorithm"}],
    model="claude-3-7-sonnet-20250219",
    extended_thinking=True
)
```

**Real-Time Information:**
```python
# Grok 3 with real-time X data
result = await api.chat_completion(
    messages=[{"role": "user", "content": "What's the latest news on AI?"}],
    model="grok-3",
    mode="big_brain",
    real_time_info=True
)
```

**Large Context Processing:**
```python
# GPT-4.1 with 1M token context
result = await api.chat_completion(
    messages=[{"role": "user", "content": "Analyze this entire codebase"}],
    model="gpt-4.1",
    max_tokens=32000
)
```

### Multi-Agent Orchestration

```python
from opendistillery import CompoundAISystem

# Create a sophisticated multi-agent workflow
system = CompoundAISystem()

# Define specialized agents
research_agent = system.create_agent(
    name="research_specialist",
    model="claude-4-opus",
    role="Research and analysis expert",
    tools=["web_search", "document_analysis"]
)

coding_agent = system.create_agent(
    name="code_specialist", 
    model="gpt-4.1",
    role="Software development expert",
    tools=["code_execution", "testing", "debugging"]
)

synthesis_agent = system.create_agent(
    name="synthesis_specialist",
    model="o3",
    role="Strategic thinking and synthesis",
    tools=["reasoning", "decision_making"]
)

# Execute complex workflow
result = await system.execute_workflow(
    task="Build a complete trading algorithm with research, implementation, and testing",
    agents=[research_agent, coding_agent, synthesis_agent],
    coordination_strategy="hierarchical"
)
```

## Production Deployment

### Docker Deployment

```bash
# Quick start with Docker Compose
git clone https://github.com/nikjois/OpenDistillery.git
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

# Monitor deployment
kubectl get pods -n opendistillery
kubectl logs -f deployment/opendistillery-api -n opendistillery
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

# Define model preferences
hub.set_preference_strategy({
    "reasoning_tasks": ["o3", "claude-4-opus", "claude-3-7-sonnet"],
    "creative_tasks": ["gpt-4.1", "claude-4-sonnet"],
    "real_time_tasks": ["grok-3", "grok-2-beta"],
    "multimodal_tasks": ["gpt-4o", "claude-4-opus", "grok-3"],
    "code_tasks": ["gpt-4.1", "claude-4-sonnet", "o3"]
})

# Automatic model selection
result = await hub.complete_task(
    task="Analyze this financial data and create visualizations",
    task_type="multimodal_analysis",
    fallback_models=True
)
```

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
    "models": ["claude-4-opus", "gpt-4.1"],
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
      {"name": "claude-4-opus", "role": "primary_analyst"},
      {"name": "gpt-4.1", "role": "data_processor"},
      {"name": "o3", "role": "risk_evaluator"}
    ]
  }'
```

## Monitoring and Observability

### Health Monitoring

```bash
# Health check endpoint
curl http://localhost:8000/health

# Detailed system status
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/metrics

# Model-specific metrics
curl http://localhost:8000/models/gpt-4.1/metrics
```

### Prometheus Metrics

```python
# Custom metrics in your application
from opendistillery.monitoring import metrics

# Track model usage
metrics.model_requests.labels(model="claude-4-opus", task_type="analysis").inc()

# Track response times
with metrics.request_duration.labels(model="gpt-4.1").time():
    result = await api.chat_completion(...)

# Track token usage
metrics.tokens_used.labels(model="o3", type="input").inc(prompt_tokens)
metrics.tokens_used.labels(model="o3", type="output").inc(completion_tokens)
```

### Grafana Dashboards

Pre-built dashboards include:
- Model performance and usage statistics
- Token consumption and cost tracking
- Response time percentiles
- Error rates and failure analysis
- System resource utilization
- Real-time request monitoring

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

## Use Cases

### Enterprise Applications

**Financial Services:**
- Real-time fraud detection with multi-model analysis
- Regulatory compliance document processing
- Risk assessment and portfolio optimization
- Automated financial report generation

**Healthcare:**
- Medical record analysis and summarization
- Drug discovery research assistance
- Clinical trial data processing
- Diagnostic support systems

**Legal & Compliance:**
- Contract analysis and risk identification
- Legal document drafting assistance
- Compliance monitoring and reporting
- Case law research and analysis

**Technology:**
- Code review and quality assessment
- Architecture design and optimization
- Technical documentation generation
- Security vulnerability analysis

### Code Examples

**Financial Analysis System:**
```python
from opendistillery import CompoundAISystem

# Create specialized financial AI system
financial_system = CompoundAISystem()
financial_system.configure({
    "domain": "finance",
    "models": {
        "primary": "claude-4-opus",
        "numerical": "gpt-4.1", 
        "reasoning": "o3"
    },
    "tools": ["financial_data_api", "calculation_engine", "charting"]
})

# Analyze quarterly performance
result = await financial_system.analyze_quarterly_performance(
    company="AAPL",
    quarter="Q4-2024",
    include_forecasting=True,
    comparison_companies=["MSFT", "GOOGL"]
)
```

**Research Assistant:**
```python
# Multi-modal research system
research_system = CompoundAISystem()
research_system.add_agent("researcher", model="claude-4-opus", tools=["web_search"])
research_system.add_agent("analyst", model="grok-3", tools=["real_time_data"])
research_system.add_agent("synthesizer", model="o3", tools=["reasoning"])

# Comprehensive research workflow
research_result = await research_system.research_topic(
    topic="Quantum Computing Market Trends 2025",
    depth="comprehensive",
    sources=["academic", "industry", "news"],
    output_format="executive_summary"
)
```

## Contributing

We welcome contributions to OpenDistillery! Please read our [Contributing Guidelines](CONTRIBUTING.md) for details on how to submit pull requests, report issues, and contribute to the project.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/nikjois/OpenDistillery.git
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

## Support & Community

### Documentation
- **Full Documentation**: [https://docs.opendistillery.ai](https://docs.opendistillery.ai)
- **API Reference**: [https://api-docs.opendistillery.ai](https://api-docs.opendistillery.ai)
- **Examples Repository**: [https://github.com/nikjois/opendistillery-examples](https://github.com/nikjois/opendistillery-examples)

### Community
- **Discord**: [Join our community](https://discord.gg/opendistillery)
- **GitHub Discussions**: [Community discussions](https://github.com/nikjois/OpenDistillery/discussions)
- **Stack Overflow**: Tag questions with `opendistillery`

### Enterprise Support
- **Email**: support@opendistillery.ai
- **Enterprise Licensing**: enterprise@opendistillery.ai
- **Professional Services**: consulting@opendistillery.ai

## Roadmap

### 2025 Q2 Planned Features
- **Multi-Modal Agents**: Enhanced vision and audio processing
- **Advanced Reasoning**: Integration with emerging reasoning models
- **Enterprise Integrations**: Salesforce, SAP, Microsoft 365 connectors
- **Performance Optimization**: Model caching and intelligent routing
- **Security Enhancements**: Advanced threat detection and response

### 2025 Q3-Q4
- **Custom Model Training**: Fine-tuning capabilities
- **Edge Deployment**: Lightweight edge computing support
- **Advanced Analytics**: Comprehensive usage and performance analytics
- **Workflow Automation**: Visual workflow designer
- **Global Deployment**: Multi-region support with data residency

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a complete list of changes and version history.

---

**OpenDistillery** - Advancing Enterprise AI with Cutting-Edge Technology

**Author**: Nik Jois (nikjois@llamasearch.ai)  
**Website**: [https://opendistillery.ai](https://opendistillery.ai)  
**GitHub**: [https://github.com/nikjois/OpenDistillery](https://github.com/nikjois/OpenDistillery)

Copyright © 2024-2025 OpenDistillery. All rights reserved.