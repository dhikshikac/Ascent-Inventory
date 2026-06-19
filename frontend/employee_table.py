from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidgetItem, QAbstractItemView,
    QHeaderView, QMessageBox, QScrollArea, QStyle, QStyleOptionHeader,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QRect
from PyQt6.QtGui import QIcon, QPalette

import os
import frontend.services.employees as employees
import frontend.services.departments as departments
import frontend.services.computers as computers
import frontend.services.instruments as instruments
from frontend import session
from frontend.api_client import ApiError
from frontend.widgets import primary_button, danger_button, empty_state, HoverTableWidget, computer_label
from frontend.dialogs import AddEmployeeDialog, AddComputerDialog, AddInstrumentDialog

_COLUMNS = [
    ("Type", "_kind"),
    ("ID", "_item_id"),
    ("Name", "_name"),
    ("Department", "_dept_name"),
    ("Device Preview", "_devices"),
    ("Notes", "_notes"),
]

# Columns used in the All Employees view
_ALL_EMP_COLUMNS = [
    ("Name", "_name"),
    ("Employee ID", "_item_id"),
    ("Department", "_dept_name"),
    ("Device Preview", "_devices"),
]

_MEDIA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "media")
_SORT_ICON_SIZE = QSize(16, 16)


def _sort_icon(filename: str) -> QIcon:
    icon = QIcon()
    icon.addFile(os.path.join(_MEDIA_DIR, filename), _SORT_ICON_SIZE)
    return icon


class _AllEmpHeaderView(QHeaderView):
    _SORT_COL = 0
    _ICON_MARGIN = 10
    _TEXT_MARGIN = 10

    def __init__(self, icon_getter, parent=None):
        super().__init__(Qt.Orientation.Horizontal, parent)
        self._icon_getter = icon_getter
        self.setSectionsClickable(True)

    def paintSection(self, painter, rect, logical_index):
        model = self.model()
        text = ""
        if model:
            text = str(model.headerData(
                logical_index, self.orientation(), Qt.ItemDataRole.DisplayRole
            ) or "")

        opt = QStyleOptionHeader()
        self.initStyleOption(opt)
        opt.rect = rect
        opt.section = logical_index
        opt.textAlignment = (
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )

        if logical_index == self._SORT_COL:
            bg_opt = QStyleOptionHeader(opt)
            bg_opt.text = ""
            self.style().drawControl(QStyle.ControlElement.CE_Header, bg_opt, painter, self)

            icon = self._icon_getter()
            icon_w = _SORT_ICON_SIZE.width() if not icon.isNull() else 0
            text_right = rect.right() - icon_w - self._ICON_MARGIN
            text_rect = QRect(
                rect.left() + self._TEXT_MARGIN, rect.top(),
                text_right - rect.left() - self._TEXT_MARGIN, rect.height(),
            )
            painter.setPen(opt.palette.color(QPalette.ColorRole.WindowText))
            painter.drawText(
                text_rect,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                text,
            )
            if not icon.isNull():
                icon_rect = QRect(
                    rect.right() - icon_w - self._ICON_MARGIN,
                    rect.center().y() - _SORT_ICON_SIZE.height() // 2,
                    icon_w,
                    _SORT_ICON_SIZE.height(),
                )
                icon.paint(painter, icon_rect)
        else:
            opt.text = text
            self.style().drawControl(QStyle.ControlElement.CE_Header, opt, painter, self)


class EmployeeListView(QWidget):
    employee_selected = pyqtSignal(str)
    computer_selected = pyqtSignal(int)
    instrument_selected = pyqtSignal(int)
    data_changed = pyqtSignal()
    department_deleted = pyqtSignal()
    search_available_changed = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ContentPanel")

        self._dept_id: int | None = None
        self._dept_name: str = ""
        self._filter: str = ""
        self._all_rows: list[dict] = []
        self._is_all_employees: bool = False

        # Sort state for All Employees view: True = A→Z, False = Z→A
        self._all_emp_sort_asc: bool = True
        self._icon_sort_up = _sort_icon("up.svg")
        self._icon_sort_down = _sort_icon("down.svg")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        #Sub-header 
        sub_header = QWidget(self)
        sub_header.setObjectName("DepartmentHeader")
        sub_header_layout = QVBoxLayout(sub_header)
        sub_header_layout.setContentsMargins(20, 14, 20, 14)
        sub_header_layout.setSpacing(10)

        title_row = QHBoxLayout()
        title_row.setSpacing(8)

        self._dept_label = QLabel("Select a department")
        self._dept_label.setObjectName("DetailName")
        title_row.addWidget(self._dept_label)

        self._count_label = QLabel("")
        self._count_label.setObjectName("DetailId")
        title_row.addWidget(self._count_label)
        title_row.addStretch()
        sub_header_layout.addLayout(title_row)

        action_row = QHBoxLayout()
        action_row.setSpacing(8)
        action_row.addStretch()

        self._add_emp_btn = primary_button("+ Add Employee")
        self._add_emp_btn.setEnabled(False)
        self._add_emp_btn.clicked.connect(self._add_employee)
        action_row.addWidget(self._add_emp_btn)

        self._add_comp_btn = primary_button("+ Add Computer")
        self._add_comp_btn.setEnabled(False)
        self._add_comp_btn.clicked.connect(self._add_computer)
        action_row.addWidget(self._add_comp_btn)

        self._add_inst_btn = primary_button("+ Add Instrument")
        self._add_inst_btn.setEnabled(False)
        self._add_inst_btn.clicked.connect(self._add_instrument)
        action_row.addWidget(self._add_inst_btn)

        self._delete_dept_btn = danger_button("Delete Department")
        self._delete_dept_btn.setEnabled(False)
        self._delete_dept_btn.hide()
        self._delete_dept_btn.clicked.connect(self._delete_department)
        action_row.addWidget(self._delete_dept_btn)
        sub_header_layout.addLayout(action_row)

        self._admin_buttons = (
            self._add_emp_btn,
            self._add_comp_btn,
            self._add_inst_btn,
            self._delete_dept_btn,
        )
        self._apply_admin_visibility()

        layout.addWidget(sub_header)

        #Main table (department view) 
        self._table_scroll = QScrollArea()
        self._table_scroll.setWidgetResizable(True)
        self._table_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._table_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._table_scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        self._table = HoverTableWidget()
        self._table.setColumnCount(len(_COLUMNS))
        self._table.setHorizontalHeaderLabels([c[0] for c in _COLUMNS])
        for i in range(len(_COLUMNS)):
            header_item = self._table.horizontalHeaderItem(i)
            if header_item:
                header_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(False)
        self._table.verticalHeader().setVisible(False)
        self._table.setShowGrid(False)
        self._table.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        table_header = self._table.horizontalHeader()
        table_header.setMinimumSectionSize(80)
        table_header.setStretchLastSection(False)
        for col, width in ((0, 110), (1, 120), (3, 170)):
            table_header.setSectionResizeMode(col, QHeaderView.ResizeMode.Fixed)
            self._table.setColumnWidth(col, width)
        for col in (2, 4, 5):
            table_header.setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)
        self._table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._table.itemSelectionChanged.connect(self._on_selection)

        self._table_scroll.setWidget(self._table)
        layout.addWidget(self._table_scroll, 1)

        #All Employees table
        self._all_emp_table = HoverTableWidget()
        self._all_emp_header = _AllEmpHeaderView(self._current_sort_icon, self._all_emp_table)
        self._all_emp_table.setHorizontalHeader(self._all_emp_header)
        self._all_emp_table.setColumnCount(len(_ALL_EMP_COLUMNS))
        self._all_emp_table.setHorizontalHeaderLabels([c[0] for c in _ALL_EMP_COLUMNS])
        self._all_emp_header.setMinimumSectionSize(80)
        self._all_emp_header.setStretchLastSection(False)
        self._all_emp_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._all_emp_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self._all_emp_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self._all_emp_header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self._all_emp_table.setColumnWidth(1, 160)
        self._all_emp_table.setColumnWidth(2, 170)
        self._all_emp_table.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self._all_emp_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._all_emp_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._all_emp_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._all_emp_table.setAlternatingRowColors(False)
        self._all_emp_table.verticalHeader().setVisible(False)
        self._all_emp_table.setShowGrid(False)
        self._all_emp_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        # Clicking the Name header toggles sort direction
        self._all_emp_header.sectionClicked.connect(
            self._on_all_emp_header_clicked
        )
        self._all_emp_table.itemSelectionChanged.connect(self._on_all_emp_selection)
        self._all_emp_table.hide()
        layout.addWidget(self._all_emp_table, 1)

        #Empty state
        self._empty = empty_state("Select a department to view inventory.")
        self._empty_label = self._empty.findChild(QLabel)
        self._empty.hide()
        layout.addWidget(self._empty, 1)

    #Public API

    def _apply_admin_visibility(self):
        is_admin = session.is_admin()
        for btn in self._admin_buttons:
            btn.setVisible(is_admin)

    def set_department(self, dept_id: int, dept_name: str):
        self._is_all_employees = False
        self._dept_id = dept_id
        self._dept_name = dept_name
        self._dept_label.setText(dept_name)
        is_admin = session.is_admin()
        for btn in (self._add_emp_btn, self._add_comp_btn, self._add_inst_btn, self._delete_dept_btn):
            btn.setEnabled(is_admin)
        self._delete_dept_btn.setVisible(is_admin)
        self._all_emp_table.hide()
        self._table_scroll.show()
        self.refresh()

    def set_all_employees(self):
        """Switch to the All Employees virtual view."""
        self._is_all_employees = True
        self._dept_id = None
        self._dept_name = ""
        self._dept_label.setText("All Employees")
        for btn in (self._add_emp_btn, self._add_comp_btn, self._add_inst_btn, self._delete_dept_btn):
            btn.setEnabled(False)
        self._delete_dept_btn.hide()
        self._table_scroll.hide()
        self._empty.hide()
        self._all_emp_sort_asc = True
        self._refresh_all_employees()

    def clear_department(self):
        self._is_all_employees = False
        self._dept_id = None
        self._dept_name = ""
        self._all_rows = []
        self._dept_label.setText("Select a department")
        self._count_label.setText("")
        for btn in (self._add_emp_btn, self._add_comp_btn, self._add_inst_btn, self._delete_dept_btn):
            btn.setEnabled(False)
        self._delete_dept_btn.hide()
        self._all_emp_table.hide()
        self._table_scroll.show()
        self._render()

    def has_inventory_rows(self) -> bool:
        return bool(self._all_rows)

    def apply_filter(self, text: str):
        self._filter = text.lower()
        if self._is_all_employees:
            self._refresh_all_employees()
        else:
            self._render()

    def refresh(self):
        if self._is_all_employees:
            self._refresh_all_employees()
            return
        if self._dept_id is None:
            self._all_rows = []
            self._render()
            return

        dept_ids = departments.get_descendant_ids(self._dept_id)
        dept_names = {d["id"]: d["name"] for d in departments.get_all_depts()}
        rows: list[dict] = []

        employee_rows = employees.get_all_dept_employees(self._dept_id)
        employee_ids = [emp["employee_id"] for emp in employee_rows]
        devices_by_employee: dict[str, list[dict]] = {}
        for device in computers.get_computers_by_employees(employee_ids):
            devices_by_employee.setdefault(device.get("employee_id"), []).append(device)

        for emp in employee_rows:
            name = f"{emp.get('first_name', '')} {emp.get('last_name', '')}".strip()
            employee_devices = devices_by_employee.get(emp["employee_id"], [])
            rows.append({
                "_kind": "Employee",
                "_item_id": emp.get("employee_id", ""),
                "_name": name,
                "_dept_name": dept_names.get(emp.get("dept_id"), "Unassigned"),
                "_devices": self._device_preview(employee_devices),
                "_notes": emp.get("notes", "") or "",
                "_employee_id": emp.get("employee_id"),
                "_record_id": emp.get("employee_id"),
            })

        for inst in instruments.get_instruments_by_labs(dept_ids):
            rows.append({
                "_kind": "Instrument",
                "_item_id": inst.get("serial_number") or f"INST-{inst.get('id')}",
                "_name": inst.get("model_name", ""),
                "_dept_name": dept_names.get(inst.get("lab_id"), "Unassigned"),
                "_devices": "",
                "_notes": inst.get("notes", "") or "",
                "_employee_id": None,
                "_record_id": inst.get("id"),
            })

        for comp in computers.get_computers_by_depts(dept_ids):
            rows.append({
                "_kind": "Computer",
                "_item_id": f"COMP-{comp.get('id')}",
                "_name": computer_label(comp),
                "_dept_name": dept_names.get(comp.get("dept_id") or comp.get("lab_id"), "Unassigned"),
                "_devices": self._computer_specs(comp),
                "_notes": comp.get("notes", "") or "",
                "_employee_id": None,
                "_record_id": comp.get("id"),
            })

        self._all_rows = rows
        self._render()

    #All Employees helpers

    def _current_sort_icon(self) -> QIcon:
        return self._icon_sort_up if self._all_emp_sort_asc else self._icon_sort_down

    def _set_all_emp_name_header(self):
        header_item = self._all_emp_table.horizontalHeaderItem(0)
        if header_item is None:
            header_item = QTableWidgetItem("Name")
            self._all_emp_table.setHorizontalHeaderItem(0, header_item)
        else:
            header_item.setText("Name")
        header_item.setTextAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self._all_emp_header.updateSection(0)

    def _refresh_all_employees(self):
        """Populate the All Employees table."""
        self._table_scroll.hide()
        self._empty.hide()
        self._all_emp_table.show()
        self._set_all_emp_name_header()

        for i in range(len(_ALL_EMP_COLUMNS)):
            header_item = self._all_emp_table.horizontalHeaderItem(i)
            if header_item:
                header_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        dept_names = {d["id"]: d["name"] for d in departments.get_all_depts()}

        all_emps = sorted(
            employees.get_all_employees(),
            key=lambda e: (
                (e.get("last_name") or "").lower(),
                (e.get("first_name") or "").lower(),
            ),
            reverse=not self._all_emp_sort_asc,
        )

        employee_ids = [emp.get("employee_id") for emp in all_emps]
        devices_by_employee: dict[str, list[dict]] = {}
        for device in computers.get_computers_by_employees(employee_ids):
            devices_by_employee.setdefault(device.get("employee_id"), []).append(device)

        f = self._filter
        if f:
            all_emps = [
                e for e in all_emps
                if f in e.get("last_name", "").lower()
                or f in e.get("first_name", "").lower()
                or f in e.get("employee_id", "").lower()
                or f in self._device_preview(
                    devices_by_employee.get(e.get("employee_id"), [])
                ).lower()
            ]

        self.search_available_changed.emit(True)

        self._all_emp_table.setRowCount(0)
        if not all_emps:
            self._all_emp_table.hide()
            self._empty.show()
            if self._empty_label:
                self._empty_label.setText("No employees found.")
            self._count_label.setText("")
            return

        count = len(all_emps)
        self._count_label.setText(
            f"{count} employee" if count == 1 else f"{count} employees"
        )

        self._all_emp_table.setRowCount(count)
        for r, emp in enumerate(all_emps):
            last = emp.get("last_name", "")
            first = emp.get("first_name", "")
            display_name = f"{last}, {first}".strip(", ")
            emp_id = emp.get("employee_id", "")
            dept_name = dept_names.get(emp.get("dept_id"), "Unassigned")
            device_preview = self._device_preview(
                devices_by_employee.get(emp_id, [])
            )

            for c, val in enumerate([display_name, emp_id, dept_name, device_preview]):
                item = QTableWidgetItem(val)
                item.setData(Qt.ItemDataRole.UserRole, {
                    "kind": "Employee",
                    "id": emp_id,
                })
                item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self._all_emp_table.setItem(r, c, item)
            self._all_emp_table.setRowHeight(r, 40)

        self._all_emp_table.repaint_all_rows()

    def _on_all_emp_header_clicked(self, logical_index: int):
        """Toggle sort direction when the Name column header is clicked."""
        if logical_index == 0:
            self._all_emp_sort_asc = not self._all_emp_sort_asc
            self._refresh_all_employees()

    def _on_all_emp_selection(self):
        sel = self._all_emp_table.selectedItems()
        if sel:
            data = sel[0].data(Qt.ItemDataRole.UserRole) or {}
            emp_id = data.get("id")
            if emp_id:
                self.employee_selected.emit(emp_id)

    def _render(self):
        f = self._filter
        rows = [
            row for row in self._all_rows
            if not f or f in self._row_search_text(row)
        ]

        self._table.setRowCount(0) 
        self.search_available_changed.emit(bool(self._all_rows)) 
        if not rows:
            self._table.hide() 
            self._table_scroll.hide()  
            self._empty.show() 
            if self._empty_label: 
                if self._dept_id is None: 
                    self._empty_label.setText("Select a department to view inventory.")
                elif self._all_rows:
                    self._empty_label.setText("No matching inventory found.")
                else:
                    self._empty_label.setText("No employees, instruments, or computers in this department.")
            self._count_label.setText("0 matches" if self._all_rows and f else "")
            return

        self._empty.hide()
        self._table_scroll.show()
        self._table.show()
        self._count_label.setText(self._count_text(rows))
        self._table.setRowCount(len(rows))

        for r, row in enumerate(rows):
            vals = [row.get(key, "") for _, key in _COLUMNS]
            for c, val in enumerate(vals):
                item = QTableWidgetItem(str(val))
                item.setData(Qt.ItemDataRole.UserRole, {
                    "kind": row.get("_kind"),
                    "id": row.get("_record_id"),
                })
                item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self._table.setItem(r, c, item)
            self._table.setRowHeight(r, 40)
        self._table.repaint_all_rows()

    def _on_selection(self):
        sel = self._table.selectedItems()
        if sel:
            data = sel[0].data(Qt.ItemDataRole.UserRole) or {}
            kind = data.get("kind")
            record_id = data.get("id")
            if kind == "Employee" and record_id:
                self.employee_selected.emit(record_id)
            elif kind == "Computer" and record_id is not None:
                self.computer_selected.emit(int(record_id))
            elif kind == "Instrument" and record_id is not None:
                self.instrument_selected.emit(int(record_id))

    #Button actions

    def _add_employee(self):
        if self._dept_id is None:
            return
        dlg = AddEmployeeDialog(dept_id=self._dept_id, parent=self)
        if dlg.exec() == AddEmployeeDialog.DialogCode.Accepted:
            self.data_changed.emit()
            self.refresh()

    def _add_computer(self):
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
        reply = QMessageBox.warning(
            self,
            "Delete Department",
            (
                f"Delete '{self._dept_name}'?\n\n"
                "This will also delete its sub-departments, employees, instruments, "
                "and computers/devices."
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            if not departments.delete_dept_by_id(self._dept_id):
                QMessageBox.warning(self, "Delete Department", "Department could not be deleted.")
                return
            self.department_deleted.emit()
        except ApiError as exc:
            QMessageBox.warning(self, "Delete Department", exc.message)

    #Utility

    def _row_search_text(self, row: dict) -> str:
        return " ".join(str(row.get(key, "")) for _, key in _COLUMNS).lower()

    def _count_text(self, rows: list[dict]) -> str:
        counts: dict[str, int] = {}
        for row in rows:
            kind = row.get("_kind", "Item")
            counts[kind] = counts.get(kind, 0) + 1

        # Webcam count for the current department
        if self._dept_id is not None:
            dept_ids = departments.get_descendant_ids(self._dept_id)
            webcam_count = computers.count_webcams_in_depts(dept_ids)
        else:
            webcam_count = 0

        parts = []
        for kind in ("Employee", "Instrument", "Computer"):
            count = counts.get(kind, 0)
            if count:
                label = kind.lower() if count == 1 else f"{kind.lower()}s"
                parts.append(f"{count} {label}")
        if webcam_count:
            label = "webcam" if webcam_count == 1 else "webcams"
            parts.append(f"{webcam_count} {label}")

        return " · ".join(parts) if parts else f"{len(rows)} items"

    def _device_preview(self, devices: list[dict]) -> str:
        if not devices:
            return "No computer assigned"
        labels = [computer_label(device) for device in devices]
        return ", ".join(labels)

    def _computer_specs(self, computer: dict) -> str:
        specs = [
            computer.get("ram"),
            computer.get("storage"),
            computer.get("os_version"),
        ]
        return " · ".join(spec for spec in specs if spec)