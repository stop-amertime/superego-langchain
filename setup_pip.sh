#!/bin/bash

# This script sets up 'pip' command to work when only 'pip3' is available

# Find pip3 location
PIP3_PATH=$(which pip3)

if [ -z "$PIP3_PATH" ]; then
  echo "Error: pip3 not found on your system."
  exit 1
fi

echo "Found pip3 at: $PIP3_PATH"

# Create a symlink for pip
echo "Creating symlink for pip..."
sudo ln -sf "$PIP3_PATH" "$(dirname "$PIP3_PATH")/pip"

# Test if it worked
if command -v pip &> /dev/null; then
  echo "Success! You can now use 'pip' command."
  echo "Pip version: $(pip --version)"
else
  echo "Failed to create the pip command. Try adding an alias to your shell config instead:"
  echo "Add 'alias pip=pip3' to your ~/.bashrc or ~/.zshrc file."
fi
