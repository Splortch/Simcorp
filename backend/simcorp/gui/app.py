"""Main entry point for SimCorp native desktop application."""
from simcorp.gui.main_window import MainWindow
import sys

def main():
    """Entry point for the application."""
    app = MainWindow()
    app.show()
    
    # Run Qt event loop
    import sys
    return app.exec_()

if __name__ == "__main__":
    sys.exit(main())
