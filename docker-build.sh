#!/bin/bash
# Docker Build Script for Supply Chain Forecasting Agent
# This script builds the Docker image(s) for the application

set -e  # Exit on error

echo "🐳 Building Supply Chain Forecasting Agent Docker Image..."
echo ""

# Build the image
docker-compose build

echo ""
echo "✅ Build completed successfully!"
echo ""
echo "📋 Next steps:"
echo "   1. Create a .env file with your GOOGLE_API_KEY"
echo "   2. Run: docker-compose up -d"
echo "   3. Access frontend at: http://localhost:8501"
echo "   4. Access backend API at: http://localhost:8000/docs"

