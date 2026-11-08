"""
Доска стикеров — панель управления. Стикеры живут независимо от панели.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QCheckBox, QScrollArea
)
from PyQt6.QtCore import Qt
from PyQt6.QtSql import QSqlQuery

from ui.sticker_widget import StickerWidget

# Глобальный словарь стикеров — живёт вне панели, не удаляется при её закрытии
_active_stickers: dict[int, StickerWidget] = {}


class StickerBoard(QWidget):
    def __init__(self, user_id: int, parent=None):
        super().__init__(parent)
        self.user_id = user_id

        self.setWindowTitle("Стикеры")
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setFixedWidth(270)

        self._build_ui()
        self._load_list()

    # ──────────────── UI ────────────────

    def _build_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("Стикеры на рабочем столе")
        title.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(title)

        hint = QLabel(
            "Отметьте заметки чтобы показать их как стикеры.\n"
            "Стикеры остаются на экране даже после закрытия панели."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(hint)

        # Прокручиваемая область с чекбоксами
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setMaximumHeight(300)

        self._list_widget = QWidget()
        self.check_layout = QVBoxLayout(self._list_widget)
        self.check_layout.setContentsMargins(0, 0, 0, 0)
        self.check_layout.setSpacing(2)
        scroll.setWidget(self._list_widget)
        layout.addWidget(scroll)

        btn_row = QHBoxLayout()
        show_all_btn = QPushButton("Показать все")
        show_all_btn.clicked.connect(self._show_all)
        btn_row.addWidget(show_all_btn)

        hide_all_btn = QPushButton("Скрыть все")
        hide_all_btn.clicked.connect(self._hide_all)
        btn_row.addWidget(hide_all_btn)
        layout.addLayout(btn_row)

        close_btn = QPushButton("Закрыть панель")
        close_btn.setStyleSheet("color: #888;")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

    def _load_list(self):
        """Заполняет список заметок чекбоксами."""
        while self.check_layout.count():
            item = self.check_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        query = QSqlQuery()
        query.prepare("""
            SELECT id, title, content, cipher, color, sticker_x, sticker_y
            FROM notes WHERE user_id = ?
            ORDER BY created_at DESC
        """)
        query.addBindValue(self.user_id)
        query.exec()

        while query.next():
            note_id = query.value(0)
            title   = query.value(1)
            content = query.value(2)
            cipher  = query.value(3)
            color   = query.value(4) or "#FFFACD"
            sx      = query.value(5)
            sy      = query.value(6)

            cb = QCheckBox(title)
            # Уже открытый стикер — ставим галочку
            cb.setChecked(note_id in _active_stickers)
            cb.setStyleSheet(
                f"QCheckBox::indicator {{ width:14px; height:14px; "
                f"background:{color}; border:1px solid #999; border-radius:2px; }}"
                f"QCheckBox::indicator:checked {{ border:2px solid #333; }}"
            )
            cb.toggled.connect(
                lambda checked, nid=note_id, t=title, c=content,
                       ci=cipher, cl=color, x=sx, y=sy:
                self._toggle(checked, nid, t, c, ci, cl, x, y)
            )
            self.check_layout.addWidget(cb)

        self.adjustSize()

    # ──────────────── Переключение стикера ────────────────

    def _toggle(self, show: bool, note_id: int, title: str,
                content: str, cipher: str, color: str, x, y):
        if show:
            if note_id not in _active_stickers:
                sticker = StickerWidget(
                    note_id=note_id,
                    title=title,
                    content=content,
                    cipher=cipher,
                    color=color,
                    x=x if x not in (None, "") else None,
                    y=y if y not in (None, "") else None,
                    on_close_callback=self._on_sticker_closed,
                )
                sticker.show()
                _active_stickers[note_id] = sticker
        else:
            if note_id in _active_stickers:
                _active_stickers[note_id].close()
                del _active_stickers[note_id]

    def _on_sticker_closed(self, note_id: int):
        """Пользователь закрыл стикер крестиком — снимаем галочку."""
        if note_id in _active_stickers:
            del _active_stickers[note_id]
        # Обновляем галочки в панели если она открыта
        self._sync_checkboxes()

    def _sync_checkboxes(self):
        """Синхронизирует состояние чекбоксов с _active_stickers."""
        for i in range(self.check_layout.count()):
            widget = self.check_layout.itemAt(i).widget()
            if isinstance(widget, QCheckBox):
                # Нет простого способа получить note_id из чекбокса —
                # просто перезагружаем список
                self._load_list()
                return

    def _show_all(self):
        for i in range(self.check_layout.count()):
            w = self.check_layout.itemAt(i).widget()
            if isinstance(w, QCheckBox):
                w.setChecked(True)

    def _hide_all(self):
        for i in range(self.check_layout.count()):
            w = self.check_layout.itemAt(i).widget()
            if isinstance(w, QCheckBox):
                w.setChecked(False)

    def closeEvent(self, event):
        # НЕ закрываем стикеры — они живут независимо
        super().closeEvent(event)
