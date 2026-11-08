"""
Один стикер — перетаскиваемое окно без рамки поверх рабочего стола.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTextEdit, QPushButton, QSizeGrip
)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtSql import QSqlQuery

from core.cipher import decrypt


def _dark(hex_color: str, amount: int = 30) -> str:
    """Возвращает чуть более тёмный вариант цвета для заголовка стикера."""
    c = QColor(hex_color)
    h, s, v, a = c.getHsv()
    c.setHsv(h, min(s + 20, 255), max(v - amount, 0), a)
    return c.name()


class StickerWidget(QWidget):
    def __init__(self, note_id: int, title: str, content: str,
                 cipher: str, color: str,
                 x: int | None, y: int | None,
                 on_close_callback=None):
        super().__init__()
        self.note_id = note_id
        self.color = color or "#FFFACD"
        self.on_close_callback = on_close_callback

        # Флаги: без рамки, всегда поверх, показывается в таскбаре
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setMinimumSize(200, 160)
        self.resize(220, 200)

        # Позиция: сохранённая или случайная
        if x is not None and y is not None:
            self.move(x, y)
        else:
            import random
            self.move(random.randint(100, 800), random.randint(100, 500))

        self._drag_pos = QPoint()
        self._build_ui(title, content, cipher)

    # ──────────────── UI ────────────────

    def _build_ui(self, title: str, content: str, cipher: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 6)
        layout.setSpacing(0)

        # ── Заголовок-полоска (за неё тащим) ──
        header = QWidget()
        header.setFixedHeight(30)
        header.setStyleSheet(
            f"background: {_dark(self.color)}; border-radius: 4px 4px 0 0;"
        )
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(8, 0, 4, 0)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("font-weight: bold; font-size: 11px; color: #333;")
        title_lbl.setWordWrap(False)
        header_layout.addWidget(title_lbl, stretch=1)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(20, 20)
        close_btn.setStyleSheet(
            "QPushButton { background: transparent; border: none; color: #555; font-size: 12px; }"
            "QPushButton:hover { color: #c0392b; }"
        )
        close_btn.clicked.connect(self._on_close)
        header_layout.addWidget(close_btn)

        layout.addWidget(header)

        # ── Тело стикера ──
        body = QWidget()
        body.setStyleSheet(f"background: {self.color};")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(8, 6, 8, 2)

        # Расшифровываем текст для показа
        try:
            plain_text = decrypt(content, cipher)
        except Exception:
            plain_text = content

        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(plain_text)
        self.text_edit.setReadOnly(False)
        self.text_edit.setStyleSheet(
            f"background: transparent; border: none; "
            f"font-size: 12px; color: #222;"
        )
        self.text_edit.setFrameShape(self.text_edit.Shape.NoFrame)
        # Сохраняем изменения при потере фокуса
        self.text_edit.focusOutEvent = self._on_text_focus_out
        body_layout.addWidget(self.text_edit)

        # Уголок для изменения размера
        grip = QSizeGrip(self)
        grip.setStyleSheet(f"background: transparent;")
        grip_row = QHBoxLayout()
        grip_row.addStretch()
        grip_row.addWidget(grip)
        body_layout.addLayout(grip_row)

        layout.addWidget(body, stretch=1)

        self.setStyleSheet(
            f"QWidget {{ background: {self.color}; border-radius: 4px; }}"
        )

    # ──────────────── Перетаскивание ────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and not self._drag_pos.isNull():
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        # Сохраняем позицию в БД
        self._save_position()
        self._drag_pos = QPoint()

    # ──────────────── Тень (paintEvent) ────────────────

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor(0, 0, 0, 40))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 4, 4)

    # ──────────────── Сохранение ────────────────

    def _save_position(self):
        query = QSqlQuery()
        query.prepare("UPDATE notes SET sticker_x = ?, sticker_y = ? WHERE id = ?")
        query.addBindValue(self.x())
        query.addBindValue(self.y())
        query.addBindValue(self.note_id)
        query.exec()

    def _on_text_focus_out(self, event):
        """Сохраняем отредактированный текст стикера обратно в БД (без шифрования)."""
        QTextEdit.focusOutEvent(self.text_edit, event)
        new_text = self.text_edit.toPlainText()
        query = QSqlQuery()
        query.prepare("UPDATE notes SET content = ?, cipher = 'none' WHERE id = ?")
        query.addBindValue(new_text)
        query.addBindValue(self.note_id)
        query.exec()

    def _on_close(self):
        self._save_position()
        if self.on_close_callback:
            self.on_close_callback(self.note_id)
        self.close()
