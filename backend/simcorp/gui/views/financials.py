"""Financial dashboard view showing charts and ledger."""
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
    QTableWidget,
)
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHeaderView

class FinancialsView(QWidget):
    """Financial dashboard with charts and ledger."""

    def __init__(self, controller) -> None:
        super().__init__()
        self.controller = controller
        
        layout = QVBoxLayout(self)
        
        # Status bar
        status_layout = QHBoxLayout()
        status_layout.setSpacing(10)
        
        cash_label = QLabel("Cash: 0 CR")
        self.cash_label = cash_label
        
        profit_label = QLabel("Profit/Loss: 0 CR")
        self.profit_label = profit_label
        
        revenue_label = QLabel("Revenue: 0 CR")
        self.revenue_label = revenue_label
        
        status_layout.addWidget(cash_label)
        status_layout.addWidget(profit_label)
        status_layout.addWidget(revenue_label)
        
        layout.addLayout(status_layout)
        
        # Financial summary group
        summary_group = QGroupBox("Financial Summary")
        summary_layout = QVBoxLayout(summary_group)
        
        cash_text = QTextEdit()
        cash_text.setReadOnly(True)
        cash_text.setMaximumHeight(150)
        summary_layout.addWidget(cash_text)
        
        layout.addWidget(summary_group)
        
        # Ledger group
        ledger_group = QGroupBox("Activity Ledger")
        ledger_layout = QVBoxLayout(ledger_group)
        
        self.ledger_table = QTableWidget()
        self.ledger_table.setColumnCount(5)
        self.ledger_table.setHorizontalHeaderLabels(["Day", "Category", "Type", "Amount (CR)", "Description"])
        self.ledger_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        ledger_layout.addWidget(self.ledger_table)
        
        layout.addWidget(ledger_group)
    
    def _refresh_state(self) -> None:
        """Refresh the displayed financial state."""
        try:
            state = self.controller.get_game_state()
            
            # Update status bar
            cash = state.get("cash", 0)
            self.cash_label.setText(f"Cash: {cash:,} CR")
            
            revenue = state.get("revenue", 0)
            self.revenue_label.setText(f"Revenue: {revenue:,} CR")
            
            profit_loss = state.get("profit_loss", 0)
            sign = "+" if profit_loss >= 0 else ""
            self.profit_label.setText(f"Profit/Loss: {sign}{profit_loss:,} CR")
            
            # Update financial summary text
            cash_text = f"""Cash Balance: {cash:,} CR
Total Revenue: {revenue:,} CR
Total Expenses: {state.get('expenses', 0):,} CR
Net Profit/Loss: {sign}{profit_loss:,} CR

Starting Cash: {state.get('starting_cash', 0):,} CR"""
            self.cash_text.setText(cash_text)
            
            # Update ledger table
            activity_log = state.get("activity_log", [])
            for row, log_entry in enumerate(activity_log[-50:], start=1):  # Last 50 entries
                day = log_entry.get("day", "N/A")
                category = log_entry.get("category", "Unknown")
                severity = log_entry.get("severity", "INFO").upper()
                
                # Parse amount from message or use default
                message = log_entry.get("message", "")
                amount_str = ""
                if "CR" in message:
                    import re
                    match = re.search(r'(\d+(?:\.\d+)?)\s*CR', message)
                    if match:
                        amount_str = f"{float(match.group(1)):,.2f}"
                
                description = log_entry.get("message", "")[:50] + "..." if len(log_entry.get("message", "")) > 50 else log_entry.get("message", "")
                
                self.ledger_table.setItem(row-1, 0, QTableWidgetItem(str(day)))
                self.ledger_table.setItem(row-1, 1, QTableWidgetItem(category))
                self.ledger_table.setItem(row-1, 2, QTableWidgetItem(severity))
                self.ledger_table.setItem(row-1, 3, QTableWidgetItem(amount_str if amount_str else "-"))
                self.ledger_table.setItem(row-1, 4, QTableWidgetItem(description))
                
        except Exception as e:
            print(f"Error loading financials: {e}")
