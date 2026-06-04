import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QListWidget, QTableWidget, QTableWidgetItem, QLabel 
)
from PyQt6.QtCore import Qt

import backend.database as database
import backend.departments as departments
import backend.employees as employees

database.init()

class SheetView(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ascent Inventory Sheet")
        self.resize(800, 600)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        left = QVBoxLayout()
        main_layout.addLayout(left, 1)

        right = QVBoxLayout()
        main_layout.addLayout(right, 3)

        left.addWidget(QLabel("Departments"))
        self.dept_list = QListWidget()
        left.addWidget(self.dept_list)

        right.addWidget(QLabel("Employees"))
        self.employee_table = QTableWidget()
        self.employee_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.employee_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        right.addWidget(self.employee_table)

        self.dept_list.currentRowChanged.connect(self.on_dept_selected)

        self.load_depts()

    def load_depts(self):
        self.dept_list.clear()
        self.all_depts = departments.get_all_depts()

        self.dept_list.addItems(["All Employees"])
        for dept in self.all_depts:
            parent = next((d for d in self.all_depts if d["id"] == dept["parent_id"]), None)
            prefix = "  └ " if parent else ""
            self.dept_list.addItem(f"{prefix}{dept['name']}")

        self.dept_list.setCurrentRow(0)

    def on_dept_selected(self, row):
        if row == 0:
            self.show_employees(employees.get_all_employees())
        else:
            dept = self.all_depts[row - 1]
            self.show_employees(employees.get_employees_by_dept(dept["id"]))
        
    def show_employees(self, employee_list):
        columns = ["employee_id", "first_name", "last_name", "dept_id", "pc_model", "monitor_model", "ram", "storage", "os_version", "webcam_specs", "desk_phone", "notes"]
        headers = ["ID", "First Name", "Last Name", "Department", "PC", "Monitor", "RAM", "Storage", "OS Version", "Webcam", "Desk Phone", "Notes"]

        self.employee_table.setRowCount(len(employee_list))
        self.employee_table.setColumnCount(len(columns))
        self.employee_table.setHorizontalHeaderLabels(headers)

        for row, emp in enumerate(employee_list):
            for col, key in enumerate(columns):
                if(key == "dept_id"):
                    val = departments.get_name(emp.get("dept_id"))
                else:
                    val = emp.get(key)
                item = QTableWidgetItem(str(val) if val is not None else "")
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                self.employee_table.setItem(row, col, item)

        self.employee_table.resizeColumnsToContents()
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SheetView()
    window.show()
    sys.exit(app.exec())
