#!/usr/bin/env python3
"""
Demo script for Video Pipeline Profiler
Shows how to run basic tests and analyze results
"""

import subprocess
import time
import os
import sys
import json
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import aiohttp
        import psutil
        print("✅ Required dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install: pip install -r profiler_requirements.txt")
        return False

def check_api_health(api_url="http://localhost:8002"):
    """Check if the video pipeline API is running"""
    try:
        import requests
        response = requests.get(f"{api_url}/api/v1/video-pipeline/health/", timeout=5)
        if response.status_code == 200:
            print(f"✅ Video Pipeline API is healthy at {api_url}")
            return True
        else:
            print(f"⚠️ API responded with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to API at {api_url}: {e}")
        print("\nTo start the API service, run:")
        print("docker run --rm -p 8002:8002 \\")
        print("  --device /dev/mpp_service \\")
        print("  --device /dev/dri \\")
        print("  --device /dev/rga \\")
        print("  --device /dev/mali0 \\")
        print("  -v $(pwd)/videos:/app/videos \\")
        print("  -v $(pwd)/frames:/app/frames \\")
        print("  atriva-vpipe-ffmpeg-rockchip")
        return False

def run_demo_test(test_name, args):
    """Run a demo test and return the results file"""
    print(f"\n🚀 Running {test_name}...")
    print(f"Command: python3 profiler_test_app.py {' '.join(args)}")
    
    try:
        result = subprocess.run(
            ["python3", "profiler_test_app.py"] + args,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            print(f"✅ {test_name} completed successfully")
            # Extract output file from args
            output_file = "profiling_results.json"
            for i, arg in enumerate(args):
                if arg == "--output" and i + 1 < len(args):
                    output_file = args[i + 1]
                    break
            return output_file
        else:
            print(f"❌ {test_name} failed")
            print("Error output:")
            print(result.stderr)
            return None
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {test_name} timed out")
        return None
    except Exception as e:
        print(f"❌ Error running {test_name}: {e}")
        return None

def analyze_results(results_file):
    """Analyze the results and generate reports"""
    if not results_file or not os.path.exists(results_file):
        print(f"❌ Results file {results_file} not found")
        return
        
    print(f"\n📊 Analyzing results from {results_file}...")
    
    try:
        result = subprocess.run(
            ["python3", "analyze_results.py", results_file],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print("✅ Analysis completed successfully")
            print("Generated files:")
            print(f"  - {results_file}")
            print(f"  - {results_file.replace('.json', '_report.html')}")
            print("  - plots/ (directory with charts)")
        else:
            print("❌ Analysis failed")
            print("Error output:")
            print(result.stderr)
            
    except Exception as e:
        print(f"❌ Error analyzing results: {e}")

def print_summary(results_file):
    """Print a quick summary of the results"""
    if not results_file or not os.path.exists(results_file):
        return
        
    try:
        with open(results_file, 'r') as f:
            data = json.load(f)
            
        summary = data.get('summary', {})
        
        print(f"\n📋 Quick Summary for {os.path.basename(results_file)}:")
        print(f"  📺 Max Channels: {summary.get('max_channels', 0)}")
        print(f"  🔥 Max CPU: {summary.get('max_cpu_percent', 0):.1f}%")
        print(f"  💾 Max Memory: {summary.get('max_memory_mb', 0):.1f}MB")
        print(f"  🖼️ Total Frames: {summary.get('total_frames', 0)}")
        print(f"  ❌ Errors: {summary.get('total_errors', 0)}")
        
    except Exception as e:
        print(f"❌ Error reading results: {e}")

def main():
    """Main demo function"""
    print("🎯 Video Pipeline Profiler Demo")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        return
        
    # Check API health
    if not check_api_health():
        print("\n💡 For this demo, we'll use sample RTSP URLs that may not be accessible.")
        print("   The profiler will still run and show how it handles connection errors.")
        print("   To test with real streams, start the API service first.\n")
    
    # Create output directory
    os.makedirs("demo_results", exist_ok=True)
    
    # Demo 1: Basic test
    print("\n📋 Demo 1: Basic Performance Test")
    print("   - 2 RTSP channels")
    print("   - 20 seconds duration")
    print("   - 1 FPS extraction")
    
    results1 = run_demo_test("Basic Test", [
        "--channels", "2",
        "--duration", "20",
        "--fps", "1",
        "--output", "demo_results/basic_test.json"
    ])
    
    if results1:
        print_summary(results1)
    
    # Demo 2: Hardware acceleration test
    print("\n📋 Demo 2: Hardware Acceleration Test")
    print("   - 1 RTSP channel")
    print("   - 15 seconds duration")
    print("   - Testing RKMPP acceleration")
    
    results2 = run_demo_test("HW Acceleration Test", [
        "--channels", "1",
        "--duration", "15",
        "--hw-accel", "rkmpp",
        "--output", "demo_results/hw_accel_test.json"
    ])
    
    if results2:
        print_summary(results2)
    
    # Demo 3: High load test
    print("\n📋 Demo 3: High Load Test")
    print("   - 3 RTSP channels")
    print("   - 25 seconds duration")
    print("   - 3 FPS extraction")
    
    results3 = run_demo_test("High Load Test", [
        "--channels", "3",
        "--duration", "25",
        "--fps", "3",
        "--start-delay", "1.0",
        "--output", "demo_results/high_load_test.json"
    ])
    
    if results3:
        print_summary(results3)
    
    # Analyze all results
    print("\n📊 Analyzing all demo results...")
    for results_file in [results1, results2, results3]:
        if results_file:
            analyze_results(results_file)
    
    # Compare results
    print("\n🔄 Comparing demo results...")
    valid_results = [r for r in [results1, results2, results3] if r and os.path.exists(r)]
    
    if len(valid_results) >= 2:
        try:
            result = subprocess.run(
                ["python3", "analyze_results.py", "--compare"] + valid_results,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                print("✅ Comparison completed successfully")
                print("Generated comparison plot: comparison/comparison_plot.png")
            else:
                print("❌ Comparison failed")
                print("Error output:")
                print(result.stderr)
                
        except Exception as e:
            print(f"❌ Error comparing results: {e}")
    
    # Final summary
    print("\n" + "="*50)
    print("🎉 Demo completed!")
    print("\n📁 Generated files:")
    print("  demo_results/")
    for file in os.listdir("demo_results"):
        if file.endswith(".json"):
            print(f"    - {file}")
    print("  plots/")
    print("    - Metrics charts")
    print("    - Correlation plots")
    print("  comparison/")
    print("    - Comparison plots")
    print("\n📄 HTML reports:")
    for file in os.listdir("demo_results"):
        if file.endswith(".json"):
            html_file = file.replace(".json", "_report.html")
            if os.path.exists(f"demo_results/{html_file}"):
                print(f"    - demo_results/{html_file}")
    
    print("\n💡 Next steps:")
    print("  1. Start the video pipeline API service")
    print("  2. Use real RTSP URLs with --rtsp-urls option")
    print("  3. Test different hardware acceleration methods")
    print("  4. Run longer stress tests")
    print("  5. Analyze results with the analyzer tool")

if __name__ == "__main__":
    main()
