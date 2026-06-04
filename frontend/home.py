from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QGridLayout, QFrame
from PyQt6.QtCore import Qt, pyqtSignal
import backend.departments as departments
import backend.employees as employees

class DeptCard(QFrame):
    clicked = pyqtSignal(int, str)  

    def __init__(self, dept_id, dept_name, emp_count):
        super().__init__()
        self.dept_id = dept_id
        self.dept_name = dept_name

        self.setFixedSize(200, 120)
        self.setFrameShape(QFrame.Shape.Box)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout()
        self.setLayout(layout)

        name_label = QLabel(dept_name)
        count_label = QLabel(f"👥 {emp_count} employees")
        layout.addWidget(name_label)
        layout.addWidget(count_label)

    def mousePressEvent(self, event):
        self.clicked.emit(self.dept_id, self.dept_name)


class HomeScreen(QWidget):
    dept_clicked = pyqtSignal(int, str)

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
            card = DeptCard(dept_id, dept_name, emp_count)
            card.clicked.connect(self.dept_clicked.emit)
            row = i // 4
            col = i % 4
            grid.addWidget(card, row, col)