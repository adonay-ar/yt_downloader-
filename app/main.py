import os
import shutil
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any

from app.downloader import (
    get_video_info,
    download_video_async,
    run_oauth2_flow,
    get_cookie_path,
    COOKIE_FILE_PATH
)

app = FastAPI(title="YTDL Premium Downloader API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper Request Models
class InfoRequest(BaseModel):
    url: str

# Endpoints
@app.post("/api/info")
def get_info(req: InfoRequest):
    """Fetches video metadata before download."""
    if not req.url:
        raise HTTPException(status_code=400, detail="URL is required")
    res = get_video_info(req.url)
    if not res.get("success"):
        return JSONResponse(status_code=400, content=res)
    return res

@app.get("/api/cookies/status")
def cookie_status():
    """Returns whether the cookies.txt file exists and its file size."""
    cookie_path = get_cookie_path()
    if cookie_path:
        size_bytes = os.path.getsize(cookie_path)
        size_kb = size_bytes / 1024
        return {
            "active": True,
            "filename": "cookies.txt",
            "size": f"{size_kb:.2f} KB"
        }
    return {"active": False}

@app.post("/api/cookies")
async def upload_cookies(file: UploadFile = File(...)):
    """Uploads cookies.txt file for yt-dlp."""
    if not file.filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="Only standard text files (.txt) are allowed.")
    
    try:
        os.makedirs(os.path.dirname(COOKIE_FILE_PATH), exist_ok=True)
        with open(COOKIE_FILE_PATH, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return {"success": True, "message": "cookies.txt uploaded successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save cookies file: {str(e)}")

@app.delete("/api/cookies")
def delete_cookies():
    """Deletes the active cookies.txt file."""
    if os.path.exists(COOKIE_FILE_PATH):
        try:
            os.remove(COOKIE_FILE_PATH)
            return {"success": True, "message": "cookies.txt deleted successfully."}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete cookies file: {str(e)}")
    return {"success": False, "message": "No active cookies.txt file found."}

@app.get("/api/downloads/list")
def list_downloads() -> List[Dict[str, Any]]:
    """Lists files inside the downloads directory with their sizes."""
    downloads_dir = "/app/downloads"
    if not os.path.exists(downloads_dir):
        return []
    
    files = []
    for f in os.listdir(downloads_dir):
        fp = os.path.join(downloads_dir, f)
        if os.path.isfile(fp):
            size_bytes = os.path.getsize(fp)
            size_mb = size_bytes / (1024 * 1024)
            files.append({
                "name": f,
                "size": f"{size_mb:.2f} MB",
                "path": f"/downloads/{f}"
            })
    # Sort files by name
    files.sort(key=lambda x: x["name"])
    return files

# WebSocket endpoint for real-time progress and OAuth2 login
@app.websocket("/ws/download")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Wait for message from the client
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "start_download":
                url = data.get("url")
                format_id = data.get("format_id", "best")
                
                # Get the running loop for thread-safe scheduling from background thread
                loop = asyncio.get_running_loop()

                # Callback to send download progress updates back to frontend
                async def on_progress(progress_data: Dict[str, Any]):
                    await websocket.send_json({
                        "type": "download_progress",
                        "data": progress_data
                    })

                def sync_on_progress(progress_data: Dict[str, Any]):
                    asyncio.run_coroutine_threadsafe(on_progress(progress_data), loop)

                # Call download runner
                # Run download task in background but await completion
                await websocket.send_json({
                    "type": "download_progress",
                    "data": {"status": "starting", "message": "Preparing yt-dlp download..."}
                })
                
                await download_video_async(url, format_id, sync_on_progress)

            elif msg_type == "start_oauth2":
                # Start OAuth2 authorization flow
                await websocket.send_json({
                    "type": "oauth_status",
                    "data": {"type": "oauth_started", "message": "Launching YouTube OAuth2 device code flow..."}
                })
                
                # Callback to push OAuth2 events to front
                async def on_oauth_status(status_data: Dict[str, Any]):
                    await websocket.send_json({
                        "type": "oauth_status",
                        "data": status_data
                    })
                
                await run_oauth2_flow(on_oauth_status)

    except WebSocketDisconnect:
        print("WebSocket client disconnected.")
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except:
            pass

# Serve static downloads folder directly
app.mount("/downloads", StaticFiles(directory="/app/downloads"), name="downloads")

# Serve UI static folder
# We check if directory exists first
static_dir = "/app/app/static"
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/")
    async def read_index():
        return FileResponse(os.path.join(static_dir, "index.html"))
else:
    # Fallback to local development path if needed
    local_static = "app/static"
    if os.path.exists(local_static):
        app.mount("/static", StaticFiles(directory=local_static), name="static")
        @app.get("/")
        async def read_index():
            return FileResponse(os.path.join(local_static, "index.html"))
