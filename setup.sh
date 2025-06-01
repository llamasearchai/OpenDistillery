#!/bin/bash

# OpenDistillery Setup Script

echo "Setting up OpenDistillery..."

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "Docker is required but not installed. Aborting." >&2; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "Docker Compose is required but not installed. Aborting." >&2; exit 1; }

# Create necessary directories
mkdir -p logs data config notebooks monitoring/grafana/provisioning

# Copy environment template if not exists
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cat > .env << EOF
# OpenDistillery Environment Variables
ENVIRONMENT=development
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://opendistillery:secure_password@localhost:5432/opendistillery
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
EOF
    echo "Please edit .env file with your configuration"
fi

# Set permissions
chmod +x setup.sh
chmod 600 .env

echo "Setup complete! Run 'docker-compose up -d' to start OpenDistillery" 