from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame, QMessageBox, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal

import backend.employees as employees
import backend.computers as computers
import backend.departments as departments
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
            QLabel#ComputerBadge {
                background-color: #F3F4F6;
                border: none;
                border-radius: 5px;
                color: #4B5563;
                font-size: 11px;
                font-weight: 600;
                padding: 4px 8px;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 14)
        layout.setSpacing(10)

        hdr = QHBoxLayout()
        badge = QLabel(computer.get("computer_type", "computer").replace("_", " ").upper())
        badge.setObjectName("ComputerBadge")
        hdr.addWidget(badge)
        hdr.addStretch()
        edit_btn = ghost_button("Edit")
        edit_btn.setFixedHeight(26)
        edit_btn.clicked.connect(lambda: self.edit_requested.emit(self._computer_id))
        hdr.addWidget(edit_btn)
        del_btn = danger_button("Delete")
        del_btn.setFixedHeight(26)
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
            layout.addWidget(h_separator())
            layout.addWidget(field_pair("Notes", computer.get("notes")))
 
 
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
        header.setStyleSheet("background-color: #F9FAFB; border-bottom: 1px solid #E5E7EB;")
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
 
        edit_btn = ghost_button("Edit Profile")
        edit_btn.clicked.connect(self._edit)
        btn_row.addWidget(edit_btn)
 
        add_dev_btn = primary_button("+ Add Computer")
        add_dev_btn.clicked.connect(self._add_device)
        btn_row.addWidget(add_dev_btn)
 
        btn_row.addStretch()
 
        del_btn = danger_button("Delete Employee")
        del_btn.clicked.connect(self._delete)
        btn_row.addWidget(del_btn)
 
        hl.addLayout(btn_row)
        outer.addWidget(header)
 
        if emp.get("notes"):
            notes_bar = QWidget()
            notes_bar.setStyleSheet("background-color: #F9FAFB; border-bottom: 1px solid #E5E7EB;")
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
        dhl.addWidget(section_label("Computers / Devices"))
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
            no_dev = QLabel("No computers assigned yet.")
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
            self.data_changed.emit()
            self._rebuild()
 
    def _edit_device(self, comp_id: int):
        dlg = EditComputerDialog(comp_id, self)
        if dlg.exec() == dlg.DialogCode.Accepted:
            self.data_changed.emit()
            self._rebuild()
 
    def _delete_device(self, comp_id: int):
        reply = QMessageBox.question(
            self, "Delete Device", "Delete this device record?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
        )
        if reply == QMessageBox.StandardButton.Yes:
            computers.delete_computer(comp_id)
            self.data_changed.emit()
            self._rebuild()