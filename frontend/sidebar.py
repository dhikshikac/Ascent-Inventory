from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, 
    QTreeWidget, QTreeWidgetItem, QDialog, QDialogButtonBox,
    QFormLayout, QLineEdit, QComboBox, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor

import backend.departments as departments
from frontend.theme import SIDEBAR_MIN_WIDTH, SIDEBAR_MAX_WIDTH
from frontend.widgets import primary_button, section_label, h_separator

class DeptTree(QTreeWidget):
    dept_selected = pyqtSignal(int, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderHidden(True)
        self.setIndentation(16)
        self.setAnimated(True) 
        self.itemClicked.connect(self._on_click)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    def refresh(self, selected_id=None):
        self.clear()
        all_depts = departments.get_all_depts()

        by_id = {d["id"]: d for d in all_depts}

        roots = [d for d in all_depts if d["parent_id"] is None]
        children_map: dict[int, list] = {}
        for d in all_depts:
            if d["parent_id"] is not None:
                children_map.setdefault(d["parent_id"], []).append(d)
        
        def add_item(parent_widget, dept):
            item = QTreeWidgetItem(parent_widget)
            item.setText(0, dept["name"])
            item.setData(0, Qt.ItemDataRole.UserRole, dept["id"])
            item.setExpanded(True)

            if dept["id"] == selected_id:
                item.setSelected(True)
            for child in children_map.get(dept["id"], []):
                add_item(item, child)
            return item
        
        for root_dept in roots:
            item = add_item(self, root_dept)
            item.setExpanded(True)

        self.expandAll()
    
    def _on_click(self, item: QTreeWidgetItem):
        dept_id = item.data(0, Qt.ItemDataRole.UserRole)
        dept_name = item.text(0)
        self.dept_selected.emit(dept_id, dept_name)

class AddDeptDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Department")
        self.setMinimumWidth(SIDEBAR_MIN_WIDTH)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        title = QLabel("Add New Department")
        title.setObjectName("DeptName")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("Department Name")
        form.addRow("Name:", self._name_edit)

        self._parent_combo = QComboBox()
        self._parent_combo.addItem("None (top-level)", None)
        for d in departments.get_all_depts():
            self._parent_combo.addItem(d["name"], d["id"])
        form.addRow("Parent Department:", self._parent_combo)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        ok_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
        ok_button.setObjectName("PrimaryBtn")
        ok_button.setText("Add")
        layout.addWidget(buttons)
    
    def _accept(self):
        name = self._name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Required", "Department name cannot be empty.")
            return
        
        parent_id = self._parent_combo.currentData()
        result = departments.add_dept(name, parent_id)
        if result is None:
            QMessageBox.warning(self, "Duplicate", f"'{name}' already exists.")
            return
        self.accept()

class Sidebar(QWidget):
    dept_selected = pyqtSignal(int, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setMinimumWidth(SIDEBAR_MIN_WIDTH)
        self.setMaximumWidth(SIDEBAR_MAX_WIDTH)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 16)
        layout.setSpacing(0)

        title = QLabel("Departments")
        title.setObjectName("SidebarTitle")
        layout.addWidget(title)

        layout.addWidget(h_separator())

        self._tree = DeptTree()
        self._tree.dept_selected.connect(self.dept_selected)
        layout.addWidget(self._tree, 1)

        layout.addWidget(h_separator())

        footer = QWidget()
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(16, 8, 16, 0)
        add_button = primary_button("+ Add Department")
        add_button.clicked.connect(self._add_dept)
        footer_layout.addWidget(add_button)
        layout.addWidget(footer)

        self._selected_id: int | None = None

    
    def refresh(self):
        self._tree.refresh(self._selected_id)

    def _add_dept(self):
        dlg = AddDeptDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.refresh()