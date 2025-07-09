# Use nyanmisaka/jellyfin:latest-rockchip as base image for Rockchip hardware acceleration
FROM nyanmisaka/jellyfin:latest-rockchip

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
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]