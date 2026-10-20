# Build Instructions for SimCorp Native Desktop App

## Overview
This guide walks you through building a native Windows `.exe` installer using **PyInstaller**.

---

## Prerequisites

1. **Python 3.10+** installed on your system
2. **pip** package manager available
3. All dependencies installed: `pip install -r requirements.txt`

---

## Step-by-Step Build Process

### 1. Install PyInstaller and Additional Dependencies

```powershell
cd backend
pip install pyinstaller
```

### 2. Create a Standalone Python Executable (Sidecar)

First, we bundle the FastAPI server as a standalone executable that can be launched by the GUI:

```powershell
# Navigate to backend directory
cd w:\Github_projects\Simcorp\backend

# Create requirements file for sidecar if not exists
echo "fastapi>=0.109.0" > sidecar_requirements.txt
echo "uvicorn[standard]>=0.27.0" >> sidecar_requirements.txt
echo "pydantic>=2.0.0" >> sidecar_requirements.txt

# Build the FastAPI server as a standalone exe
pyinstaller --name simcorp-sidecar `
    --onefile `
    --clean `
    --add-data "simcorp;simcorp" `
    --hidden-import=fastapi `
    --hidden-import=uvicorn `
    --hidden-import=pydantic `
    backend/simcorp/api/server.py `
    -p sidecar_requirements.txt

# The executable will be in dist/simcorp-sidecar.exe
```

### 3. Build the Main GUI Application

Now we bundle the entire PySide6 application:

```powershell
cd w:\Github_projects\Simcorp\backend

# Build with proper package path for simcorp module and all dependencies
pyinstaller --name SimCorp `
    --windowed `
    --clean `
    --add-data "simcorp;simcorp" `
    --hidden-import=PySide6 `
    --hidden-import=matplotlib `
    --hidden-import=sqlite3 `
    simcorp/gui/run.py

### 4. Locate Your Built EXE

After building, you'll find:
- **Executable**: `dist/SimCorp.exe` (single-file executable)
- **Installer** (optional): Use tools like NSIS or Inno Setup to create an installer

---

## Alternative: Simple PyInstaller Build

For a quicker build without creating a sidecar:

```powershell
cd w:\Github_projects\Simcorp\backend

pyinstaller --name SimCorp `
    --windowed `
    --clean `
    --add-data "simcorp;simcorp" `
    --hidden-import=fastapi `
    --hidden-import=uvicorn `
    simcorp/gui/run.py
```

This bundles everything into a single `.exe` file in the `dist/` folder.

---

## Testing the Built Application

1. **Locate the executable**: `w:\Github_projects\Simcorp\backend\dist\SimCorp.exe`
2. **Run it directly** (no Python required):
   ```powershell
   .\dist\SimCorp.exe
   ```
3. **Verify functionality**:
   - Check that the UI loads correctly
   - Test creating a new game via File → New Game
   - Verify all tabs are accessible

---

## Distribution Options

### Option A: Single EXE (Simplest)
- Copy `dist\SimCorp.exe` to any Windows machine
- No Python installation required on target machines

### Option B: Installer Package
Use tools like **NSIS** or **Inno Setup** to create an installer:

```powershell
# Example using Inno Setup Script (innosetup.iss)
[Code]
Procedure Initialize;
  ExtractTemporaryFile('SimCorp.exe');
End;
```

### Option C: Portable Version
- Copy the entire `dist/` folder to a USB drive
- Run directly from the portable location

---

## Troubleshooting

### "Module Not Found" Errors
If you see import errors, add missing modules to PyInstaller:

```powershell
pyinstaller --name SimCorp `
    --windowed `
    --clean `
    --add-data "simcorp;simcorp" `
    --hidden-import=<missing_module> `
    simcorp/gui/run.py
```

### Database Issues
The SQLite database will be created automatically on first run. If it's corrupted:
1. Close the application
2. Delete `simcorp.db` from the backend directory
3. Restart the app to create a fresh database

### Large EXE Size
PyInstaller bundles all dependencies, resulting in larger file sizes (~50-100MB). This is normal for Python applications.

---

## Final Notes

- The built `.exe` is **standalone** - no Python installation required on target machines
- All data (database, settings) is stored locally by default
- You can customize the startup directory in `main_window_new.py` if needed

For advanced packaging options or creating installers for distribution, consider using tools like:
- [NSIS](https://nsis.sourceforge.io/)
- [Inno Setup](https://jrsoftware.org/isinfo.php)
- [Advanced Installer](https://www.advancedinstaller.com/)
