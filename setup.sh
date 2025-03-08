#!/bin/bash

# This script sets up and runs the Superego LangGraph project

# Text colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Superego LangGraph Setup ===${NC}"
echo

# Check if OpenRouter API key is provided
if [ "$1" == "" ]; then
  echo -e "${YELLOW}No OpenRouter API key provided. You'll need to set this manually in backend/.env${NC}"
  USE_KEY=false
else
  echo -e "${GREEN}Using provided OpenRouter API key${NC}"
  USE_KEY=true
fi

# Setup backend
echo -e "${GREEN}Setting up backend...${NC}"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
  echo -e "${RED}Python 3 is not installed. Please install Python 3.8+ and try again.${NC}"
  exit 1
fi

# Check for pip/pip3
PIP_CMD="pip"
if ! command -v pip &> /dev/null; then
  if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}Neither pip nor pip3 is installed. Please install pip and try again.${NC}"
    exit 1
  else
    echo -e "${YELLOW}Using pip3 instead of pip${NC}"
    PIP_CMD="pip3"
  fi
fi

# Check for virtualenv
if ! command -v virtualenv &> /dev/null; then
  echo -e "${YELLOW}virtualenv not found. Installing virtualenv...${NC}"
  $PIP_CMD install virtualenv
fi

# Create and activate virtual environment
echo "Creating Python virtual environment..."
virtualenv venv
source venv/bin/activate

# Install backend dependencies
echo "Installing backend dependencies..."
$PIP_CMD install -r backend/requirements.txt

# Set up environment variables
if [ "$USE_KEY" = true ]; then
  echo "Setting OpenRouter API key in .env file..."
  echo "OPENROUTER_API_KEY=$1" > backend/.env
  echo "HOST=0.0.0.0" >> backend/.env
  echo "PORT=8000" >> backend/.env
  echo "BASE_MODEL=anthropic/claude-3.7-sonnet" >> backend/.env
  echo "SUPEREGO_MODEL=anthropic/claude-3.7-sonnet:thinking" >> backend/.env
  echo "FRONTEND_URL=http://localhost:3000" >> backend/.env
fi

# Setup frontend
echo -e "\n${GREEN}Setting up frontend...${NC}"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
  echo -e "${RED}Node.js is not installed. Please install Node.js 14+ and try again.${NC}"
  exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
  echo -e "${RED}npm is not installed. Please install npm and try again.${NC}"
  exit 1
fi

# Install frontend dependencies
echo "Installing frontend dependencies..."
cd frontend
npm install
cd ..

echo -e "\n${GREEN}Setup complete!${NC}"
echo
echo -e "${YELLOW}To run the application:${NC}"
echo "1. In one terminal: cd backend && python run.py"
echo "2. In another terminal: cd frontend && npm run dev"
echo
echo -e "${GREEN}Backend will run at: ${NC}http://localhost:8000"
echo -e "${GREEN}Frontend will run at: ${NC}http://localhost:3000"
echo
echo -e "${YELLOW}Note: ${NC}Make sure to set your OpenRouter API key in backend/.env before running!"
