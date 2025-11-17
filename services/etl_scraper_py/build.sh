#!/bin/bash
# Build script for Google Cloud Functions
# This script runs during the build phase to install Playwright browsers

set -e

echo "Installing Playwright browsers for Cloud Functions..."

# Install Playwright browsers
python3 -m playwright install chromium

echo "Playwright browsers installed successfully"
