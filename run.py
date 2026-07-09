import sys
import os
import threading
import time
import webbrowser
import urllib.request

# Fix for PyInstaller --noconsole mode where sys.stdout and sys.stderr are None
if sys.stdout is None:
    sys.stdout = open(os.devnull, 'w')
if sys.stderr is None:
    sys.stderr = open(os.devnull, 'w')

# Intercept command line calls when yt-dlp is launched in a subprocess inside the frozen executable
if len(sys.argv) > 1 and sys.argv[1] == "--run-ytdl":
    import yt_dlp
    # Remove our custom parameter so yt-dlp receives only its expected arguments
    sys.argv.pop(1)
    sys.exit(yt_dlp.main())

# Add the workspace root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def is_server_running() -> bool:
    """Checks if the FastAPI server is already running on port 38282."""
    try:
        url = "http://127.0.0.1:38282/api/update/version"
        with urllib.request.urlopen(url, timeout=1.0) as response:
            return response.status == 200
    except Exception:
        return False

if __name__ == "__main__":
    if is_server_running():
        # Server is already running. Just open the browser and exit immediately.
        webbrowser.open("http://127.0.0.1:38282")
        sys.exit(0)

    # Proceed with normal server startup
    from app.main import app
    import uvicorn

    def open_browser():
        # Wait a brief moment for the FastAPI server to initialize
        time.sleep(2.0)
        webbrowser.open("http://127.0.0.1:38282")

    # Start browser thread
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Run Uvicorn server programmatically
    uvicorn.run(app, host="127.0.0.1", port=38282, log_level="info")
