from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QLineEdit, QVBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap

from frontend.theme import SIDEBAR_MIN_WIDTH

class HeaderBar(QWidget):
    search_changed = pyqtSignal(str)
    _LOGO_V_MARGIN = 12
    _LOGO_H_MARGIN = 12

    def __init__(self, context: str = "", show_search: bool = True, parent = None):
        super().__init__(parent)
        self.setObjectName("HeaderBar")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._source_pixmap = QPixmap("media/ascent-logo.png")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 16, 0)
        layout.setSpacing(0)

        self._brand = QWidget()
        self._brand.setObjectName("BrandArea")
        self._brand.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        brand_layout = QVBoxLayout(self._brand)
        brand_layout.setContentsMargins(self._LOGO_H_MARGIN, self._LOGO_V_MARGIN, self._LOGO_H_MARGIN, self._LOGO_V_MARGIN)
        brand_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        brand_layout.setSpacing(0)

        self._title = QLabel()
        self._title.setObjectName("AppTitle")
        self._title.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand_layout.addWidget(self._title, 0, Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self._brand)
        self.set_brand_width(SIDEBAR_MIN_WIDTH)

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

    def set_search_text(self, text: str):
        if hasattr(self, "_search"):
            self._search.setText(text)

    def clear_search(self):
        if hasattr(self, "_search"):
            self._search.clear()

    def set_search_visible(self, visible: bool):
        if hasattr(self, "_search"):
            self._search.setVisible(visible)

    def set_brand_width(self, width: int):
        self._brand.setFixedWidth(width)
        inner_width = max(1, width - 2 * self._LOGO_H_MARGIN)
        scaled = self._source_pixmap.scaledToWidth(
            inner_width, Qt.TransformationMode.SmoothTransformation
        )
        self._title.setPixmap(scaled)
        self._title.setFixedSize(scaled.size())
        self.setFixedHeight(scaled.height() + 2 * self._LOGO_V_MARGIN)