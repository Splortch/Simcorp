# SimCorp Desktop App - Project Plan

## Overview

This document outlines the planned architecture and implementation for converting the SimCorp business simulation from a web-based application to a native desktop application.

---

## Current State

### Backend Architecture ✅ Complete

The backend is fully implemented with:

- **FastAPI REST Server** (`backend/simcorp/api/server.py`)
  - Simulation state management
  - Game control endpoints (clock, events)
  - Business actions (hiring, loans, R&D, products)
  - AI integration support
  
- **Simulation Engine** (`backend/simcorp/engine/`)
  - Core game logic and simulation mechanics
  - Database persistence (SQLite)
  
- **AI Integration** (`backend/simcorp/ai/`)
  - LMStudio client for local LLM connections
  - AI orchestrator for autonomous agent management
  - Hierarchical task planning

### Frontend Architecture ✅ Complete

The frontend is fully implemented with:

- **React + TypeScript** application
- **Vite** build system
- Modern UI components (Activity & Ledger, Financial Charts, Agents Tab)
- Task creation and AI manager panels

---

## Desktop App Options

After research, two primary frameworks were evaluated:

### 1. Electron ⚠️ Not Recommended

**Pros:**
- Mature ecosystem with many ready-to-use templates
- Easy to integrate existing web frontend
- Large community support

**Cons:**
- Heavy memory footprint (~150MB+)
- Larger bundle size
- Native Node.js dependency adds complexity
- Less "native" feel on Windows

### 2. Tauri ✅ Recommended

**Pros:**
- Tiny bundle size (<20MB)
- Low memory footprint (uses system WebView)
- Rust-based backend for better security and performance
- Can embed existing web frontend via `tauri dev` or build static files
- Native file system access
- Better Windows integration

**Cons:**
- Smaller ecosystem than Electron
- Requires Rust toolchain setup
- Slightly steeper learning curve

---

## Recommended Architecture: Tauri 2.x

### Project Structure

```
SimCorp/
├── backend/                    # Existing Python backend (keep as-is)
│   ├── simcorp/
│   │   ├── api/server.py      # FastAPI endpoints
│   │   ├── engine/            # Simulation logic
│   │   ├── ai/                # AI integration
│   │   └── models/            # Data schemas
│   └── simcorp.db             # SQLite database
│
├── frontend/                   # Existing React frontend (keep as-is)
│   ├── src/
│   │   ├── App.tsx           # Main application component
│   │   ├── components/       # UI components
│   │   └── types.ts          # TypeScript types
│   └── package.json
│
├── desktop/                   # NEW: Tauri desktop app
│   ├── src-tauri/            # Rust backend for Tauri
│   │   ├── Cargo.toml        # Rust dependencies
│   │   ├── tauri.conf.json   # Tauri configuration
│   │   └── main.rs           # Tauri entry point
│   └── public/               # Static files (optional)
│
└── scripts/                   # Build and deployment scripts
    ├── build.py              # Python backend packaging
    └── deploy.sh             # Deployment automation
```

### Integration Strategy

#### Option A: Direct HTTP Communication (Recommended for MVP)

The Tauri desktop app will communicate with the existing FastAPI backend via HTTP:

1. **Tauri Frontend** embeds the existing React frontend
2. **React App** makes HTTP requests to `http://localhost:8000` (FastAPI server)
3. **FastAPI Backend** handles all business logic and AI operations
4. **SQLite Database** is shared via file path between backend processes

**Advantages:**
- Zero code changes needed for existing Python backend
- React frontend requires only minor CORS adjustments
- Fast development cycle
- Can run `fastapi dev server.py` alongside Tauri during development

#### Option B: Rust Proxy Layer (For Production)

Create a Rust service in `src-tauri/` that:

1. Acts as HTTP proxy to FastAPI backend
2. Handles file system operations for SQLite
3. Provides native Windows APIs when needed
4. Can be bundled with the desktop app

**Advantages:**
- Single executable deployment
- Better security (Rust memory safety)
- Native performance for file I/O
- Can implement offline-first capabilities

---

## Implementation Plan

### Phase 1: Tauri Setup (Week 1)

#### Tasks:
- [ ] Install Rust toolchain (`rustup`)
- [ ] Initialize Tauri project in `desktop/` folder
- [ ] Configure `tauri.conf.json`:
  - Set window title and icon
  - Configure dev server to point to React frontend
  - Enable file system permissions for SQLite access
- [ ] Create basic Tauri shell application

#### Deliverables:
- Working "Hello World" Tauri app
- Development environment configured
- Build pipeline functional

### Phase 2: Frontend Integration (Week 1-2)

#### Tasks:
- [ ] Update React frontend to work with Tauri dev server
- [ ] Configure Vite to output static files for Tauri embedding
- [ ] Test existing UI components in Tauri environment
- [ ] Implement Tauri commands for file system access (if needed)

#### Deliverables:
- Full SimCorp UI running inside Tauri window
- All existing features functional
- Development workflow established (`tauri dev`)

### Phase 3: Backend Integration (Week 2-3)

#### Tasks:
- [ ] Configure FastAPI to serve on `localhost:8000`
- [ ] Update CORS settings for Tauri origin
- [ ] Implement shared SQLite database path between processes
- [ ] Test API communication from React frontend
- [ ] Create startup scripts for both backend and desktop app

#### Deliverables:
- Seamless integration between FastAPI, React, and Tauri
- Database persistence working correctly
- All simulation features functional

### Phase 4: Build & Packaging (Week 3)

#### Tasks:
- [ ] Configure PyInstaller for Python backend packaging
- [ ] Create build script that packages:
  - Rust binary from Tauri
  - FastAPI server executable
  - SQLite database schema
- [ ] Test packaged EXE on clean Windows machine
- [ ] Create installer (Inno Setup or NSIS)

#### Deliverables:
- Standalone `.exe` installer
- Portable version (optional)
- Deployment documentation

### Phase 5: AI Integration Testing (Week 3-4)

#### Tasks:
- [ ] Test LMStudio connection from packaged app
- [ ] Verify AI agent orchestration works offline
- [ ] Test hierarchical task planning with local LLMs
- [ ] Document AI configuration requirements

#### Deliverables:
- Working AI features in packaged app
- Configuration guide for LLM connections
- Troubleshooting documentation

---

## Technical Decisions

### Database Strategy

**Current:** SQLite file at `backend/simcorp.db`

**Approach:** Shared database file
- Both FastAPI and Tauri will access the same SQLite file
- Use file path configuration (not hardcoded)
- Consider WAL mode for concurrent access: `.mode wal`

**Alternative:** Rust proxy with embedded SQLite
- More complex but allows true single-exe deployment
- Requires migrating database schema to Rust-compatible format

### Communication Protocol

**Primary:** HTTP/REST between React frontend and FastAPI backend
- Existing API endpoints can be used directly
- No protocol changes needed

**Secondary:** Tauri commands for native operations
- File system access
- System tray integration (optional)
- Windows-specific features

### Build Pipeline

```bash
# Development
cd desktop/
tauri dev                    # Starts React + Tauri
# In separate terminal:
fastapi dev backend/api/server.py  # Backend server

# Production Build
cd desktop/
npm run tauri build          # Builds Rust binary + bundles frontend

# Python Backend Packaging (separate)
pyinstaller --name SimCorp \
    --onefile \
    --add "backend/simcorp" \
    backend/api/server.py
```

---

## Dependencies

### Frontend (Existing)
- React 18+
- TypeScript 5.x
- Vite 5.x
- Tailwind CSS (if used)

### Desktop (New)
- Tauri 2.x
- Rust 1.70+
- WebView2 (Windows - auto-installed)

### Backend (Existing)
- Python 3.10+
- FastAPI
- SQLAlchemy
- Pydantic

---

## Deployment Targets

### Windows (Primary)
- **Installer:** Inno Setup or NSIS
- **Requirements:** .NET Runtime, WebView2 (auto-installed)
- **Size:** ~50-80 MB total

### macOS / Linux (Future)
- Tauri handles platform-specific builds
- DMG for macOS, AppImage/DEB for Linux

---

## Success Criteria

1. ✅ All existing simulation features work in desktop app
2. ✅ AI agents function with local LLMs (LMStudio)
3. ✅ Database persistence works correctly across restarts
4. ✅ Standalone EXE installer available
5. ✅ No external dependencies required (except Python runtime for backend)

---

## Next Steps

1. **Immediate:** Install Rust and Tauri CLI
2. **Week 1:** Set up basic Tauri project structure
3. **Week 2:** Integrate existing React frontend
4. **Week 3:** Configure backend communication
5. **Week 4:** Build first production-ready EXE

---

## Resources

- [Tauri Documentation](https://tauri.app/v1/guides/getting-started/setup)
- [FastAPI CORS Configuration](https://fastapi.tiangolo.com/tutorial/cors/)
- [PyInstaller Guide](https://www.pyinstaller.org/docs/guides/Production/)
- [Inno Setup Wiki](https://jrsoftware.org/ins/setup.php)

---

*Last Updated: 2026-10-19*
*Status: Planning Phase*
