#!/usr/bin/env python3
"""
Video Pipeline Profiler Launcher
Easy launcher for profiling tools from the root directory
"""

import sys
import os
import subprocess
import argparse

def run_profiler_tool(tool_name, args=None):
    """Run a profiler tool from the profiler directory"""
    profiler_dir = os.path.join(os.path.dirname(__file__), 'profiler')
    tool_path = os.path.join(profiler_dir, tool_name)
    
    if not os.path.exists(tool_path):
        print(f"❌ Tool {tool_name} not found in {profiler_dir}")
        return False
    
    # Change to profiler directory
    original_dir = os.getcwd()
    os.chdir(profiler_dir)
    
    try:
        # Build command
        cmd = [sys.executable, tool_name]
        if args:
            cmd.extend(args)
        
        print(f"🚀 Running: {' '.join(cmd)}")
        print(f"📁 Working directory: {profiler_dir}")
        print("-" * 50)
        
        # Run the tool
        result = subprocess.run(cmd)
        return result.returncode == 0
        
    finally:
        # Restore original directory
        os.chdir(original_dir)

def main():
    parser = argparse.ArgumentParser(description='Video Pipeline Profiler Launcher')
    parser.add_argument('tool', choices=[
        'verify_hw_accel.py',
        'profiler_test_app.py', 
        'analyze_results.py',
        'test_profiler.py',
        'demo_profiler.py',
        'test_ffmpeg_hw.py'
    ], help='Profiler tool to run')
    parser.add_argument('args', nargs=argparse.REMAINDER, help='Arguments to pass to the tool')
    
    args = parser.parse_args()
    
    print("🎯 Video Pipeline Profiler Launcher")
    print("=" * 50)
    
    success = run_profiler_tool(args.tool, args.args)
    
    if success:
        print("\n✅ Tool completed successfully")
        sys.exit(0)
    else:
        print("\n❌ Tool failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
