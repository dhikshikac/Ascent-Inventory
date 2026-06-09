from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidgetItem, QAbstractItemView,
    QHeaderView, QMessageBox,
) 
from PyQt6.QtCore import Qt, pyqtSignal

import backend.employees as employees
import backend.departments as departments
import backend.computers as computers
import backend.instruments as instruments
from frontend.widgets import primary_button, danger_button, empty_state, HoverTableWidget
from frontend.dialogs import AddEmployeeDialog, AddComputerDialog, AddInstrumentDialog

_COLUMNS = [
    ("Type", "kind"),
    ("Name", "name"),
    ("ID / Serial", "identifier"),
    ("Department / Owner", "owner"),
    ("Details", "details"),
    ("Notes", "notes"),
]

class EmployeeListView(QWidget):
    employee_selected = pyqtSignal(str)
    data_changed = pyqtSignal()
    department_deleted = pyqtSignal()
    search_visibility_changed = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ContentPanel")

        self._dept_id: int | None = None
        self._dept_name: str = ""
        self._filter: str = ""
        self._all_rows: list[dict] = []
        self._computers_by_employee: dict[str, list[dict]] = {}
 
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        sub_header = QWidget(self)
        sub_header.setStyleSheet("background-color: #F9FAFB; border-bottom: 1px solid #E5E7EB;")
        sub_header.setFixedHeight(72)
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

        self._add_dev_btn = primary_button("+ Add Computer")
        self._add_dev_btn.setEnabled(False)
        self._add_dev_btn.clicked.connect(self._add_device)
        sub_header_layout.addWidget(self._add_dev_btn)

        self._add_inst_btn = primary_button("+ Add Instrument")
        self._add_inst_btn.setEnabled(False)
        self._add_inst_btn.clicked.connect(self._add_instrument)
        sub_header_layout.addWidget(self._add_inst_btn)

        self._delete_dept_btn = danger_button("Delete Department")
        self._delete_dept_btn.setEnabled(False)
        self._delete_dept_btn.clicked.connect(self._delete_department)
        sub_header_layout.addWidget(self._delete_dept_btn)

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
        self._table.setColumnWidth(0, 105)
        self._table.setColumnWidth(1, 190)
        self._table.setColumnWidth(2, 120)
        self._table.setColumnWidth(3, 210)
        self._table.setColumnWidth(4, 300)
        layout.addWidget(self._table, 1)
 
        self._empty = empty_state("No employees, computers, or instruments in this department.")
        self._empty.hide()
        layout.addWidget(self._empty, 1)

    def set_department(self, dept_id: int, dept_name: str):
        self._dept_id = dept_id
        self._dept_name = dept_name
        self._dept_label.setText(dept_name)
        for btn in (self._add_emp_btn, self._add_dev_btn, self._add_inst_btn, self._delete_dept_btn):
            btn.setEnabled(True)
        self.refresh()

    def clear_department(self):
        self._dept_id = None
        self._dept_name = ""
        self._filter = ""
        self._all_rows = []
        self._computers_by_employee = {}
        self._dept_label.setText("Select a department")
        self._count_label.setText("")
        for btn in (self._add_emp_btn, self._add_dev_btn, self._add_inst_btn, self._delete_dept_btn):
            btn.setEnabled(False)
        self._table.setRowCount(0)
        self._table.hide()
        self._empty.hide()
        self.search_visibility_changed.emit(False)

    def has_searchable_rows(self) -> bool:
        return bool(self._all_rows)
 
    def apply_filter(self, text: str):
        self._filter = text.lower()
        self._render()
 
    def refresh(self):
        if self._dept_id is None:
            self.search_visibility_changed.emit(False)
            return

        dept_ids = departments.get_descendant_dept_ids(self._dept_id)
        employee_rows = employees.get_all_dept_employees(self._dept_id)
        employee_ids = [emp["employee_id"] for emp in employee_rows]
        computer_rows = computers.get_computers_for_depts(dept_ids, employee_ids)
        instrument_rows = instruments.get_instruments_for_depts(dept_ids)

        self._computers_by_employee = {}
        for computer in computer_rows:
            employee_id = computer.get("employee_id")
            if employee_id:
                self._computers_by_employee.setdefault(employee_id, []).append(computer)

        employee_lookup = {emp["employee_id"]: emp for emp in employee_rows}
        rows = []
        rows.extend(self._employee_row(emp) for emp in employee_rows)
        rows.extend(self._computer_row(computer, employee_lookup) for computer in computer_rows)
        rows.extend(self._instrument_row(inst) for inst in instrument_rows)
        self._all_rows = rows
        self._render()
  
    def _render(self):
        f = self._filter
        rows = [
            row for row in self._all_rows
            if not f or f in row["search"]
        ]
 
        self._table.setRowCount(0)
        if not rows:
            self._table.hide(); self._empty.show()
            self._count_label.setText("No matching items" if self._all_rows else "")
            self.search_visibility_changed.emit(bool(self._all_rows))
            return
 
        self._empty.hide(); self._table.show()
        self._count_label.setText(self._count_text(rows))
        self._table.setRowCount(len(rows))
 
        for r, row in enumerate(rows):
            vals = [
                row["type"],
                row["name"],
                row["identifier"],
                row["owner"],
                row["details"],
                row["notes"],
            ]
            for c, val in enumerate(vals):
                item = QTableWidgetItem(str(val))
                item.setData(Qt.ItemDataRole.UserRole, row["payload"])
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self._table.setItem(r, c, item)
            self._table.setRowHeight(r, 40)
            self._table._repaint_row(r)
        self.search_visibility_changed.emit(True)
 
    def _on_selection(self):
        sel = self._table.selectedItems()
        if not sel:
            return
        payload = sel[0].data(Qt.ItemDataRole.UserRole)
        if payload.get("kind") == "employee":
            self.employee_selected.emit(payload["id"])

    def _employee_row(self, emp: dict) -> dict:
        name = f"{emp.get('first_name', '')} {emp.get('last_name', '')}".strip()
        row = {
            "type": "Employee",
            "name": name,
            "identifier": emp.get("employee_id", ""),
            "owner": departments.get_name(emp.get("dept_id")),
            "details": self._employee_device_preview(emp.get("employee_id")),
            "notes": emp.get("notes") or "",
            "payload": {"kind": "employee", "id": emp.get("employee_id")},
        }
        row["search"] = self._search_blob(row)
        return row

    def _computer_row(self, computer: dict, employee_lookup: dict[str, dict]) -> dict:
        employee_id = computer.get("employee_id")
        owner = departments.get_name(computer.get("dept_id") or computer.get("lab_id"))
        if employee_id and employee_id in employee_lookup:
            emp = employee_lookup[employee_id]
            owner = f"{emp.get('first_name', '')} {emp.get('last_name', '')} ({employee_id})".strip()
        elif employee_id:
            owner = employee_id

        row = {
            "type": "Computer",
            "name": self._computer_title(computer),
            "identifier": f"#{computer.get('id')}",
            "owner": owner,
            "details": self._computer_specs(computer),
            "notes": computer.get("notes") or "",
            "payload": {"kind": "computer", "id": computer.get("id")},
        }
        row["search"] = self._search_blob(row)
        return row

    def _instrument_row(self, instrument: dict) -> dict:
        row = {
            "type": "Instrument",
            "name": instrument.get("model_name") or f"Instrument #{instrument.get('id')}",
            "identifier": instrument.get("serial_number") or f"#{instrument.get('id')}",
            "owner": departments.get_name(instrument.get("lab_id")),
            "details": "Lab instrument",
            "notes": instrument.get("notes") or "",
            "payload": {"kind": "instrument", "id": instrument.get("id")},
        }
        row["search"] = self._search_blob(row)
        return row

    def _employee_device_preview(self, employee_id: str) -> str:
        employee_computers = self._computers_by_employee.get(employee_id, [])
        if not employee_computers:
            return "No computer assigned"

        previews = []
        for computer in employee_computers[:2]:
            title = self._computer_title(computer)
            specs = self._computer_specs(computer)
            previews.append(f"{title} - {specs}" if specs else title)
        if len(employee_computers) > 2:
            previews.append(f"+{len(employee_computers) - 2} more")
        return "; ".join(previews)

    def _computer_title(self, computer: dict) -> str:
        return computer.get("pc_model") or computer.get("monitor_model") or f"Computer #{computer.get('id')}"

    def _computer_specs(self, computer: dict) -> str:
        specs = [
            computer.get("monitor_model"),
            computer.get("ram"),
            computer.get("storage"),
            computer.get("os_version"),
        ]
        return " | ".join(spec for spec in specs if spec)

    def _search_blob(self, row: dict) -> str:
        return " ".join(str(row.get(key) or "") for key in ("type", "name", "identifier", "owner", "details", "notes")).lower()

    def _count_text(self, rows: list[dict]) -> str:
        counts = {"Employee": 0, "Computer": 0, "Instrument": 0}
        for row in rows:
            counts[row["type"]] += 1
        total = len(rows)
        parts = [
            f"{counts['Employee']} employee{'s' if counts['Employee'] != 1 else ''}",
            f"{counts['Computer']} computer{'s' if counts['Computer'] != 1 else ''}",
            f"{counts['Instrument']} instrument{'s' if counts['Instrument'] != 1 else ''}",
        ]
        return f"{total} item{'s' if total != 1 else ''} - " + ", ".join(parts)
 
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
            self.data_changed.emit()
            self.refresh()
 
    def _add_instrument(self):
        if self._dept_id is None:
            return
        dlg = AddInstrumentDialog(lab_id=self._dept_id, parent=self)
        if dlg.exec() == AddInstrumentDialog.DialogCode.Accepted:
            self.data_changed.emit()
            self.refresh()

    def _delete_department(self):
        if self._dept_id is None:
            return

        impact = departments.get_delete_impact(self._dept_id)
        dept_note = ""
        if impact["departments"] > 1:
            dept_note = f"\nThis also removes {impact['departments'] - 1} sub-department(s)."

        reply = QMessageBox.warning(
            self,
            "Delete Department",
            (
                f"Delete '{self._dept_name}'?\n\n"
                "This will permanently delete the department and its employees, "
                "instruments, and devices/computers.\n\n"
                f"Employees: {impact['employees']}\n"
                f"Computers/devices: {impact['computers']}\n"
                f"Instruments: {impact['instruments']}"
                f"{dept_note}"
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if reply == QMessageBox.StandardButton.Yes:
            departments.delete_dept_by_id(self._dept_id)
            self.clear_department()
            self.department_deleted.emit()
            self.data_changed.emit()