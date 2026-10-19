# SimCorp: AI-Powered Business Management Simulation Game

SimCorp is a business management simulation game where you establish and operate an enterprise in a dynamic economy. An autonomous AI management team coordinates operations, sales, marketing, and strategy, with all decisions backed by an authoritative SQLite double-entry ledger.

---

## Current Status

SimCorp includes a local simulation engine, persistent SQLite saves, a React dashboard, AI management/workforce features, and a Windows desktop packaging workflow. Features and test coverage are still evolving; see the roadmap below for planned work.

- **Architecture:** Local-first Windows desktop application powered by a deterministic Python economic simulation engine, SQLite persistence, and a React + TypeScript + Tailwind CSS executive dashboard.
- **Starting Conditions:** Brand-new company starting with 10,000 credits, production lines, demand calculations, and double-entry ledger records.
- **Clock & Simulation:** Configurable simulation clock with Pause, Resume, Speed (1x, 2x, 5x), and discrete step capabilities.
- **Economics & Accounting:** Actual manufacturing costs (COGS), daily fixed OPEX (50 cr/day), inventory tracking, and genuine customer demand curves (no fake revenue).
- **Executive Dashboard:** Live charts tracking cash balance and enterprise valuation over time, real-time P&L (revenue vs profit), product line configuration, and an auditable transaction ledger.

---

## Project Structure

```
Simcorp/
├── backend/
│   ├── simcorp/
│   │   ├── engine/       # Deterministic simulation clock, economics, and SQLite db
│   │   ├── models/       # Pydantic schemas and typed definitions
│   │   └── api/          # FastAPI REST endpoints and static SPA hosting
│   └── tests/            # pytest suite verifying economic loop and constraints
├── frontend/             # React + Vite + TypeScript + Tailwind CSS desktop UI
│   ├── src/
│   │   ├── components/   # Executive widgets (Charts, ProductManager, Ledger, TopBar)
│   │   └── types.ts      # TypeScript state definitions
│   └── package.json
├── desktop_launcher.py   # Windows desktop launcher with native WebView
├── simcorp.db            # Persistent local SQLite database (auto-generated)
└── README.md
```

---

## Getting Started

### Prerequisites

- **Python 3.11+**
- **Node.js 18+ & npm**
- **Windows OS**

### 1. Install Backend Dependencies

```powershell
python -m pip install fastapi uvicorn pydantic pytest httpx pywebview
```

### 2. Build the Desktop Frontend

```powershell
cd frontend
npm install
npm run build
cd ..
```

### 3. Launch SimCorp Desktop Application

Run the native desktop application window:

```powershell
python desktop_launcher.py
```

*Alternatively, run in browser/dev mode:*
- Backend: `python -m uvicorn simcorp.api.server:app --app-dir backend --reload`
- Frontend dev server: `cd frontend; npm run dev` (available at `http://127.0.0.1:5173`)

---

## Running the Automated Test Suite

Run pytest to verify the economic calculations, non-negative inventory enforcement, solvency warnings, and transaction integrity:

```powershell
$env:PYTHONPATH="backend"
python -m pytest backend/tests
```

The automated test suite is run in GitHub Actions for pull requests and pushes to main.

---

## Roadmap

- [x] **Milestone 1:** Working foundation, desktop shell, SQLite persistence, deterministic day clock, ledger transactions, interactive dashboard, and automated tests.
- [ ] **Milestone 2:** Multi-segment customer demand, suppliers, lead times, resource purchasing, and random market events.
- [x] **Milestone 3:** Local LLM integration (LM Studio) with management roles and fallback rules.
- [x] **Milestone 4:** Executive committee (CFO, CMO, R&D) with multi-agent coordination.
- [ ] **Milestone 5:** Research tree, competitors, and advanced organizational growth.
- [ ] **Milestone 6:** Polish, achievements, and installer packaging.

---

## License

MIT License. See [LICENSE](LICENSE) for details.
