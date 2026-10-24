"""Resource path resolver for both development and PyInstaller bundled applications."""
import os
import sys
from pathlib import Path


def get_project_root() -> Path:
    """Get the project root directory."""
    if getattr(sys, "frozen", False):
        # Running as PyInstaller bundle - use executable location
        return Path(sys.executable).parent.parent
    else:
        # Development mode - use source tree
        return Path(__file__).resolve().parent.parent.parent.parent


def get_data_dir() -> Path:
    """Get the data directory for persistent storage."""
    if getattr(sys, "frozen", False):
        # PyInstaller bundle - store in user's AppData
        appdata = os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")
        return Path(appdata) / "SimCorp"
    else:
        # Development - use project root
        return get_project_root()


def get_frontend_dir() -> Path | None:
    """Get the frontend assets directory. Returns None if not available."""
    project_root = get_project_root()
    
    # Try bundled location first (PyInstaller)
    bundled_frontend = project_root / "frontend" / "dist"
    if bundled_frontend.exists():
        return bundled_frontend
    
    # Fall back to source build location
    source_frontend = project_root.parent / "desktop" / "dist"
    if source_frontend.exists():
        return source_frontend
    
    return None


def get_static_files_dir() -> Path | None:
    """Get the static files directory for PyInstaller bundles."""
    if getattr(sys, "frozen", False):
        # In bundled mode, static files are in the same dir as executable
        return Path(sys.executable).parent.parent / "frontend" / "dist"
    else:
        return None


def verify_frontend_available() -> bool:
    """Verify that frontend assets are available."""
    frontend_dir = get_frontend_dir()
    if not frontend_dir:
        return False
    
    # Check for index.html (SPA entry point)
    index_path = frontend_dir / "index.html"
    if not index_path.exists():
        return False
    
    # Also check for some common assets to ensure SPA fallback will work
    assets_to_check = ["assets", "styles.css"]
    has_assets = any((frontend_dir / asset).exists() for asset in assets_to_check)
    
    return True


def get_app_data_path(filename: str) -> Path:
    """Get a path within the app data directory."""
    data_dir = get_data_dir()
    return data_dir / filename
