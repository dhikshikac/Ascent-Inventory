from PyQt6.QtWidgets import (QWidget, QLabel, QVBoxLayout, QFrame, 
                              QPushButton, QLineEdit, QScrollArea)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont
import backend.employees as employees

class EmployeeCard(QFrame):
    def __init__(self, first_name, last_name, employee_id):
        super().__init__()
        self.setFixedHeight(90)
        self.setStyleSheet("""
            EmployeeCard {
                background-color: #f9f9f7;
                border: 1px solid #ddd;
                border-radius: 8px;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 12, 20, 12)
        self.setLayout(layout)

        name_label = QLabel(f"{first_name} {last_name}")
        name_label.setFont(QFont("Georgia", 13))
        layout.addWidget(name_label)

        id_label = QLabel(employee_id)
        id_label.setFont(QFont("Courier", 10))
        id_label.setStyleSheet("color: #666;")
        layout.addWidget(id_label)


class EmployeeListScreen(QWidget):
    back_clicked = pyqtSignal()

    def __init__(self, dept_id, dept_name):
        super().__init__()
        self.all_employees = employees.get_all_dept_employees(dept_id)
        self.setStyleSheet("background-color: #ffffff;")

        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(16)
        self.setLayout(layout)

        back_btn = QPushButton("← All Departments")
        back_btn.setFixedWidth(180)
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.setStyleSheet("""
            QPushButton {
                background: none;
                border: none;
                color: #444;
                font-size: 13px;
                text-align: left;
                padding: 0;
            }
            QPushButton:hover {
                color: #000;
            }
        """)
        back_btn.clicked.connect(self.back_clicked.emit)
        layout.addWidget(back_btn)

        title = QLabel(dept_name)
        title.setFont(QFont("Georgia", 26))
        layout.addWidget(title)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search employees...")
        self.search_bar.setFixedHeight(40)
        self.search_bar.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ccc;
                border-radius: 20px;
                padding: 0 16px;
                font-size: 14px;
                background-color: #f9f9f9;
            }
        """)
        self.search_bar.textChanged.connect(self.filter_employees)
        layout.addWidget(self.search_bar)

        self.count_label = QLabel(f"{len(self.all_employees)} employees")
        self.count_label.setStyleSheet("color: #666; font-size: 13px;")
        layout.addWidget(self.count_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.list_container = QWidget()
        self.list_layout = QVBoxLayout()
        self.list_layout.setSpacing(10)
        self.list_container.setLayout(self.list_layout)

        scroll.setWidget(self.list_container)
        layout.addWidget(scroll)

        self.render_employees(self.all_employees)

    def render_employees(self, emp_list):
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.count_label.setText(f"{len(emp_list)} employees")

        for emp in emp_list:
            card = EmployeeCard(emp["first_name"], emp["last_name"], emp["employee_id"])
            self.list_layout.addWidget(card)

    def filter_employees(self, text):
        filtered = [e for e in self.all_employees
                    if text.lower() in e["first_name"].lower()
                    or text.lower() in e["last_name"].lower()
                    or text.lower() in e["employee_id"].lower()]
        self.render_employees(filtered)