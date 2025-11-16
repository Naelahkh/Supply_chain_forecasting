#!/bin/bash
# Docker Test Script for Supply Chain Forecasting Agent
# This script tests if the Docker setup is working correctly

set -e

echo "🧪 Testing Docker Setup..."
echo ""

# Check Docker installation
echo "1️⃣ Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed!"
    exit 1
fi
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed!"
    exit 1
fi
echo "✅ Docker and Docker Compose are installed"

# Check if .env file exists
echo ""
echo "2️⃣ Checking environment file..."
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "   Create one with: echo 'GOOGLE_API_KEY=your_key' > .env"
else
    echo "✅ .env file found"
fi

# Check if models directory exists
echo ""
echo "3️⃣ Checking models directory..."
if [ ! -d "models" ]; then
    echo "⚠️  Warning: models directory not found!"
else
    model_count=$(find models -type f \( -name "*.pkl" -o -name "*.joblib" -o -name "*.h5" \) 2>/dev/null | wc -l)
    echo "✅ models directory found ($model_count model files)"
fi

# Check if knowledge_base directory exists
echo ""
echo "4️⃣ Checking knowledge_base directory..."
if [ ! -d "knowledge_base" ]; then
    echo "⚠️  Warning: knowledge_base directory not found!"
else
    echo "✅ knowledge_base directory found"
fi

# Test Docker build (dry-run)
echo ""
echo "5️⃣ Testing Docker build..."
if docker-compose config > /dev/null 2>&1; then
    echo "✅ docker-compose.yml is valid"
else
    echo "❌ docker-compose.yml has errors!"
    docker-compose config
    exit 1
fi

# Check if containers are running
echo ""
echo "6️⃣ Checking running containers..."
if docker-compose ps | grep -q "Up"; then
    echo "✅ Containers are running"
    
    # Test health check
    echo ""
    echo "7️⃣ Testing health check..."
    sleep 2
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend health check passed"
    else
        echo "⚠️  Backend health check failed (might still be starting)"
    fi
else
    echo "ℹ️  Containers are not running"
    echo "   Start them with: docker-compose up -d"
fi

echo ""
echo "✅ Docker setup test completed!"
echo ""
echo "📋 Next steps:"
echo "   If containers are not running:"
echo "   - Build: docker-compose build"
echo "   - Start: docker-compose up -d"
echo "   - Logs:  docker-compose logs -f"

