import os
from pathlib import Path

# FFmpeg executable path
FFMPEG_PATH = "ffmpeg"
FFPROBE_PATH = "ffprobe"

# Hardware acceleration priority ( CUDA / QSV / VAAPI)
HW_ACCEL_OPTIONS = ["cuda", "qsv", "vaapi", "none"]  # Priority order

# Set up paths
UPLOAD_FOLDER = Path("/app/videos")
OUTPUT_FOLDER = Path("/app/frames")
