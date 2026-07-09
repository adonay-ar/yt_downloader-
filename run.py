import sys
import os
import threading
import time
import webbrowser

# Intercept command line calls when yt-dlp is launched in a subprocess inside the frozen executable
if len(sys.argv) > 1 and sys.argv[1] == "--run-ytdl":
    import yt_dlp
    # Remove our custom parameter so yt-dlp receives only its expected arguments
    sys.argv.pop(1)
    sys.exit(yt_dlp.main())

# Add the workspace root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn
from app.main import app

def open_browser():
    # Wait a brief moment for the FastAPI server to initialize
    time.sleep(2.0)
    webbrowser.open("http://127.0.0.1:38282")

if __name__ == "__main__":
    # Start browser thread
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Run Uvicorn server programmatically
    uvicorn.run(app, host="127.0.0.1", port=38282, log_level="info")
