from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout,
    QTreeWidget, QTreeWidgetItem, QDialog, QDialogButtonBox,
    QFormLayout, QLineEdit, QComboBox, QMessageBox, QFrame,
    QPushButton
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

import backend.departments as departments
from frontend.theme import SIDEBAR_MIN_WIDTH, SIDEBAR_MAX_WIDTH
from frontend.widgets import primary_button, section_label, h_separator

_DEPT_NAME_ROLE = Qt.ItemDataRole.UserRole.value + 1
_DEPT_ID_ROLE   = Qt.ItemDataRole.UserRole

# Sentinel dept_id for the "All Employees" virtual tab
ALL_EMPLOYEES_ID = -1



class DeptTree(QTreeWidget):
    dept_selected = pyqtSignal(int, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderHidden(True)
        self.setIndentation(16)
        self.setAnimated(True)
        self.setRootIsDecorated(False) # Kept False to hide native OS arrows
        self.itemClicked.connect(self._on_click)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
       
        # Track expanded states across full database reloads
        self._expanded_ids: set[int] = set()

    def refresh(self, selected_id=None):
        """
        Only called on initial startup or when a brand-new department 
        is added via the AddDeptDialog.
        """
        self.blockSignals(True)
        self.clear()
        all_depts = departments.get_all_depts()

        roots = [d for d in all_depts if d["parent_id"] is None]
        children_map: dict[int, list] = {}
        for d in all_depts:
            if d["parent_id"] is not None:
                children_map.setdefault(d["parent_id"], []).append(d)

        def add_item(parent_widget, dept, depth=0):
            item = QTreeWidgetItem(parent_widget)
            has_children = bool(children_map.get(dept["id"]))
            is_expanded = dept["id"] in self._expanded_ids

            name = dept["name"]
            if has_children:
                chevron = "▼" if is_expanded else "▶"
                item.setText(0, f"{name}  {chevron}")
            else:
                item.setText(0, f"  {name}" if depth > 0 else name)

            item.setData(0, _DEPT_ID_ROLE, dept["id"])
            item.setData(0, _DEPT_NAME_ROLE, dept["name"])
           
            if dept["id"] == selected_id:
                item.setSelected(True)

            # Build ALL items into the tree structure immediately
            if has_children:
                for child in children_map.get(dept["id"], []):
                    add_item(item, child, depth + 1)
                # Apply initial expansion state smoothly
                item.setExpanded(is_expanded)

            return item

        for root_dept in roots:
            add_item(self, root_dept)

        self.blockSignals(False)

    def _on_click(self, item: QTreeWidgetItem):
        dept_id   = item.data(0, _DEPT_ID_ROLE)
        dept_name = item.data(0, _DEPT_NAME_ROLE)

        # Check if this dept has children natively without DB calls
        has_children = item.childCount() > 0

        if has_children:
            self.blockSignals(True)
            
            # Toggle native state and tracking set
            if item.isExpanded():
                item.setExpanded(False)
                self._expanded_ids.discard(dept_id)
                item.setText(0, f"{dept_name}  ▶")
                
                # Clear selection when collapsing per your spec
                self.clearSelection() 
            else:
                item.setExpanded(True)
                self._expanded_ids.add(dept_id)
                item.setText(0, f"{dept_name}  ▼")
                
                # Keep parent highlighted when expanding
                self.clearSelection()
                item.setSelected(True)
                
            self.blockSignals(False)
        else:
            # Leaf dept — load inventory and highlight natively
            self.clearSelection()
            item.setSelected(True)
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

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        ok_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
        ok_button.setObjectName("PrimaryBtn")
        ok_button.setText("Add")
        ok_button.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_button = buttons.button(QDialogButtonBox.StandardButton.Cancel)
        cancel_button.setObjectName("GhostBtn")
        cancel_button.setCursor(Qt.CursorShape.PointingHandCursor)
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
    dept_selected          = pyqtSignal(int, str)
    all_employees_selected = pyqtSignal()  # fired when All Employees tab is clicked

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setMinimumWidth(SIDEBAR_MIN_WIDTH)
        self.setMaximumWidth(SIDEBAR_MAX_WIDTH)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        title = QLabel("Departments")
        title.setObjectName("SidebarTitle")
        layout.addWidget(title)

        layout.addWidget(h_separator())

        # ── All Employees tab ──────────────────────────────────────────
        self._all_emp_btn = QPushButton("All Employees")
        self._all_emp_btn.setObjectName("AllEmployeesBtn")
        self._all_emp_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._all_emp_btn.setFlat(True)
        self._all_emp_btn.setCheckable(True)  # Fixes highlighting & toggle state
        
        # Forces text completely to the left side edge with padding
        self._all_emp_btn.setStyleSheet("text-align: left; padding-left: 16px;")
        
        self._all_emp_btn.clicked.connect(self._on_all_employees)
        layout.addWidget(self._all_emp_btn)

        # ── Department tree ────────────────────────────────────────────
        self._tree = DeptTree()
        self._tree.dept_selected.connect(self._on_dept_selected)
        layout.addWidget(self._tree, 1)

        layout.addWidget(h_separator())

        # ── Footer: Add Department ─────────────────────────────────────
        footer = QWidget()
        footer.setObjectName("SidebarFooter")
        footer.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(16, 10, 16, 18)
        add_button = primary_button("+ Add Department")
        add_button.clicked.connect(self._add_dept)
        footer_layout.addWidget(add_button)
        layout.addWidget(footer)

        self._selected_id: int | None = None

    def refresh(self):
        self._tree.refresh(self._selected_id)

    def clear_selection(self):
        self._selected_id = None
        self._tree.clearSelection()
        self._all_emp_btn.setChecked(False)

    def _on_dept_selected(self, dept_id: int, dept_name: str):
        self._selected_id = dept_id
        self._all_emp_btn.setChecked(False)
        self.dept_selected.emit(dept_id, dept_name)

    def _on_all_employees(self):
        self._selected_id = None
        self._tree.clearSelection()
        self._all_emp_btn.setChecked(True)
        self.all_employees_selected.emit()

    def _add_dept(self):
        dlg = AddDeptDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.refresh()