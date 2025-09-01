#!/usr/bin/env python3
"""
Atriva Video Pipeline Profiling Test Application
Tests the video decoding API with multiple RTSP channels and reports CPU/memory usage
"""

import asyncio
import aiohttp
import time
import psutil
import json
import argparse
import sys
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import threading
import signal
import os

@dataclass
class ProfilingMetrics:
    """Data class for storing profiling metrics"""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    active_channels: int
    total_frames: int
    errors: List[str]

@dataclass
class TestConfig:
    """Configuration for the profiling test"""
    api_base_url: str
    rtsp_urls: List[str]
    test_duration: int
    channel_start_delay: float
    fps: int
    hardware_accel: Optional[str]
    output_file: str
    monitor_interval: float

class VideoPipelineProfiler:
    """Main profiling class for testing video pipeline with multiple RTSP channels"""
    
    def __init__(self, config: TestConfig):
        self.config = config
        self.metrics: List[ProfilingMetrics] = []
        self.active_channels: Dict[str, Dict] = {}
        self.session: Optional[aiohttp.ClientSession] = None
        self.monitoring = False
        self.total_frames = 0
        self.errors = []
        
    async def start_session(self):
        """Initialize HTTP session"""
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout)
        
        # Initialize system-wide CPU measurement to avoid initial 0.0 value
        psutil.cpu_percent()
        
    async def stop_session(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            
    def get_system_metrics(self) -> ProfilingMetrics:
        """Get current system metrics"""
        # Get system-wide CPU and memory usage
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        
        return ProfilingMetrics(
            timestamp=time.time(),
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_mb=memory.used / 1024 / 1024,  # Convert to MB
            active_channels=len(self.active_channels),
            total_frames=self.total_frames,
            errors=self.errors.copy()
        )
        
    async def start_channel_decode(self, camera_id: str, rtsp_url: str) -> bool:
        """Start decoding for a single RTSP channel"""
        try:
            if not self.session:
                raise Exception("Session not initialized")
                
            print(f"Decoding rtsp stream: {rtsp_url}")
            url = f"{self.config.api_base_url}/api/v1/video-pipeline/decode/"
            data = {
                'camera_id': camera_id,
                'url': rtsp_url,
                'fps': str(self.config.fps)
            }
            
            if self.config.hardware_accel:
                data['force_format'] = self.config.hardware_accel
                
            async with self.session.post(url, data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Started decode for camera {camera_id}: {result.get('message', 'Unknown')}")
                    self.active_channels[camera_id] = {
                        'rtsp_url': rtsp_url,
                        'start_time': time.time(),
                        'status': 'running'
                    }
                    return True
                else:
                    error_text = await response.text()
                    error_msg = f"Failed to start camera {camera_id}: HTTP {response.status} - {error_text}"
                    print(f"❌ {error_msg}")
                    self.errors.append(error_msg)
                    return False
                    
        except Exception as e:
            error_msg = f"Error starting camera {camera_id}: {str(e)}"
            print(f"❌ {error_msg}")
            self.errors.append(error_msg)
            return False
            
    async def stop_channel_decode(self, camera_id: str) -> bool:
        """Stop decoding for a single RTSP channel"""
        try:
            if not self.session:
                return False
                
            url = f"{self.config.api_base_url}/api/v1/video-pipeline/decode/stop/"
            data = {'camera_id': camera_id}
            
            async with self.session.post(url, data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"🛑 Stopped decode for camera {camera_id}: {result.get('message', 'Unknown')}")
                    if camera_id in self.active_channels:
                        del self.active_channels[camera_id]
                    return True
                else:
                    error_text = await response.text()
                    print(f"⚠️ Failed to stop camera {camera_id}: HTTP {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            print(f"⚠️ Error stopping camera {camera_id}: {str(e)}")
            return False
            
    async def get_channel_status(self, camera_id: str) -> Optional[Dict]:
        """Get status for a single RTSP channel"""
        try:
            if not self.session:
                return None
                
            url = f"{self.config.api_base_url}/api/v1/video-pipeline/decode/status/"
            params = {'camera_id': camera_id}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return None
                    
        except Exception as e:
            print(f"⚠️ Error getting status for camera {camera_id}: {str(e)}")
            return None
            
    async def update_frame_counts(self):
        """Update total frame count from all active channels"""
        total = 0
        for camera_id in list(self.active_channels.keys()):
            status = await self.get_channel_status(camera_id)
            if status and 'frame_count' in status:
                total += status['frame_count']
                # Update channel status
                if camera_id in self.active_channels:
                    self.active_channels[camera_id]['status'] = status.get('status', 'unknown')
                    self.active_channels[camera_id]['frame_count'] = status.get('frame_count', 0)
                    
        self.total_frames = total
        
    async def monitor_system(self):
        """Monitor system resources and collect metrics"""
        self.monitoring = True
        start_time = time.time()
        
        while self.monitoring:
            try:
                # Update frame counts
                await self.update_frame_counts()
                
                # Collect metrics
                metrics = self.get_system_metrics()
                self.metrics.append(metrics)
                
                # Print current status
                elapsed = time.time() - start_time
                print(f"📊 [{elapsed:.1f}s] CPU: {metrics.cpu_percent:.1f}% | "
                      f"Memory: {metrics.memory_mb:.1f}MB ({metrics.memory_percent:.1f}%) | "
                      f"Channels: {metrics.active_channels} | "
                      f"Frames: {metrics.total_frames}")
                
                if metrics.errors:
                    print(f"⚠️ Errors: {len(metrics.errors)}")
                    
                await asyncio.sleep(self.config.monitor_interval)
                
            except Exception as e:
                print(f"❌ Error in monitoring: {str(e)}")
                await asyncio.sleep(self.config.monitor_interval)
                
    async def run_profiling_test(self):
        """Run the complete profiling test"""
        print(f"🚀 Starting Video Pipeline Profiling Test")
        print(f"📡 API URL: {self.config.api_base_url}")
        print(f"📺 RTSP Channels: {len(self.config.rtsp_urls)}")
        print(f"⏱️ Test Duration: {self.config.test_duration}s")
        print(f"🎬 FPS: {self.config.fps}")
        print(f"🔧 Hardware Acceleration: {self.config.hardware_accel or 'auto'}")
        print(f"📊 Monitor Interval: {self.config.monitor_interval}s")
        print("-" * 80)
        
        # Start monitoring in background
        monitor_task = asyncio.create_task(self.monitor_system())
        
        # Start channels with delay
        start_tasks = []
        for i, rtsp_url in enumerate(self.config.rtsp_urls):
            camera_id = f"camera_{i+1:03d}"
            task = asyncio.create_task(
                self.start_channel_decode(camera_id, rtsp_url)
            )
            start_tasks.append(task)
            
            # Wait before starting next channel
            if i < len(self.config.rtsp_urls) - 1:
                await asyncio.sleep(self.config.channel_start_delay)
                
        # Wait for all channels to start
        start_results = await asyncio.gather(*start_tasks, return_exceptions=True)
        successful_starts = sum(1 for result in start_results if result is True)
        print(f"✅ Successfully started {successful_starts}/{len(self.config.rtsp_urls)} channels")
        
        # Run for specified duration
        print(f"⏳ Running test for {self.config.test_duration} seconds...")
        await asyncio.sleep(self.config.test_duration)
        
        # Stop monitoring
        self.monitoring = False
        await monitor_task
        
        # Stop all channels
        print("🛑 Stopping all channels...")
        stop_tasks = []
        for camera_id in list(self.active_channels.keys()):
            task = asyncio.create_task(self.stop_channel_decode(camera_id))
            stop_tasks.append(task)
            
        if stop_tasks:
            await asyncio.gather(*stop_tasks, return_exceptions=True)
            
        # Save results
        self.save_results()
        
    def save_results(self):
        """Save profiling results to file"""
        try:
            results = {
                'test_config': asdict(self.config),
                'summary': {
                    'total_metrics': len(self.metrics),
                    'test_start': datetime.fromtimestamp(self.metrics[0].timestamp if self.metrics else time.time()).isoformat(),
                    'test_end': datetime.fromtimestamp(self.metrics[-1].timestamp if self.metrics else time.time()).isoformat(),
                    'max_channels': max([m.active_channels for m in self.metrics]) if self.metrics else 0,
                    'max_cpu_percent': max([m.cpu_percent for m in self.metrics]) if self.metrics else 0,
                    'max_memory_mb': max([m.memory_mb for m in self.metrics]) if self.metrics else 0,
                    'total_frames': self.total_frames,
                    'total_errors': len(self.errors)
                },
                'metrics': [asdict(m) for m in self.metrics],
                'errors': self.errors
            }
            
            with open(self.config.output_file, 'w') as f:
                json.dump(results, f, indent=2)
                
            print(f"💾 Results saved to {self.config.output_file}")
            
            # Print summary
            self.print_summary(results['summary'])
            
        except Exception as e:
            print(f"❌ Error saving results: {str(e)}")
            
    def print_summary(self, summary: Dict):
        """Print test summary"""
        print("\n" + "="*80)
        print("📊 PROFILING TEST SUMMARY")
        print("="*80)
        print(f"📈 Total Metrics Collected: {summary['total_metrics']}")
        print(f"🕐 Test Duration: {summary['test_start']} to {summary['test_end']}")
        print(f"📺 Max Active Channels: {summary['max_channels']}")
        print(f"🔥 Max CPU Usage: {summary['max_cpu_percent']:.1f}%")
        print(f"💾 Max Memory Usage: {summary['max_memory_mb']:.1f}MB")
        print(f"🖼️ Total Frames Decoded: {summary['total_frames']}")
        print(f"❌ Total Errors: {summary['total_errors']}")
        print("="*80)

def create_sample_rtsp_urls(count: int) -> List[str]:
    """Create sample RTSP URLs for testing"""
    base_urls = [
        "rtsp://192.168.9.108:8554/stream1",
        "rtsp://192.168.9.108:8554/stream6", 
        "rtsp://192.168.9.108:8554/stream3",
        "rtsp://192.168.9.108:8554/stream3",
        "rtsp://192.168.9.108:8554/stream1",
        "rtsp://192.168.9.108:8554/stream7",
        "rtsp://192.168.9.108:8554/stream7",
        "rtsp://192.168.9.108:8554/stream4",
        "rtsp://192.168.9.108:8554/stream1",
        "rtsp://192.168.9.108:8554/stream6"
    ]
    
    # Cycle through base URLs if more channels requested
    urls = []
    for i in range(count):
        base_url = base_urls[i % len(base_urls)]
        urls.append(base_url)
        
    return urls

def signal_handler(signum, frame):
    """Handle interrupt signals"""
    print("\n🛑 Received interrupt signal. Stopping test...")
    sys.exit(0)

async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Video Pipeline Profiling Test")
    parser.add_argument("--api-url", default="http://localhost:8002", 
                       help="API base URL (default: http://localhost:8002)")
    parser.add_argument("--channels", type=int, default=5,
                       help="Number of RTSP channels to test (default: 5)")
    parser.add_argument("--duration", type=int, default=60,
                       help="Test duration in seconds (default: 60)")
    parser.add_argument("--start-delay", type=float, default=2.0,
                       help="Delay between starting channels in seconds (default: 2.0)")
    parser.add_argument("--fps", type=int, default=1,
                       help="Frames per second to extract (default: 1)")
    parser.add_argument("--hw-accel", choices=["rkmpp", "v4l2", "rga", "none"],
                       help="Force hardware acceleration method")
    parser.add_argument("--output", default="profiling_results.json",
                       help="Output file for results (default: profiling_results.json)")
    parser.add_argument("--monitor-interval", type=float, default=1.0,
                       help="Monitoring interval in seconds (default: 1.0)")
    parser.add_argument("--rtsp-urls", nargs="+",
                       help="Custom RTSP URLs (if not provided, sample URLs will be generated)")
    
    args = parser.parse_args()
    
    # Set up signal handler
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create RTSP URLs
    # if args.rtsp_urls:
    #    rtsp_urls = args.rtsp_urls
    #sselse:

    print(f"Channels: {args.channels}")
    rtsp_urls = create_sample_rtsp_urls(args.channels)
        
    print(f"RTSP URLs: {rtsp_urls}")
    # Create config
    config = TestConfig(
        api_base_url=args.api_url,
        rtsp_urls=rtsp_urls,
        test_duration=args.duration,
        channel_start_delay=args.start_delay,
        fps=args.fps,
        hardware_accel=args.hw_accel,
        output_file=args.output,
        monitor_interval=args.monitor_interval
    )
    
    print(f"Config: {config}    ")
    # Create and run profiler
    profiler = VideoPipelineProfiler(config)
    
    try:
        await profiler.start_session()
        await profiler.run_profiling_test()
    finally:
        await profiler.stop_session()

if __name__ == "__main__":
    asyncio.run(main())
