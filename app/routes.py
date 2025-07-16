from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from typing import Optional, Dict
from pathlib import Path
from app.services.ffmpeg_utils import decode_video2frames_in_jpeg, capture_snapshot, record_clip, get_video_info, get_all_hwaccel
from app.models.schemas import SnapshotRequest, RecordRequest
from config import UPLOAD_FOLDER, OUTPUT_FOLDER
import requests
import subprocess
import os
import threading
import shutil
import time
from fastapi.responses import FileResponse

# Create router with prefix and tags for better organization
router = APIRouter(
    prefix="/api/v1/video-pipeline",
    tags=["Video Pipeline"]
)

UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)  # Ensure the folder exists
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

# Global decode task manager
# Structure: { camera_id: { 'process': Popen, 'output_folder': str, 'status': str, 'last_error': str|None } }
decode_tasks: Dict[str, dict] = {}
task_lock = threading.Lock()

def cleanup_camera_frames(camera_id: str):
    """Clean up all frames for a specific camera"""
    try:
        camera_folder = OUTPUT_FOLDER / camera_id
        if camera_folder.exists():
            # Remove all .jpg files in the camera folder
            for file in camera_folder.glob("*.jpg"):
                file.unlink()
            print(f"Cleaned up frames for camera {camera_id}")
    except Exception as e:
        print(f"Error cleaning up frames for camera {camera_id}: {e}")

def cleanup_orphaned_frames():
    """Clean up frames for cameras that no longer exist in decode_tasks"""
    try:
        # Get all camera folders
        for camera_folder in OUTPUT_FOLDER.iterdir():
            if camera_folder.is_dir():
                camera_id = camera_folder.name
                # Check if this camera is still in active decode tasks
                with task_lock:
                    if camera_id not in decode_tasks or decode_tasks[camera_id]['status'] == 'stopped':
                        # Camera is not active, clean up its frames
                        cleanup_camera_frames(camera_id)
    except Exception as e:
        print(f"Error cleaning up orphaned frames: {e}")

def download_video(url: str, save_path: Path):
    """Download a video file from a given URL and save it locally."""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Ensure the request was successful

        with save_path.open("wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return save_path
    except requests.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Failed to download video: {str(e)}")

@router.post("/video-info/")
async def video_info(video: UploadFile = File(...)):
    """Get video metadata and information"""
    file_path = UPLOAD_FOLDER / video.filename
    print('Getting video file: {file_path}')
    # Save the uploaded file
    with file_path.open("wb") as buffer:
        buffer.write(await video.read())
    print(f"File uploaded successfully to {str(file_path)}")
    print("Getting video info...")
    info = get_video_info(file_path)
    if info["codec"]:
        return {"message": "Video information retrieved", "info": info}
    raise HTTPException(status_code=500, detail="Could not retrieve video information")

@router.post("/video-info-url/")
async def video_info_url(url: str = Form(...)):
    """Get video metadata and information from URL"""
    print(f"Getting video info from URL: {url}")
    info = get_video_info(url)
    if info.get("codec") and "error" not in info:
        return {"message": "Video information retrieved", "info": info}
    raise HTTPException(status_code=500, detail=f"Could not retrieve video information: {info.get('error', 'Unknown error')}")

@router.get("/hw-accel-cap/")
async def hw_accel_cap():
    """Check available hardware acceleration options"""
    result = get_all_hwaccel()
    return {"message": result}

def get_frame_count(output_folder):
    try:
        return len([f for f in os.listdir(output_folder) if f.endswith('.jpg')])
    except Exception:
        return 0

def is_process_running(proc):
    return proc and proc.poll() is None

@router.post("/decode/")
async def decode_video(
    camera_id: str = Form(...),
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = Form(None),
    fps: Optional[int] = Form(1),
    force_format: Optional[str] = Form(None)
):
    print(f"[DEBUG] /decode/ called with camera_id={camera_id}, url={url}, fps={fps}, force_format={force_format}, file={'provided' if file else 'none'}")
    """Start decoding for a camera and register the process."""
    if not file and not url:
        raise HTTPException(status_code=400, detail="Either a file or a URL must be provided.")

    # Check if a decode task already exists for this camera
    with task_lock:
        existing_task = decode_tasks.get(camera_id)
        if existing_task and existing_task['process'] and is_process_running(existing_task['process']):
            return {
                "message": "Decoding already running", 
                "camera_id": camera_id, 
                "output_folder": existing_task['output_folder'],
                "status": "already_running"
            }
        elif existing_task and existing_task['status'] == 'running':
            return {
                "message": "Decoding already running", 
                "camera_id": camera_id, 
                "output_folder": existing_task['output_folder'],
                "status": "already_running"
            }

    # Prepare input
    if file:
        input_path = UPLOAD_FOLDER / file.filename
        print(f"Decoding video file: {input_path}")
        with input_path.open("wb") as buffer:
            buffer.write(await file.read())
    elif url:
        print(f"Decoding video URL: {url}")
        input_path = url

    # Prepare output folder for this camera
    output_folder = OUTPUT_FOLDER / camera_id
    output_folder.mkdir(parents=True, exist_ok=True)

    # Clean up any existing frames for this camera before starting new decode
    cleanup_camera_frames(camera_id)

    try:
        print(f"[DEBUG] Starting decode task for camera_id={camera_id}")
        # Run ffmpeg decode asynchronously in a subprocess
        print(f"Starting decode for camera {camera_id} with input: {input_path}")
        
        # Build ffmpeg command with Rockchip hardware acceleration
        input_path_str = str(input_path)
        
        # Get the best hardware acceleration for RK3588
        from app.services.ffmpeg_utils import get_best_hwaccel
        hw_accel = get_best_hwaccel(force_format)
        print(f"Using RK3588 hardware acceleration: {hw_accel}")
        
        if input_path_str.startswith('rtsp://'):
            if hw_accel == "rkmpp":
                ffmpeg_cmd = [
                    "ffmpeg", "-hwaccel", "rkmpp", "-rtsp_transport", "tcp", "-i", input_path_str,
                    "-vf", f"fps={fps},format=rgb24",
                    f"{output_folder}/frame_%04d.jpg"
                ]
            elif hw_accel == "v4l2":
                ffmpeg_cmd = [
                    "ffmpeg", "-hwaccel", "v4l2", "-rtsp_transport", "tcp", "-i", input_path_str,
                    "-vf", f"fps={fps},format=rgb24",
                    f"{output_folder}/frame_%04d.jpg"
                ]
            elif hw_accel == "rga":
                ffmpeg_cmd = [
                    "ffmpeg", "-rtsp_transport", "tcp", "-i", input_path_str,
                    "-vf", f"fps={fps},format=rgb24,rga=format=rgb24",
                    f"{output_folder}/frame_%04d.jpg"
                ]
            else:
                ffmpeg_cmd = [
                    "ffmpeg", "-rtsp_transport", "tcp", "-i", input_path_str,
                    "-vf", f"fps={fps},format=rgb24",
                    f"{output_folder}/frame_%04d.jpg"
                ]
        else:
            if hw_accel == "rkmpp":
                ffmpeg_cmd = [
                    "ffmpeg", "-hwaccel", "rkmpp", "-i", input_path_str,
                    "-vf", f"fps={fps},format=rgb24",
                    f"{output_folder}/frame_%04d.jpg"
                ]
            elif hw_accel == "v4l2":
                ffmpeg_cmd = [
                    "ffmpeg", "-hwaccel", "v4l2", "-i", input_path_str,
                    "-vf", f"fps={fps},format=rgb24",
                    f"{output_folder}/frame_%04d.jpg"
                ]
            elif hw_accel == "rga":
                ffmpeg_cmd = [
                    "ffmpeg", "-i", input_path_str,
                    "-vf", f"fps={fps},format=rgb24,rga=format=rgb24",
                    f"{output_folder}/frame_%04d.jpg"
                ]
            else:
                ffmpeg_cmd = [
                    "ffmpeg", "-i", input_path_str,
                    "-vf", f"fps={fps},format=rgb24",
                    f"{output_folder}/frame_%04d.jpg"
                ]
        
        print(f"Running RK3588 FFmpeg command: {ffmpeg_cmd}")
        proc = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Register the task as running
        with task_lock:
            decode_tasks[camera_id] = {
                'process': proc,
                'output_folder': str(output_folder),
                'status': 'running',
                'last_error': None
            }
        
        print(f"Decode started for camera {camera_id}, process PID: {proc.pid}")
        return {
            "message": "Decoding started", 
            "camera_id": camera_id, 
            "output_folder": str(output_folder),
            "status": "started"
        }
        
    except Exception as e:
        error_msg = f"Failed to start decode: {str(e)}"
        print(f"Error in decode for camera {camera_id}: {error_msg}")
        with task_lock:
            decode_tasks[camera_id] = {
                'process': None,
                'output_folder': str(output_folder),
                'status': 'error',
                'last_error': error_msg
            }
        raise HTTPException(status_code=500, detail=error_msg)

@router.post("/decode/stop/")
async def stop_decode(camera_id: str = Form(...)):
    """Stop decoding for a camera."""
    with task_lock:
        task = decode_tasks.get(camera_id)
        if not task:
            raise HTTPException(status_code=404, detail="No decode task found for this camera.")
        
        proc = task['process']
        if proc is None:
            # Synchronous decode completed - just mark as stopped
            task['status'] = 'stopped'
            print(f"Marked synchronous decode task as stopped for camera {camera_id}")
            # Clean up frames when stopping
            cleanup_camera_frames(camera_id)
            return {"message": "Decoding stopped", "camera_id": camera_id}
        
        # Handle subprocess-based decoding
        if is_process_running(proc):
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        task['status'] = 'stopped'
        
        # Clean up frames when stopping
        cleanup_camera_frames(camera_id)
        return {"message": "Decoding stopped", "camera_id": camera_id}

@router.get("/decode/status/")
async def decode_status(camera_id: str):
    """Get the status of the decode task for a camera."""
    with task_lock:
        task = decode_tasks.get(camera_id)
        if not task:
            return {"camera_id": camera_id, "status": "not_started", "frame_count": 0}
        
        proc = task['process']
        if proc is None:
            # No process (error or not started)
            frame_count = get_frame_count(task['output_folder'])
            return {
                "camera_id": camera_id,
                "status": task['status'],
                "frame_count": frame_count,
                "last_error": task.get('last_error')
            }
        
        # Check if subprocess is still running
        running = is_process_running(proc)
        frame_count = get_frame_count(task['output_folder'])
        
        # Update status if process completed
        if not running and task['status'] == 'running':
            return_code = proc.poll()
            if return_code == 0:
                task['status'] = 'completed'
                print(f"Decode process completed successfully for camera {camera_id}")
            else:
                task['status'] = 'error'
                task['last_error'] = f"Process exited with code {return_code}"
                print(f"Decode process failed for camera {camera_id} with code {return_code}")
        
        return {
            "camera_id": camera_id,
            "status": task['status'],
            "frame_count": frame_count,
            "last_error": task.get('last_error')
        }

@router.post("/snapshot/")
async def snapshot(request: SnapshotRequest):
    """Capture a snapshot from video at specified timestamp"""
    result = capture_snapshot(request.video_url, request.timestamp, request.output_image)
    if result.returncode == 0:
        return {"message": "Snapshot captured", "output": request.output_image}
    raise HTTPException(status_code=500, detail=result.stderr)

@router.post("/record/")
async def record(request: RecordRequest):
    """Record a video clip from specified start time and duration"""
    result = record_clip(request.video_url, request.start_time, request.duration, request.output_path)
    if result.returncode == 0:
        return {"message": "Recording successful", "output": request.output_path}
    raise HTTPException(status_code=500, detail=result.stderr)

# Health check endpoint
@router.get("/health/")
async def health_check():
    """Health check for video pipeline service"""
    return {"status": "healthy", "service": "video-pipeline"}

# Debug endpoint
@router.get("/debug/")
async def debug_info():
    """Debug information for video pipeline service on Rockchip RK3588"""
    import socket
    import os
    from app.services.ffmpeg_utils import get_all_hwaccel, get_best_hwaccel
    
    # Get hardware acceleration information
    hw_accel_info = get_all_hwaccel()
    best_hw_accel = get_best_hwaccel()
    
    return {
        "status": "running",
        "service": "video-pipeline",
        "platform": "Rockchip RK3588",
        "hostname": socket.gethostname(),
        "port": 8002,
        "hardware_acceleration": {
            "available": hw_accel_info.get("available_hw_accelerations", []),
            "best_option": best_hw_accel,
            "rk3588_options": ["rkmpp", "v4l2", "rga", "none"]
        },
        "environment": {
            "FFMPEG_PATH": os.getenv("FFMPEG_PATH", "ffmpeg"),
            "FFPROBE_PATH": os.getenv("FFPROBE_PATH", "ffprobe")
        }
    }

@router.post("/cleanup/")
async def cleanup_frames(camera_id: Optional[str] = Form(None)):
    """Clean up frames for a specific camera or all orphaned frames"""
    if camera_id:
        cleanup_camera_frames(camera_id)
        return {"message": f"Cleaned up frames for camera {camera_id}"}
    else:
        cleanup_orphaned_frames()
        return {"message": "Cleaned up all orphaned frames"}

@router.get("/latest-frame/")
async def get_latest_frame(camera_id: str):
    """Get the latest decoded frame for a camera"""
    with task_lock:
        task = decode_tasks.get(camera_id)
        if not task:
            raise HTTPException(status_code=404, detail="No decode task found for this camera.")
        
        output_folder = Path(task['output_folder'])
        if not output_folder.exists():
            raise HTTPException(status_code=500, detail="Output folder does not exist for this camera.")
        
        frame_count = get_frame_count(output_folder)
        if frame_count == 0:
            raise HTTPException(status_code=500, detail="No frames found in the output folder for this camera.")
        
        latest_frame_path = output_folder / f"frame_{frame_count - 1:04d}.jpg"
        if not latest_frame_path.exists():
            raise HTTPException(status_code=500, detail="Latest frame does not exist in the output folder for this camera.")
        
        # Check if the latest frame is too old (more than 5 minutes)
        current_time = time.time()
        frame_mtime = latest_frame_path.stat().st_mtime
        if current_time - frame_mtime > 300:  # 5 minutes = 300 seconds
            print(f"Warning: Latest frame for camera {camera_id} is too old ({current_time - frame_mtime:.1f}s), cleaning up")
            cleanup_camera_frames(camera_id)
            raise HTTPException(status_code=500, detail="Latest frame is too old, frames have been cleaned up")
        
        return FileResponse(latest_frame_path)