from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, QListWidget, QTableWidget,
    QTableWidgetItem, QAbstractItemView, QFrame, QSizePolicy, QPushButton,
    QStyledItemDelegate, QStyle
)
from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QFont, QColor

def primary_button(text: str, parent=None) -> QPushButton:
    btn = QPushButton(text, parent)
    btn.setObjectName("PrimaryBtn")
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    return btn

def ghost_button(text: str, parent=None) -> QPushButton:
    btn = QPushButton(text, parent)
    btn.setObjectName("GhostBtn")
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    return btn

def danger_button(text: str, parent=None) -> QPushButton:
    btn = QPushButton(text, parent)
    btn.setObjectName("DangerBtn")
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    return btn

def back_button(text: str, parent=None) -> QPushButton:
    btn = QPushButton(text, parent)
    btn.setObjectName("BackBtn")
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    return btn

def section_label(text: str, parent=None) -> QLabel:
    label = QLabel(text.upper(), parent)
    label.setObjectName("SectionLabel")
    return label

def h_separator() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFrameShadow(QFrame.Shadow.Sunken)
    line.setStyleSheet("color: #E5E7EB; background-color: #E5E7EB; max-height: 1px;")
    return line

def v_separator() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.Shape.VLine)
    line.setFrameShadow(QFrame.Shadow.Sunken)
    line.setStyleSheet("color: #E5E7EB; background-color: #E5E7EB; max-width: 1px;")
    return line

def empty_state(message: str) -> QWidget:
    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label = QLabel(message)
    label.setObjectName("EmptyStateLabel")
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label.setWordWrap(True)
    layout.addWidget(label)
    return widget

def field_pair(label_text: str, value_text:str, parent=None) -> QWidget:
    widget = QWidget(parent)
    widget.setObjectName("FieldPair")
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(2)
    
    label = QLabel(label_text.upper())
    label.setObjectName("FieldLabel")
    
    value = QLabel(value_text or "-")
    value.setObjectName("FieldValue")
    value.setWordWrap(True)

    layout.addWidget(label)
    layout.addWidget(value)
    return widget

def spacer(horizontal: bool = True) -> QWidget:
    widget = QWidget()
    if horizontal:
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    else:
        widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
    return widget


_HOVER_COLOR   = QColor("#DBEAFE")
_DEFAULT_COLOR = QColor("#FFFFFF")
_SELECTED_COLOR = QColor("#7E9DDE")

class HoverRowDelegate(QStyledItemDelegate):
    """Paints the hovered table row across every cell."""

    def paint(self, painter, option, index):
        table = self.parent()
        if (
            isinstance(table, HoverTableWidget)
            and index.row() == table.hovered_row()
            and not (option.state & QStyle.StateFlag.State_Selected)
        ):
            painter.save()
            painter.fillRect(option.rect, _HOVER_COLOR)
            painter.restore()
        super().paint(painter, option, index)

class HoverTableWidget(QTableWidget):
    """QTableWidget that highlights the entire hovered row."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._hovered_row = -1
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)
        self.viewport().installEventFilter(self)
        self.setItemDelegate(HoverRowDelegate(self))
        self.cellEntered.connect(self._on_cell_entered)

    def eventFilter(self, source, event):
        if source is self.viewport():
            if event.type() == QEvent.Type.MouseMove:
                item = self.itemAt(event.pos())
                new_row = item.row() if item else -1
                if new_row != self._hovered_row:
                    old_row = self._hovered_row
                    self._hovered_row = new_row
                    self._repaint_row(old_row)
                    self._repaint_row(new_row)
            elif event.type() == QEvent.Type.Leave:
                old_row = self._hovered_row
                self._hovered_row = -1
                self._repaint_row(old_row)
        return super().eventFilter(source, event)

    def _on_cell_entered(self, row: int, _column: int):
        if row != self._hovered_row:
            old_row = self._hovered_row
            self._hovered_row = row
            self._repaint_row(old_row)
            self._repaint_row(row)

    def repaint_all_rows(self):
        for row in range(self.rowCount()):
            self._repaint_row(row)
        self.viewport().update()

    def hovered_row(self) -> int:
        return self._hovered_row

    def _repaint_row(self, row: int):
        if row < 0 or row >= self.rowCount():
            return
        is_selected = any(item.row() == row for item in self.selectedItems())
        if is_selected:
            color = _SELECTED_COLOR
        elif row == self._hovered_row:
            color = _HOVER_COLOR
        else:
            color = _DEFAULT_COLOR
        for col in range(self.columnCount()):
            item = self.item(row, col)
            if item:
                item.setBackground(color)
        self.viewport().update()

    def selectionChanged(self, selected, deselected):
        super().selectionChanged(selected, deselected)
        for idx in deselected.indexes():
            self._repaint_row(idx.row())
        for idx in selected.indexes():
            self._repaint_row(idx.row())