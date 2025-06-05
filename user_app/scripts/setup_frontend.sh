#!/bin/bash

# Navigate to the frontend directory
cd "$(dirname "$0")/../frontend"

# Install dependencies
npm install

# Build the application
npm run build 