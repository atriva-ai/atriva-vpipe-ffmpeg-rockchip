#!/usr/bin/env python3
"""
Simple test script for the Video Pipeline Profiler
Demonstrates different test configurations
"""

import asyncio
import subprocess
import sys
import os

def check_api_health(api_url: str) -> bool:
    """Check if the API is running and healthy"""
    try:
        import requests
        response = requests.get(f"{api_url}/api/v1/video-pipeline/health/", timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ API health check failed: {e}")
        return False

def run_profiler_test(config_name: str, args: list):
    """Run the profiler with specific configuration"""
    print(f"\n🚀 Running {config_name} test...")
    print(f"Command: python3 profiler_test_app.py {' '.join(args)}")
    
    try:
        result = subprocess.run(
            ["python3", "profiler_test_app.py"] + args,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout
        )
        
        if result.returncode == 0:
            print(f"✅ {config_name} test completed successfully")
            print("Output:")
            print(result.stdout)
        else:
            print(f"❌ {config_name} test failed")
            print("Error:")
            print(result.stderr)
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {config_name} test timed out")
    except Exception as e:
        print(f"❌ Error running {config_name} test: {e}")

def main():
    """Main function to run different test configurations"""
    print("🎯 Video Pipeline Profiler Test Suite")
    print("=" * 50)
    
    # Check if API is running
    api_url = "http://localhost:8002"
    if not check_api_health(api_url):
        print(f"❌ API at {api_url} is not responding. Please start the video pipeline service first.")
        print("Run: docker run --rm -p 8002:8002 --device /dev/mpp_service --device /dev/dri --device /dev/rga --device /dev/mali0 atriva-vpipe-ffmpeg-rockchip")
        return
    
    print(f"✅ API at {api_url} is healthy")
    
    # Test 1: Basic test with 3 channels, 30 seconds
    print("\n📋 Test 1: Basic Performance Test")
    print("   - 3 RTSP channels")
    print("   - 30 seconds duration")
    print("   - 1 FPS extraction")
    print("   - Auto hardware acceleration")
    
    run_profiler_test("Basic", [
        "--channels", "3",
        "--duration", "30",
        "--fps", "1",
        "--output", "test1_basic_results.json"
    ])
    
    # Test 2: Hardware acceleration comparison
    print("\n📋 Test 2: Hardware Acceleration Comparison")
    print("   - 2 RTSP channels")
    print("   - 20 seconds duration")
    print("   - Testing different HW acceleration methods")
    
    # Test with RKMPP
    run_profiler_test("RKMPP", [
        "--channels", "2",
        "--duration", "20",
        "--hw-accel", "rkmpp",
        "--output", "test2_rkmpp_results.json"
    ])
    
    # Test with V4L2
    run_profiler_test("V4L2", [
        "--channels", "2",
        "--duration", "20",
        "--hw-accel", "v4l2",
        "--output", "test2_v4l2_results.json"
    ])
    
    # Test with software decoding
    run_profiler_test("Software", [
        "--channels", "2",
        "--duration", "20",
        "--hw-accel", "none",
        "--output", "test2_software_results.json"
    ])
    
    # Test 3: High load test
    print("\n📋 Test 3: High Load Test")
    print("   - 8 RTSP channels")
    print("   - 60 seconds duration")
    print("   - 5 FPS extraction")
    print("   - Stress testing the system")
    
    run_profiler_test("High Load", [
        "--channels", "8",
        "--duration", "60",
        "--fps", "5",
        "--start-delay", "1.0",
        "--output", "test3_highload_results.json"
    ])
    
    # Test 4: Custom RTSP URLs (if available)
    print("\n📋 Test 4: Custom RTSP URLs Test")
    print("   - Using specific RTSP URLs")
    print("   - 2 channels")
    print("   - 30 seconds duration")
    
    # Example with some common test RTSP URLs
    custom_urls = [
        "rtsp://demo:demo@ipvmdemo.dyndns.org:5541/onvif-media/media.amp",
        "rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mp4"
    ]
    
    run_profiler_test("Custom URLs", [
        "--channels", "2",
        "--duration", "30",
        "--rtsp-urls"] + custom_urls + [
        "--output", "test4_custom_results.json"
    ])
    
    print("\n🎉 All tests completed!")
    print("📊 Check the generated JSON files for detailed results:")
    print("   - test1_basic_results.json")
    print("   - test2_rkmpp_results.json")
    print("   - test2_v4l2_results.json")
    print("   - test2_software_results.json")
    print("   - test3_highload_results.json")
    print("   - test4_custom_results.json")

if __name__ == "__main__":
    main()
