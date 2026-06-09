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
from frontend.detail_panel import EmployeeDetailView, InventoryDetailView

_LIST_IDX   = 0
_DETAIL_IDX = 1
_INV_DETAIL_IDX = 2


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
        self._header.set_search_visible(False)
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
        self._current_dept_id: int | None = None
        self._current_dept_name: str = ""

    # ── Slots ─────────────────────────────────────────────────────────────

    def _on_dept_selected(self, dept_id: int, dept_name: str):
        self._current_dept_id = dept_id
        self._current_dept_name = dept_name
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
        self._current_dept_id = None
        self._current_dept_name = ""
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


def run():
    import backend.database as database
    #from seed import seed

    database.init()
    #seed()

    app = QApplication(sys.argv)
    app.setApplicationName("Ascent Inventory")

    window = MainWindow()
    window.show()
    sys.exit(app.exec())