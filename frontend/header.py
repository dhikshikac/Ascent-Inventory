from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QLineEdit
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

class HeaderBar(QWidget):
    search_changed = pyqtSignal(str)

    def __init__(self, context: str = "", show_search: bool = True, parent = None):
        super().__init__(parent)
        self.setObjectName("HeaderBar")
        self.setFixedHeight(48)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 16, 0)
        layout.setSpacing(0)

        title = QLabel("ASCENT Inventory")
        title.setObjectName("AppTitle")
        f = title.font()
        f.setWeight(QFont.Weight.Bold)
        f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 2)
        title.setFont(f)
        layout.addWidget(title)

        if context:
            sep = QLabel(" / ")
            sep.setObjectName("HeaderSeparator")
            sep.setStyleSheet(f"color: #E5E7EB; font-size: 16px; padding: 0 4px;")
            layout.addWidget(sep)

            context_label = QLabel(context)
            context_label.setObjectName("HeaderContext")
            layout.addWidget(context_label)
        
        layout.addStretch()

        if show_search:
            self._search = QLineEdit()
            self._search.setObjectName("SearchBar")
            self._search.setPlaceholderText("Search employees, IDs...")
            self._search.textChanged.connect(self.search_changed)
            layout.addWidget(self._search)
            self._search.hide()

    def set_search_text(self, text: str):
        if hasattr(self, "_search"):
            self._search.setText(text)

    def clear_search(self):
        if hasattr(self, "_search"):
            self._search.clear()

    def set_search_visible(self, visible: bool):
        if not hasattr(self, "_search"):
            return
        if not visible:
            self._search.blockSignals(True)
            self._search.clear()
            self._search.blockSignals(False)
        self._search.setVisible(visible)