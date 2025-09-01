#!/usr/bin/env python3
"""
Hardware Acceleration Verification Script
Verifies hardware acceleration support for video decoding at OS and Docker levels
"""

import subprocess
import json
import os
import sys
import requests
import time
from typing import Dict, List, Optional

class HWAccelVerifier:
    """Hardware acceleration verification class"""
    
    def __init__(self):
        self.results = {
            "os_level": {},
            "docker_level": {},
            "api_level": {},
            "ffmpeg_level": {},
            "summary": {}
        }
    
    def run_command(self, cmd: List[str], timeout: int = 30) -> Dict:
        """Run a command and return results"""
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=timeout
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": "Command timed out",
                "returncode": -1
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "returncode": -1
            }
    
    def check_os_devices(self) -> Dict:
        """Check hardware devices at OS level"""
        print("🔍 Checking OS-level hardware devices...")
        
        devices = {}
        
        # Check MPP service device
        mpp_result = self.run_command(["ls", "-la", "/dev/mpp_service"])
        devices["mpp_service"] = {
            "exists": mpp_result["success"],
            "output": mpp_result["stdout"] if mpp_result["success"] else mpp_result["stderr"]
        }
        
        # Check DRI devices
        dri_result = self.run_command(["ls", "-la", "/dev/dri"])
        devices["dri"] = {
            "exists": dri_result["success"],
            "output": dri_result["stdout"] if dri_result["success"] else dri_result["stderr"]
        }
        
        # Check RGA device
        rga_result = self.run_command(["ls", "-la", "/dev/rga"])
        devices["rga"] = {
            "exists": rga_result["success"],
            "output": rga_result["stdout"] if rga_result["success"] else rga_result["stderr"]
        }
        
        # Check Mali GPU device
        mali_result = self.run_command(["ls", "-la", "/dev/mali0"])
        devices["mali0"] = {
            "exists": mali_result["success"],
            "output": mali_result["stdout"] if mali_result["success"] else mali_result["stderr"]
        }
        
        # Check CPU architecture
        arch_result = self.run_command(["uname", "-m"])
        devices["architecture"] = {
            "value": arch_result["stdout"].strip() if arch_result["success"] else "unknown",
            "success": arch_result["success"]
        }
        
        # Check kernel version
        kernel_result = self.run_command(["uname", "-r"])
        devices["kernel"] = {
            "value": kernel_result["stdout"].strip() if kernel_result["success"] else "unknown",
            "success": kernel_result["success"]
        }
        
        return devices
    
    def check_docker_devices(self) -> Dict:
        """Check if Docker can access hardware devices"""
        print("🐳 Checking Docker-level device access...")
        
        docker_devices = {}
        
        # Check if Docker is running
        docker_result = self.run_command(["docker", "info"])
        docker_devices["docker_running"] = {
            "running": docker_result["success"],
            "output": docker_result["stdout"] if docker_result["success"] else docker_result["stderr"]
        }
        
        # Test Docker device mounting
        test_cmd = [
            "docker", "run", "--rm",
            "--device", "/dev/mpp_service",
            "--device", "/dev/dri",
            "--device", "/dev/rga", 
            "--device", "/dev/mali0",
            "alpine:latest",
            "ls", "-la", "/dev/"
        ]
        
        docker_test_result = self.run_command(test_cmd)
        docker_devices["device_mounting"] = {
            "success": docker_test_result["success"],
            "output": docker_test_result["stdout"] if docker_test_result["success"] else docker_test_result["stderr"]
        }
        
        return docker_devices
    
    def check_ffmpeg_hw_accel(self) -> Dict:
        """Check FFmpeg hardware acceleration support"""
        print("🎬 Checking FFmpeg hardware acceleration...")
        
        ffmpeg_info = {}
        
        # Check FFmpeg version and build info
        version_result = self.run_command(["ffmpeg", "-version"])
        ffmpeg_info["version"] = {
            "success": version_result["success"],
            "output": version_result["stdout"] if version_result["success"] else version_result["stderr"]
        }
        
        # Check available hardware accelerators
        hwaccel_result = self.run_command(["ffmpeg", "-hide_banner", "-hwaccels"])
        ffmpeg_info["hwaccels"] = {
            "success": hwaccel_result["success"],
            "output": hwaccel_result["stdout"] if hwaccel_result["success"] else hwaccel_result["stderr"]
        }
        
        # Check available decoders
        decoders_result = self.run_command(["ffmpeg", "-hide_banner", "-decoders"])
        ffmpeg_info["decoders"] = {
            "success": decoders_result["success"],
            "output": decoders_result["stdout"] if decoders_result["success"] else decoders_result["stderr"]
        }
        
        # Check specific RKMPP decoder
        rkmpp_result = self.run_command(["ffmpeg", "-hide_banner", "-decoders", "|", "grep", "rkmpp"])
        ffmpeg_info["rkmpp_decoder"] = {
            "success": rkmpp_result["success"],
            "output": rkmpp_result["stdout"] if rkmpp_result["success"] else rkmpp_result["stderr"]
        }
        
        return ffmpeg_info
    
    def check_api_hw_accel(self, api_url: str = "http://localhost:8002") -> Dict:
        """Check API-level hardware acceleration support"""
        print("🌐 Checking API-level hardware acceleration...")
        
        api_info = {}
        
        # Check API health
        try:
            health_response = requests.get(f"{api_url}/api/v1/video-pipeline/health/", timeout=5)
            api_info["health"] = {
                "success": health_response.status_code == 200,
                "status_code": health_response.status_code,
                "response": health_response.text
            }
        except Exception as e:
            api_info["health"] = {
                "success": False,
                "error": str(e)
            }
        
        # Test hardware acceleration with a simple decode request
        if api_info["health"]["success"]:
            test_data = {
                "camera_id": "hw_test",
                "url": "rtsp://192.168.9.108:8554/stream1",
                "fps": "1",
                "force_format": "rkmpp"
            }
            
            try:
                response = requests.post(
                    f"{api_url}/api/v1/video-pipeline/decode/",
                    data=test_data,
                    timeout=10
                )
                api_info["hw_test"] = {
                    "success": response.status_code == 200,
                    "status_code": response.status_code,
                    "response": response.text
                }
                
                # Stop the test channel
                if response.status_code == 200:
                    stop_response = requests.post(
                        f"{api_url}/api/v1/video-pipeline/decode/stop/",
                        data={"camera_id": "hw_test"},
                        timeout=5
                    )
                    api_info["hw_test_stop"] = {
                        "success": stop_response.status_code == 200,
                        "status_code": stop_response.status_code
                    }
                    
            except Exception as e:
                api_info["hw_test"] = {
                    "success": False,
                    "error": str(e)
                }
        
        return api_info
    
    def test_hw_decoding_performance(self, api_url: str = "http://localhost:8002") -> Dict:
        """Test hardware decoding performance"""
        print("⚡ Testing hardware decoding performance...")
        
        performance = {}
        
        # Test with hardware acceleration
        hw_test_data = {
            "camera_id": "perf_hw_test",
            "url": "rtsp://192.168.9.108:8554/stream1", 
            "fps": "1",
            "force_format": "rkmpp"
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{api_url}/api/v1/video-pipeline/decode/",
                data=hw_test_data,
                timeout=10
            )
            hw_start_time = time.time() - start_time
            
            performance["hw_startup"] = {
                "success": response.status_code == 200,
                "time_ms": hw_start_time * 1000,
                "status_code": response.status_code
            }
            
            # Wait a bit and check status
            time.sleep(2)
            status_response = requests.get(
                f"{api_url}/api/v1/video-pipeline/decode/status/",
                params={"camera_id": "perf_hw_test"},
                timeout=5
            )
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                performance["hw_status"] = {
                    "success": True,
                    "status": status_data.get("status", "unknown"),
                    "frame_count": status_data.get("frame_count", 0)
                }
            
            # Stop the test
            stop_response = requests.post(
                f"{api_url}/api/v1/video-pipeline/decode/stop/",
                data={"camera_id": "perf_hw_test"},
                timeout=5
            )
            
        except Exception as e:
            performance["hw_test"] = {
                "success": False,
                "error": str(e)
            }
        
        return performance
    
    def generate_summary(self) -> Dict:
        """Generate a summary of all checks"""
        summary = {
            "overall_status": "UNKNOWN",
            "hw_accel_available": False,
            "issues": [],
            "recommendations": []
        }
        
        # Check OS level
        os_devices = self.results["os_level"]
        required_devices = ["mpp_service", "dri", "rga", "mali0"]
        missing_devices = []
        
        for device in required_devices:
            if device in os_devices and not os_devices[device]["exists"]:
                missing_devices.append(device)
        
        if missing_devices:
            summary["issues"].append(f"Missing OS devices: {', '.join(missing_devices)}")
        
        # Check Docker level
        docker_devices = self.results["docker_level"]
        if not docker_devices.get("docker_running", {}).get("running", False):
            summary["issues"].append("Docker is not running")
        
        if not docker_devices.get("device_mounting", {}).get("success", False):
            summary["issues"].append("Docker cannot mount hardware devices")
        
        # Check FFmpeg level
        ffmpeg_info = self.results["ffmpeg_level"]
        if not ffmpeg_info.get("hwaccels", {}).get("success", False):
            summary["issues"].append("FFmpeg hardware acceleration check failed")
        
        # Check API level
        api_info = self.results["api_level"]
        if not api_info.get("health", {}).get("success", False):
            summary["issues"].append("API is not responding")
        
        # Determine overall status
        if not summary["issues"]:
            summary["overall_status"] = "PASS"
            summary["hw_accel_available"] = True
            summary["recommendations"].append("Hardware acceleration appears to be working correctly")
        else:
            summary["overall_status"] = "FAIL"
            summary["recommendations"].append("Fix the issues listed above to enable hardware acceleration")
        
        return summary
    
    def run_all_checks(self, api_url: str = "http://localhost:8002"):
        """Run all hardware acceleration checks"""
        print("🔧 Hardware Acceleration Verification")
        print("=" * 50)
        
        # OS level checks
        self.results["os_level"] = self.check_os_devices()
        
        # Docker level checks
        self.results["docker_level"] = self.check_docker_devices()
        
        # FFmpeg level checks
        self.results["ffmpeg_level"] = self.check_ffmpeg_hw_accel()
        
        # API level checks
        self.results["api_level"] = self.check_api_hw_accel(api_url)
        
        # Performance test
        self.results["performance"] = self.test_hw_decoding_performance(api_url)
        
        # Generate summary
        self.results["summary"] = self.generate_summary()
        
        return self.results
    
    def print_results(self):
        """Print verification results"""
        print("\n" + "=" * 50)
        print("📊 VERIFICATION RESULTS")
        print("=" * 50)
        
        # OS Level
        print("\n🔍 OS Level:")
        os_devices = self.results["os_level"]
        for device, info in os_devices.items():
            if device in ["mpp_service", "dri", "rga", "mali0"]:
                status = "✅" if info["exists"] else "❌"
                print(f"   {status} {device}: {'Available' if info['exists'] else 'Missing'}")
            else:
                print(f"   📋 {device}: {info.get('value', 'unknown')}")
        
        # Docker Level
        print("\n🐳 Docker Level:")
        docker_devices = self.results["docker_level"]
        docker_running = docker_devices.get("docker_running", {}).get("running", False)
        print(f"   {'✅' if docker_running else '❌'} Docker running: {docker_running}")
        
        device_mounting = docker_devices.get("device_mounting", {}).get("success", False)
        print(f"   {'✅' if device_mounting else '❌'} Device mounting: {device_mounting}")
        
        # FFmpeg Level
        print("\n🎬 FFmpeg Level:")
        ffmpeg_info = self.results["ffmpeg_level"]
        hwaccels_success = ffmpeg_info.get("hwaccels", {}).get("success", False)
        print(f"   {'✅' if hwaccels_success else '❌'} Hardware accelerators: {'Available' if hwaccels_success else 'Failed'}")
        
        if hwaccels_success:
            hwaccels_output = ffmpeg_info["hwaccels"]["output"]
            print(f"   📋 Available accelerators: {hwaccels_output.strip()}")
        
        # API Level
        print("\n🌐 API Level:")
        api_info = self.results["api_level"]
        api_health = api_info.get("health", {}).get("success", False)
        print(f"   {'✅' if api_health else '❌'} API health: {api_health}")
        
        hw_test = api_info.get("hw_test", {}).get("success", False)
        print(f"   {'✅' if hw_test else '❌'} Hardware acceleration test: {hw_test}")
        
        # Performance
        print("\n⚡ Performance:")
        performance = self.results["performance"]
        hw_startup = performance.get("hw_startup", {})
        if hw_startup.get("success", False):
            print(f"   🚀 Hardware startup time: {hw_startup.get('time_ms', 0):.1f}ms")
        
        # Summary
        print("\n📋 Summary:")
        summary = self.results["summary"]
        status_icon = "✅" if summary["overall_status"] == "PASS" else "❌"
        print(f"   {status_icon} Overall Status: {summary['overall_status']}")
        print(f"   {'✅' if summary['hw_accel_available'] else '❌'} Hardware Acceleration: {'Available' if summary['hw_accel_available'] else 'Not Available'}")
        
        if summary["issues"]:
            print("\n⚠️ Issues Found:")
            for issue in summary["issues"]:
                print(f"   • {issue}")
        
        if summary["recommendations"]:
            print("\n💡 Recommendations:")
            for rec in summary["recommendations"]:
                print(f"   • {rec}")
    
    def save_results(self, filename: str = "hw_accel_verification.json"):
        """Save results to JSON file"""
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n💾 Results saved to: {filename}")

def main():
    """Main function"""
    verifier = HWAccelVerifier()
    
    # Get API URL from command line or use default
    api_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8002"
    
    print(f"🎯 Hardware Acceleration Verification")
    print(f"🌐 API URL: {api_url}")
    
    # Run all checks
    results = verifier.run_all_checks(api_url)
    
    # Print results
    verifier.print_results()
    
    # Save results
    verifier.save_results()
    
    # Exit with appropriate code
    if results["summary"]["overall_status"] == "PASS":
        print("\n✅ Hardware acceleration verification PASSED")
        sys.exit(0)
    else:
        print("\n❌ Hardware acceleration verification FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()
