from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLabel,
    QLineEdit, QComboBox, QTextEdit, QDialogButtonBox,
    QMessageBox, QApplication,
)
from PyQt6.QtCore import Qt

import frontend.services.departments as departments
import frontend.services.employees as employees
import frontend.services.computers as computers
import frontend.services.instruments as instruments
from frontend.api_client import ApiError
from frontend.workers import run_api_task


def _ok_cancel(parent_dialog: QDialog, ok_text="Save") -> QDialogButtonBox:
    buttons = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Ok |
        QDialogButtonBox.StandardButton.Cancel
    )

    ok_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
    ok_button.setObjectName("PrimaryBtn")
    ok_button.setText(ok_text)
    ok_button.setCursor(Qt.CursorShape.PointingHandCursor)
    cancel_button = buttons.button(QDialogButtonBox.StandardButton.Cancel)
    cancel_button.setObjectName("GhostBtn")
    cancel_button.setCursor(Qt.CursorShape.PointingHandCursor)
    buttons.rejected.connect(parent_dialog.reject)
    return buttons


def _run_save(dialog: QDialog, buttons: QDialogButtonBox, task, error_title: str):
    buttons.setEnabled(False)
    QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)

    def on_success(_result):
        QApplication.restoreOverrideCursor()
        dialog.accept()

    def on_error(exc: Exception):
        QApplication.restoreOverrideCursor()
        buttons.setEnabled(True)
        message = exc.message if isinstance(exc, ApiError) else str(exc)
        QMessageBox.warning(dialog, error_title, message)

    run_api_task(task, on_success, on_error)


def _clear_layout(layout):
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.deleteLater()


class AddEmployeeDialog(QDialog):

    def __init__(self, dept_id: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Employee")
        self.setMinimumWidth(480)
        self.setModal(True)
        self._dept_id = dept_id
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(28, 24, 28, 20)
        self._layout.setSpacing(16)
        self._buttons = None
        self._build_form(departments.get_cached_depts() or [])

    def _populate_dept_combo(self, all_depts: list[dict]):
        self._dept_combo.clear()
        current_index = 0
        for i, dept in enumerate(all_depts):
            self._dept_combo.addItem(dept["name"], dept["id"])
            if dept["id"] == self._dept_id:
                current_index = i
        self._dept_combo.setCurrentIndex(current_index)

    def _build_form(self, all_depts: list[dict]):
        title = QLabel("Add New Employee")
        title.setObjectName("DetailName")
        self._layout.addWidget(title)

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
        if all_depts:
            self._populate_dept_combo(all_depts)
        else:
            self._dept_combo.addItem("Loading departments…", self._dept_id)
            run_api_task(
                departments.prefetch,
                self._populate_dept_combo,
                lambda exc: QMessageBox.warning(
                    self,
                    "Add Employee",
                    exc.message if isinstance(exc, ApiError) else str(exc),
                ),
            )
        form.addRow("Department *", self._dept_combo)

        self._notes_edit = QTextEdit()
        self._notes_edit.setPlaceholderText("Optional notes...")
        self._notes_edit.setFixedHeight(70)
        form.addRow("Notes", self._notes_edit)

        self._layout.addLayout(form)

        self._buttons = _ok_cancel(self, "Add Employee")
        self._buttons.accepted.connect(self._accept)
        self._layout.addWidget(self._buttons)

    def _accept(self):
        employee_id = self._id_edit.text().strip()
        first = self._first_edit.text().strip()
        last = self._last_edit.text().strip()
        dept_id = self._dept_combo.currentData()
        notes = self._notes_edit.toPlainText().strip()

        if not employee_id or not first or not last:
            QMessageBox.warning(self, "Required", "Please fill in all required fields.")
            return

        def task():
            if employees.employee_exists(employee_id):
                raise ApiError(409, f"Employee ID '{employee_id}' already exists.")
            employees.add_employee(employee_id, dept_id, first, last, notes=notes)

        _run_save(self, self._buttons, task, "Add Employee")


class EditEmployeeDialog(QDialog):

    def __init__(self, employee_id: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Employee")
        self.setMinimumWidth(480)
        self.setModal(True)
        self._employee_id = employee_id
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(28, 24, 28, 20)
        self._layout.setSpacing(16)
        self._buttons = None
        self._layout.addWidget(QLabel("Loading…"))

        run_api_task(
            lambda: employees.get_employee(employee_id),
            self._on_loaded,
            self._on_load_error,
        )

    def _on_load_error(self, exc: Exception):
        message = exc.message if isinstance(exc, ApiError) else str(exc)
        QMessageBox.warning(self, "Edit Employee", message)
        self.reject()

    def _on_loaded(self, employee):
        if not employee:
            self.reject()
            return
        _clear_layout(self._layout)
        self._build_form(employee)

    def _populate_dept_combo(self, all_depts: list[dict], selected_id: int):
        self._dept_combo.clear()
        current_index = 0
        for i, dept in enumerate(all_depts):
            self._dept_combo.addItem(dept["name"], dept["id"])
            if dept["id"] == selected_id:
                current_index = i
        self._dept_combo.setCurrentIndex(current_index)

    def _build_form(self, employee: dict):
        title = QLabel(f"Edit Employee - {employee['first_name']} {employee['last_name']}")
        title.setObjectName("DeptName")
        self._layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        id_label = QLabel(self._employee_id)
        id_label.setObjectName("EmployeeID")
        form.addRow("Employee ID", id_label)

        self._first_edit = QLineEdit(employee["first_name"])
        form.addRow("First Name *", self._first_edit)

        self._last_edit = QLineEdit(employee["last_name"])
        form.addRow("Last Name *", self._last_edit)

        self._dept_combo = QComboBox()
        cached = departments.get_cached_depts()
        if cached:
            self._populate_dept_combo(cached, employee["dept_id"])
        else:
            self._dept_combo.addItem("Loading departments…", employee["dept_id"])
            run_api_task(
                departments.prefetch,
                lambda depts: self._populate_dept_combo(depts, employee["dept_id"]),
                None,
            )
        form.addRow("Department", self._dept_combo)

        self._notes_edit = QTextEdit()
        self._notes_edit.setPlainText(employee.get("notes") or "")
        self._notes_edit.setFixedHeight(70)
        form.addRow("Notes", self._notes_edit)

        self._layout.addLayout(form)

        self._buttons = _ok_cancel(self, "Save Changes")
        self._buttons.accepted.connect(self._accept)
        self._layout.addWidget(self._buttons)

    def _accept(self):
        first = self._first_edit.text().strip()
        last = self._last_edit.text().strip()
        if not first or not last:
            QMessageBox.warning(self, "Required", "Please fill in all required fields.")
            return

        dept_id = self._dept_combo.currentData()
        notes = self._notes_edit.toPlainText().strip()

        def task():
            employees.edit_employee(
                self._employee_id,
                first_name=first,
                last_name=last,
                dept_id=dept_id,
                notes=notes,
            )

        _run_save(self, self._buttons, task, "Edit Employee")


class AddComputerDialog(QDialog):

    def __init__(self, employee_id: str | None = None, dept_id: int | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Computer")
        self.setMinimumWidth(520)
        self.setModal(True)
        self._employee_id = employee_id
        self._dept_id = dept_id

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 20)
        layout.setSpacing(16)

        title = QLabel("New Computer")
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

        self._webcam_edit = QLineEdit()
        self._webcam_edit.setPlaceholderText("e.g. Logitech C920")
        form.addRow("Webcam", self._webcam_edit)

        self._phone_edit = QLineEdit()
        self._phone_edit.setPlaceholderText("e.g. Cisco 7841")
        form.addRow("Desk Phone", self._phone_edit)

        layout.addLayout(form)

        self._buttons = _ok_cancel(self, "Add Computer")
        self._buttons.accepted.connect(self._accept)
        layout.addWidget(self._buttons)

    def _accept(self):
        def task():
            computers.add_computer(
                computer_type="employee" if self._employee_id else "shared",
                employee_id=self._employee_id,
                dept_id=self._dept_id,
                pc_model=self._pc_edit.text().strip(),
                monitor_model=self._monitor_edit.text().strip(),
                ram=self._ram_edit.text().strip(),
                storage=self._storage_edit.text().strip(),
                os_version=self._os_edit.text().strip(),
                webcam_specs=self._webcam_edit.text().strip(),
                desk_phone=self._phone_edit.text().strip(),
            )

        _run_save(self, self._buttons, task, "Add Computer")


class EditComputerDialog(QDialog):

    def __init__(self, computer_id: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Device")
        self.setMinimumWidth(520)
        self.setModal(True)
        self._computer_id = computer_id
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(28, 24, 28, 20)
        self._layout.setSpacing(16)
        self._buttons = None
        self._layout.addWidget(QLabel("Loading…"))

        run_api_task(
            lambda: computers.get_computer(computer_id),
            self._on_loaded,
            self._on_load_error,
        )

    def _on_load_error(self, exc: Exception):
        message = exc.message if isinstance(exc, ApiError) else str(exc)
        QMessageBox.warning(self, "Edit Device", message)
        self.reject()

    def _on_loaded(self, computer):
        if not computer:
            self.reject()
            return
        _clear_layout(self._layout)
        self._build_form(computer)

    def _build_form(self, computer: dict):
        title = QLabel("Edit Device")
        title.setObjectName("DetailName")
        self._layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        def field(placeholder, val):
            edit = QLineEdit(val or "")
            edit.setPlaceholderText(placeholder)
            return edit

        self._monitor = field("e.g. Dell U2722D", computer.get("monitor_model") or "")
        self._pc = field("e.g. Dell OptiPlex 7090", computer.get("pc_model") or "")
        self._ram = field("e.g. 16 GB", computer.get("ram") or "")
        self._storage = field("e.g. 512 GB SSD", computer.get("storage") or "")
        self._os = field("e.g. Windows 11 Pro", computer.get("os_version") or "")
        self._webcam = field("e.g. Logitech C920", computer.get("webcam_specs") or "")
        self._phone = field("e.g. Cisco 7841", computer.get("desk_phone") or "")

        form.addRow("Monitor Model", self._monitor)
        form.addRow("PC Model", self._pc)
        form.addRow("RAM", self._ram)
        form.addRow("Storage", self._storage)
        form.addRow("OS Version", self._os)
        form.addRow("Webcam", self._webcam)
        form.addRow("Desk Phone", self._phone)

        self._notes = QTextEdit()
        self._notes.setPlainText(computer.get("notes") or "")
        self._notes.setFixedHeight(60)
        form.addRow("Notes", self._notes)

        self._layout.addLayout(form)

        self._buttons = _ok_cancel(self, "Save Changes")
        self._buttons.accepted.connect(self._accept)
        self._layout.addWidget(self._buttons)

    def _accept(self):
        def task():
            computers.edit_computer(
                self._computer_id,
                pc_model=self._pc.text().strip(),
                monitor_model=self._monitor.text().strip(),
                ram=self._ram.text().strip(),
                storage=self._storage.text().strip(),
                os_version=self._os.text().strip(),
                webcam_specs=self._webcam.text().strip(),
                desk_phone=self._phone.text().strip(),
                notes=self._notes.toPlainText().strip(),
            )

        _run_save(self, self._buttons, task, "Edit Device")


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

        self._buttons = _ok_cancel(self, "Add Instrument")
        self._buttons.accepted.connect(self._accept)
        layout.addWidget(self._buttons)

    def _accept(self):
        name = self._name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Required", "Instrument name cannot be empty.")
            return

        model = self._model_edit.text().strip()
        notes = self._notes_edit.toPlainText().strip()

        def task():
            instruments.add_instrument(self._lab_id, name, model, notes)

        _run_save(self, self._buttons, task, "Add Instrument")
