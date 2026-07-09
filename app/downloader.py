import re
import subprocess
import os
import sys
import asyncio
import yt_dlp
from typing import Callable, Optional, Dict, Any

from app.paths import (
    get_base_dir,
    get_downloads_dir,
    get_cookies_dir,
    get_cookie_file_path
)

# Ensure downloads and cookies directories exist
get_downloads_dir()
get_cookies_dir()

# Define path for cookies file
COOKIE_FILE_PATH = get_cookie_file_path()

def get_cookie_path() -> Optional[str]:
    """Returns the cookie path if the cookie file exists and is not empty."""
    cookie_path = get_cookie_file_path()
    if os.path.exists(cookie_path) and os.path.getsize(cookie_path) > 0:
        return cookie_path
    return None

def format_duration(seconds: Optional[int]) -> str:
    """Formats duration in seconds to MM:SS or HH:MM:SS."""
    if seconds is None:
        return "Unknown"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"

def get_video_info(url: str) -> Dict[str, Any]:
    """Extracts video metadata using yt-dlp."""
    cookie_path = get_cookie_path()
    ydl_opts = {
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'retries': 10,
        'fragment_retries': 10,
        'socket_timeout': 30,
    }
    if cookie_path:
        ydl_opts['cookiefile'] = cookie_path

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            if not info:
                raise ValueError("Could not extract video information.")
            
            # Format list filter: we only want standard video+audio or separate audio formats for representation
            formats = []
            seen_resolutions = set()
            
            # Add general presets
            formats.append({
                'id': 'best',
                'resolution': 'Best Quality (Combined)',
                'ext': 'mp4',
                'note': 'Highest resolution video with audio merged'
            })
            formats.append({
                'id': 'bestaudio/best',
                'resolution': 'Audio Only (MP3/M4A)',
                'ext': 'mp3',
                'note': 'Extract audio at best bitrate'
            })

            # Extract actual formats available
            raw_formats = info.get('formats', [])
            for f in raw_formats:
                height = f.get('height')
                ext = f.get('ext')
                # Filter formats to standard readable ones
                if height and height >= 360 and ext == 'mp4':
                    res_str = f"{height}p"
                    if res_str not in seen_resolutions:
                        seen_resolutions.add(res_str)
                        formats.append({
                            'id': f.get('format_id'),
                            'resolution': f"{res_str} (MP4)",
                            'ext': ext,
                            'note': f.get('format_note', 'Standard Video')
                        })

            return {
                'success': True,
                'title': info.get('title'),
                'duration': format_duration(info.get('duration')),
                'thumbnail': info.get('thumbnail'),
                'channel': info.get('uploader'),
                'views': info.get('view_count', 0),
                'formats': formats
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

async def download_video_async(url: str, format_id: str, progress_callback: Callable[[Dict[str, Any]], None]):
    """Downloads video using yt-dlp python API with a progress hook."""
    cookie_path = get_cookie_path()
    
    # Base options
    ydl_opts = {
        'outtmpl': os.path.join(get_downloads_dir(), '%(title)s.%(ext)s'),
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'retries': 10,
        'fragment_retries': 10,
        'socket_timeout': 30,
    }

    # Check for local ffmpeg in the base directory
    base_dir = get_base_dir()
    ffmpeg_exe = "ffmpeg.exe" if sys.platform.startswith("win") else "ffmpeg"
    local_ffmpeg = os.path.join(base_dir, ffmpeg_exe)
    if os.path.exists(local_ffmpeg):
        ydl_opts['ffmpeg_location'] = local_ffmpeg

    if cookie_path:
        ydl_opts['cookiefile'] = cookie_path

    # Configure formats
    if format_id == 'best':
        # yt-dlp default best video + best audio
        ydl_opts['format'] = 'bestvideo+bestaudio/best'
        ydl_opts['merge_output_format'] = 'mp4'
    elif format_id == 'bestaudio/best':
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    else:
        # Download specific format and merge with best audio for full video
        ydl_opts['format'] = f"{format_id}+bestaudio/best"
        ydl_opts['merge_output_format'] = 'mp4'

    # Progress Hook definition
    def progress_hook(d):
        if d['status'] == 'downloading':
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            downloaded = d.get('downloaded_bytes', 0)
            
            percent = 0.0
            if total_bytes > 0:
                percent = (downloaded / total_bytes) * 100
                
            speed = d.get('speed')  # bytes/sec
            speed_str = "0 B/s"
            if speed:
                if speed > 1024 * 1024:
                    speed_str = f"{speed / (1024*1024):.2f} MiB/s"
                elif speed > 1024:
                    speed_str = f"{speed / 1024:.2f} KiB/s"
                else:
                    speed_str = f"{speed} B/s"

            eta = d.get('eta')
            eta_str = "Calculating..."
            if eta is not None:
                eta_str = f"{eta}s"

            # Clean filename
            filename = os.path.basename(d.get('filename', ''))
            
            progress_callback({
                'status': 'downloading',
                'percent': f"{percent:.1f}",
                'speed': speed_str,
                'eta': eta_str,
                'filename': filename
            })
        elif d['status'] == 'finished':
            filename = os.path.basename(d.get('filename', ''))
            progress_callback({
                'status': 'merging',
                'filename': filename,
                'message': 'Post-processing/Merging video and audio layers...'
            })

    ydl_opts['progress_hooks'] = [progress_hook]

    # Run in standard thread pool to keep asyncio event loop unblocked
    def run_dl():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

    try:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, run_dl)
        progress_callback({
            'status': 'completed',
            'message': 'Download completed successfully!'
        })
    except Exception as e:
        progress_callback({
            'status': 'failed',
            'error': str(e)
        })

async def run_oauth2_flow(ws_send_callback: Callable[[Dict[str, Any]], Any]):
    """Runs yt-dlp in a subprocess to trigger and wait for YouTube OAuth2 flow."""
    # We use a dummy link to trigger authentication, --skip-download avoids downloading the video
    if getattr(sys, 'frozen', False):
        # In frozen executable, we invoke our own executable with --run-ytdl
        cmd = [
            sys.executable,
            "--run-ytdl",
            "--username", "oauth2",
            "--password", "",
            "--skip-download",
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        ]
    else:
        # In python environment, run yt_dlp package directly
        cmd = [
            sys.executable,
            "-m", "yt_dlp",
            "--username", "oauth2",
            "--password", "",
            "--skip-download",
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        ]
    
    try:
        # Create subprocess and read lines asynchronously
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        
        auth_url = None
        auth_code = None
        
        while True:
            line_bytes = await process.stdout.readline()
            if not line_bytes:
                break
                
            line = line_bytes.decode('utf-8', errors='ignore').strip()
            print(f"[OAuth Subprocess] {line}")
            
            # Check for oauth device login instruction
            # Example: [youtube+oauth2] To sign in, use a web browser to open the page https://google.com/device and enter the code ABCD-EFGH
            if "To sign in, use a web browser" in line:
                # Match URL and Code using Regex
                url_match = re.search(r'https?://[^\s]+', line)
                code_match = re.search(r'enter the code\s+([A-Z0-9-]+)', line)
                
                if url_match and code_match:
                    auth_url = url_match.group(0)
                    auth_code = code_match.group(1)
                    
                    await ws_send_callback({
                        'type': 'oauth_prompt',
                        'url': auth_url,
                        'code': auth_code,
                        'message': 'Please visit the Google device login URL and paste the authentication code.'
                    })
            
            elif "Authorization successful" in line or "Saving token to cache" in line:
                await ws_send_callback({
                    'type': 'oauth_success',
                    'message': 'YouTube OAuth2 authentication successful! Tokens cached successfully.'
                })
        
        # Wait for process to fully exit
        exit_code = await process.wait()
        
        if exit_code == 0:
            await ws_send_callback({
                'type': 'oauth_finished',
                'message': 'Authentication process completed.'
            })
        else:
            await ws_send_callback({
                'type': 'oauth_failed',
                'message': f'Authentication process exited with error code {exit_code}.'
            })
            
    except Exception as e:
        await ws_send_callback({
            'type': 'oauth_failed',
            'message': f'Failed to run authentication flow: {str(e)}'
        })
