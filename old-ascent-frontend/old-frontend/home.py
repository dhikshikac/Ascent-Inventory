from PyQt6.QtWidgets import (QWidget, QLabel, QVBoxLayout, QGridLayout, 
                              QFrame, QLineEdit, QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
import backend.departments as departments
import backend.employees as employees

class DeptCard(QFrame):
    clicked = pyqtSignal(int, str)

    def __init__(self, dept_id, dept_name, emp_count):
        super().__init__()
        self.dept_id = dept_id
        self.dept_name = dept_name

        self.setFixedSize(220, 130)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            DeptCard {
                background-color: #f9f9f7;
                border: 1px solid #ddd;
                border-radius: 8px;
            }
            DeptCard:hover {
                border: 1px solid #999;
                background-color: #f0f0ec;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        self.setLayout(layout)

        folder_label = QLabel("🗂")
        folder_label.setFont(QFont("Arial", 20))
        layout.addWidget(folder_label)

        name_label = QLabel(dept_name)
        name_label.setFont(QFont("Georgia", 13))
        layout.addWidget(name_label)

        count_label = QLabel(f"👥  {emp_count} employees")
        count_label.setFont(QFont("Courier", 10))
        count_label.setStyleSheet("color: #666;")
        layout.addWidget(count_label)

    def mousePressEvent(self, event):
        self.clicked.emit(self.dept_id, self.dept_name)


class HomeScreen(QWidget):
    dept_clicked = pyqtSignal(int, str)

    def __init__(self):
        super().__init__()
        self.all_depts = departments.get_all_depts()
        self.setStyleSheet("background-color: #ffffff;")

        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        self.setLayout(layout)

        title = QLabel("Company Directory")
        title.setFont(QFont("Georgia", 26))
        layout.addWidget(title)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search departments...")
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
        self.search_bar.textChanged.connect(self.filter_depts)
        layout.addWidget(self.search_bar)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.grid_widget = QWidget()
        self.grid = QGridLayout()
        self.grid.setSpacing(16)
        self.grid_widget.setLayout(self.grid)

        scroll.setWidget(self.grid_widget)
        layout.addWidget(scroll)

        self.render_cards(self.all_depts)

    def render_cards(self, dept_list):
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for i, dept in enumerate(dept_list):
            dept_id = dept["id"]
            dept_name = dept["name"]
            emp_count = len(employees.get_all_dept_employees(dept_id))
            card = DeptCard(dept_id, dept_name, emp_count)
            card.clicked.connect(self.dept_clicked.emit)
            row = i // 4
            col = i % 4
            self.grid.addWidget(card, row, col)

    def filter_depts(self, text):
        filtered = [d for d in self.all_depts if text.lower() in d["name"].lower()]
        self.render_cards(filtered)

        #hi 