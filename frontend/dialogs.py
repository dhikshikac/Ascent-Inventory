from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QLineEdit, QComboBox, QTextEdit, QDialogButtonBox,
    QMessageBox, QWidget, QTabWidget, QGridLayout, QSizePolicy
)
from PyQt6.QtCore import Qt

import backend.departments as departments
import backend.employees as employees
import backend.computers as computers
import backend.instruments as instruments

def _ok_cancel(parent_dialog: QDialog, ok_text="Save") -> QDialogButtonBox:
    buttons = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Ok | 
        QDialogButtonBox.StandardButton.Cancel
    )

    ok_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
    ok_button.setObjectName("PrimaryBtn")
    ok_button.setText(ok_text)
    buttons.rejected.connect(parent_dialog.reject)
    return buttons

class AddEmployeeDialog(QDialog):

    def __init__(self, dept_id: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Employee")
        self.setMinimumWidth(480)
        self.setModal(True)
        self._dept_id = dept_id

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 20)
        layout.setSpacing(16)

        title = QLabel("Add New Employee")
        title.setObjectName("DeptName")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        self._id_edit = QLineEdit()
        self._id_edit.setPlaceholderText("e.g. EMP-001")
        form.addRow("Employee ID *", self._id_edit)
 
        self._first_edit = QLineEdit()
        self._first_edit.setPlaceholderText("First name")
        form.addRow("First Name *", self._first_edit)
 
        self._last_edit = QLineEdit()
        self._last_edit.setPlaceholderText("Last name")
        form.addRow("Last Name *", self._last_edit)

        self._dept_combo = QComboBox()
        all_depts = departments.get_all_depts()
        current_index = 0
        for i, d in enumerate(all_depts):
            self._dept_combo.addItem(d["name"], d["id"])
            if d["id"] == dept_id:
                current_index = i
        self._dept_combo.setCurrentIndex(current_index)
        form.addRow("Department *", self._dept_combo)

        self._notes_edit = QTextEdit()
        self._notes_edit.setPlaceholderText("Optional notes...")
        self._notes_edit.setFixedHeight(70)
        form.addRow("Notes", self._notes_edit)

        layout.addLayout(form)

        buttons = _ok_cancel(self, "Add Employee")
        buttons.accepted.connect(self._accept)
        layout.addWidget(buttons)
    
    def _accept(self):
        employee_id = self._id_edit.text().strip()
        first = self._first_edit.text().strip()
        last = self._last_edit.text().strip()
        dept_id = self._dept_combo.currentData()
        notes = self._notes_edit.toPlainText().strip()

        if not employee_id or not first or not last:
            QMessageBox.warning(self, "Required", "Please fill in all required fields.")
            return
        
        if employees.employee_exists(employee_id):
            QMessageBox.warning(self, "Duplicate", f"Employee ID '{employee_id}' already exists.")
            return

        employees.add_employee(employee_id, dept_id, first, last, notes=notes)
        self.accept()

class EditEmployeeDialog(QDialog):

    def __init__(self, employee_id: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Employee")
        self.setMinimumWidth(480)
        self.setModal(True)
        self._employee_id = employee_id

        employee = employees.get_employee(employee_id)
        if not employee:
            self.reject()
            return

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 20)
        layout.setSpacing(16)

        title = QLabel(f"Edit Employee - {employee['first_name']} {employee['last_name']}")
        title.setObjectName("DeptName")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        id_label = QLabel(employee_id)
        id_label.setObjectName("EmployeeID")
        form.addRow("Employee ID", id_label)

        self._first_edit = QLineEdit(employee["first_name"])
        form.addRow("First Name *", self._first_edit)

        self._last_edit = QLineEdit(employee["last_name"])
        form.addRow("Last Name *", self._last_edit)

        self._dept_combo = QComboBox()
        all_depts = departments.get_all_depts()
        current_index = 0
        for i, d in enumerate(all_depts):
            self._dept_combo.addItem(d["name"], d["id"])
            if d["id"] == employee["dept_id"]:
                current_index = i
        self._dept_combo.setCurrentIndex(current_index)
        form.addRow("Department", self._dept_combo)

        self._notes_edit = QTextEdit()
        self._notes_edit.setPlainText(employee.get("notes") or "")
        self._notes_edit.setFixedHeight(70)
        form.addRow("Notes", self._notes_edit)

        layout.addLayout(form)

        buttons = _ok_cancel(self, "Save Changes")
        buttons.accepted.connect(self._accept)
        layout.addWidget(buttons)

    def _accept(self):
        first = self._first_edit.text().strip()
        last = self._last_edit.text().strip()
        if not first or not last:
            QMessageBox.warning(self, "Required", "Please fill in all required fields.")
            return
        
        employees.edit_employee(
            self._employee_id,
            first_name=first,
            last_name=last,
            dept_id=self._dept_combo.currentData(),
            notes=self._notes_edit.toPlainText().strip()
        )
        self.accept()

class AddComputerDialog(QDialog):

    def __init__(self, employee_id: str | None = None, dept_id: int | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Device")
        self.setMinimumWidth(520)
        self.setModal(True)
        self._employee_id = employee_id
        self._dept_id = dept_id

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 20)
        layout.setSpacing(16)

        title = QLabel("New Device / Computer")
        title.setObjectName("DetailName")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        self._pc_edit = QLineEdit()
        self._pc_edit.setPlaceholderText("e.g. Dell XPS 15")
        form.addRow("PC Model *", self._pc_edit)

        self._monitor_edit = QLineEdit()
        self._monitor_edit.setPlaceholderText("e.g. Dell UltraSharp U2723QE")
        form.addRow("Monitor Model", self._monitor_edit)

        self._ram_edit = QLineEdit()
        self._ram_edit.setPlaceholderText("e.g. 16 GB")
        form.addRow("RAM", self._ram_edit)

        self._storage_edit = QLineEdit()
        self._storage_edit.setPlaceholderText("e.g. 512 GB SSD")
        form.addRow("Storage", self._storage_edit)

        self._os_edit = QLineEdit()
        self._os_edit.setPlaceholderText("e.g. Windows 11 Pro")
        form.addRow("OS Version", self._os_edit)

        layout.addLayout(form)

        buttons = _ok_cancel(self, "Add Device")
        buttons.accepted.connect(self._accept)
        layout.addWidget(buttons)
    
    def _accept(self):
        computers.add_computer(
            computer_type="employee" if self._employee_id else "shared",
            employee_id=self._employee_id,
            dept_id=self._dept_id,
            pc_model=self._pc_edit.text().strip(),
            monitor_model=self._monitor_edit.text().strip(),
            ram=self._ram_edit.text().strip(),
            storage=self._storage_edit.text().strip(),
            os_version=self._os_edit.text().strip(),
        )
        self.accept()

class EditComputerDialog(QDialog):

    def __init__(self, computer_id: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Device")
        self.setMinimumWidth(520)
        self.setModal(True)
        self._computer_id = computer_id

        computer = computers.get_computer(computer_id)
        if not computer:
            self.reject()
            return

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 20)
        layout.setSpacing(16)

        title = QLabel(f"Edit Device")
        title.setObjectName("DetailName")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        def field(placeholder, val):
            e = QLineEdit(val or "")
            e.setPlaceholderText(placeholder)
            return e
 
        self._monitor  = field("e.g. Dell U2722D",       computer.get("monitor_model") or "")
        self._pc       = field("e.g. Dell OptiPlex 7090", computer.get("pc_model") or "")
        self._ram      = field("e.g. 16 GB",              computer.get("ram") or "")
        self._storage  = field("e.g. 512 GB SSD",         computer.get("storage") or "")
        self._os       = field("e.g. Windows 11 Pro",     computer.get("os_version") or "")
        self._webcam   = field("e.g. Logitech C920",      computer.get("webcam_specs") or "")
        self._phone    = field("e.g. Cisco 7841",         computer.get("desk_phone") or "")
 
        form.addRow("Monitor Model", self._monitor)
        form.addRow("PC Model",      self._pc)
        form.addRow("RAM",           self._ram)
        form.addRow("Storage",       self._storage)
        form.addRow("OS Version",    self._os)
        form.addRow("Webcam",        self._webcam)
        form.addRow("Desk Phone",    self._phone)
 
        self._notes = QTextEdit()
        self._notes.setPlainText(comp.get("notes") or "")
        self._notes.setFixedHeight(60)
        form.addRow("Notes", self._notes)
 
        layout.addLayout(form)
 
        buttons = _ok_cancel(self, "Save Changes")
        buttons.accepted.connect(self._accept)
        layout.addWidget(buttons)

    def _accept(self):
        computers.edit_computer(
            self._computer_id,
            pc_model=self._pc.text().strip(),
            monitor_model=self._monitor.text().strip(),
            ram=self._ram.text().strip(),
            storage=self._storage.text().strip(),
            os_version=self._os.text().strip(),
            webcam_specs=self._webcam.text().strip(),
            desk_phone=self._phone.text().strip(),
            notes=self._notes.toPlainText().strip()
        )
        self.accept()

class AddInstrumentDialog(QDialog):
    def __init__(self, lab_id: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Instrument")
        self.setMinimumWidth(520)
        self.setModal(True)
        self._lab_id = lab_id

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 20)
        layout.setSpacing(16)

        title = QLabel("Add New Instrument")
        title.setObjectName("DetailName")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("e.g. Oscilloscope")
        form.addRow("Instrument Name *", self._name_edit)

        self._model_edit = QLineEdit()
        self._model_edit.setPlaceholderText("e.g. Tektronix TBS2000")
        form.addRow("Model", self._model_edit)

        self._notes_edit = QTextEdit()
        self._notes_edit.setPlaceholderText("Optional notes...")
        self._notes_edit.setFixedHeight(60)
        form.addRow("Notes", self._notes_edit)

        layout.addLayout(form)

        buttons = _ok_cancel(self, "Add Instrument")
        buttons.accepted.connect(self._accept)
        layout.addWidget(buttons)
    
    def _accept(self):
        name = self._name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Required", "Instrument name cannot be empty.")
            return
        
        instruments.add_instrument(
            self._lab_id,
            name,
            self._model_edit.text().strip(),
            self._notes_edit.toPlainText().strip()
        )
        self.accept()