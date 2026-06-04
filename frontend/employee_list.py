from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QFrame, QPushButton, QHBoxLayout
from PyQt6.QtCore import pyqtSignal
import backend.employees as employees

class EmployeeCard(QFrame):
    def __init__(self, first_name, last_name, employee_id):
        super().__init__()
        self.setFrameShape(QFrame.Shape.Box)
        self.setFixedHeight(80)

        layout = QVBoxLayout()
        self.setLayout(layout)

        name_label = QLabel(f"{first_name} {last_name}")
        id_label = QLabel(employee_id)

        layout.addWidget(name_label)
        layout.addWidget(id_label)


class EmployeeListScreen(QWidget):
    back_clicked = pyqtSignal()

    def __init__(self, dept_id, dept_name):
        super().__init__()

        layout = QVBoxLayout()
        self.setLayout(layout)

    
        back_btn = QPushButton("← All Departments")
        back_btn.clicked.connect(self.back_clicked.emit)
        layout.addWidget(back_btn)

  
        title = QLabel(dept_name)
        layout.addWidget(title)

    

        emp_list = employees.get_all_dept_employees(dept_id)
        count_label = QLabel(f"{len(emp_list)} employees")
        layout.addWidget(count_label)

        for emp in emp_list:
            card = EmployeeCard(emp["first_name"], emp["last_name"], emp["employee_id"])
            layout.addWidget(card)