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

# Checkout and pull production
echo "Checking out production branch..."
git checkout production
echo "Pulling latest changes from production..."
git pull origin production

# Checkout and pull staging
echo "Checking out staging branch..."
git checkout staging
echo "Pulling latest changes from staging..."
git pull origin staging

# Checkout and pull webapp_config_generation
echo "Checking out webapp_config_generation branch..."
git checkout webapp_config_generation
echo "Pulling latest changes from webapp_config_generation..."
git pull origin webapp_config_generation

# Merge staging into webapp_config_generation
echo "Merging staging into webapp_config_generation..."
git merge -X theirs staging -m "Merge staging into webapp_config_generation branch - auto-resolved conflicts by taking staging changes"

# Push the changes to webapp_config_generation
echo "Pushing changes to webapp_config_generation..."
git push origin webapp_config_generation

echo "Operation completed successfully!"

### Begin merge of webapp into staging ###
# Check the diff between webapp_config_generation and staging branches, and filter only files outside the allowed directories
DIFF=$(git diff --name-only webapp_config_generation staging | grep -vE 'jobs/|sources/' || true)

if [ -n "$DIFF" ]; then
  echo "The following changes were found outside of the allowed directories:"
  echo "$DIFF"
  echo "Please resolve these changes on GitHub before proceeding."
  exit 1
else
  echo "All changes are within the allowed directories. Proceeding with the merge."
fi

# Checkout staging branch again
echo "Checking out staging branch..."
git checkout staging

# Merge webapp_config_generation into staging
echo "Merging webapp_config_generation into staging..."
git merge webapp_config_generation -m "Merge webapp_config_generation into staging branch"

# Push the changes to staging
echo "Pushing changes to staging..."
git push origin staging

git checkout production

# Return to the original directory
cd -

echo "webapp_automation and staging merges comleted successfully!"
