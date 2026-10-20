# SimCorp Desktop App - Quick Plan Summary

## 🎯 Goal
Convert SimCorp business simulation from web-based to native Windows desktop application.

---

## ✅ Current Status

**Backend:** Complete (FastAPI + Python)
- Simulation engine working
- AI integration with LMStudio ready
- REST API endpoints functional

**Frontend:** Complete (React + TypeScript)
- All UI components built
- Financial charts and activity tracking working
- Task creation and agent management operational

---

## 🏗️ Recommended Architecture: Tauri 2.x

| Feature | Electron | **Tauri** ✅ |
|---------|----------|--------------|
| Bundle Size | ~150MB+ | <20MB |
| Memory Usage | High | Low (uses WebView) |
| Native Feel | Generic | Excellent |
| Security | Moderate | High (Rust-based) |

---

## 📋 Implementation Roadmap

### Phase 1: Setup (Week 1)
- [ ] Install Rust toolchain
- [ ] Initialize Tauri project
- [ ] Configure `tauri.conf.json`
- [ ] Create basic shell app

### Phase 2: Frontend Integration (Week 1-2)
- [ ] Embed React frontend in Tauri
- [ ] Configure Vite for static output
- [ ] Test all UI components

### Phase 3: Backend Connection (Week 2-3)
- [ ] HTTP communication setup
- [ ] Shared SQLite database path
- [ ] CORS configuration
- [ ] Startup scripts

### Phase 4: Build & Package (Week 3)
- [ ] PyInstaller for Python backend
- [ ] Tauri build pipeline
- [ ] Create EXE installer
- [ ] Test on clean Windows machine

### Phase 5: AI Testing (Week 3-4)
- [ ] LMStudio offline testing
- [ ] Agent orchestration verification
- [ ] Documentation

---

## 🔧 Integration Strategy

**Approach:** Direct HTTP Communication

```
┌─────────────┐     HTTP/REST      ┌─────────────┐
│   Tauri     │ ◄────────────────► │ FastAPI     │
│  (React UI) │                    │  (Backend)  │
└─────────────┘                    └─────────────┘
       ↑                                  ↓
       │                          SQLite Database
       └──────────────────────────────────────┘
```

**Benefits:**
- Zero backend code changes needed
- Fast development cycle
- Can run components independently during dev

---

## 📦 Build Commands

### Development
```bash
# Terminal 1 - Backend
fastapi dev backend/api/server.py

# Terminal 2 - Desktop App
cd desktop/
tauri dev
```

### Production Build
```bash
cd desktop/
npm run tauri build
```

---

## 🎯 Success Criteria

- [x] All simulation features work
- [ ] AI agents function offline
- [ ] Database persistence correct
- [ ] Standalone EXE available
- [ ] No external dependencies needed

---

## 📚 Key Resources

- [Tauri Docs](https://tauri.app/v1/guides/getting-started/setup)
- [FastAPI CORS](https://fastapi.tiangolo.com/tutorial/cors/)
- [PyInstaller Guide](https://www.pyinstaller.org/docs/guides/Production/)

---

*Last Updated: 2026-10-19 | Status: Planning Phase*
