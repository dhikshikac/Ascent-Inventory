import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from frontend.home import HomeScreen
import backend.database as database
from seed import seed

database.init()
seed()

app = QApplication(sys.argv)

window = QMainWindow()
window.setWindowTitle("Ascent Inventory")
window.resize(1000, 700)

home = HomeScreen()
window.setCentralWidget(home)

window.show()
sys.exit(app.exec())