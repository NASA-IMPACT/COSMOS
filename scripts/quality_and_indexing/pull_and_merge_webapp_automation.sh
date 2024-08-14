#!/bin/bash

set -e

# Navigate to the correct repository
cd "../../sinequa_configs"

# Ensure the script only runs if pointing to the correct remote
REPO_URL="git@github.com:NASA-IMPACT/sde-backend.git"
CURRENT_URL=$(git config --get remote.origin.url)

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

### Begin merge of webapp into dev ###
# Check the diff between webapp_config_generation and dev branches, and filter only files outside the allowed directories
DIFF=$(git diff --name-only webapp_config_generation dev | grep -vE 'jobs/|sources/' || true)

if [ -n "$DIFF" ]; then
  echo "The following changes were found outside of the allowed directories:"
  echo "$DIFF"
  echo "Please resolve these changes on GitHub before proceeding."
  exit 1
else
  echo "All changes are within the allowed directories. Proceeding with the merge."
fi

# Checkout dev branch again
echo "Checking out dev branch..."
git checkout dev

# Merge webapp_config_generation into dev
echo "Merging webapp_config_generation into dev..."
git merge webapp_config_generation -m "Merge webapp_config_generation into dev branch"

# Push the changes to dev
echo "Pushing changes to dev..."
git push origin dev

# Return to the original directory
cd -

echo "webapp_automation and dev merges comleted successfully!"
