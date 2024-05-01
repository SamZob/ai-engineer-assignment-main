#!/bin/bash

# Define your image name
IMAGE_NAME="code_snippet_generator"

# Check if the .env file exists
if [ ! -f .env ]; then
    echo "Please create a .env file, see .env.example for reference"
    exit 1
fi

# Build the Docker image
docker build -t $IMAGE_NAME .

# Run the Docker container
docker run --rm -p 8000:8000 --env-file .env $IMAGE_NAME
