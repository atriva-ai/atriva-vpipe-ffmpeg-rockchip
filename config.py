import os
from pathlib import Path

# FFmpeg executable path
FFMPEG_PATH = "ffmpeg"
FFPROBE_PATH = "ffprobe"

# Hardware acceleration priority for Rockchip RK3588
# Set to software decoding only
# HW_ACCEL_OPTIONS = ["none"]  # Only software decoding for now
# rkmpp: Rockchip Media Process Platform (hardware video decoder/encoder)
# v4l2: Video4Linux2 hardware acceleration
# rga: Rockchip Graphics Acceleration (for image processing)
# none: Software fallback
HW_ACCEL_OPTIONS = ["rkmpp", "v4l2", "rga", "none"]  # Priority order for RK3588

# Set up paths
UPLOAD_FOLDER = Path("/app/videos")
OUTPUT_FOLDER = Path("/app/frames")
