"""Entry point for SimCorp native desktop application."""
import sys
from pathlib import Path

# Add backend directory to Python path (for PyInstaller bundled app)
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from simcorp.gui.main_window_new import MainWindow

def main():
    """Entry point for the application."""
    app = MainWindow()
    app.show()
    
    # Run Qt event loop
    return app.exec_()

if __name__ == "__main__":
    sys.exit(main())
