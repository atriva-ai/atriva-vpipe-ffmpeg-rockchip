import subprocess, json
from config import FFMPEG_PATH, FFPROBE_PATH, HW_ACCEL_OPTIONS, OUTPUT_FOLDER
from pathlib import Path

def get_video_info(input_url: str):
    """Retrieve video format, resolution, frame rate, codec, etc. using ffmpeg to decode first frame."""
    # Use ffmpeg to decode just the first frame and get stream info
    if input_url.startswith('rtsp://'):
        command = [
            FFMPEG_PATH, "-rtsp_transport", "tcp", "-i", input_url,
            "-frames:v", "1",  # Decode only 1 frame
            "-f", "null", "-"  # Output to null (discard the frame)
        ]
    else:
        command = [
            FFMPEG_PATH, "-i", input_url,
            "-frames:v", "1",  # Decode only 1 frame
            "-f", "null", "-"  # Output to null (discard the frame)
        ]
    
    try:
        print(f"Running command: {command}")
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        
        # Parse the ffmpeg output to extract stream information
        output_lines = result.stderr.split('\n')  # ffmpeg info goes to stderr
        
        video_info = {
            "format": "unknown",
            "codec": "unknown",
            "width": "unknown",
            "height": "unknown",
            "fps": 0.0,
            "duration": 0.0
        }
        
        # Parse stream information from ffmpeg output
        for line in output_lines:
            line = line.strip()
            
            # Extract codec information
            if "Stream #0:0: Video:" in line:
                # Example: Stream #0:0: Video: mpeg4, yuv420p(tv, progressive), 640x480 [SAR 1:1 DAR 4:3], q=2-31, 200 kb/s, 1 fps, 90k tbn
                parts = line.split(',')
                if len(parts) >= 3:
                    # Extract codec
                    codec_part = parts[0].split(':')[-1].strip()
                    video_info["codec"] = codec_part.split()[0] if codec_part else "unknown"
                    
                    # Extract resolution
                    resolution_part = parts[2].strip()
                    if 'x' in resolution_part:
                        try:
                            width, height = resolution_part.split('x')
                            video_info["width"] = int(width)
                            video_info["height"] = int(height.split()[0])  # Remove any trailing text
                        except (ValueError, IndexError):
                            pass
                    
                    # Extract frame rate
                    for part in parts:
                        if 'fps' in part:
                            try:
                                fps_str = part.split()[0]  # Get the fps value
                                video_info["fps"] = float(fps_str)
                            except (ValueError, IndexError):
                                pass
                            break
            
            # Extract format information
            elif "Input #0" in line and "from" in line:
                # Example: Input #0, lavfi, from 'testsrc=duration=3600:size=640x480:rate=1':
                if "rtsp" in line.lower():
                    video_info["format"] = "rtsp"
                elif "lavfi" in line:
                    video_info["format"] = "lavfi"
                else:
                    video_info["format"] = "unknown"
        
        print(f"Stream info: {video_info}")
        return video_info
        
    except subprocess.CalledProcessError as e:
        print(f"Error extracting video info: {str(e)}")
        print(f"ffmpeg stderr: {e.stderr}")
        return {"error": f"Failed to get video info: {str(e)}"}
    except Exception as e:
        print(f"Error extracting video info: {str(e)}")
        return {"error": f"Failed to get video info: {str(e)}"}

def get_all_hwaccel():
    """Check available hardware acceleration options on an x86 platform"""
    command = [FFMPEG_PATH, "-hwaccels"]

    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, text=True, check=True)
        hw_accels = result.stdout.strip().split("\n")[1:]  # Ignore the first line
    except subprocess.CalledProcessError:
        hw_accels = []

    print(f"Hardware acceleration: {hw_accels}")
    return {"available_hw_accelerations": hw_accels}

def get_best_hwaccel(force_format=None):
    """Check available hardware acceleration and return the best option for Rockchip RK3588."""
    if force_format and force_format in HW_ACCEL_OPTIONS:
        return force_format  # Use the forced format if specified and valid
    
    # Test Rockchip hardware acceleration options in priority order
    for accel in HW_ACCEL_OPTIONS:
        if accel == "none":
            print(f"✅ Using software decoding (none)")
            return "none"
        try:
            # Test if the hardware acceleration works by running a simple ffmpeg probe
            test_command = [
                FFMPEG_PATH, "-hwaccel", accel, "-f", "lavfi", "-i", "nullsrc", "-frames:v", "1", "-f", "null", "-"
            ]
            result = subprocess.run(test_command, capture_output=True, text=True)

            # A working hwaccel should return success (exit code 0)
            if result.returncode == 0:
                print(f"✅ {accel} is supported on RK3588!")
                return accel
            else:
                print(f"❌ {accel} test failed: {result.stderr}")
        except FileNotFoundError:
            print(f"❌ {accel} not available")
            continue
    
    # If no hardware acceleration works, fall back to software decoding
    print(f"⚠️ No hardware acceleration available, using software decoding")
    return "none"

def decode_video2frames_in_jpeg(input_path: str, output_path: str, force_format: str = "none", fps: int = 1, camera_id: str = None):
    """Decode video and extract frames as JPEG at specified FPS using Rockchip RK3588 hardware acceleration."""
    hw_accel = get_best_hwaccel(force_format)
    print(f"Transcoding videos to JPEGs using RK3588 HW mode: {hw_accel}")
    
    # get video info
    print(f"Getting video info from input: {input_path}")
    v_info = get_video_info(input_path)
    print(f"Video format: {v_info['format']}, codec: {v_info['codec']}, width: {v_info['width']}, height: {v_info['height']}, fps: {v_info['fps']}")

    # Use camera_id for output folder if provided, otherwise use video name
    if camera_id:
        video_output_folder = OUTPUT_FOLDER / camera_id
        video_name = camera_id
    else:
        # Fallback to original behavior for backward compatibility
        video_name = Path(input_path).stem  # Extract filename without extension
        video_output_folder = OUTPUT_FOLDER / video_name
    
    print(f"Creating output frames folder: {video_output_folder}")
    video_output_folder.mkdir(parents=True, exist_ok=True)

    # Naming format: <video_file_name>_<time_in_seconds_from_0>_<Nth-frame-in-a-second>.jpg
    output_template = str(video_output_folder / f"{video_name}_%04d.jpg")
    print(f"Output template: {output_template}")

    # Build command with Rockchip-specific hardware acceleration support
    if hw_accel == "none":
        if input_path.startswith('rtsp://'):
            command = [
                FFMPEG_PATH, "-rtsp_transport", "tcp", "-i", input_path,
                "-vf", f"fps={fps},format=rgb24",
                output_template
            ]
        else:
            command = [
                FFMPEG_PATH, "-i", input_path,
                "-vf", f"fps={fps},format=rgb24",
                output_template
            ]
    elif hw_accel == "rkmpp":
        # Use Rockchip MPP hardware acceleration
        if input_path.startswith('rtsp://'):
            command = [
                FFMPEG_PATH, "-hwaccel", "rkmpp", "-rtsp_transport", "tcp", "-i", input_path,
                "-vf", f"fps={fps},format=rgb24",
                output_template
            ]
        else:
            command = [
                FFMPEG_PATH, "-hwaccel", "rkmpp", "-i", input_path,
                "-vf", f"fps={fps},format=rgb24",
                output_template
            ]
    elif hw_accel == "v4l2":
        # Use Video4Linux2 hardware acceleration
        if input_path.startswith('rtsp://'):
            command = [
                FFMPEG_PATH, "-hwaccel", "v4l2", "-rtsp_transport", "tcp", "-i", input_path,
                "-vf", f"fps={fps},format=rgb24",
                output_template
            ]
        else:
            command = [
                FFMPEG_PATH, "-hwaccel", "v4l2", "-i", input_path,
                "-vf", f"fps={fps},format=rgb24",
                output_template
            ]
    elif hw_accel == "rga":
        # Use Rockchip RGA for image processing acceleration
        if input_path.startswith('rtsp://'):
            command = [
                FFMPEG_PATH, "-rtsp_transport", "tcp", "-i", input_path,
                "-vf", f"fps={fps},format=rgb24,rga=format=rgb24",
                output_template
            ]
        else:
            command = [
                FFMPEG_PATH, "-i", input_path,
                "-vf", f"fps={fps},format=rgb24,rga=format=rgb24",
                output_template
            ]
    else:
        # Fallback to software decoding
        if input_path.startswith('rtsp://'):
            command = [
                FFMPEG_PATH, "-rtsp_transport", "tcp", "-i", input_path,
                "-vf", f"fps={fps},format=rgb24",
                output_template
            ]
        else:
            command = [
                FFMPEG_PATH, "-i", input_path,
                "-vf", f"fps={fps},format=rgb24",
                output_template
            ]
    print(f"Running RK3588 FFmpeg command: {command}")

    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg error: {result.stderr}")

    return str(video_output_folder)

def capture_snapshot(input_url: str, timestamp: str, output_image: str):
    """Capture image snapshot at a given timestamp"""
    if input_url.startswith('rtsp://'):
        command = [
            FFMPEG_PATH, "-rtsp_transport", "tcp", "-i", input_url, "-ss", timestamp,
            "-frames:v", "1", output_image
        ]
    else:
        command = [
            FFMPEG_PATH, "-i", input_url, "-ss", timestamp,
            "-frames:v", "1", output_image
        ]
    return subprocess.run(command, capture_output=True, text=True)

def record_clip(input_url: str, start_time: str, duration: str, output_path: str):
    """Record a video clip from a given timestamp and duration"""
    if input_url.startswith('rtsp://'):
        command = [
            FFMPEG_PATH, "-rtsp_transport", "tcp", "-i", input_url, "-ss", start_time,
            "-t", duration, "-c:v", "copy", "-c:a", "copy", output_path
        ]
    else:
        command = [
            FFMPEG_PATH, "-i", input_url, "-ss", start_time,
            "-t", duration, "-c:v", "copy", "-c:a", "copy", output_path
        ]
    return subprocess.run(command, capture_output=True, text=True)
