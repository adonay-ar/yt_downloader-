import os
import shutil
import urllib.request
import zipfile
import json
import sys
import platform
import tempfile
import subprocess
from app.paths import get_base_dir, get_version_file_path

def get_current_version():
    version_file = get_version_file_path()
    if os.path.exists(version_file):
        try:
            with open(version_file, "r", encoding="utf-8") as f:
                return f.read().strip()
        except:
            pass
    return "1.0.0"

def compare_versions(v1: str, v2: str) -> bool:
    """Returns True if v2 > v1."""
    try:
        t1 = tuple(map(int, v1.split('.')))
        t2 = tuple(map(int, v2.split('.')))
        return t2 > t1
    except Exception:
        # Fallback to simple equality if format is non-standard
        return v2 != v1

def check_for_updates(update_url: str):
    current = get_current_version()
    try:
        req = urllib.request.Request(
            update_url, 
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            remote_version = data.get("version", "1.0.0")
            zip_url = data.get("zip_url", "")
            exe_url = data.get("exe_url", "")
            release_notes = data.get("release_notes", "No release notes provided.")
            
            update_available = compare_versions(current, remote_version)
            return {
                "success": True,
                "update_available": update_available,
                "current_version": current,
                "remote_version": remote_version,
                "release_notes": release_notes,
                "zip_url": zip_url,
                "exe_url": exe_url
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "current_version": current
        }

def perform_update(zip_url: str):
    base_dir = get_base_dir()
    temp_dir = tempfile.gettempdir()
    temp_zip = os.path.join(temp_dir, "update.zip")
    extract_dir = os.path.join(temp_dir, "update_extracted")
    
    # Clean and recreate temporary folders
    if os.path.exists(extract_dir):
        shutil.rmtree(extract_dir)
    os.makedirs(extract_dir, exist_ok=True)
    
    try:
        # 1. Download zip
        req = urllib.request.Request(
            zip_url, 
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        with urllib.request.urlopen(req, timeout=45) as response:
            with open(temp_zip, 'wb') as f:
                f.write(response.read())
        
        # 2. Extract zip
        with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        # 3. Find extracted root directory
        extracted_items = os.listdir(extract_dir)
        if not extracted_items:
            raise Exception("Downloaded archive is empty.")
        
        # If there is a single top-level folder (GitHub defaults to reponame-branchname)
        if len(extracted_items) == 1 and os.path.isdir(os.path.join(extract_dir, extracted_items[0])):
            src_root = os.path.join(extract_dir, extracted_items[0])
        else:
            src_root = extract_dir
            
        # 4. Copy files recursively to base_dir
        for root, dirs, files in os.walk(src_root):
            rel_path = os.path.relpath(root, src_root)
            if rel_path == ".":
                dest_dir = base_dir
            else:
                dest_dir = os.path.join(base_dir, rel_path)
                
            os.makedirs(dest_dir, exist_ok=True)
            
            for file in files:
                src_file = os.path.join(root, file)
                dest_file = os.path.join(dest_dir, file)
                
                # Skip volume directories to prevent index locked threads or data loss
                skip_paths = ["downloads", "cache", "cookies", ".git", ".github"]
                if any(part in rel_path.split(os.sep) for part in skip_paths) or file in skip_paths:
                    continue
                    
                shutil.copy2(src_file, dest_file)
        
        # 5. Clean up temp files
        if os.path.exists(temp_zip):
            try: os.remove(temp_zip)
            except: pass
        if os.path.exists(extract_dir):
            try: shutil.rmtree(extract_dir)
            except: pass
            
        return {"success": True}
        
    except Exception as e:
        # Clean up on exception
        if os.path.exists(temp_zip):
            try: os.remove(temp_zip) 
            except: pass
        if os.path.exists(extract_dir):
            try: shutil.rmtree(extract_dir) 
            except: pass
        return {"success": False, "error": str(e)}

def perform_exe_update(exe_url: str, version: str) -> dict:
    """Downloads a new exe version and schedules a self-replacement batch file."""
    try:
        current_exe_path = sys.executable
        if not getattr(sys, 'frozen', False):
            return {"success": False, "error": "Application is not running as a compiled executable."}
            
        temp_dir = tempfile.gettempdir()
        temp_exe_name = f"yt_downloader_{version}.exe"
        temp_exe_path = os.path.join(temp_dir, temp_exe_name)
        
        # 1. Download the new exe
        req = urllib.request.Request(
            exe_url, 
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        with urllib.request.urlopen(req, timeout=120) as response:
            with open(temp_exe_path, 'wb') as f:
                f.write(response.read())
                
        # Verify size
        if os.path.getsize(temp_exe_path) < 1000000:  # should be at least a few megabytes
            raise Exception("Downloaded executable is too small. Check URL.")

        # 2. Write the batch file that will replace the executable
        bat_path = os.path.join(temp_dir, "update_ytdl.bat")
        
        # Windows batch to wait for process to terminate, overwrite exe, delete temp exe, start new exe and delete itself
        bat_content = f"""@echo off
title Actualizando YouTube Downloader...
echo Esperando a que finalice la aplicacion...
timeout /t 3 /nobreak > nul

:retry
copy /y "{temp_exe_path}" "{current_exe_path}"
if errorlevel 1 (
    echo Reintentando en 2 segundos...
    timeout /t 2 /nobreak > nul
    goto retry
)

echo Iniciando nueva version...
start "" "{current_exe_path}"
(goto) 2>nul & del "%~f0"
"""
        with open(bat_path, "w", encoding="ansi") as f:
            f.write(bat_content)
            
        # 3. Launch batch script asynchronously and detached
        if platform.system() == "Windows":
            # Start batch script detached
            subprocess.Popen(
                [bat_path], 
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS
            )
        else:
            return {"success": False, "error": "Auto-update for executable only supported on Windows."}
            
        return {"success": True}
        
    except Exception as e:
        return {"success": False, "error": str(e)}
