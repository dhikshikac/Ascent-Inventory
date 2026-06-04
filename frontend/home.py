from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QGridLayout, QFrame
from PyQt6.QtCore import Qt
import backend.departments as departments
import backend.employees as employees

class DeptCard(QFrame):
    def __init__(self, dept_name, emp_count):
        super().__init__()
        self.setFixedSize(200, 120)
        self.setFrameShape(QFrame.Shape.Box)
        layout = QVBoxLayout()
        self.setLayout(layout)
        name_label = QLabel(dept_name)
        count_label = QLabel(f"👥 {emp_count} employees")
        layout.addWidget(name_label)
        layout.addWidget(count_label)


class HomeScreen(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)

        title = QLabel("Company Directory")
        layout.addWidget(title)

        grid = QGridLayout()
        layout.addLayout(grid)

        all_depts = departments.get_all_depts()

        for i, dept in enumerate(all_depts):
            dept_id = dept["id"]
            dept_name = dept["name"]
            emp_count = len(employees.get_all_dept_employees(dept_id))
            card = DeptCard(dept_name, emp_count)
            row = i // 4
            col = i % 4
            grid.addWidget(card, row, col)