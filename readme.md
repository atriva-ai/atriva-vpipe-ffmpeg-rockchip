# Atriva Video Pipeline API Service with FFmpeg

## Overview
This project is a **API-based video pipeline service** that utilizes **FFmpeg** for decoding, hardware-accelerated transcoding, and extracting frames from videos. The API supports processing videos from a file upload or a direct URL input.

## Features
- 🚀 **Video Upload & Processing**
- 🎥 **Supports File & URL-based Input**
- ⚡ **Hardware Acceleration** (CUDA, QSV, VAAPI)
- 📸 **Extract Frames as JPEGs**
- 📊 **Retrieve Video Metadata**
- 🐳 **Dockerized Environment**

## Getting Started

### Prerequisites
Ensure you have the following installed on your system:
- [Docker](https://docs.docker.com/get-docker/)
- NVIDIA/Intel drivers (if using hardware acceleration)

### Build & Run with Docker

#### 1️⃣ **Build the Docker Image**
```sh
docker build -t atriva-video-pipe .
```

#### 2️⃣ **Run the Container**
```sh
docker run --rm -p 8000:8000 \
  --device /dev/dri:/dev/dri \  # Pass GPU device for VAAPI acceleration
  -v $(pwd)/videos:/app/videos \  # Mount video storage
  -v $(pwd)/frames:/app/frames \  # Mount frame output
  fastapi-video-processor
```

### API Endpoints

#### 🚀 **Upload & Process Video**
```http
POST /decode_video/
```
**Parameters:**
- `file`: Video file upload (optional)
- `url`: Video URL (optional)
- `fps`: Frames per second to extract (default: 1)
- `format`: Output format (optional)

#### 📊 **Get Video Metadata**
```http
POST /video_info/
```
**Parameters:**
- `file`: Video file upload
- `url`: Video URL (optional)

### Hardware Acceleration Support
The application prioritizes the following hardware accelerations:
1. **CUDA** (NVIDIA)
2. **QSV** (Intel Quick Sync Video)
3. **VAAPI** (Linux GPU Acceleration)

To use VAAPI, run:
```sh
docker run --device /dev/dri:/dev/dri atriva-video-pipe
```
For CUDA (NVIDIA), use:
```sh
docker run --runtime=nvidia atriva-video-pipe
```

### Troubleshooting
#### **Permission Issues with Output Directories**
If the container cannot write to `/app/frames`, ensure proper permissions:
```sh
mkdir -p frames videos
chmod -R 777 frames videos
```

#### **Checking Available Hardware Acceleration**
To list supported hardware acceleration methods inside the container:
```sh
ffmpeg -hwaccels
```

#### **Debugging VAAPI Issues**
Check if VAAPI devices are accessible inside the container:
```sh
docker run --rm --device /dev/dri:/dev/dri fastapi-video-processor vainfo
```

## License
MIT License

## Contributing
Pull requests are welcome! Feel free to submit issues for feature requests or bug fixes.


