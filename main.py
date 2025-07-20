from fastapi import FastAPI
from app.routes import router  # Import API routes
from config import UPLOAD_FOLDER, OUTPUT_FOLDER
import logging
# import debugpy

# debugpy.listen(("0.0.0.0", 5678))  # Allow debugger to connect
# print("Waiting for debugger to attach...")
# debugpy.wait_for_client()

# Configure logging to suppress health check logs
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

# Ensure base folder exists
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Video Pipeline API (Rockchip RK3588)", version="1.0")

# Include Routes
app.include_router(router)

@app.get("/")
def root():
    return {"message": "FFMPEG Video Pipeline API is running on Rockchip RK3588!"}
