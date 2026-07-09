import os
import sys

def get_base_dir() -> str:
    """Returns the base directory of the application."""
    if getattr(sys, 'frozen', False):
        # Running inside PyInstaller bundle
        # User downloads and cookies are saved next to the executable
        return os.path.dirname(sys.executable)
    # Running in normal Python environment
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    # If parent_dir is root or doesn't exist, fallback to docker style /app
    if not parent_dir or parent_dir == '/' or not os.path.exists(parent_dir):
        return "/app"
    return parent_dir

def get_downloads_dir() -> str:
    """Returns the path to the downloads directory."""
    path = os.path.join(get_base_dir(), "downloads")
    os.makedirs(path, exist_ok=True)
    return path

def get_cookies_dir() -> str:
    """Returns the path to the cookies directory."""
    path = os.path.join(get_base_dir(), "cookies")
    os.makedirs(path, exist_ok=True)
    return path

def get_cookie_file_path() -> str:
    """Returns the path to the cookies.txt file."""
    return os.path.join(get_cookies_dir(), "cookies.txt")

def get_static_dir() -> str:
    """Returns the path to the static files directory."""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # For PyInstaller single-file bundle, static resources are inside sys._MEIPASS
        return os.path.join(sys._MEIPASS, 'app', 'static')
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    local_static = os.path.join(current_dir, 'static')
    if os.path.exists(local_static):
        return local_static
    return "/app/app/static"

def get_version_file_path() -> str:
    """Returns the path to the version.txt file."""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # In frozen executable, version.txt is bundled
        return os.path.join(sys._MEIPASS, 'app', 'version.txt')
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, 'version.txt')
