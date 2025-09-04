# Use nyanmisaka/jellyfin:latest-rockchip as base image for Rockchip hardware acceleration
FROM nyanmisaka/jellyfin:latest-rockchip

# Remove Jellyfin media server components
RUN rm -rf /jellyfin /etc/services.d/jellyfin /etc/cont-init.d/*jellyfin* /etc/s6-overlay/s6-rc.d/user/contents.d/jellyfin

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Create a working directory
WORKDIR /app

# Copy application files
COPY . /app

# Ensure following directories exist (for volume mounting)
# RUN mkdir -p /app/recording && chmod -R 777 /app/recording
# VOLUME ["/app/recording"]
# RUN mkdir -p /app/snapshots && chmod -R 777 /app/snapshots
# VOLUME ["/app/snapshots"]

# Install python3, python3-venv, and python3-pip for Debian-based Rockchip ARM
# Some mirrors have Release files that are "not valid yet" if the container clock differs.
# Disable APT date validation during update to avoid build failures.
RUN apt-get -o Acquire::Check-Valid-Until=false -o Acquire::Check-Date=false update && apt-get install -y \
    python3 \
    python3-venv \
    python3-pip \
    curl \
    procps \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Create a virtual environment
RUN python3 -m venv /app/venv

# Activate virtual environment
ENV PATH="/app/venv/bin:$PATH"

# Copy requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Expose FastAPI port
EXPOSE 8002

# Create a base image label
LABEL description="Production image with Python 3.12, FastAPI, and FFmpeg with Rockchip hardware acceleration"

# Command to run the FastAPI app
ENTRYPOINT ["python", "-m", "uvicorn"]
CMD ["main:app", "--host", "0.0.0.0", "--port", "8002"]

ENV PATH="/usr/lib/jellyfin-ffmpeg:$PATH"