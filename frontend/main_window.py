# frontend/main_window.py
# Two-panel layout: sidebar (left) + stacked right panel (list ↔ detail)

import sys
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QApplication
)

from frontend.theme import load_stylesheet, WINDOW_MAX_HEIGHT, WINDOW_MIN_WIDTH
from frontend.header import HeaderBar
from frontend.sidebar import Sidebar
from frontend.employee_table import EmployeeListView
from frontend.detail_panel import EmployeeDetailView

_LIST_IDX   = 0
_DETAIL_IDX = 1


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ascent — Inventory")
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MAX_HEIGHT)
        self.resize(1200, 760)
        self.setStyleSheet(load_stylesheet())

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header ────────────────────────────────────────────────────────
        self._header = HeaderBar(show_search=True)
        self._header.search_changed.connect(self._on_search)
        root.addWidget(self._header)

        # ── Body ──────────────────────────────────────────────────────────
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        # Left: sidebar
        self._sidebar = Sidebar()
        self._sidebar.dept_selected.connect(self._on_dept_selected)
        body.addWidget(self._sidebar)

        # Right: stacked widget — list view OR detail view
        self._stack = QStackedWidget()

        self._list_view = EmployeeListView()
        self._list_view.employee_selected.connect(self._show_detail)
        self._list_view.data_changed.connect(self._sidebar.refresh)

        self._detail_view = EmployeeDetailView()
        self._detail_view.back_clicked.connect(self._show_list)
        self._detail_view.data_changed.connect(self._on_detail_data_changed)

        self._stack.addWidget(self._list_view)   # index 0
        self._stack.addWidget(self._detail_view) # index 1

        body.addWidget(self._stack, 1)
        root.addLayout(body, 1)

        self._sidebar.refresh()
        self._current_dept_id: int | None = None
        self._current_dept_name: str = ""

    # ── Slots ─────────────────────────────────────────────────────────────

    def _on_dept_selected(self, dept_id: int, dept_name: str):
        self._current_dept_id = dept_id
        self._current_dept_name = dept_name
        self._list_view.set_department(dept_id, dept_name)
        self._stack.setCurrentIndex(_LIST_IDX)
        self._header.clear_search()

    def _show_detail(self, employee_id: str):
        self._detail_view.load(employee_id)
        self._stack.setCurrentIndex(_DETAIL_IDX)

    def _show_list(self):
        self._list_view.refresh()
        self._stack.setCurrentIndex(_LIST_IDX)

    def _on_detail_data_changed(self):
        # After an edit/delete in detail, refresh the list underneath
        self._list_view.refresh()
        self._sidebar.refresh()

    def _on_search(self, text: str):
        # Search only applies to the list view
        if self._stack.currentIndex() == _LIST_IDX:
            self._list_view.apply_filter(text)


def run():
    import backend.database as database
    from seed import seed

    database.init()
    seed()

    app = QApplication(sys.argv)
    app.setApplicationName("Ascent Inventory")

    window = MainWindow()
    window.show()
    sys.exit(app.exec())