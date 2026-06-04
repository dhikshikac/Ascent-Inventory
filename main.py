import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from frontend.home import HomeScreen
from frontend.employee_list import EmployeeListScreen
import backend.database as database
from seed import seed

database.init()
seed()

app = QApplication(sys.argv)

window = QMainWindow()
window.setWindowTitle("Ascent Inventory")
window.resize(1000, 700)

def show_home():
    home = HomeScreen()
    home.dept_clicked.connect(show_employee_list)
    window.setCentralWidget(home)

def show_employee_list(dept_id, dept_name):
    emp_screen = EmployeeListScreen(dept_id, dept_name)
    emp_screen.back_clicked.connect(show_home)
    window.setCentralWidget(emp_screen)

show_home()
window.show()
sys.exit(app.exec())