"""HR dashboard view for managing employees."""
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
    QListWidget,
    QListWidgetItem,
    QDialog,
    QLineEdit,
    QSpinBox,
    QComboBox,
)
from PySide6.QtCore import Qt

class HRDashboardView(QWidget):
    """HR dashboard for managing employees."""

    def __init__(self, controller) -> None:
        super().__init__()
        self.controller = controller
        
        layout = QVBoxLayout(self)
        
        # Status bar
        status_layout = QHBoxLayout()
        status_layout.setSpacing(10)
        
        total_employees_label = QLabel("Total Employees: 0")
        self.total_employees_label = total_employees_label
        
        payroll_cost_label = QLabel("Daily Payroll: 0 CR")
        self.payroll_cost_label = payroll_cost_label
        
        status_layout.addWidget(total_employees_label)
        status_layout.addWidget(payroll_cost_label)
        
        layout.addLayout(status_layout)
        
        # Employees list group
        employees_group = QGroupBox("Active Employees")
        employees_layout = QVBoxLayout(employees_group)
        
        self.employees_list = QListWidget()
        self.employees_list.itemDoubleClicked.connect(self._on_employee_selected)
        employees_layout.addWidget(self.employees_list)
        
        layout.addWidget(employees_group)
        
        # Hire employee dialog button
        hire_btn = QPushButton("Hire New Employee")
        hire_btn.clicked.connect(self._open_hire_dialog)
        layout.addWidget(hire_btn, alignment=Qt.AlignCenter)
    
    def _refresh_state(self) -> None:
        """Refresh the displayed HR state."""
        # Get employees list
        try:
            employees = self.controller.list_employees()
            
            for emp in employees:
                item_text = f"{emp['id']}: {emp['name']} ({emp['role']}) - {emp['department']}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, emp.get('id'))
                self.employees_list.addItem(item)
            
            # Update status bar
            total_employees = len(employees)
            self.total_employees_label.setText(f"Total Employees: {total_employees}")
            
            # Calculate payroll (simplified - would need actual wage data from DB)
            self.payroll_cost_label.setText("Daily Payroll: Calculating...")
        except Exception as e:
            print(f"Error loading employees: {e}")
    
    def _open_hire_dialog(self) -> None:
        """Open dialog to hire new employee."""
        from simcorp.models.schemas import HireEmployeeRequest
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Hire New Employee")
        layout = QVBoxLayout(dialog)
        
        form_layout = QFormLayout()
        
        name_input = QLineEdit()
        name_input.setPlaceholderText("Employee Name")
        
        role_combo = QComboBox()
        roles = ["Manager", "Engineer", "Designer", "Sales Rep", "HR Specialist"]
        for role in roles:
            role_combo.addItem(role, role)
        
        dept_combo = QComboBox()
        depts = ["Engineering", "Design", "Sales", "HR", "Marketing"]
        for dept in depts:
            dept_combo.addItem(dept, dept)
        
        wage_spin = QSpinBox()
        wage_spin.setRange(10, 500)
        wage_spin.setValue(50)
        wage_spin.setSuffix(" CR/day")
        
        form_layout.addRow("Name:", name_input)
        form_layout.addRow("Role:", role_combo)
        form_layout.addRow("Department:", dept_combo)
        form_layout.addRow("Daily Wage:", wage_spin)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            dialog
        )
        buttons.accepted.connect(self._confirm_hire)
        buttons.rejected.connect(dialog.close)
        
        layout.addLayout(form_layout)
        layout.addWidget(buttons)
        
        dialog.exec()
    
    def _confirm_hire(self) -> None:
        """Confirm hiring new employee."""
        name = self.findChild(QLineEdit, "name_input").text()
        role_combo = self.findChild(QComboBox, "role_combo")
        dept_combo = self.findChild(QComboBox, "dept_combo")
        wage_spin = self.findChild(QSpinBox, "wage_spin")
        
        role = role_combo.currentText()
        department = dept_combo.currentText()
        daily_wage = wage_spin.value()
        
        req = HireEmployeeRequest(
            name=name,
            role=role,
            department=department,
            daily_wage=daily_wage,
        )
        
        try:
            result = self.controller.hire_employee(req)
            print(f"Employee hired: {result}")
            self._refresh_state()
        except Exception as e:
            print(f"Error hiring employee: {e}")
    
    def _on_employee_selected(self, item) -> None:
        """Handle employee selection."""
        emp_id = item.data(Qt.UserRole)
        # Could show details or perform actions on selected employee
