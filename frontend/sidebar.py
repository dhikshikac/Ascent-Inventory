from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout,
    QTreeWidget, QTreeWidgetItem, QDialog, QDialogButtonBox,
    QFormLayout, QLineEdit, QComboBox, QMessageBox, QFrame,
    QPushButton, QStyledItemDelegate, QStyle, QStyleOptionViewItem,
)
from PyQt6.QtCore import Qt, pyqtSignal, QRect
from PyQt6.QtGui import QIcon, QColor, QPainter

import backend.departments as departments
from frontend.theme import (
    SIDEBAR_MIN_WIDTH, SIDEBAR_MAX_WIDTH,
    SIDEBAR_BKG, ROW_SELECTED, ROW_HOVER, TEXT_PRIMARY, TEXT_ON_DARK,
)
from frontend.widgets import primary_button, section_label, h_separator

_DEPT_NAME_ROLE = Qt.ItemDataRole.UserRole.value + 1
_DEPT_ID_ROLE   = Qt.ItemDataRole.UserRole

ALL_EMPLOYEES_ID = -1


class _DeptRowDelegate(QStyledItemDelegate):
    ICON_SIZE = 14
    ICON_MARGIN = 10
    _SIDEBAR = QColor(SIDEBAR_BKG)
    _SELECTED = QColor(ROW_SELECTED)
    _HOVER = QColor(ROW_HOVER)

    def __init__(self, icon_down: QIcon, icon_up: QIcon, parent=None):
        super().__init__(parent)
        self._icon_down = icon_down
        self._icon_up = icon_up

    def _item_depth(self, item: QTreeWidgetItem) -> int:
        depth = 0
        parent = item.parent()
        while parent:
            depth += 1
            parent = parent.parent()
        return depth

    def _item_indent(self, tree: QTreeWidget, item: QTreeWidgetItem) -> int:
        return tree.indentation() * self._item_depth(item)

    def paint(self, painter, option, index):
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)

        tree = opt.widget
        item = tree.itemFromIndex(index) if isinstance(tree, QTreeWidget) else None
        indent = self._item_indent(tree, item) if item and tree else 0
        content_rect = QRect(option.rect)

        row_rect = QRect(option.rect)
        if indent:
            row_rect = row_rect.adjusted(-indent, 0, 0, 0)

        selected = bool(opt.state & QStyle.StateFlag.State_Selected)
        hovered = bool(opt.state & QStyle.StateFlag.State_MouseOver)

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if selected:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(self._SELECTED)
            painter.drawRoundedRect(row_rect, 5, 5)
        elif hovered:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(self._HOVER)
            painter.drawRoundedRect(row_rect, 5, 5)
        elif indent:
            indent_rect = QRect(
                option.rect.left() - indent, option.rect.top(),
                indent, option.rect.height(),
            )
            painter.fillRect(indent_rect, self._SIDEBAR)
        painter.restore()

        text = index.data(Qt.ItemDataRole.DisplayRole) or ""
        text_left = content_rect.left() + 8 + indent
        text_right = content_rect.right()
        if item and item.childCount() > 0:
            text_right -= self.ICON_SIZE + self.ICON_MARGIN

        text_rect = QRect(
            text_left, content_rect.top(),
            text_right - text_left, content_rect.height(),
        )
        if selected:
            painter.setPen(QColor(TEXT_ON_DARK))
        else:
            painter.setPen(QColor(TEXT_PRIMARY))
        painter.drawText(
            text_rect,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            text,
        )

        if item and item.childCount() > 0:
            icon = self._icon_up if item.isExpanded() else self._icon_down
            icon_rect = QRect(
                content_rect.right() - self.ICON_SIZE - self.ICON_MARGIN,
                content_rect.center().y() - self.ICON_SIZE // 2,
                self.ICON_SIZE,
                self.ICON_SIZE,
            )
            icon.paint(painter, icon_rect)


class DeptTree(QTreeWidget):
    dept_selected = pyqtSignal(int, str)
    all_employees_selected = pyqtSignal() 

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderHidden(True)
        self.setIndentation(16)
        self.setAnimated(True)
        self.setRootIsDecorated(False) 
        self.itemClicked.connect(self._on_click)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._icon_down = QIcon("media/down.svg")
        self._icon_up = QIcon("media/up.svg")
        self.setItemDelegate(_DeptRowDelegate(self._icon_down, self._icon_up, self))

        self._expanded_ids: set[int] = set()

    def refresh(self, selected_id=None):
        self.blockSignals(True)
        self.clear()

        all_emp_item = QTreeWidgetItem(self)
        all_emp_item.setText(0, "All Employees")
        all_emp_item.setData(0, _DEPT_ID_ROLE, ALL_EMPLOYEES_ID)
        all_emp_item.setData(0, _DEPT_NAME_ROLE, "All Employees")
        
        if selected_id == ALL_EMPLOYEES_ID:
            all_emp_item.setSelected(True)

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

            item.setText(0, dept["name"])

            item.setData(0, _DEPT_ID_ROLE, dept["id"])
            item.setData(0, _DEPT_NAME_ROLE, dept["name"])
           
            if dept["id"] == selected_id:
                item.setSelected(True)

            if has_children:
                for child in sorted(
                    children_map.get(dept["id"], []), key=lambda d: d["name"].lower()
                ):
                    add_item(item, child, depth + 1)
                item.setExpanded(is_expanded)

            return item

        for root_dept in sorted(roots, key=lambda d: d["name"].lower()):
            add_item(self, root_dept)

        self.blockSignals(False)

    def _on_click(self, item: QTreeWidgetItem):
        dept_id   = item.data(0, _DEPT_ID_ROLE)
        dept_name = item.data(0, _DEPT_NAME_ROLE)

        # Handle the custom virtual "All Employees" top item click
        if dept_id == ALL_EMPLOYEES_ID:
            self.clearSelection()
            item.setSelected(True)
            self.all_employees_selected.emit()
            return

        has_children = item.childCount() > 0

        if has_children:
            self.blockSignals(True)
            if item.isExpanded():
                item.setExpanded(False)
                self._expanded_ids.discard(dept_id)
                self.clearSelection()
            else:
                item.setExpanded(True)
                self._expanded_ids.add(dept_id)
                self.clearSelection()
                item.setSelected(True)
            self.viewport().update()
            self.blockSignals(False)
        else:
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
    all_employees_selected = pyqtSignal()
    width_changed          = pyqtSignal(int)

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

        # ── Unified Department Tree Framework ──────────────────────────
        self._tree = DeptTree()
        self._tree.dept_selected.connect(self._on_dept_selected)
        
        # Capture the updated virtual tab emission here
        self._tree.all_employees_selected.connect(self._on_all_employees)
        
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

        # Initialize tracking with the virtual ID selected by default on boot
        self._selected_id: int | None = None

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.width_changed.emit(self.width())

    def refresh(self):
        self._tree.refresh(self._selected_id)

    def clear_selection(self):
        self._selected_id = None
        self._tree.clearSelection()

    def _on_dept_selected(self, dept_id: int, dept_name: str):
        self._selected_id = dept_id
        self.dept_selected.emit(dept_id, dept_name)

    def _on_all_employees(self):
        self._selected_id = ALL_EMPLOYEES_ID
        self.all_employees_selected.emit()

    def _add_dept(self):
        dlg = AddDeptDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

            