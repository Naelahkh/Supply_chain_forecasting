#!/bin/bash
# Docker Stop Script for Supply Chain Forecasting Agent
# This script stops the Docker containers

echo "🛑 Stopping Supply Chain Forecasting Agent..."
echo ""

# Stop the services
docker-compose down

echo ""
echo "✅ Services stopped!"

