#!/bin/bash

# Ensure script fails on any error
set -e

echo "Installing dependencies from requirements.txt..."
# Install requirements.txt
# We confirm that requirements.txt has botocore==1.34.0 and urllib3==1.26.20 which are compatible.
# Providing a clean install command helps avoid user-supplied extra arguments causing conflicts.
pip install -r requirements.txt

echo "Installation complete."
