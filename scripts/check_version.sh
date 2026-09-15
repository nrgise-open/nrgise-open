#!/bin/bash
#
# This Script checks if the version of nrgise has been updated before a merge into master can be done.
#

PYPROJECT_FILE="pyproject.toml"

# Function to extract the version from pyproject.toml
get_version() {
    local file="$1"
    grep -E '^\s*version\s*=' "$file" | head -n1 | sed -E 's/version\s*=\s*"(.*)"/\1/'
}

new_version=$(get_version "$PYPROJECT_FILE")

# Get the version from the master branch
MASTER_VERSION=$(git show origin/main:"$PYPROJECT_FILE" | grep -E '^\s*version\s*=' | head -n1 | sed -E 's/version\s*=\s*"(.*)"/\1/')


echo "Version on master is: $MASTER_VERSION"
echo "Version of this branch is: $new_version"
# Clean up the temporary directory
rm -rf "$temp_dir"

version_le() {
  [ "$(printf '%s\n' "$1" "$2" | sort -V | head -n1)" = "$1" ]
}


if version_le "$new_version" "$MASTER_VERSION"; then    
   
    echo "Error: Version has not been incremented. Please increment the version in the setup.py file according to the
    pattern MAJOR.MINOR.PATCH"
    exit 1
fi