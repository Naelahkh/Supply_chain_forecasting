#!/bin/bash
# Docker Start Script for Supply Chain Forecasting Agent
# This script starts the Docker containers

set -e  # Exit on error

echo "🚀 Starting Supply Chain Forecasting Agent..."
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "   Please create a .env file with your GOOGLE_API_KEY"
    echo "   Example: echo 'GOOGLE_API_KEY=your_key_here' > .env"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Start the services
docker-compose up -d

echo ""
echo "⏳ Waiting for services to start..."
sleep 5

# Check health
echo ""
echo "📊 Checking service health..."
docker-compose ps

echo ""
echo "✅ Services started!"
echo ""
echo "📋 Access points:"
echo "   Frontend (Streamlit): http://localhost:8501"
echo "   Backend API:         http://localhost:8000"
echo "   API Documentation:   http://localhost:8000/docs"
echo "   Health Check:        http://localhost:8000/health"
echo ""
echo "📝 Useful commands:"
echo "   View logs:      docker-compose logs -f"
echo "   Stop services:  docker-compose down"
echo "   Restart:        docker-compose restart"

