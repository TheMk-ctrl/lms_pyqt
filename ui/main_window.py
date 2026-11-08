"""
Главное окно: сетка карточек-заметок.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QScrollArea,
    QMessageBox, QStatusBar, QToolBar, QComboBox,
    QFileDialog, QGridLayout, QFrame, QSizePolicy, QSpacerItem
)
from PyQt6.QtSql import QSqlQuery
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QAction, QColor, QFont, QIcon

from ui.note_dialog import NoteDialog
from ui.view_note_dialog import ViewNoteDialog
from ui.cipher_demo_window import CipherDemoWindow
from core.cipher import cipher_names as get_cipher_names

CIPHER_LABELS = get_cipher_names()  # {'none': 'Без шифрования', 'caesar': 'Шифр Цезаря', ...}


# ──────────────────────────────────────────────
#  Карточка заметки
# ──────────────────────────────────────────────

class NoteCard(QFrame):
    def __init__(self, note_id, title, category, cipher, color, created,
                 on_click, on_edit, on_delete):
        super().__init__()
        self.note_id  = note_id
        self._on_click  = on_click
        self._on_edit   = on_edit
        self._on_delete = on_delete

        self.setFixedSize(210, 150)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        bg = color or "#FFFACD"
        c  = QColor(bg)
        c.setHsv(c.hsvHue(), min(c.hsvSaturation() + 40, 255), max(c.value() - 50, 0))
        border = c.name()

        self._base_style = f"""
            NoteCard {{
                background: {bg};
                border: 1.5px solid {border};
                border-radius: 10px;
            }}
        """
        self._hover_style = f"""
            NoteCard {{
                background: {bg};
                border: 2px solid #4a90d9;
                border-radius: 10px;
            }}
        """
        self.setStyleSheet(self._base_style)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 8)
        layout.setSpacing(3)

        # Цветная полоска сверху
        stripe = QFrame()
        stripe.setFixedHeight(4)
        stripe.setStyleSheet(f"background:{border}; border-radius:2px;")
        layout.addWidget(stripe)

        # Заголовок
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(
            "font-weight: bold; font-size: 12px; color: #1a1a2e; background: transparent;"
        )
        title_lbl.setWordWrap(True)
        title_lbl.setMaximumHeight(38)
        layout.addWidget(title_lbl)

        # Категория
        cat_lbl = QLabel(f"  {category or '—'}")
        cat_lbl.setStyleSheet("font-size: 10px; color: #555; background: transparent;")
        layout.addWidget(cat_lbl)

        # Шифр — читаемое название
        cipher_readable = CIPHER_LABELS.get(cipher, cipher)
        lock = "🔓" if cipher == "none" else "🔒"
        cipher_lbl = QLabel(f"  {lock} {cipher_readable}")
        cipher_lbl.setStyleSheet("font-size: 10px; color: #777; background: transparent;")
        layout.addWidget(cipher_lbl)

        layout.addStretch()

        # Нижняя строка: дата + кнопки
        bottom = QHBoxLayout()
        bottom.setSpacing(4)

        date_lbl = QLabel(created[:10] if created else "")
        date_lbl.setStyleSheet("font-size: 9px; color: #999; background: transparent;")
        bottom.addWidget(date_lbl)
        bottom.addStretch()

        for icon_text, tip, slot, hover_color in [
            ("✎", "Редактировать", lambda _, nid=note_id: self._on_edit(nid),   "#4a90d9"),
            ("✕", "Удалить",       lambda _, nid=note_id, t=title: self._on_delete(nid, t), "#e74c3c"),
        ]:
            btn = QPushButton(icon_text)
            btn.setFixedSize(24, 24)
            btn.setToolTip(tip)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(0,0,0,0.07);
                    border: none; border-radius: 5px;
                    font-size: 12px; color: #555;
                }}
                QPushButton:hover {{
                    background: {hover_color}; color: white;
                }}
            """)
            btn.clicked.connect(slot)
            bottom.addWidget(btn)

        layout.addLayout(bottom)

    def enterEvent(self, e):
        self.setStyleSheet(self._hover_style)

    def leaveEvent(self, e):
        self.setStyleSheet(self._base_style)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._on_click(self.note_id)


# ──────────────────────────────────────────────
#  Главное окно
# ──────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self, user_id: int, username: str):
        super().__init__()
        self.user_id  = user_id
        self.username = username
        self._cards: list[NoteCard] = []

        self.setWindowTitle(f"CryptoNotes — {username}")
        self.setMinimumSize(880, 580)

        # Общий стиль приложения
        self.setStyleSheet("""
            QMainWindow { background: #f0f2f5; }
            QToolBar {
                background: #1a1a2e;
                spacing: 4px;
                padding: 4px 8px;
                border: none;
            }
            QToolBar QToolButton {
                color: #ccc;
                background: transparent;
                border: none;
                border-radius: 6px;
                padding: 5px 12px;
                font-size: 13px;
            }
            QToolBar QToolButton:hover {
                background: rgba(255,255,255,0.12);
                color: white;
            }
            QToolBar::separator {
                background: rgba(255,255,255,0.15);
                width: 1px;
                margin: 4px 2px;
            }
            QStatusBar {
                background: #1a1a2e;
                color: #aaa;
                font-size: 11px;
            }
            QLineEdit {
                border: 1px solid #d0d5dd;
                border-radius: 8px;
                padding: 7px 12px;
                background: white;
                font-size: 13px;
            }
            QLineEdit:focus { border: 1.5px solid #4a90d9; }
            QComboBox {
                border: 1px solid #d0d5dd;
                border-radius: 8px;
                padding: 6px 10px;
                background: white;
                font-size: 13px;
            }
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical {
                background: #f0f2f5; width: 8px; border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #c0c8d8; border-radius: 4px; min-height: 30px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)

        self._build_toolbar()
        self._build_central()
        self._build_statusbar()
        self._refresh_grid()

    # ──────────────── Тулбар ────────────────

    def _build_toolbar(self):
        tb = QToolBar()
        tb.setMovable(False)
        tb.setIconSize(QSize(16, 16))
        self.addToolBar(tb)

        # Логотип / название
        logo = QLabel("  CryptoNotes")
        logo.setStyleSheet(
            "color: white; font-size: 15px; font-weight: bold; padding-right: 16px;"
        )
        tb.addWidget(logo)
        tb.addSeparator()

        for label, slot, tip in [
            ("+ Новая заметка",   self._on_add,           "Создать новую заметку (Ctrl+N)"),
            ("Демо шифров",       self._open_cipher_demo, "Посмотреть как работают алгоритмы"),
            ("Экспорт в .txt",    self._export_to_txt,    "Сохранить все заметки в текстовый файл"),
            ("Стикеры",           self._open_stickers,    "Показать заметки как стикеры на рабочем столе"),
        ]:
            act = QAction(label, self)
            act.setToolTip(tip)
            act.triggered.connect(slot)
            tb.addAction(act)

        # Имя пользователя справа
        spacer = QWidget(); spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        tb.addWidget(spacer)
        user_lbl = QLabel(f"  {self.username}  ")
        user_lbl.setStyleSheet(
            "color: #aaa; font-size: 12px; padding: 4px 8px; "
            "background: rgba(255,255,255,0.08); border-radius: 6px;"
        )
        tb.addWidget(user_lbl)

    # ──────────────── Центральная часть ────────────────

    def _build_central(self):
        central = QWidget()
        central.setStyleSheet("background: #f0f2f5;")
        self.setCentralWidget(central)
        vbox = QVBoxLayout(central)
        vbox.setContentsMargins(16, 12, 16, 12)
        vbox.setSpacing(10)

        # Панель фильтров — строго фиксированная высота
        filter_panel = QFrame()
        filter_panel.setFixedHeight(46)
        filter_panel.setStyleSheet(
            "background: white; border-radius: 10px; border: 1px solid #e8eaf0;"
        )
        fp_layout = QHBoxLayout(filter_panel)
        fp_layout.setContentsMargins(12, 0, 12, 0)
        fp_layout.setSpacing(10)

        search_icon = QLabel("🔍")
        search_icon.setStyleSheet("background: transparent;")
        fp_layout.addWidget(search_icon)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Поиск по заголовку...")
        self.search_edit.setStyleSheet(
            "border: none; background: transparent; font-size: 13px;"
        )
        self.search_edit.textChanged.connect(self._refresh_grid)
        fp_layout.addWidget(self.search_edit, stretch=1)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFixedHeight(24)
        sep.setStyleSheet("background: #e8eaf0; margin: 0 4px;")
        fp_layout.addWidget(sep)

        cat_lbl = QLabel("Категория:")
        cat_lbl.setStyleSheet("background: transparent; color: #666; font-size: 12px;")
        fp_layout.addWidget(cat_lbl)

        self.cat_combo = QComboBox()
        self.cat_combo.setMinimumWidth(150)
        self.cat_combo.setStyleSheet("border: none; background: transparent;")
        self.cat_combo.currentIndexChanged.connect(self._refresh_grid)
        fp_layout.addWidget(self.cat_combo)

        vbox.addWidget(filter_panel)

        # Счётчик заметок — фиксированная высота
        self.count_lbl = QLabel("")
        self.count_lbl.setFixedHeight(18)
        self.count_lbl.setStyleSheet("color: #888; font-size: 11px; margin-left: 4px;")
        vbox.addWidget(self.count_lbl)

        # Прокручиваемая область — ВСЕГДА видима, растягивается на всё оставшееся место
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        vbox.addWidget(self.scroll, stretch=1)

        # Контейнер внутри scroll: сетка карточек + метка «пусто»
        self.scroll_container = QWidget()
        self.scroll_container.setStyleSheet("background: transparent;")
        sc_layout = QVBoxLayout(self.scroll_container)
        sc_layout.setContentsMargins(0, 0, 0, 0)
        sc_layout.setSpacing(0)

        self.grid_widget = QWidget()
        self.grid_widget.setStyleSheet("background: transparent;")
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(14)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        sc_layout.addWidget(self.grid_widget)

        # Пустое состояние — внутри scroll, изначально скрыто
        self.empty_lbl = QLabel("Заметок пока нет.\nНажмите «+ Новая заметка» чтобы начать.")
        self.empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_lbl.setStyleSheet("color: #bbb; font-size: 15px; padding: 80px 0;")
        self.empty_lbl.hide()
        sc_layout.addWidget(self.empty_lbl)

        sc_layout.addStretch(1)
        self.scroll.setWidget(self.scroll_container)

    def _build_statusbar(self):
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage(f"Добро пожаловать, {self.username}!")

    # ──────────────── Сетка ────────────────

    def _refresh_grid(self):
        """Полная перезагрузка: запрос к БД + пересборка карточек."""
        # Удаляем старые карточки из layout и памяти
        for card in self._cards:
            self.grid_layout.removeWidget(card)
            card.hide()
            card.deleteLater()
        self._cards.clear()

        # Очищаем все ячейки grid
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        search = self.search_edit.text().strip()
        cat_id = self.cat_combo.currentData() if self.cat_combo.count() else -1

        # Строим запрос с параметрами — защита от SQL-инъекций через prepare/bindValue
        conditions = ["n.user_id = :user_id"]
        if search:
            conditions.append("n.title LIKE :search")
        if cat_id and cat_id != -1:
            conditions.append("n.category_id = :cat_id")

        sql = f"""
            SELECT n.id, n.title, COALESCE(c.title,'—'), n.cipher, n.color, n.created_at
            FROM notes n
            LEFT JOIN categories c ON c.id = n.category_id
            WHERE {' AND '.join(conditions)}
            ORDER BY n.created_at DESC
        """

        q = QSqlQuery()
        q.prepare(sql)
        q.bindValue(":user_id", self.user_id)
        if search:
            q.bindValue(":search", f"%{search}%")
        if cat_id and cat_id != -1:
            q.bindValue(":cat_id", cat_id)
        q.exec()

        notes = []
        while q.next():
            notes.append(tuple(q.value(i) for i in range(6)))

        # Пустое состояние — scroll всегда видим
        self.grid_widget.setVisible(bool(notes))
        self.empty_lbl.setVisible(not bool(notes))

        cols = max(1, (self.scroll.width() - 30) // 224)
        for i, (nid, title, cat, cipher, color, created) in enumerate(notes):
            card = NoteCard(
                note_id=nid, title=title, category=cat,
                cipher=cipher, color=color or "#FFFACD", created=created,
                on_click=self._on_view,
                on_edit=self._on_edit,
                on_delete=self._on_delete,
            )
            self.grid_layout.addWidget(card, i // cols, i % cols)
            self._cards.append(card)

        if notes:
            self.grid_layout.setRowStretch(len(notes) // cols + 1, 1)

        self._fill_categories()
        n = len(notes)
        self.count_lbl.setText(
            f"{n} {'заметка' if n==1 else 'заметки' if 2<=n<=4 else 'заметок'}"
        )
        self.status.showMessage(f"Заметок: {n}  |  {self.username}")

    def _relayout_cards(self):
        """Только перераскладывает существующие карточки по колонкам — без запроса к БД."""
        if not self._cards:
            return
        cols = max(1, (self.scroll.width() - 30) // 224)
        for i, card in enumerate(self._cards):
            self.grid_layout.addWidget(card, i // cols, i % cols)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Пересчитываем только количество колонок, не перестраиваем всё
        self._relayout_cards()

    def _fill_categories(self):
        cur = self.cat_combo.currentData()
        self.cat_combo.blockSignals(True)
        self.cat_combo.clear()
        self.cat_combo.addItem("Все категории", -1)
        q = QSqlQuery("SELECT id, title FROM categories ORDER BY title")
        while q.next():
            self.cat_combo.addItem(q.value(1), q.value(0))
        for i in range(self.cat_combo.count()):
            if self.cat_combo.itemData(i) == cur:
                self.cat_combo.setCurrentIndex(i); break
        self.cat_combo.blockSignals(False)

    # ──────────────── CRUD ────────────────

    def _on_view(self, note_id):
        dlg = ViewNoteDialog(note_id, parent=self)
        dlg.exec()
        self._refresh_grid()

    def _on_add(self):
        dlg = NoteDialog(self.user_id, parent=self)
        if dlg.exec(): self._refresh_grid()

    def _on_edit(self, note_id):
        dlg = NoteDialog(self.user_id, note_id=note_id, parent=self)
        if dlg.exec(): self._refresh_grid()

    def _on_delete(self, note_id, title):
        reply = QMessageBox.question(
            self, "Удаление", f"Удалить заметку «{title}»?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            q = QSqlQuery()
            q.prepare("DELETE FROM notes WHERE id = ?")
            q.addBindValue(note_id); q.exec()
            self._refresh_grid()
            self.status.showMessage(f"Заметка «{title}» удалена.")

    # ──────────────── Прочее ────────────────

    def _export_to_txt(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить заметки", f"{self.username}_notes.txt", "Текстовые файлы (*.txt)"
        )
        if not path: return
        q = QSqlQuery()
        q.prepare("""
            SELECT n.title, n.content, n.cipher, c.title, n.created_at
            FROM notes n LEFT JOIN categories c ON c.id = n.category_id
            WHERE n.user_id = ? ORDER BY n.created_at DESC
        """)
        q.addBindValue(self.user_id); q.exec()
        lines = [f"Заметки: {self.username}\n{'='*40}\n"]
        while q.next():
            t, c, ci, cat, cr = (q.value(i) for i in range(5))
            lines.append(f"[{cr}] {t}\nКатегория: {cat or '—'}  Шифр: {ci}\n{c}\n{'-'*40}\n")
        try:
            with open(path, "w", encoding="utf-8") as f: f.write("\n".join(lines))
            QMessageBox.information(self, "Готово", f"Экспорт завершён:\n{path}")
        except OSError as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def _open_cipher_demo(self):
        self.cipher_win = CipherDemoWindow(parent=None)
        self.cipher_win.show()

    def _open_stickers(self):
        from ui.sticker_board import StickerBoard
        self.sticker_board = StickerBoard(self.user_id, parent=None)
        self.sticker_board.show()
