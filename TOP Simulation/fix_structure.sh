#!/bin/bash

# Create __init__.py files
touch core/__init__.py
touch test/__init__.py

# Move theta to correct location
cp theta_minimal.yaml test/

echo "✓ Structure fixed"