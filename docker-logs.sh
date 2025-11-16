#!/bin/bash
# Docker Logs Script for Supply Chain Forecasting Agent
# This script shows logs from Docker containers

SERVICE=${1:-""}  # Optional service name (backend or frontend)

if [ -z "$SERVICE" ]; then
    echo "📋 Showing logs for all services..."
    docker-compose logs -f
else
    echo "📋 Showing logs for $SERVICE service..."
    docker-compose logs -f "$SERVICE"
fi

