# Video Pipeline Profiler Tools

This directory contains comprehensive profiling and testing tools for the Atriva Video Pipeline API service. These tools help verify hardware acceleration, test performance, and analyze results.

## 📁 Directory Structure

```
profiler/
├── README.md                           # This file
├── PROFILER_README.md                   # Detailed profiler documentation
├── profiler_test_app.py                 # Main profiling application
├── analyze_results.py                   # Results analysis and visualization
├── test_profiler.py                     # Test suite runner
├── demo_profiler.py                     # Demo configurations
├── verify_hw_accel.py                   # Hardware acceleration verification
├── test_ffmpeg_hw.py                    # Direct FFmpeg hardware testing
├── profiler_requirements.txt            # Profiler dependencies
├── analyzer_requirements.txt            # Analyzer dependencies
├── prof_venv/                          # Python virtual environment
├── plots/                              # Generated plots and charts
├── *.json                              # Profiling results
└── *.html                              # HTML reports
```

## 🚀 Quick Start

### 1. Hardware Acceleration Verification

First, verify that hardware acceleration is working:

```bash
cd profiler
python3 verify_hw_accel.py
```

### 2. Run Basic Profiling Test

```bash
python3 profiler_test_app.py --channels 3 --duration 30
```

### 3. Analyze Results

```bash
python3 analyze_results.py profiling_results.json
```

## 🛠️ Tools Overview

### Core Profiling Tools

#### `profiler_test_app.py`
- **Purpose**: Main profiling application for testing video pipeline performance
- **Features**: Multi-channel RTSP testing, real-time monitoring, hardware acceleration testing
- **Usage**: `python3 profiler_test_app.py --channels 5 --duration 60`

#### `analyze_results.py`
- **Purpose**: Analyze profiling results and generate visualizations
- **Features**: Performance charts, correlation analysis, HTML reports
- **Usage**: `python3 analyze_results.py profiling_results.json`

### Testing Tools

#### `verify_hw_accel.py`
- **Purpose**: Comprehensive hardware acceleration verification
- **Features**: OS-level, Docker-level, FFmpeg-level, and API-level checks
- **Usage**: `python3 verify_hw_accel.py [api_url]`

#### `test_ffmpeg_hw.py`
- **Purpose**: Direct FFmpeg hardware acceleration testing
- **Features**: RKMPP decoder testing, performance comparison
- **Usage**: `python3 test_ffmpeg_hw.py`

#### `test_profiler.py`
- **Purpose**: Test suite runner with different configurations
- **Features**: Automated testing with various parameters
- **Usage**: `python3 test_profiler.py`

#### `demo_profiler.py`
- **Purpose**: Demo configurations and examples
- **Features**: Pre-configured test scenarios
- **Usage**: `python3 demo_profiler.py`

## 📊 Output Files

### Results Files
- `profiling_results.json` - Raw profiling data
- `hw_accel_verification.json` - Hardware acceleration verification results
- `test*_results.json` - Test-specific results

### Reports and Visualizations
- `profiling_results_report.html` - HTML report with statistics
- `plots/` - Generated charts and graphs
  - `profiling_results_metrics.png` - Time series plots
  - `profiling_results_correlation.png` - Correlation matrix

## 🔧 Setup

### 1. Install Dependencies

```bash
# Install profiler dependencies
pip install -r profiler_requirements.txt

# Install analyzer dependencies (optional)
pip install -r analyzer_requirements.txt
```

### 2. Virtual Environment (Optional)

```bash
# Activate virtual environment
source prof_venv/bin/activate

# Or create new environment
python3 -m venv prof_venv
source prof_venv/bin/activate
pip install -r profiler_requirements.txt
```

## 📈 Usage Examples

### Basic Performance Test
```bash
python3 profiler_test_app.py \
  --channels 5 \
  --duration 60 \
  --fps 1 \
  --hw-accel rkmpp \
  --output basic_test.json
```

### Hardware Acceleration Test
```bash
python3 verify_hw_accel.py http://localhost:8002
```

### Performance Analysis
```bash
python3 analyze_results.py basic_test.json
```

### Compare Multiple Tests
```bash
python3 analyze_results.py --compare test1.json test2.json test3.json
```

## 🎯 Hardware Acceleration Verification

The verification tools check:

### OS Level
- ✅ MPP service device (`/dev/mpp_service`)
- ✅ DRI devices (`/dev/dri`)
- ✅ RGA device (`/dev/rga`)
- ✅ Mali GPU (`/dev/mali0`)

### FFmpeg Level
- ✅ RKMPP hardware accelerator
- ✅ RKMPP decoders (H.264, HEVC, VP8, VP9, AV1, MPEG)

### Docker Level
- ✅ Device mounting capabilities
- ✅ Hardware device access

## 📋 Test Configurations

### Performance Test Configurations

| Use Case | Channels | FPS | HW Accel | Duration |
|----------|----------|-----|----------|----------|
| Basic Test | 1-3 | 1 | rkmpp | 30s |
| Performance Test | 3-5 | 1-2 | rkmpp | 60s |
| Stress Test | 6-10 | 2-5 | rkmpp | 120s |
| Max Load | 10+ | 5+ | rkmpp | 300s |

### Expected Performance (RK3588)

| Metric | Expected Range |
|--------|----------------|
| CPU Usage (1 channel) | 5-15% |
| CPU Usage (5 channels) | 20-40% |
| CPU Usage (10 channels) | 40-70% |
| Memory Usage (1 channel) | 50-100MB |
| Memory Usage (5 channels) | 200-400MB |
| Memory Usage (10 channels) | 400-800MB |

## 🔍 Troubleshooting

### Common Issues

#### 1. API Connection Failed
```
❌ API at http://localhost:8002 is not responding
```
**Solution**: Start the video pipeline service first

#### 2. Hardware Acceleration Not Working
```
❌ Hardware acceleration verification FAILED
```
**Solution**: Check device permissions and Docker device mounting

#### 3. RTSP Stream Unavailable
```
❌ Failed to start camera: HTTP 500 - FFmpeg process failed
```
**Solution**: Verify RTSP URL accessibility and network connectivity

### Debug Commands

```bash
# Check hardware devices
ls -la /dev/mpp_service /dev/dri /dev/rga /dev/mali0

# Check FFmpeg hardware support
ffmpeg -hide_banner -hwaccels

# Check RKMPP decoders
ffmpeg -hide_banner -decoders | grep rkmpp

# Test Docker device mounting
docker run --rm --device /dev/mpp_service alpine:latest ls -la /dev/
```

## 📚 Additional Documentation

- `PROFILER_README.md` - Detailed profiler documentation
- `API_INTEGRATION_GUIDE.md` - API integration guide
- Generated HTML reports for detailed analysis

## 🤝 Contributing

1. Follow the existing code structure
2. Add tests for new functionality
3. Update documentation
4. Test with different hardware configurations
