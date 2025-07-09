#!/bin/bash
CONTAINER_NAME="atriva-vpipe"
IMAGE_NAME="atriva-vpipe-ffmpeg"

echo "🛑 Stopping and removing old container..."
docker stop $CONTAINER_NAME 2>/dev/null && docker rm $CONTAINER_NAME 2>/dev/null

echo "🗑️  Removing old image..."
docker rmi $IMAGE_NAME 2>/dev/null

echo "🚀 Rebuilding the Docker image..."
docker build -t $IMAGE_NAME .

echo "🎯 Running the new container..."
# Intel VAAPI
docker run -d -p 8000:8000 -p 5678:5678 -v $(pwd)/frames:/app/frames -v $(pwd)/videos:/app/videos -e LIBVA_DRIVER_NAME=iHD --device /dev/dri:/dev/dri --name $CONTAINER_NAME $IMAGE_NAME
# AMD VAAPI
# docker run -d -p 8000:8000 -p 5678:5678 -v $(pwd)/frames:/app/frames -v $(pwd)/videos:/app/videos -e LIBVA_DRIVER_NAME=radeonsi --device /dev/dri:/dev/dri --name $CONTAINER_NAME $IMAGE_NAME
# NVIDIA VAAPI
# docker run -d -p 8000:8000 -p 5678:5678 -v $(pwd)/frames:/app/frames -v $(pwd)/videos:/app/videos -e LIBVA_DRIVER_NAME=nvidia --device /dev/dri:/dev/dri --name $CONTAINER_NAME $IMAGE_NAME

echo "✅ Done!"
