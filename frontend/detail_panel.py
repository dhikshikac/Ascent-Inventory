from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame, QMessageBox, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal

import backend.employees as employees
import backend.computers as computers
import backend.departments as departments
import backend.instruments as instruments
from frontend.widgets import (
        primary_button, ghost_button, danger_button, back_button,
        section_label, field_pair, h_separator, empty_state
)

from frontend.dialogs import EditEmployeeDialog, AddComputerDialog, EditComputerDialog 

class ComputerCard(QFrame):
    edit_requested = pyqtSignal(int)
    delete_requested = pyqtSignal(int)

    def __init__(self, computer: dict, parent=None):
        super().__init__(parent)
        self._computer_id = computer.get("id")
        self.setObjectName("ComputerCard")
        self.setStyleSheet("""
            QFrame#ComputerCard {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
            }
            QFrame#ComputerCard QLabel,
            QFrame#ComputerCard QWidget#FieldPair {
                background-color: transparent;
                border: none;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 14)
        layout.setSpacing(10)

        hdr = QHBoxLayout()
        badge = QLabel(self._device_kind(computer))
        badge.setStyleSheet("""
            background-color: transparent;
            color: #4B5563;
            font-weight: 600;
            padding: 0;
        """)
        hdr.addWidget(badge)
        hdr.addStretch()
        edit_btn = ghost_button("Edit")
        edit_btn.setMinimumHeight(36)
        edit_btn.clicked.connect(lambda: self.edit_requested.emit(self._computer_id))
        hdr.addWidget(edit_btn)
        del_btn = danger_button("Delete")
        del_btn.setMinimumHeight(36)
        del_btn.clicked.connect(lambda: self.delete_requested.emit(self._computer_id))
        hdr.addWidget(del_btn)
        layout.addLayout(hdr)
        layout.addWidget(h_separator())

        grid = QGridLayout()
        grid.setHorizontalSpacing(20)
        grid.setVerticalSpacing(10)
        specs = [
            ("Monitor",    computer.get("monitor_model")),
            ("PC Model",   computer.get("pc_model")),
            ("RAM",        computer.get("ram")),
            ("Storage",    computer.get("storage")),
            ("OS Version", computer.get("os_version")),
            ("Webcam",     computer.get("webcam_specs")),
            ("Desk Phone", computer.get("desk_phone")),
        ]
        for i, (lbl, val) in enumerate(specs):
            row, col = divmod(i, 2)
            grid.addWidget(field_pair(lbl, val), row, col)
        layout.addLayout(grid)

        if computer.get("notes"):
            layout.addWidget(field_pair("Notes", computer.get("notes")))

    def _device_kind(self, computer: dict) -> str:
        if computer.get("pc_model"):
            return "COMPUTER"
        if computer.get("monitor_model"):
            return "MONITOR"
        if computer.get("desk_phone"):
            return "DESK PHONE"
        if computer.get("webcam_specs"):
            return "WEBCAM"
        return "DEVICE"
 
 
class EmployeeDetailView(QWidget):

    back_clicked = pyqtSignal()
    data_changed = pyqtSignal()
 
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ContentPanel")
        self._employee_id: str | None = None
 
        self._root_layout = QVBoxLayout(self)
        self._root_layout.setContentsMargins(0, 0, 0, 0)
        self._root_layout.setSpacing(0)
        self._content_widget: QWidget | None = None
  
    def load(self, employee_id: str):
        self._employee_id = employee_id
        self._rebuild()
  
    def _rebuild(self):
        if self._content_widget:
            self._content_widget.deleteLater()
            self._content_widget = None
 
        emp = employees.get_employee(self._employee_id)
        if not emp:
            return
 
        dept_name = departments.get_name(emp.get("dept_id"))
 
        self._content_widget = QWidget()
        outer = QVBoxLayout(self._content_widget)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
 
        header = QWidget()
        header.setObjectName("EmployeeDetailHeader")
        hl = QVBoxLayout(header)
        hl.setContentsMargins(24, 16, 24, 18)
        hl.setSpacing(4)
 
        back_btn = back_button("← Back to list")
        back_btn.clicked.connect(self.back_clicked)
        hl.addWidget(back_btn)
        hl.addSpacing(8)
 
        name_lbl = QLabel(f"{emp['first_name']} {emp['last_name']}")
        name_lbl.setObjectName("DetailName")
        hl.addWidget(name_lbl)
 
        meta_lbl = QLabel(f"{emp['employee_id']}  ·  {dept_name}")
        meta_lbl.setObjectName("DetailId")
        hl.addWidget(meta_lbl)
 
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        btn_row.setContentsMargins(0, 12, 0, 0)
        btn_row.addStretch()
 
        edit_btn = ghost_button("Edit Profile")
        edit_btn.clicked.connect(self._edit)
        btn_row.addWidget(edit_btn)
 
        add_dev_btn = primary_button("+ Add Computer")
        add_dev_btn.setMinimumWidth(140)
        add_dev_btn.clicked.connect(self._add_device)
        btn_row.addWidget(add_dev_btn)
 
        del_btn = danger_button("Delete Employee")
        del_btn.clicked.connect(self._delete)
        btn_row.addWidget(del_btn)
 
        hl.addLayout(btn_row)
        outer.addWidget(header)
 
        if emp.get("notes"):
            notes_bar = QWidget()
            notes_bar.setObjectName("EmployeeNotes")
            nl = QVBoxLayout(notes_bar)
            nl.setContentsMargins(24, 12, 24, 12)
            nl.setSpacing(4)
            nl.addWidget(section_label("Notes"))
            note_val = QLabel(emp["notes"])
            note_val.setObjectName("FieldValue")
            note_val.setWordWrap(True)
            nl.addWidget(note_val)
            outer.addWidget(notes_bar)
 
        dev_hdr = QWidget()
        dhl = QHBoxLayout(dev_hdr)
        dhl.setContentsMargins(24, 16, 24, 8)
        dhl.addWidget(section_label("Devices"))
        dhl.addStretch()
        outer.addWidget(dev_hdr)
 
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
 
        scroll_inner = QWidget()
        sl = QVBoxLayout(scroll_inner)
        sl.setContentsMargins(24, 4, 24, 24)
        sl.setSpacing(12)
        sl.setAlignment(Qt.AlignmentFlag.AlignTop)
 
        comp_list = computers.get_computers_by_employee(self._employee_id)
        if comp_list:
            for comp in comp_list:
                card = ComputerCard(comp)
                card.edit_requested.connect(self._edit_device)
                card.delete_requested.connect(self._delete_device)
                sl.addWidget(card)
        else:
            no_dev = QLabel("No devices assigned yet.")
            no_dev.setObjectName("EmptyState")
            no_dev.setAlignment(Qt.AlignmentFlag.AlignCenter)
            sl.addWidget(no_dev)
 
        sl.addStretch()
        scroll.setWidget(scroll_inner)
        outer.addWidget(scroll, 1)
 
        self._root_layout.addWidget(self._content_widget)
  
    def _edit(self):
        dlg = EditEmployeeDialog(self._employee_id, self)
        if dlg.exec() == dlg.DialogCode.Accepted:
            self.data_changed.emit()
            self._rebuild()
 
    def _delete(self):
        emp = employees.get_employee(self._employee_id)
        if not emp:
            return
        reply = QMessageBox.question(
            self, "Delete Employee",
            f"Delete {emp['first_name']} {emp['last_name']}? This also removes all their devices.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
        )
        if reply == QMessageBox.StandardButton.Yes:
            employees.delete_employee(self._employee_id)
            self._employee_id = None
            self.data_changed.emit()
            self.back_clicked.emit()
 
    def _add_device(self):
        dlg = AddComputerDialog(employee_id=self._employee_id, parent=self)
        if dlg.exec() == dlg.DialogCode.Accepted:
            self._rebuild()
 
    def _edit_device(self, comp_id: int):
        dlg = EditComputerDialog(comp_id, self)
        if dlg.exec() == dlg.DialogCode.Accepted:
            self._rebuild()
 
    def _delete_device(self, comp_id: int):
        reply = QMessageBox.question(
            self, "Delete Device", "Delete this device record?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
        )
        if reply == QMessageBox.StandardButton.Yes:
            computers.delete_computer(comp_id)
            self._rebuild()


class InventoryDetailView(QWidget):

    back_clicked = pyqtSignal()
    data_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ContentPanel")
        self._kind: str | None = None
        self._record_id: int | None = None

        self._root_layout = QVBoxLayout(self)
        self._root_layout.setContentsMargins(0, 0, 0, 0)
        self._root_layout.setSpacing(0)
        self._content_widget: QWidget | None = None

    def load(self, kind: str, record_id: int):
        self._kind = kind
        self._record_id = record_id
        self._rebuild()

    def _rebuild(self):
        if self._content_widget:
            self._content_widget.deleteLater()
            self._content_widget = None

        if self._kind == "Computer":
            record = computers.get_computer(self._record_id)
            if not record:
                return
            self._build_computer(record)
        elif self._kind == "Instrument":
            record = instruments.get_instrument(self._record_id)
            if not record:
                return
            self._build_instrument(record)

    def _base_content(self, title: str, meta: str):
        self._content_widget = QWidget()
        outer = QVBoxLayout(self._content_widget)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        header = QWidget()
        header.setObjectName("EmployeeDetailHeader")
        hl = QVBoxLayout(header)
        hl.setContentsMargins(24, 16, 24, 18)
        hl.setSpacing(4)

        back_btn = back_button("← Back to list")
        back_btn.clicked.connect(self.back_clicked)
        hl.addWidget(back_btn)
        hl.addSpacing(8)

        name_lbl = QLabel(title)
        name_lbl.setObjectName("DetailName")
        hl.addWidget(name_lbl)

        meta_lbl = QLabel(meta)
        meta_lbl.setObjectName("DetailId")
        hl.addWidget(meta_lbl)

        outer.addWidget(header)
        return outer

    def _build_computer(self, computer: dict):
        dept_id = computer.get("dept_id") or computer.get("lab_id")
        dept_name = departments.get_name(dept_id)
        title = _computer_label(computer)
        outer = self._base_content(title, f"COMP-{computer.get('id')}  ·  {dept_name}")

        scroll, body = self._detail_body()
        body.addWidget(section_label("Computer Specs"))

        grid = QGridLayout()
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(12)
        specs = [
            ("Type", computer.get("computer_type", "computer").replace("_", " ").title()),
            ("Monitor", computer.get("monitor_model")),
            ("PC Model", computer.get("pc_model")),
            ("RAM", computer.get("ram")),
            ("Storage", computer.get("storage")),
            ("OS Version", computer.get("os_version")),
            ("Webcam", computer.get("webcam_specs")),
            ("Desk Phone", computer.get("desk_phone")),
        ]
        for i, (label, value) in enumerate(specs):
            row, col = divmod(i, 2)
            grid.addWidget(field_pair(label, value), row, col)
        body.addLayout(grid)

        if computer.get("notes"):
            body.addWidget(field_pair("Notes", computer.get("notes")))

        body.addStretch()
        outer.addWidget(scroll, 1)
        self._root_layout.addWidget(self._content_widget)

    def _build_instrument(self, instrument: dict):
        dept_name = departments.get_name(instrument.get("lab_id"))
        title = instrument.get("model_name") or f"Instrument {instrument.get('id')}"
        serial = instrument.get("serial_number") or f"INST-{instrument.get('id')}"
        outer = self._base_content(title, f"{serial}  ·  {dept_name}")

        scroll, body = self._detail_body()
        body.addWidget(section_label("Instrument Specs"))

        grid = QGridLayout()
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(12)
        specs = [
            ("Instrument Name", instrument.get("model_name")),
            ("Serial Number", instrument.get("serial_number")),
            ("Department", dept_name),
        ]
        for i, (label, value) in enumerate(specs):
            grid.addWidget(field_pair(label, value), i, 0)
        body.addLayout(grid)

        if instrument.get("notes"):
            body.addWidget(field_pair("Notes", instrument.get("notes")))

        body.addStretch()
        outer.addWidget(scroll, 1)
        self._root_layout.addWidget(self._content_widget)

    def _detail_body(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        scroll_inner = QWidget()
        body = QVBoxLayout(scroll_inner)
        body.setContentsMargins(24, 20, 24, 24)
        body.setSpacing(14)
        body.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(scroll_inner)
        return scroll, body


def _computer_label(computer: dict) -> str:
    for key in ("pc_model", "monitor_model", "os_version"):
        value = computer.get(key)
        if value:
            return value
    return f"Computer {computer.get('id')}"