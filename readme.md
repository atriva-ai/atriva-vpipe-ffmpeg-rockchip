# Atriva Video Pipeline API Service with FFmpeg (Rockchip Edition)

## Overview
This project is an **API-based video pipeline service** that utilizes **FFmpeg** for decoding, hardware-accelerated transcoding, and extracting frames from videos. The API supports processing videos from a file upload or a direct URL input, optimized for **Rockchip RK3588** SoCs.

## Features
- 🚀 **Video Upload & Processing**
- 🎥 **Supports File & URL-based Input**
- ⚡ **Rockchip Hardware Acceleration** (RKMPP/V4L2/RGA)
- 📸 **Extract Frames as JPEGs**
- 📊 **Retrieve Video Metadata**
- 🐳 **Dockerized Environment**

## Hardware Acceleration: Rockchip RK3588 Support
This image is based on [`nyanmisaka/jellyfin:latest-rockchip`](https://hub.docker.com/r/nyanmisaka/jellyfin), which includes:
- FFmpeg with Rockchip MPP (Media Process Platform) and RGA (2D Raster Graphic Acceleration) support
- Optimized for RK3588/3588S SoCs and compatible Rockchip devices
- Zero-copy transcoding pipeline for efficient video processing

### Rockchip Hardware Acceleration Options
The service automatically detects and uses the best available hardware acceleration:

1. **RKMPP** (`rkmpp`): Rockchip Media Process Platform
   - Hardware video decoder/encoder
   - Best performance for video processing
   - Primary choice for RK3588

2. **V4L2** (`v4l2`): Video4Linux2
   - Hardware acceleration via V4L2 interface
   - Fallback option if RKMPP is not available

3. **RGA** (`rga`): Rockchip Graphics Acceleration
   - 2D graphics acceleration for image processing
   - Used for format conversion and scaling

4. **Software** (`none`): CPU-based processing
   - Fallback when hardware acceleration is not available

### Required Devices for Hardware Acceleration
To enable hardware acceleration, you must pass the following devices to Docker:
```
  --device /dev/mpp_service \
  --device /dev/dri \
  --device /dev/rga \
  --device /dev/mali0 \
```

## Getting Started

### Prerequisites
Ensure you have the following installed on your system:
- [Docker](https://docs.docker.com/get-docker/)
- A supported Rockchip SoC (e.g., RK3588/3588S)
- Kernel and drivers for Rockchip hardware acceleration (see [Jellyfin Rockchip HWA Docs](https://jellyfin.org/docs/general/administration/hardware-acceleration/rockchip/))

### Build & Run with Docker

#### 1️⃣ **Build the Docker Image**
```sh
docker build -t atriva-vpipe-ffmpeg-rockchip .
```

#### 2️⃣ **Run the Container with Rockchip Devices**
```sh
docker run --rm -p 8002:8002 \
  --device /dev/mpp_service \
  --device /dev/dri \
  --device /dev/rga \
  --device /dev/mali0 \
  -v $(pwd)/videos:/app/videos \
  -v $(pwd)/frames:/app/frames \
  atriva-vpipe-ffmpeg-rockchip
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

### Checking Hardware Acceleration
To list supported hardware acceleration methods inside the container:
```sh
ffmpeg -hwaccels
```

## 🧪 Profiling and Testing Tools

This project includes comprehensive profiling and testing tools located in the `profiler/` directory. These tools help verify hardware acceleration, test performance, and analyze results.

### Quick Profiling Commands

#### Hardware Acceleration Verification
```bash
# From root directory
python3 run_profiler.py verify_hw_accel.py

# Or directly from profiler directory
cd profiler
python3 verify_hw_accel.py
```

#### Performance Testing
```bash
# Run basic profiling test
python3 run_profiler.py profiler_test_app.py --channels 3 --duration 30

# Analyze results
python3 run_profiler.py analyze_results.py profiling_results.json
```

#### Direct FFmpeg Testing
```bash
# Test FFmpeg hardware acceleration directly
python3 run_profiler.py test_ffmpeg_hw.py
```

### Available Profiling Tools

- **`verify_hw_accel.py`** - Comprehensive hardware acceleration verification
- **`profiler_test_app.py`** - Main profiling application for performance testing
- **`analyze_results.py`** - Results analysis and visualization
- **`test_ffmpeg_hw.py`** - Direct FFmpeg hardware acceleration testing
- **`test_profiler.py`** - Test suite runner with different configurations
- **`demo_profiler.py`** - Demo configurations and examples

For detailed documentation, see [`profiler/README.md`](profiler/README.md).

## Troubleshooting
#### **Permission Issues with Output Directories**
If the container cannot write to `/app/frames`, ensure proper permissions:
```sh
mkdir -p frames videos
chmod -R 777 frames videos
```

#### **Checking Device Availability**
To verify that Rockchip devices are available inside the container:
```sh
docker run --rm \
  --device /dev/mpp_service \
  --device /dev/dri \
  --device /dev/rga \
  --device /dev/mali0 \
  atriva-vpipe-ffmpeg-rockchip ls /dev
```

## License
MIT License

## Contributing
Pull requests are welcome! Feel free to submit issues for feature requests or bug fixes.


