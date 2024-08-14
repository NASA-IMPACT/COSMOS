#!/bin/bash

set -e

# Navigate to the correct repository
cd "../../sinequa_configs"

# Ensure the script only runs if pointing to the correct remote
REPO_URL="git@github.com:NASA-IMPACT/sde-backend.git"
CURRENT_URL=$(git -C "$REPO_DIR" config --get remote.origin.url)

if [ "$CURRENT_URL" != "$REPO_URL" ]; then
  echo "Error: This script can only be run in the repository with the remote URL '$REPO_URL'."
  echo "Current remote URL is '$CURRENT_URL'. Exiting."
  exit 1
fi

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
git merge -X theirs dev -m "Merge dev into webapp_config_generation branch - auto-resolved conflicts by taking dev changes"

# Push the changes to webapp_config_generation
echo "Pushing changes to webapp_config_generation..."
git push origin webapp_config_generation

echo "Operation completed successfully!"

# Return to the original directory
cd -
