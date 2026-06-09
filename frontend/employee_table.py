from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidgetItem, QAbstractItemView,
    QHeaderView,
) 
from PyQt6.QtCore import Qt, pyqtSignal

import backend.employees as employees
import backend.departments as departments
from frontend.widgets import primary_button, ghost_button, empty_state, HoverTableWidget
from frontend.dialogs import AddEmployeeDialog, AddComputerDialog, AddInstrumentDialog

_COLUMNS = [
    ("Employee ID", "employee_id"),
    ("First Name", "first_name"),
    ("Last Name", "last_name"),
    ("Department", "_dept_name"),
    ("Notes", "_notes"),
]

class EmployeeListView(QWidget):
    employee_selected = pyqtSignal(str)
    data_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ContentPanel")

        self._dept_id: int | None = None
        self._filter: str = ""
        self._all_rows: list[dict] = []
 
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        sub_header = QWidget(self)
        sub_header.setStyleSheet("background-color: #F9FAFB; border-bottom: 1px solid #E5E7EB;")
        sub_header_layout = QHBoxLayout(sub_header)
        sub_header_layout.setContentsMargins(20, 14, 20, 14)
        sub_header_layout.setSpacing(8)

        self._dept_label = QLabel("Select a department")
        self._dept_label.setObjectName("DetailName")
        sub_header_layout.addWidget(self._dept_label)

        self._count_label = QLabel("")
        self._count_label.setObjectName("DetailId")
        sub_header_layout.addWidget(self._count_label)
        sub_header_layout.addStretch()

        self._add_emp_btn = primary_button("+ Add Employee")
        self._add_emp_btn.setEnabled(False)
        self._add_emp_btn.clicked.connect(self._add_employee)
        sub_header_layout.addWidget(self._add_emp_btn)

        self._add_dev_btn = ghost_button("+ Add Device")
        self._add_dev_btn.setEnabled(False)
        self._add_dev_btn.clicked.connect(self._add_device)
        sub_header_layout.addWidget(self._add_dev_btn)

        self._add_inst_btn = ghost_button("+ Add Instrument")
        self._add_inst_btn.setEnabled(False)
        self._add_inst_btn.clicked.connect(self._add_instrument)
        sub_header_layout.addWidget(self._add_inst_btn)

        layout.addWidget(sub_header)

        self._table = HoverTableWidget()
        self._table.setColumnCount(len(_COLUMNS))
        self._table.setHorizontalHeaderLabels([c[0] for c in _COLUMNS])
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(False)
        self._table.verticalHeader().setVisible(False)
        self._table.setShowGrid(False)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self._table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._table.itemSelectionChanged.connect(self._on_selection)
        self._table.setColumnWidth(0, 130)
        self._table.setColumnWidth(1, 130)
        self._table.setColumnWidth(2, 140)
        self._table.setColumnWidth(3, 170)
        layout.addWidget(self._table, 1)
 
        self._empty = empty_state("No employees in this department.")
        self._empty.hide()
        layout.addWidget(self._empty)

    def set_department(self, dept_id: int, dept_name: str):
        self._dept_id = dept_id
        self._dept_label.setText(dept_name)
        for btn in (self._add_emp_btn, self._add_dev_btn, self._add_inst_btn):
            btn.setEnabled(True)
        self.refresh()
 
    def apply_filter(self, text: str):
        self._filter = text.lower()
        self._render()
 
    def refresh(self):
        if self._dept_id is None:
            return
        self._all_rows = employees.get_all_dept_employees(self._dept_id)
        self._render()
  
    def _render(self):
        f = self._filter
        rows = [
            e for e in self._all_rows
            if not f
            or f in (e.get("employee_id") or "").lower()
            or f in (e.get("first_name") or "").lower()
            or f in (e.get("last_name") or "").lower()
        ]
 
        self._table.setRowCount(0)
        if not rows:
            self._table.hide(); self._empty.show()
            self._count_label.setText("")
            return
 
        self._empty.hide(); self._table.show()
        self._count_label.setText(f"{len(rows)} employee{'s' if len(rows) != 1 else ''}")
        self._table.setRowCount(len(rows))
 
        for r, emp in enumerate(rows):
            vals = [
                emp.get("employee_id", ""),
                emp.get("first_name", ""),
                emp.get("last_name", ""),
                departments.get_name(emp.get("dept_id")),
                emp.get("notes", "") or "",
            ]
            for c, val in enumerate(vals):
                item = QTableWidgetItem(str(val))
                item.setData(Qt.ItemDataRole.UserRole, emp["employee_id"])
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self._table.setItem(r, c, item)
            self._table.setRowHeight(r, 40)
 
    def _on_selection(self):
        sel = self._table.selectedItems()
        if sel:
            self.employee_selected.emit(sel[0].data(Qt.ItemDataRole.UserRole))
 
    def _add_employee(self):
        if self._dept_id is None:
            return
        dlg = AddEmployeeDialog(dept_id=self._dept_id, parent=self)
        if dlg.exec() == AddEmployeeDialog.DialogCode.Accepted:
            self.data_changed.emit()
            self.refresh()
 
    def _add_device(self):
        if self._dept_id is None:
            return
        dlg = AddComputerDialog(dept_id=self._dept_id, parent=self)
        if dlg.exec() == AddComputerDialog.DialogCode.Accepted:
            self.refresh()
 
    def _add_instrument(self):
        if self._dept_id is None:
            return
        dlg = AddInstrumentDialog(lab_id=self._dept_id, parent=self)
        if dlg.exec() == AddInstrumentDialog.DialogCode.Accepted:
            self.refresh()