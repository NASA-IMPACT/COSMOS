#!/bin/bash

set -e

# Checkout and pull master
echo "Checking out master branch..."
git checkout master
echo "Pulling latest changes from master..."
git pull origin master

# Checkout and pull dev
echo "Checking out dev branch..."
git checkout dev
echo "Pulling latest changes from dev..."
git pull origin dev

# Checkout and pull webapp_config_generation
echo "Checking out webapp_config_generation branch..."
git checkout webapp_config_generation
echo "Pulling latest changes from webapp_config_generation..."
git pull origin webapp_config_generation

# Merge dev into webapp_config_generation
echo "Merging dev into webapp_config_generation..."
git merge -X theirs dev

# Push the changes to webapp_config_generation
echo "Pushing changes to webapp_config_generation..."
git push origin webapp_config_generation

echo "Operation completed successfully!"
