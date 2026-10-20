# SimCorp Native Desktop Application - Build Instructions

## Overview
This project converts your React + FastAPI web application into a native Windows `.exe` using **PySide6** (Qt for Python).

## Architecture
- **Frontend**: PySide6 widgets (native Qt controls)
- **Backend**: FastAPI simulation engine bundled as sidecar or direct imports
- **Data**: SQLite database stored locally

---

## Quick Start

### 1. Install Dependencies
```powershell
cd backend
pip install -r requirements.txt
```

### 2. Run the Application (Development)
```powershell
python simcorp/gui/run.py
```

### 3. Build the EXE (Production)
See [BUILD.md](BUILD.md) for detailed build instructions using PyInstaller.

---

## Project Structure

```
backend/
├── simcorp/
│   ├── api/
│   │   ├── controller.py      # Business logic bridge
│   │   └── server.py          # FastAPI endpoints (optional for dev)
│   ├── engine/                 # Simulation engine
│   ├── models/                 # Data schemas
│   └── gui/                    # PySide6 UI layer
│       ├── main_window_new.py  # Main window with tabs
│       ├── run.py              # Entry point script
│       └── views/
│           ├── game_dashboard.py
│           ├── ai_manager.py
│           ├── hr_dashboard.py
│           └── financials.py
```

---

## Features Implemented

### Game Dashboard Tab
- Real-time simulation state display (day, cash, company info)
- Clock controls: Pause/Resume/Step Forward
- Product list with status indicators

### AI Manager Tab  
- AI health monitoring
- Configuration management (model, temperature, max tokens)
- Pending decisions review and approval/rejection
- "Run AI Review Now" button for manual triggers

### HR & Employees Tab
- Active employees list
- Hire new employee dialog (name, role, department, wage)
- Payroll cost tracking

### Financials Tab
- Cash balance display
- Revenue and profit/loss metrics
- Activity ledger with last 50 transactions
- Transaction categories: Sales, Wages, Loan Repayment, etc.

---

## Building the EXE

See [BUILD.md](BUILD.md) for complete PyInstaller packaging instructions.

---

## Troubleshooting

### Module Not Found Error
Ensure you're running from the `backend` directory or set PYTHONPATH:
```powershell
$env:PYTHONPATH="w:\Github_projects\Simcorp\backend"
python simcorp/gui/run.py
```

### Database Issues
The SQLite database is created automatically on first run. If it's corrupted, delete `simcorp.db` and restart the app.

---

## License
See [LICENSE](../../LICENSE)
