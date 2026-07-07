import os
import shutil
import urllib.request
import zipfile
import json
import sys

BASE_DIR = "/app"  # Mapped workspace root in Docker

def get_current_version():
    version_file = os.path.join(BASE_DIR, "app", "version.txt")
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
            release_notes = data.get("release_notes", "No release notes provided.")
            
            update_available = compare_versions(current, remote_version)
            return {
                "success": True,
                "update_available": update_available,
                "current_version": current,
                "remote_version": remote_version,
                "release_notes": release_notes,
                "zip_url": zip_url
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "current_version": current
        }

def perform_update(zip_url: str):
    temp_zip = "/tmp/update.zip"
    extract_dir = "/tmp/update_extracted"
    
    # Clean and recreate temporary folders
    if os.path.exists(extract_dir):
        shutil.rmtree(extract_dir)
    os.makedirs(extract_dir, exist_ok=True)
    os.makedirs("/tmp", exist_ok=True)
    
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
            
        # 4. Copy files recursively to /app
        for root, dirs, files in os.walk(src_root):
            rel_path = os.path.relpath(root, src_root)
            if rel_path == ".":
                dest_dir = BASE_DIR
            else:
                dest_dir = os.path.join(BASE_DIR, rel_path)
                
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
            os.remove(temp_zip)
        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir)
            
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
