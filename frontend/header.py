from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QLineEdit, QVBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap

from frontend.theme import SIDEBAR_MIN_WIDTH, TEXT_SECONDARY
from frontend.resources import asset_path


class HeaderBar(QWidget):
    search_changed = pyqtSignal(str)
    _LOGO_V_MARGIN = 12
    _LOGO_H_MARGIN = 12
    _MAX_LOGO_HEIGHT = 52

    def __init__(self, context: str = "", show_search: bool = True, parent=None):
        super().__init__(parent)
        self.setObjectName("HeaderBar")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._source_pixmap = self._load_logo()

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
            sep.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 16px; padding: 0 4px;")
            layout.addWidget(sep)

            context_label = QLabel(context)
            context_label.setObjectName("HeaderContext")
            layout.addWidget(context_label)

        layout.addStretch()

        if show_search:
            self._search = QLineEdit()
            self._search.setObjectName("SearchBar")
            self._search.setPlaceholderText("Search employees, IDs...")
            self._search_debounce = QTimer(self)
            self._search_debounce.setSingleShot(True)
            self._search_debounce.setInterval(200)
            self._search_debounce.timeout.connect(self._emit_search)
            self._search.textChanged.connect(self._on_search_text_changed)
            layout.addWidget(self._search)

    def _on_search_text_changed(self, _text: str):
        self._search_debounce.start()

    def _emit_search(self):
        if hasattr(self, "_search"):
            self.search_changed.emit(self._search.text())

    def _load_logo(self) -> QPixmap:
        path = asset_path("media", "ascent-logo.png")
        pixmap = QPixmap(path)
        if pixmap.isNull():
            print(f"Warning: header logo not found at {path}")
        return pixmap

    def clear_search(self):
        if hasattr(self, "_search"):
            self._search.clear()

    def set_search_visible(self, visible: bool):
        if hasattr(self, "_search"):
            self._search.setVisible(visible)

    def set_brand_width(self, width: int):
        self._brand.setFixedWidth(width)
        inner_width = max(1, width - 2 * self._LOGO_H_MARGIN)
        if self._source_pixmap.isNull():
            self.setFixedHeight(self._MAX_LOGO_HEIGHT + 2 * self._LOGO_V_MARGIN)
            return
        scaled = self._source_pixmap.scaled(
            inner_width,
            self._MAX_LOGO_HEIGHT,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._title.setPixmap(scaled)
        self._title.setFixedSize(scaled.size())
        self.setFixedHeight(scaled.height() + 2 * self._LOGO_V_MARGIN)
