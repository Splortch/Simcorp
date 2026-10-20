"""Game dashboard view showing simulation state and controls."""
import sys
from typing import List, Dict, Any

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGroupBox,
    QTextEdit,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from simcorp.models.schemas import FullGameState


class GameDashboardView(QWidget):
    """Main game dashboard showing simulation state and controls."""

    def __init__(self, controller) -> None:
        super().__init__()
        self.controller = controller
        
        layout = QVBoxLayout(self)
        
        # Status bar (day, clock status)
        status_layout = QHBoxLayout()
        status_layout.setSpacing(10)
        
        day_label = QLabel("Day 0")
        day_label.setFont(QFont("Arial", 24, QFont.Bold))
        self.day_label = day_label
        
        cash_label = QLabel("Cash: 0 CR")
        cash_label.setFont(QFont("Arial", 18))
        self.cash_label = cash_label
        
        status_layout.addWidget(day_label)
        status_layout.addWidget(cash_label)
        
        layout.addLayout(status_layout)
        
        # Game info group
        game_info_group = QGroupBox("Game Info")
        game_info_layout = QVBoxLayout(game_info_group)
        
        company_label = QLabel("Company: Default Corp")
        self.company_label = company_label
        
        mode_label = QLabel("Mode: Standard")
        self.mode_label = mode_label
        
        difficulty_label = QLabel("Difficulty: Normal")
        self.difficulty_label = difficulty_label
        
        game_info_layout.addWidget(company_label)
        game_info_layout.addWidget(mode_label)
        game_info_layout.addWidget(difficulty_label)
        
        layout.addWidget(game_info_group)
        
        # Clock controls
        clock_group = QGroupBox("Clock Controls")
        clock_layout = QVBoxLayout(clock_group)
        
        pause_btn = QPushButton("Pause")
        pause_btn.clicked.connect(lambda: self._control_clock("pause"))
        
        resume_btn = QPushButton("Resume")
        resume_btn.clicked.connect(lambda: self._control_clock("resume"))
        
        step_btn = QPushButton("Step Forward (1 Day)")
        step_btn.clicked.connect(lambda: self._control_clock("step"))
        
        clock_layout.addWidget(pause_btn)
        clock_layout.addWidget(resume_btn)
        clock_layout.addWidget(step_btn)
        
        layout.addWidget(clock_group)
        
        # Products list
        products_group = QGroupBox("Products")
        products_layout = QVBoxLayout(products_group)
        
        self.products_text = QTextEdit()
        self.products_text.setReadOnly(True)
        self.products_text.setMaximumHeight(200)
        products_layout.addWidget(self.products_text)
        
        layout.addWidget(products_group)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._refresh_state)
        layout.addWidget(refresh_btn, alignment=Qt.AlignCenter)
    
    def _control_clock(self, action: str) -> None:
        """Control the simulation clock."""
        from simcorp.models.schemas import ClockControlRequest
        
        req = ClockControlRequest(action=action)
        try:
            self.controller.control_clock(req)
            self._refresh_state()
        except Exception as e:
            print(f"Clock control error: {e}")
    
    def _refresh_state(self) -> None:
        """Refresh the displayed state."""
        state = self.controller.get_game_state()
        
        # Update status bar
        clock = state["clock"]
        day_label = f"Day {clock['current_day']}"
        self.day_label.setText(day_label)
        
        cash = state.get("cash", 0)
        self.cash_label.setText(f"Cash: {cash:,} CR")
        
        # Update game info
        company = state.get("company", "Unknown")
        self.company_label.setText(f"Company: {company}")
        
        mode = state.get("mode", "Standard")
        self.mode_label.setText(f"Mode: {mode}")
        
        difficulty = state.get("difficulty", "Normal")
        self.difficulty_label.setText(f"Difficulty: {difficulty}")
        
        # Update products list
        products_text = []
        for product in state.get("products", []):
            prod_id = product["id"]
            name = product.get("name", "Unknown")
            price = product.get("selling_price", 0)
            target = product.get("daily_production_target", 0)
            status = product.get("status", "Active")
            
            products_text.append(f"• {prod_id}: {name} | Price: {price} CR | Target: {target}/day | Status: {status}")
        
        self.products_text.setText("\n".join(products_text))
