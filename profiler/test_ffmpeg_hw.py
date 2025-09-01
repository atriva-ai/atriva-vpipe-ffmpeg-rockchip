#!/usr/bin/env python3
"""
Test FFmpeg Hardware Acceleration Directly
"""

import subprocess
import json
import time

def test_ffmpeg_hw_accel():
    """Test FFmpeg hardware acceleration directly"""
    print("🎬 Testing FFmpeg Hardware Acceleration Directly")
    print("=" * 50)
    
    # Test 1: Check available hardware accelerators
    print("\n1. Checking available hardware accelerators:")
    try:
        result = subprocess.run(["ffmpeg", "-hide_banner", "-hwaccels"], 
                               capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ Available accelerators:")
            print(result.stdout)
        else:
            print("❌ Failed to get hardware accelerators")
            print(result.stderr)
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Check RKMPP decoder specifically
    print("\n2. Checking RKMPP decoder support:")
    try:
        result = subprocess.run(["ffmpeg", "-hide_banner", "-decoders"], 
                               capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            rkmpp_decoders = []
            for line in result.stdout.split('\n'):
                if 'rkmpp' in line.lower():
                    rkmpp_decoders.append(line.strip())
            
            if rkmpp_decoders:
                print("✅ RKMPP decoders found:")
                for decoder in rkmpp_decoders:
                    print(f"   {decoder}")
            else:
                print("❌ No RKMPP decoders found")
        else:
            print("❌ Failed to get decoders")
            print(result.stderr)
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Test hardware decoding with a sample RTSP stream
    print("\n3. Testing hardware decoding with RTSP stream:")
    print("   Testing: rtsp://192.168.9.108:8554/stream1")
    
    # Create a simple test command that uses RKMPP
    test_cmd = [
        "ffmpeg",
        "-hide_banner",
        "-rtsp_transport", "tcp",
        "-hwaccel", "rkmpp",
        "-i", "rtsp://192.168.9.108:8554/stream1",
        "-t", "5",  # 5 seconds
        "-f", "null",
        "-"
    ]
    
    try:
        start_time = time.time()
        result = subprocess.run(test_cmd, capture_output=True, text=True, timeout=30)
        end_time = time.time()
        
        if result.returncode == 0:
            print("✅ Hardware decoding test PASSED")
            print(f"   Time taken: {end_time - start_time:.2f} seconds")
            
            # Check if RKMPP was actually used
            if "rkmpp" in result.stderr.lower():
                print("✅ RKMPP hardware acceleration confirmed in use")
            else:
                print("⚠️ RKMPP may not have been used (check stderr)")
                
        else:
            print("❌ Hardware decoding test FAILED")
            print(f"   Return code: {result.returncode}")
            print("   Error output:")
            print(result.stderr)
            
    except subprocess.TimeoutExpired:
        print("⏰ Hardware decoding test timed out")
    except Exception as e:
        print(f"❌ Error during hardware decoding test: {e}")
    
    # Test 4: Compare software vs hardware decoding
    print("\n4. Comparing software vs hardware decoding performance:")
    
    # Software decoding test
    print("   Testing software decoding...")
    sw_cmd = [
        "ffmpeg",
        "-hide_banner",
        "-rtsp_transport", "tcp",
        "-i", "rtsp://192.168.9.108:8554/stream1",
        "-t", "3",  # 3 seconds
        "-f", "null",
        "-"
    ]
    
    try:
        sw_start = time.time()
        sw_result = subprocess.run(sw_cmd, capture_output=True, text=True, timeout=20)
        sw_end = time.time()
        sw_time = sw_end - sw_start
        
        if sw_result.returncode == 0:
            print(f"   ✅ Software decoding: {sw_time:.2f} seconds")
        else:
            print(f"   ❌ Software decoding failed: {sw_result.returncode}")
            
    except Exception as e:
        print(f"   ❌ Software decoding error: {e}")
        sw_time = None
    
    # Hardware decoding test
    print("   Testing hardware decoding...")
    hw_cmd = [
        "ffmpeg",
        "-hide_banner",
        "-rtsp_transport", "tcp",
        "-hwaccel", "rkmpp",
        "-i", "rtsp://192.168.9.108:8554/stream1",
        "-t", "3",  # 3 seconds
        "-f", "null",
        "-"
    ]
    
    try:
        hw_start = time.time()
        hw_result = subprocess.run(hw_cmd, capture_output=True, text=True, timeout=20)
        hw_end = time.time()
        hw_time = hw_end - hw_start
        
        if hw_result.returncode == 0:
            print(f"   ✅ Hardware decoding: {hw_time:.2f} seconds")
            
            # Compare performance
            if sw_time and hw_time:
                speedup = sw_time / hw_time
                print(f"   📊 Speedup: {speedup:.2f}x faster with hardware")
                
                if speedup > 1.0:
                    print("   🎉 Hardware acceleration is working!")
                else:
                    print("   ⚠️ Hardware decoding may not be faster (could be network limited)")
                    
        else:
            print(f"   ❌ Hardware decoding failed: {hw_result.returncode}")
            print("   Error output:")
            print(hw_result.stderr)
            
    except Exception as e:
        print(f"   ❌ Hardware decoding error: {e}")

if __name__ == "__main__":
    test_ffmpeg_hw_accel()
