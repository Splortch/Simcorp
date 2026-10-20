"""
Main application window for SimCorp native desktop app.
Provides the core layout: tab-based navigation + main content area.
"""
import sys
from pathlib import Path
from typing import TYPE_CHECKING, List, Dict, Any

from PySide6.QtWidgets import (
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
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QFont

from simcorp.api.controller import SimCorpController


class MainWindow(QMainWindow):
    """Main application window with sidebar navigation and content area."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("SimCorp Business Simulation")
        self.setMinimumSize(1200, 800)
        
        # Initialize controller (singleton-like instance)
        self.controller = SimCorpController()
        self.controller.start_app()

        # Main layout: sidebar + content area
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Sidebar navigation panel
        self.sidebar = QNavigationArea()
        sidebar_widget = QWidget()
        sidebar_layout = QVBoxLayout(sidebar_widget)
        sidebar_layout.addWidget(self.sidebar)
        main_layout.addWidget(sidebar_widget, stretch=0)

        # Main content area (stacked widget for different views)
        self.content_stack = QStackedWidget()
        main_layout.addWidget(self.content_stack, stretch=1)

        # Create initial views
        self._create_game_view()
        self._create_ai_view()
        self._create_hr_view()
        self._create_financials_view()

        # Connect sidebar actions to stack widget
        self._connect_sidebar_actions()

    def _create_game_view(self) -> None:
        """Create the main game dashboard view."""
        from simcorp.gui.views.game_dashboard import GameDashboardView
        self.game_view = GameDashboardView(self.controller)
        self.content_stack.addWidget(self.game_view)

    def _create_ai_view(self) -> None:
        """Create AI management view."""
        from simcorp.gui.views.ai_manager import AIManagerView
        self.ai_view = AIManagerView(self.controller)
        self.content_stack.addWidget(self.ai_view)

    def _create_hr_view(self) -> None:
        """Create HR/employees view."""
        from simcorp.gui.views.hr_dashboard import HRDashboardView
        self.hr_view = HRDashboardView(self.controller)
        self.content_stack.addWidget(self.hr_view)

    def _create_financials_view(self) -> None:
        """Create financial charts and ledger view."""
        from simcorp.gui.views.financials import FinancialsView
        self.financials_view = FinancialsView(self.controller)
        self.content_stack.addWidget(self.financials_view)

    def _connect_sidebar_actions(self) -> None:
        """Connect sidebar navigation actions to content stack."""
        # Get the main window widget (where we can add menu bar and toolbar)
        menubar = self.menuBar()
        
        # File Menu
        file_menu = menubar.addMenu("File")
        new_game_action = QAction("&New Game", self)
        new_game_action.setShortcut("Ctrl+N")
        new_game_action.triggered.connect(self._new_game)
        file_menu.addAction(new_game_action)
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View Menu
        view_menu = menubar.addMenu("View")
        toggle_sidebar_action = QAction("&Sidebar", self)
        toggle_sidebar_action.setCheckable(True)
        toggle_sidebar_action.setChecked(True)
        toggle_sidebar_action.toggled.connect(self._toggle_sidebar)
        view_menu.addAction(toggle_sidebar_action)

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

    def _toggle_sidebar(self, visible: bool) -> None:
        """Toggle sidebar visibility."""
        if not visible:
            self.sidebar.setVisible(False)
            # Adjust layout to fill space
            main_layout.setSpacing(0)
        else:
            self.sidebar.setVisible(True)

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
