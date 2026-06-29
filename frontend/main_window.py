# frontend/main_window.py
# Two-panel layout: sidebar (left) + stacked right panel (list ↔ detail)

import sys
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QApplication, QDialog, QMessageBox
)

from frontend.theme import load_stylesheet, WINDOW_MIN_HEIGHT, WINDOW_MIN_WIDTH
from frontend.header import HeaderBar
from frontend.sidebar import Sidebar
from frontend.employee_table import EmployeeListView
from frontend.detail_panel import EmployeeDetailView, InventoryDetailView
from frontend import session
from frontend.api_client import ApiClient, ApiError, clear_client

_LIST_IDX   = 0
_DETAIL_IDX = 1
_INV_DETAIL_IDX = 2


class MainWindow(QMainWindow):
    def __init__(self, user=None):
        super().__init__()
        self._user = user or session.user() or {}
        self.setWindowTitle("Ascent — Inventory")
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.resize(1200, 760)
        self.setStyleSheet(load_stylesheet())

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        #Header 
        self._header = HeaderBar(show_search=True)
        self._header.search_changed.connect(self._on_search)
        self._header.set_search_visible(False)
        root.addWidget(self._header)

        #Body 
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        #Left: Sidebar
        self._sidebar = Sidebar()
        self._sidebar.set_user(
            self._user.get("email", ""),
            self._user.get("role", "viewer"),
        )
        self._sidebar.sign_out_requested.connect(self._on_sign_out)
        self._sidebar.dept_selected.connect(self._on_dept_selected)
        self._sidebar.all_employees_selected.connect(self._on_all_employees_selected)
        self._sidebar.width_changed.connect(self._header.set_brand_width)

        body.addWidget(self._sidebar)

        #Right: list view OR detail view
        self._stack = QStackedWidget()

        self._list_view = EmployeeListView()
        self._list_view.employee_selected.connect(self._show_detail)
        self._list_view.computer_selected.connect(lambda comp_id: self._show_inventory_detail("Computer", comp_id))
        self._list_view.instrument_selected.connect(lambda inst_id: self._show_inventory_detail("Instrument", inst_id))
        self._list_view.data_changed.connect(self._sidebar.refresh)
        self._list_view.department_deleted.connect(self._on_department_deleted)
        self._list_view.search_available_changed.connect(self._on_search_available_changed)

        self._detail_view = EmployeeDetailView()
        self._detail_view.back_clicked.connect(self._show_list)
        self._detail_view.data_changed.connect(self._on_detail_data_changed)

        self._inventory_detail_view = InventoryDetailView()
        self._inventory_detail_view.back_clicked.connect(self._show_list)
        self._inventory_detail_view.data_changed.connect(self._on_detail_data_changed)

        self._stack.addWidget(self._list_view)   # index 0
        self._stack.addWidget(self._detail_view) # index 1
        self._stack.addWidget(self._inventory_detail_view) # index 2

        body.addWidget(self._stack, 1)
        root.addLayout(body, 1)

        self._sidebar.refresh()

    #Slots

    def _on_all_employees_selected(self):
        self._stack.setCurrentIndex(_LIST_IDX)
        self._header.clear_search()
        self._list_view.set_all_employees()

    def _on_dept_selected(self, dept_id: int, dept_name: str):
        self._stack.setCurrentIndex(_LIST_IDX)
        self._header.clear_search()
        self._list_view.set_department(dept_id, dept_name)

    def _show_detail(self, employee_id: str):
        self._header.set_search_visible(False)
        self._detail_view.load(employee_id)
        self._stack.setCurrentIndex(_DETAIL_IDX)

    def _show_inventory_detail(self, kind: str, record_id: int):
        self._header.set_search_visible(False)
        self._inventory_detail_view.load(kind, record_id)
        self._stack.setCurrentIndex(_INV_DETAIL_IDX)

    def _show_list(self):
        self._list_view.refresh()
        self._stack.setCurrentIndex(_LIST_IDX)
        self._header.set_search_visible(self._list_view.has_inventory_rows())

    def _on_detail_data_changed(self):
        self._list_view.refresh()
        self._sidebar.refresh()

    def _on_department_deleted(self):
        self._sidebar.clear_selection()
        self._sidebar.refresh()
        self._list_view.clear_department()
        self._header.clear_search()
        self._header.set_search_visible(False)

    def _on_search_available_changed(self, available: bool):
        if self._stack.currentIndex() == _LIST_IDX:
            self._header.set_search_visible(available)

    def _on_search(self, text: str):
        if self._stack.currentIndex() == _LIST_IDX:
            self._list_view.apply_filter(text)

    def _on_sign_out(self):
        reply = QMessageBox.question(
            self,
            "Sign out",
            "Sign out of Ascent Inventory?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        clear_client()
        session.clear()
        QApplication.instance().quit()


def authenticate():
    from frontend.login_window import LoginDialog
    from backend.auth_client import sign_in, AuthError
    from backend import api_server

    try:
        api_server.ensure_running()
    except RuntimeError as exc:
        QMessageBox.critical(None, "Server", str(exc))
        return None

    login = LoginDialog()
    if login.exec() != QDialog.DialogCode.Accepted:
        return None

    try:
        auth_session = sign_in(login.email(), login.password())
    except AuthError as exc:
        QMessageBox.critical(None, "Login failed", exc.message)
        return None
    except Exception as exc:
        QMessageBox.critical(None, "Login failed", str(exc))
        return None

    client = ApiClient(auth_session["id_token"], auth_session.get("refresh_token"))
    from frontend.api_client import set_client
    set_client(client)

    try:
        user = client.get("/me")
    except ApiError as exc:
        QMessageBox.critical(None, "Login failed", exc.message)
        clear_client()
        return None

    session.set_session(user, auth_session.get("refresh_token"))
    return user


def run():
    from backend import api_server

    app = QApplication(sys.argv)
    app.setApplicationName("Ascent Inventory")
    app.aboutToQuit.connect(api_server.stop)

    user = authenticate()
    if user is None:
        sys.exit(0)

    window = MainWindow(user=user)
    window.show()
    sys.exit(app.exec())
