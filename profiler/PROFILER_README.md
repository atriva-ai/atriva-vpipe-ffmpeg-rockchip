 # Video Pipeline Profiling Test Application

A comprehensive testing and profiling tool for the Atriva Video Pipeline API service. This application allows you to test video decoding performance with multiple RTSP channels and monitor CPU/memory usage in real-time.

## Features

- 🚀 **Multi-Channel Testing**: Test multiple RTSP streams simultaneously
- 📊 **Real-time Monitoring**: Monitor CPU and memory usage during tests
- 🔧 **Hardware Acceleration Testing**: Test different hardware acceleration methods (RKMPP, V4L2, RGA)
- 📈 **Performance Metrics**: Collect detailed performance metrics over time
- 📄 **Comprehensive Reports**: Generate JSON results and HTML reports
- 📊 **Visualization**: Create charts and graphs from test results
- 🔄 **Comparison Tools**: Compare results from different test configurations

## Prerequisites

### System Requirements
- Python 3.7+
- Atriva Video Pipeline API service running (Docker container)
- Network access to RTSP streams
- Sufficient system resources for testing

### Dependencies
Install the required Python packages:

```bash
# For the profiler
pip install -r profiler_requirements.txt

# For the analyzer (optional)
pip install -r analyzer_requirements.txt
```

## Quick Start

### 1. Start the Video Pipeline Service

First, ensure the video pipeline service is running:

```bash
docker run --rm -p 8002:8002 \
  --device /dev/mpp_service \
  --device /dev/dri \
  --device /dev/rga \
  --device /dev/mali0 \
  -v $(pwd)/videos:/app/videos \
  -v $(pwd)/frames:/app/frames \
  atriva-vpipe-ffmpeg-rockchip
```

### 2. Run a Basic Test

```bash
# Basic test with 3 channels for 30 seconds
python3 profiler_test_app.py --channels 3 --duration 30
```

### 3. Analyze Results

```bash
# Analyze the results and generate plots
python3 analyze_results.py profiling_results.json
```

## Usage Examples

### Basic Performance Test

```bash
# Test 5 RTSP channels for 60 seconds
python3 profiler_test_app.py \
  --channels 5 \
  --duration 60 \
  --fps 1 \
  --output basic_test.json
```

### Hardware Acceleration Comparison

```bash
# Test with RKMPP hardware acceleration
python3 profiler_test_app.py \
  --channels 3 \
  --duration 30 \
  --hw-accel rkmpp \
  --output rkmpp_test.json

# Test with V4L2 hardware acceleration
python3 profiler_test_app.py \
  --channels 3 \
  --duration 30 \
  --hw-accel v4l2 \
  --output v4l2_test.json

# Test with software decoding
python3 profiler_test_app.py \
  --channels 3 \
  --duration 30 \
  --hw-accel none \
  --output software_test.json
```

### High Load Stress Test

```bash
# Test 10 channels with high FPS
python3 profiler_test_app.py \
  --channels 10 \
  --duration 120 \
  --fps 5 \
  --start-delay 1.0 \
  --output stress_test.json
```

### Custom RTSP URLs

```bash
# Test with specific RTSP URLs
python3 profiler_test_app.py \
  --rtsp-urls \
    "rtsp://192.168.1.100:554/stream1" \
    "rtsp://192.168.1.101:554/stream1" \
    "rtsp://192.168.1.102:554/stream1" \
  --duration 45 \
  --output custom_test.json
```

## Command Line Options

### Profiler Options

| Option | Description | Default |
|--------|-------------|---------|
| `--api-url` | API base URL | `http://localhost:8002` |
| `--channels` | Number of RTSP channels | `5` |
| `--duration` | Test duration in seconds | `60` |
| `--start-delay` | Delay between starting channels | `2.0` |
| `--fps` | Frames per second to extract | `1` |
| `--hw-accel` | Hardware acceleration method | `auto` |
| `--output` | Output file for results | `profiling_results.json` |
| `--monitor-interval` | Monitoring interval in seconds | `1.0` |
| `--rtsp-urls` | Custom RTSP URLs | `auto-generated` |

### Hardware Acceleration Options

- `rkmpp`: Rockchip Media Process Platform (recommended for RK3588)
- `v4l2`: Video4Linux2 hardware acceleration
- `rga`: Rockchip Graphics Acceleration
- `none`: Software decoding (no hardware acceleration)

### Analyzer Options

| Option | Description |
|--------|-------------|
| `results_file` | JSON results file to analyze |
| `--output-dir` | Output directory for plots | `plots` |
| `--compare` | Compare multiple result files |
| `--no-plots` | Skip generating plots |
| `--no-report` | Skip generating HTML report |

## Test Configurations

### 1. Basic Performance Test
```bash
python3 profiler_test_app.py --channels 3 --duration 30 --fps 1
```
- **Purpose**: Basic functionality test
- **Use Case**: Verify API is working correctly
- **Expected**: Low CPU/memory usage, successful frame extraction

### 2. Hardware Acceleration Comparison
```bash
# Test different HW acceleration methods
python3 profiler_test_app.py --channels 2 --duration 20 --hw-accel rkmpp
python3 profiler_test_app.py --channels 2 --duration 20 --hw-accel v4l2
python3 profiler_test_app.py --channels 2 --duration 20 --hw-accel none
```
- **Purpose**: Compare performance of different acceleration methods
- **Use Case**: Determine optimal hardware acceleration for your setup
- **Expected**: RKMPP should show best performance on RK3588

### 3. High Load Stress Test
```bash
python3 profiler_test_app.py --channels 8 --duration 60 --fps 5 --start-delay 1.0
```
- **Purpose**: Stress test the system
- **Use Case**: Determine maximum capacity
- **Expected**: Higher CPU/memory usage, potential bottlenecks

### 4. Scalability Test
```bash
# Test increasing number of channels
for channels in 1 2 4 6 8 10; do
  python3 profiler_test_app.py --channels $channels --duration 30 --output scalability_${channels}ch.json
done
```
- **Purpose**: Understand system scalability
- **Use Case**: Capacity planning
- **Expected**: Linear increase in resource usage

## Output Files

### JSON Results File
The profiler generates a JSON file with detailed metrics:

```json
{
  "test_config": {
    "api_base_url": "http://localhost:8002",
    "rtsp_urls": ["rtsp://192.168.1.100:554/stream1"],
    "test_duration": 60,
    "channel_start_delay": 2.0,
    "fps": 1,
    "hardware_accel": "rkmpp",
    "output_file": "profiling_results.json",
    "monitor_interval": 1.0
  },
  "summary": {
    "total_metrics": 60,
    "test_start": "2024-01-15T10:00:00",
    "test_end": "2024-01-15T10:01:00",
    "max_channels": 1,
    "max_cpu_percent": 25.5,
    "max_memory_mb": 150.2,
    "total_frames": 60,
    "total_errors": 0
  },
  "metrics": [
    {
      "timestamp": 1705312800.0,
      "cpu_percent": 15.2,
      "memory_percent": 2.1,
      "memory_mb": 120.5,
      "active_channels": 1,
      "total_frames": 1,
      "errors": []
    }
  ],
  "errors": []
}
```

### Generated Files
- `profiling_results.json`: Raw test data
- `profiling_results_report.html`: HTML report with statistics
- `plots/profiling_results_metrics.png`: Time series plots
- `plots/profiling_results_correlation.png`: Correlation matrix

## Analysis and Visualization

### Generate Plots
```bash
python3 analyze_results.py profiling_results.json
```

### Compare Multiple Tests
```bash
python3 analyze_results.py --compare test1.json test2.json test3.json
```

### Generate HTML Report Only
```bash
python3 analyze_results.py profiling_results.json --no-plots
```

## Troubleshooting

### Common Issues

#### 1. API Connection Failed
```
❌ Error starting camera camera_001: Connection refused
```
**Solution**: Ensure the video pipeline service is running and accessible.

#### 2. RTSP Stream Unavailable
```
❌ Failed to start camera camera_001: HTTP 500 - FFmpeg process failed
```
**Solution**: Check RTSP URL accessibility and network connectivity.

#### 3. High Memory Usage
```
💾 Max Memory Usage: 2048.0MB
```
**Solution**: Reduce number of channels or FPS, or increase system memory.

#### 4. High CPU Usage
```
🔥 Max CPU Usage: 95.2%
```
**Solution**: Enable hardware acceleration or reduce load.

### Debug Mode
Run with verbose output:
```bash
python3 profiler_test_app.py --channels 1 --duration 10 --monitor-interval 0.5
```

### Health Check
Check API health before testing:
```bash
curl http://localhost:8002/api/v1/video-pipeline/health/
```

## Performance Guidelines

### Recommended Settings for RK3588

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
| Frame Rate | 1-5 FPS per channel |

## Integration with CI/CD

### Automated Testing
```bash
#!/bin/bash
# Run automated performance tests

# Start video pipeline service
docker run -d --name video-pipeline \
  --device /dev/mpp_service \
  --device /dev/dri \
  --device /dev/rga \
  --device /dev/mali0 \
  -p 8002:8002 \
  atriva-vpipe-ffmpeg-rockchip

# Wait for service to start
sleep 10

# Run performance test
python3 profiler_test_app.py \
  --channels 5 \
  --duration 60 \
  --output ci_test_results.json

# Analyze results
python3 analyze_results.py ci_test_results.json

# Check performance thresholds
python3 -c "
import json
with open('ci_test_results.json') as f:
    data = json.load(f)
summary = data['summary']
if summary['max_cpu_percent'] > 80:
    exit(1)
if summary['max_memory_mb'] > 1000:
    exit(1)
print('Performance test passed')
"

# Cleanup
docker stop video-pipeline
docker rm video-pipeline
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details.
