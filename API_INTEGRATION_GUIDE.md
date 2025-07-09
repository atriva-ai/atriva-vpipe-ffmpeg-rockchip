# Video Pipeline API Integration Guide

## Overview

The Video Pipeline service provides FFmpeg-based video processing capabilities for the retail dashboard application. This guide explains how to integrate the video pipeline API with the main dashboard backend while maintaining service independence.

## Architecture

### Current Structure
```
services/video-pipeline/
├── main.py                 # Standalone FastAPI app
├── app/
│   ├── routes.py          # Main API router with prefix and tags
│   ├── services/
│   │   └── ffmpeg_utils.py # Core FFmpeg functionality
│   └── models/
│       └── schemas.py      # Pydantic schemas
└── config.py              # Configuration

dashboard-backend/app/routes/
└── video_pipeline.py      # Integration router
```

## Integration Approaches

### Option 1: Service-to-Service Communication (Recommended)

The video pipeline remains a standalone service, and the main dashboard backend acts as a proxy/API gateway.

**Benefits:**
- Service independence
- Scalability
- Technology isolation
- Easy deployment

**Implementation:**
```python
# dashboard-backend/app/routes/video_pipeline.py
@router.post("/camera/{camera_id}/video-info/")
async def get_camera_video_info(
    camera_id: int,
    video: UploadFile = File(...),
    db: Session = Depends(get_db),
    client: httpx.AsyncClient = Depends(get_video_pipeline_client)
):
    # Verify camera exists in dashboard DB
    camera = camera_crud.get_camera(db, camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    # Forward request to video pipeline service
    files = {"video": (video.filename, video.file, video.content_type)}
    response = await client.post(f"{VIDEO_PIPELINE_URL}/api/v1/video-pipeline/video-info/", files=files)
    return response.json()
```

### Option 2: Direct Integration

Import video pipeline functionality directly into the main backend.

**Benefits:**
- Single deployment
- Lower latency
- Shared database

**Drawbacks:**
- Tight coupling
- Complex dependencies
- Harder to scale independently

## API Endpoints

### Video Pipeline Service (Standalone)
```
POST /api/v1/video-pipeline/video-info/     # Get video metadata
GET  /api/v1/video-pipeline/hw-accel-cap/   # Hardware acceleration info
POST /api/v1/video-pipeline/decode/         # Extract frames
POST /api/v1/video-pipeline/snapshot/       # Capture snapshot
POST /api/v1/video-pipeline/record/         # Record clip
GET  /api/v1/video-pipeline/health/         # Health check
```

### Dashboard Backend Integration
```
GET  /api/v1/video-pipeline/health/                    # Service health
POST /api/v1/video-pipeline/camera/{id}/video-info/    # Camera video info
POST /api/v1/video-pipeline/camera/{id}/decode/        # Camera video decode
POST /api/v1/video-pipeline/camera/{id}/snapshot/      # Camera snapshot
POST /api/v1/video-pipeline/camera/{id}/record/        # Camera recording
GET  /api/v1/video-pipeline/hw-accel-cap/              # Hardware capabilities
```

## Configuration

### Environment Variables
```bash
# Video Pipeline Service URL
VIDEO_PIPELINE_URL=http://video-pipeline:8002

# FFmpeg Configuration
FFMPEG_PATH=ffmpeg
FFPROBE_PATH=ffprobe
HW_ACCEL_OPTIONS=["cuda", "qsv", "vaapi", "none"]
```

### Docker Compose Integration
```yaml
services:
  video-pipeline:
    build: ./services/video-pipeline
    ports:
      - "8002:8002"
    volumes:
      - video_data:/app/videos
      - frame_data:/app/frames
    environment:
      - FFMPEG_PATH=ffmpeg
      - FFPROBE_PATH=ffprobe

  dashboard-backend:
    build: ./dashboard-backend
    ports:
      - "8000:8000"
    environment:
      - VIDEO_PIPELINE_URL=http://video-pipeline:8002
    depends_on:
      - video-pipeline
```

## Usage Examples

### 1. Get Video Information
```bash
curl -X POST "http://localhost:8000/api/v1/video-pipeline/camera/1/video-info/" \
  -H "Content-Type: multipart/form-data" \
  -F "video=@sample.mp4"
```

### 2. Extract Frames
```bash
curl -X POST "http://localhost:8000/api/v1/video-pipeline/camera/1/decode/" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@sample.mp4" \
  -F "fps=5" \
  -F "force_format=cuda"
```

### 3. Capture Snapshot
```bash
curl -X POST "http://localhost:8000/api/v1/video-pipeline/camera/1/snapshot/" \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "rtsp://camera.example.com/stream",
    "timestamp": "00:00:30",
    "output_image": "/app/snapshots/snapshot.jpg"
  }'
```

## Error Handling

The integration router includes comprehensive error handling:

1. **Camera Validation**: Verifies camera exists in dashboard database
2. **Service Health**: Checks video pipeline service availability
3. **Request Forwarding**: Handles communication errors gracefully
4. **Response Processing**: Validates and formats responses

## Security Considerations

1. **Authentication**: Add JWT token validation for camera access
2. **Authorization**: Verify user permissions for camera operations
3. **Input Validation**: Sanitize file uploads and URLs
4. **Rate Limiting**: Implement request throttling
5. **CORS**: Configure cross-origin requests appropriately

## Monitoring and Logging

### Health Checks
```python
@router.get("/health/")
async def video_pipeline_health():
    """Check video pipeline service health"""
    try:
        response = await client.get(f"{VIDEO_PIPELINE_URL}/api/v1/video-pipeline/health/")
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Video pipeline service unavailable: {str(e)}")
```

### Logging
```python
import logging

logger = logging.getLogger(__name__)

@router.post("/camera/{camera_id}/decode/")
async def decode_camera_video(camera_id: int, ...):
    logger.info(f"Processing video decode for camera {camera_id}")
    # ... implementation
```

## Future Enhancements

1. **WebSocket Support**: Real-time video processing status
2. **Batch Processing**: Multiple video processing
3. **Caching**: Frame and metadata caching
4. **Analytics Integration**: Connect with analytics pipeline
5. **Storage Management**: Automatic cleanup of processed files

## Troubleshooting

### Common Issues

1. **Service Unavailable**: Check video-pipeline container status
2. **FFmpeg Errors**: Verify hardware acceleration support
3. **File Permissions**: Ensure proper volume mounts
4. **Network Issues**: Validate service communication

### Debug Commands
```bash
# Check video pipeline service
docker logs video-pipeline

# Test FFmpeg installation
docker exec video-pipeline ffmpeg -version

# Check hardware acceleration
curl http://localhost:8002/api/v1/video-pipeline/hw-accel-cap/
``` 