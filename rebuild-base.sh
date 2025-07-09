#!/bin/bash
IMAGE_NAME_BASE="atriva-vpipe-ffmpeg-base"
CONTAINER_NAME_BASE="atriva-vpipe-base"
# Re-used previous image
CONTAINER_NAME_PROD="atriva-vpipe"
IMAGE_NAME_PROD="atriva-vpipe-ffmpeg"

echo "🛑 Stopping and removing old container..."
docker stop $CONTAINER_NAME_PROD 2>/dev/null && docker rm $CONTAINER_NAME_PROD 2>/dev/null
docker stop $CONTAINER_NAME_BASE 2>/dev/null && docker rm $CONTAINER_NAME_BASE 2>/dev/null

# echo "🗑️  Removing old image..."
docker rmi $IMAGE_NAME_BASE 2>/dev/null

# echo "🚀 Rebuilding the Docker image..."
docker build -t $IMAGE_NAME_BASE -f Dockerfile.base .

echo "🎯 Running the new base container for development..."
docker run --rm -it -p 8000:8000 -p 5678:5678 -v $(pwd):/app -w /app -v $(pwd)/frames:/app/frames -v $(pwd)/videos:/app/videos -e LIBVA_DRIVER_NAME=iHD --device /dev/dri:/dev/dri --name $CONTAINER_NAME_BASE $IMAGE_NAME_BASE

echo "✅ Done!"
