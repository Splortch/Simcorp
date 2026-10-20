"""
Main application window for SimCorp native desktop app.
Provides the core layout: tab-based navigation + main content area.
"""
import sys
from pathlib import Path
from typing import TYPE_CHECKING, List, Dict, Any

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QStackedWidget,
    QLabel,
    QPushButton,
    QLineEdit,
    QSpinBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QGroupBox,
    QTextEdit,
    QListWidget,
    QListWidgetItem,
    QComboBox,
    QDialogButtonBox,
    QTableWidget,
    QTabWidget,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction

from simcorp.api.controller import SimCorpController


class MainWindow(QMainWindow):
    """Main application window with tab-based navigation and content area."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("SimCorp Business Simulation")
        self.setMinimumSize(1200, 800)
        
        # Initialize controller (singleton-like instance)
        self.controller = SimCorpController()
        self.controller.start_app()

        # Main layout: tab widget + content area
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Tab widget for navigation (Game, AI, HR, Financials)
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget, stretch=1)

        # Create initial views
        self._create_game_tab()
        self._create_ai_tab()
        self._create_hr_tab()
        self._create_financials_tab()

    def _create_game_tab(self) -> None:
        """Create the main game dashboard tab."""
        from simcorp.gui.views.game_dashboard import GameDashboardView
        self.game_view = GameDashboardView(self.controller)
        self.tab_widget.addTab(self.game_view, "Game Dashboard")

    def _create_ai_tab(self) -> None:
        """Create AI management tab."""
        from simcorp.gui.views.ai_manager import AIManagerView
        self.ai_view = AIManagerView(self.controller)
        self.tab_widget.addTab(self.ai_view, "AI Manager")

    def _create_hr_tab(self) -> None:
        """Create HR/employees tab."""
        from simcorp.gui.views.hr_dashboard import HRDashboardView
        self.hr_view = HRDashboardView(self.controller)
        self.tab_widget.addTab(self.hr_view, "HR & Employees")

    def _create_financials_tab(self) -> None:
        """Create financial charts and ledger tab."""
        from simcorp.gui.views.financials import FinancialsView
        self.financials_view = FinancialsView(self.controller)
        self.tab_widget.addTab(self.financials_view, "Financials")

    def _new_game(self) -> None:
        """Create a new game."""
        from simcorp.models.schemas import NewGameRequest
        
        # Simple dialog for new game setup
        self.new_game_dialog = QDialog(self)
        self.new_game_dialog.setWindowTitle("New Game")
        layout = QVBoxLayout(self.new_game_dialog)

        form_layout = QFormLayout()
        
        company_name_input = QLineEdit()
        company_name_input.setPlaceholderText("Company Name")
        starting_cash_spin = QSpinBox()
        starting_cash_spin.setRange(10000, 1000000)
        starting_cash_spin.setValue(100000)
        starting_cash_spin.setSuffix(" CR")

        form_layout.addRow("Company Name:", company_name_input)
        form_layout.addRow("Starting Cash:", starting_cash_spin)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            self.new_game_dialog
        )
        buttons.accepted.connect(self._confirm_new_game)
        buttons.rejected.connect(self.new_game_dialog.close)
        layout.addLayout(form_layout)
        layout.addWidget(buttons)

        self.new_game_dialog.exec()

    def _confirm_new_game(self) -> None:
        """Confirm and create new game."""
        company_name = self.new_game_dialog.findChild(QLineEdit, "company_name_input").text()
        starting_cash = self.new_game_dialog.findChild(QSpinBox, "starting_cash_spin").value()
        
        req = NewGameRequest(
            company_name=company_name,
            starting_cash=starting_cash,
            initial_product_name="Product A",
            initial_product_price=50,
            initial_product_cost=20,
            initial_daily_target=10,
            mode="Standard",
            difficulty="Normal",
            campaign_goal="Profitability",
            campaign_target_value=1000000,
            campaign_deadline_days=365,
        )
        
        self.controller.create_new_game(req)
        self.new_game_dialog.close()

    def closeEvent(self, event) -> None:
        """Clean shutdown on window close."""
        self.controller.stop_app()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set application style (optional - can use Fuchsia or other Qt stylesheets)
    from PySide6.QtWidgets import QApplication, QStyleFactory
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())
