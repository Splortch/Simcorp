"""AI management view for reviewing and approving AI decisions."""
import sys
from typing import List, Dict, Any

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QGroupBox,
    QListWidget,
    QListWidgetItem,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

class AIManagerView(QWidget):
    """AI management view for reviewing and approving AI decisions."""

    def __init__(self, controller) -> None:
        super().__init__()
        self.controller = controller
        
        layout = QVBoxLayout(self)
        
        # Status bar
        status_layout = QHBoxLayout()
        status_layout.setSpacing(10)
        
        ai_health_label = QLabel("AI Health: Checking...")
        ai_health_label.setFont(QFont("Arial", 14))
        self.ai_health_label = ai_health_label
        
        last_review_label = QLabel("Last Review: Never")
        self.last_review_label = last_review_label
        
        status_layout.addWidget(ai_health_label)
        status_layout.addWidget(last_review_label)
        
        layout.addLayout(status_layout)
        
        # AI Config group
        config_group = QGroupBox("AI Configuration")
        config_layout = QVBoxLayout(config_group)
        
        self.config_text = QTextEdit()
        self.config_text.setReadOnly(True)
        self.config_text.setMaximumHeight(150)
        config_layout.addWidget(self.config_text)
        
        save_config_btn = QPushButton("Save Configuration")
        save_config_btn.clicked.connect(lambda: self._save_config())
        config_layout.addWidget(save_config_btn, alignment=Qt.AlignCenter)
        
        layout.addWidget(config_group)
        
        # AI Decisions group
        decisions_group = QGroupBox("AI Decisions Pending Review")
        decisions_layout = QVBoxLayout(decisions_group)
        
        self.decisions_list = QListWidget()
        self.decisions_list.itemDoubleClicked.connect(self._on_decision_selected)
        decisions_layout.addWidget(self.decisions_list)
        
        layout.addWidget(decisions_group)
        
        # Action buttons
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(10)
        
        review_now_btn = QPushButton("Run AI Review Now")
        review_now_btn.clicked.connect(lambda: self._run_review(force=True))
        actions_layout.addWidget(review_now_btn)
        
        approve_selected_btn = QPushButton("Approve Selected")
        approve_selected_btn.clicked.connect(self._approve_selected)
        actions_layout.addWidget(approve_selected_btn)
        
        reject_selected_btn = QPushButton("Reject Selected")
        reject_selected_btn.clicked.connect(self._reject_selected)
        actions_layout.addWidget(reject_selected_btn)
        
        layout.addLayout(actions_layout)
    
    def _refresh_state(self) -> None:
        """Refresh the displayed AI state."""
        # Check AI health
        try:
            health = self.controller.check_ai_health()
            status_text = "✓ Healthy" if health.get("status") == "ok" else f"⚠ {health.get('message', 'Unknown')}"
            self.ai_health_label.setText(f"AI Health: {status_text}")
        except Exception as e:
            self.ai_health_label.setText(f"AI Health: Error - {str(e)}")
        
        # Get AI config
        try:
            cfg = self.controller.get_ai_config()
            config_str = f"Model: {cfg.get('model', 'N/A')}\nTemperature: {cfg.get('temperature', 0.7)}\nMax Tokens: {cfg.get('max_tokens', 1024)}"
            self.config_text.setText(config_str)
        except Exception as e:
            self.config_text.setText(f"Error loading config: {str(e)}")
        
        # Get pending decisions
        try:
            state = self.controller.get_game_state()
            ai_decisions = state.get("ai_decisions", [])
            
            for decision in ai_decisions:
                item = QListWidgetItem(decision.get("description", "No description"))
                item.setData(Qt.UserRole, decision.get("id"))
                self.decisions_list.addItem(item)
        except Exception as e:
            print(f"Error loading decisions: {e}")
    
    def _run_review(self, force: bool = False) -> None:
        """Run AI management review."""
        try:
            if force:
                result = self.controller.trigger_ai_review_now()
            else:
                state = self.controller.get_game_state()
                result = self.controller.ai_orchestrator.run_management_cycle(state)
            
            # Refresh to show new decisions
            self._refresh_state()
        except Exception as e:
            print(f"AI review error: {e}")
    
    def _save_config(self) -> None:
        """Save AI configuration."""
        try:
            cfg = self.controller.get_ai_config()
            result = self.controller.update_ai_config(cfg)
            print("Configuration saved.")
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def _on_decision_selected(self, item) -> None:
        """Handle decision selection."""
        decision_id = item.data(Qt.UserRole)
        self._refresh_state()  # Refresh to show updated state
    
    def _approve_selected(self) -> None:
        """Approve selected decision."""
        if not self.decisions_list.currentItem():
            print("No decision selected.")
            return
        
        decision_id = self.decisions_list.currentItem().data(Qt.UserRole)
        try:
            result = self.controller.approve_ai_decision(decision_id)
            print(f"Decision {decision_id} approved.")
            self._refresh_state()
        except Exception as e:
            print(f"Error approving decision: {e}")
    
    def _reject_selected(self) -> None:
        """Reject selected decision."""
        if not self.decisions_list.currentItem():
            print("No decision selected.")
            return
        
        decision_id = self.decisions_list.currentItem().data(Qt.UserRole)
        try:
            result = self.controller.reject_ai_decision(decision_id)
            print(f"Decision {decision_id} rejected.")
            self._refresh_state()
        except Exception as e:
            print(f"Error rejecting decision: {e}")
