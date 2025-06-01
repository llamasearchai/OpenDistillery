# OpenDistillery

A simple compound AI system for companies and any scale production deployments.

## Overview

OpenDistillery is an advanced AI orchestration platform that enables enterprises to build, deploy, and manage sophisticated compound AI systems. It provides a comprehensive framework for multi-agent workflows, advanced reasoning capabilities, and production-ready infrastructure.

## Features

- **Advanced Reasoning Engines**: ReAct, Tree of Thoughts, and Graph of Thoughts implementations
- **Multi-Agent System**: Specialized agents for reasoning, data processing, ML, and orchestration
- **Enterprise Security**: JWT authentication, RBAC, API key management, and audit logging
- **Production Monitoring**: Prometheus metrics, distributed tracing, health checks, and alerting
- **Scalable Architecture**: Horizontal scaling, load balancing, and fault tolerance
- **Enterprise Integrations**: Support for major enterprise systems and custom APIs

## Quick Start

### Prerequisites

- Docker 24.0+ and Docker Compose 2.0+
- Python 3.8+
- 16GB+ RAM, 8+ CPU cores
- PostgreSQL 15+ (or use Docker)
- Redis 7+ (or use Docker)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/llamasearchai/OpenDistillery.git
cd OpenDistillery
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Start with Docker Compose:
```bash
docker-compose up -d
```

4. Verify deployment:
```bash
curl http://localhost:8000/health
```

## Documentation

- [Production Deployment Guide](README_PRODUCTION.md)
- [API Documentation](http://localhost:8000/docs)
- [Architecture Overview](docs/architecture.md)

## Development

### Local Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Start development server
uvicorn src.api.server:app --reload
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_api.py
```

## Architecture

OpenDistillery uses a microservices architecture with the following components:

- **API Server**: FastAPI-based REST API
- **Agent System**: Multi-agent orchestration framework
- **Reasoning Engines**: Advanced AI reasoning implementations
- **Database**: PostgreSQL for persistent storage
- **Cache**: Redis for high-performance caching
- **Monitoring**: Prometheus + Grafana stack

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Support & Contact

For enterprise support, partnership inquiries, or security issues, please contact:

**Nik Jois**  
Email: [nikjois@llamasearch.ai](mailto:nikjois@llamasearch.ai)

## Contributing

Please read our contributing guidelines before submitting pull requests.