from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLabel,
    QLineEdit, QDialogButtonBox, QMessageBox,
)
from PyQt6.QtCore import Qt

from frontend.theme import load_stylesheet


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sign in — Ascent Inventory")
        self.setMinimumWidth(420)
        self.setModal(True)
        self.setStyleSheet(load_stylesheet())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 20)
        layout.setSpacing(16)

        title = QLabel("Sign in")
        title.setObjectName("DetailName")
        layout.addWidget(title)

        subtitle = QLabel("Use your Firebase email and password.")
        subtitle.setObjectName("DetailMeta")
        layout.addWidget(subtitle)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        self._email_edit = QLineEdit()
        self._email_edit.setPlaceholderText("you@company.com")
        form.addRow("Email", self._email_edit)

        self._password_edit = QLineEdit()
        self._password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._password_edit.setPlaceholderText("Password")
        self._password_edit.returnPressed.connect(self._try_accept)
        form.addRow("Password", self._password_edit)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        ok_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
        ok_button.setObjectName("PrimaryBtn")
        ok_button.setText("Sign in")
        ok_button.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_button = buttons.button(QDialogButtonBox.StandardButton.Cancel)
        cancel_button.setObjectName("GhostBtn")
        cancel_button.setCursor(Qt.CursorShape.PointingHandCursor)
        buttons.accepted.connect(self._try_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._email_edit.setFocus()

    def _try_accept(self):
        if not self.email():
            QMessageBox.warning(self, "Sign in", "Email is required.")
            return
        if not self.password():
            QMessageBox.warning(self, "Sign in", "Password is required.")
            return
        self.accept()

    def email(self) -> str:
        return self._email_edit.text().strip()

    def password(self) -> str:
        return self._password_edit.text()
