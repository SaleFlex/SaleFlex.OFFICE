"""
Startup splash/about form for SaleFlex.OFFICE.
"""

from __future__ import annotations

import os

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QFont, QGuiApplication, QIcon, QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import QLabel, QSizePolicy, QSpacerItem, QVBoxLayout, QWidget

from settings.settings import Settings


class StartupForm(QWidget):
    """Display startup progress before login is available."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent=parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setFixedSize(500, 420)
        self._set_window_icon()

        self._title_label = QLabel("SaleFlex.OFFICE", self)
        self._title_label.setAlignment(Qt.AlignHCenter)
        self._title_label.setFont(QFont("Segoe UI", 26, QFont.Bold))
        self._title_label.setStyleSheet("color: #f8fafc; background: transparent;")

        self._version_label = QLabel(f"Version {Settings().app_version}", self)
        self._version_label.setAlignment(Qt.AlignHCenter)
        self._version_label.setFont(QFont("Segoe UI", 12))
        self._version_label.setStyleSheet("color: #cbd5e1; background: transparent;")

        self._message_label = QLabel("", self)
        self._message_label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self._message_label.setWordWrap(True)
        self._message_label.setFont(QFont("Segoe UI", 10))
        self._message_label.setStyleSheet(
            "color: #e2e8f0;"
            "background: rgba(15, 23, 42, 0.45);"
            "padding: 10px 14px;"
            "border: 1px solid rgba(148, 163, 184, 0.25);"
            "border-radius: 8px;"
            "min-height: 42px;"
        )
        self._message_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        layout = QVBoxLayout()
        layout.setContentsMargins(28, 34, 28, 26)
        layout.setSpacing(12)
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Fixed))
        layout.addWidget(self._title_label, alignment=Qt.AlignHCenter)
        layout.addWidget(self._version_label, alignment=Qt.AlignHCenter)
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))
        layout.addWidget(self._message_label)
        self.setLayout(layout)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, QColor(15, 23, 42))
        gradient.setColorAt(0.5, QColor(30, 41, 59))
        gradient.setColorAt(1, QColor(17, 24, 39))
        painter.fillRect(self.rect(), gradient)

        pen = QPen(QColor(255, 255, 255, 38), 1)
        painter.setPen(pen)
        painter.drawRoundedRect(1, 1, self.width() - 2, self.height() - 2, 8, 8)

    def show(self) -> None:  # type: ignore[override]
        self._center_on_primary_screen()
        super().show()

    def update_message(self, message: str) -> None:
        """Update startup progress text."""
        self._message_label.setText(message or "")
        self._message_label.repaint()
        QGuiApplication.processEvents()

    def dispose(self) -> None:
        """Close the startup form safely."""
        self.hide()
        self.setParent(None)
        self.deleteLater()

    def _set_window_icon(self) -> None:
        icon_path = Settings().app_icon
        if icon_path and os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

    def _center_on_primary_screen(self) -> None:
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            return
        geometry: QRect = screen.geometry()
        x = geometry.x() + (geometry.width() - self.width()) // 2
        y = geometry.y() + (geometry.height() - self.height()) // 2
        self.move(x, y)
