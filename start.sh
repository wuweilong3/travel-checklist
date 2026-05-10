#!/bin/bash
set -e
echo "Starting travel checklist backend..."
cd backend
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "Starting server..."
uvicorn api.routes:app --host 0.0.0.0 --port ${PORT:-8000}