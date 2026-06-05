#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "Building frontend..."
cd frontend
npm ci
npm run build
cd ..

echo "Installing backend dependencies..."
pip install -r requirements.txt

echo "Build complete."
