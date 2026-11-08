"""
Диалог создания / редактирования заметки.
При редактировании — загружает расшифрованный текст, при сохранении — шифрует.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QTextEdit, QComboBox, QPushButton,
    QMessageBox, QColorDialog, QFrame, QSizePolicy
)
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtCore import Qt
from PyQt6.QtSql import QSqlQuery

from core.cipher import encrypt, decrypt, cipher_names


class NoteDialog(QDialog):
    def __init__(self, user_id: int, note_id: int | None = None, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.note_id = note_id
        self.is_edit = note_id is not None
        self.selected_color = "#FFFACD"

        self.setWindowTitle("Редактировать заметку" if self.is_edit else "Новая заметка")
        self.setMinimumWidth(520)
        self.setMinimumHeight(480)
        self.setStyleSheet("""
            QDialog { background: #f7f8fa; }
            QLabel  { color: #444; font-size: 12px; }
            QLineEdit, QTextEdit, QComboBox {
                border: 1px solid #d0d5dd;
                border-radius: 6px;
                padding: 6px 8px;
                background: white;
                font-size: 13px;
                color: #222;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
                border: 1.5px solid #4a90d9;
            }
            QPushButton {
                border-radius: 6px;
                padding: 7px 18px;
                font-size: 13px;
            }
        """)

        self._build_ui()
        if self.is_edit:
            self._load_note()

    # ──────────────── UI ────────────────

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 18, 20, 16)

        # Заголовок диалога
        header = QLabel("Редактировать заметку" if self.is_edit else "Новая заметка")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #1a1a2e; margin-bottom: 4px;")
        layout.addWidget(header)

        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #e0e0e0;"); layout.addWidget(sep)

        # Заголовок заметки
        layout.addWidget(QLabel("Заголовок"))
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Краткое название заметки...")
        layout.addWidget(self.title_edit)

        # Категория + Шифрование в одну строку
        row2 = QHBoxLayout()
        row2.setSpacing(12)

        cat_col = QVBoxLayout()
        cat_col.addWidget(QLabel("Категория"))
        self.cat_combo = QComboBox()
        self._fill_categories()
        cat_col.addWidget(self.cat_combo)
        row2.addLayout(cat_col)

        cipher_col = QVBoxLayout()
        cipher_col.addWidget(QLabel("Шифрование"))
        self.cipher_combo = QComboBox()
        for cid, cname in cipher_names().items():
            self.cipher_combo.addItem(cname, cid)
        self.cipher_combo.currentIndexChanged.connect(self._on_cipher_changed)
        cipher_col.addWidget(self.cipher_combo)
        row2.addLayout(cipher_col)

        key_col = QVBoxLayout()
        self.key_label = QLabel("Ключ XOR")
        key_col.addWidget(self.key_label)
        self.key_edit = QLineEdit("secret")
        self.key_edit.setMaximumWidth(110)
        key_col.addWidget(self.key_edit)
        row2.addLayout(key_col)

        layout.addLayout(row2)
        self._on_cipher_changed()  # скрыть/показать поле ключа

        # Текст заметки
        layout.addWidget(QLabel("Текст заметки"))
        self.content_edit = QTextEdit()
        self.content_edit.setPlaceholderText("Введите текст...")
        self.content_edit.setMinimumHeight(140)
        layout.addWidget(self.content_edit)

        # Цвет
        color_lbl = QLabel("Цвет карточки")
        layout.addWidget(color_lbl)

        color_row = QHBoxLayout()
        color_row.setSpacing(6)
        self._preset_colors = [
            ("#FFFACD", "Жёлтый"),   ("#FFD1DC", "Розовый"),
            ("#B5EAD7", "Зелёный"),  ("#C7CEEA", "Голубой"),
            ("#FFDAC1", "Оранжевый"),("#E2F0CB", "Лайм"),
            ("#D4E6F1", "Синий"),    ("#F9EBEA", "Красный"),
            ("#F8F8F8", "Белый"),
        ]
        for hex_color, tip in self._preset_colors:
            btn = QPushButton()
            btn.setFixedSize(28, 28)
            btn.setToolTip(tip)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(
                f"background:{hex_color}; border:2px solid #bbb; border-radius:14px; padding:0;"
            )
            btn.clicked.connect(lambda _, c=hex_color: self._pick_preset(c))
            color_row.addWidget(btn)

        custom_btn = QPushButton("+")
        custom_btn.setFixedSize(28, 28)
        custom_btn.setToolTip("Свой цвет")
        custom_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        custom_btn.setStyleSheet(
            "background: white; border: 2px dashed #aaa; border-radius: 14px; "
            "font-size: 16px; color: #888; padding: 0;"
        )
        custom_btn.clicked.connect(self._pick_custom_color)
        color_row.addWidget(custom_btn)

        color_row.addSpacing(8)
        self.color_preview = QLabel()
        self.color_preview.setFixedSize(60, 28)
        self.color_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.color_preview.setStyleSheet(
            f"background:{self.selected_color}; border:2px solid #888; border-radius:6px;"
        )
        self.color_preview.setText("Цвет")
        color_row.addWidget(self.color_preview)
        color_row.addStretch()
        layout.addLayout(color_row)

        # Кнопки
        sep2 = QFrame(); sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet("color: #e0e0e0;"); layout.addWidget(sep2)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = QPushButton("Отмена")
        cancel_btn.setStyleSheet(
            "background: #f0f0f0; color: #555; border: 1px solid #ccc;"
        )
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        self.save_btn = QPushButton("Сохранить")
        self.save_btn.setStyleSheet(
            "background: #4a90d9; color: white; border: none; font-weight: bold;"
        )
        self.save_btn.setDefault(True)
        self.save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(self.save_btn)

        layout.addLayout(btn_row)

    def _on_cipher_changed(self):
        is_xor = self.cipher_combo.currentData() == "xor"
        self.key_label.setVisible(is_xor)
        self.key_edit.setVisible(is_xor)

    def _pick_preset(self, color: str):
        self.selected_color = color
        self.color_preview.setStyleSheet(
            f"background:{color}; border:2px solid #888; border-radius:6px;"
        )

    def _pick_custom_color(self):
        c = QColorDialog.getColor(QColor(self.selected_color), self, "Выберите цвет")
        if c.isValid():
            self._pick_preset(c.name())

    def _fill_categories(self):
        self.cat_combo.clear()
        self.cat_combo.addItem("— нет —", None)
        q = QSqlQuery("SELECT id, title FROM categories ORDER BY title")
        while q.next():
            self.cat_combo.addItem(q.value(1), q.value(0))

    # ──────────────── Загрузка ────────────────

    def _load_note(self):
        """Загружает заметку и РАСШИФРОВЫВАЕТ текст для редактирования."""
        q = QSqlQuery()
        q.prepare("SELECT title, content, cipher, category_id, color FROM notes WHERE id = ?")
        q.addBindValue(self.note_id)
        q.exec()
        if not q.next():
            return

        title, content, cipher, cat_id, color = (q.value(i) for i in range(5))

        self.title_edit.setText(title)

        # Выставляем шифр ДО расшифровки
        idx = self.cipher_combo.findData(cipher)
        if idx >= 0:
            self.cipher_combo.setCurrentIndex(idx)

        # Расшифровываем текст — пользователь редактирует plaintext
        try:
            plain = decrypt(content, cipher, self.key_edit.text())
        except Exception:
            plain = content  # если не получилось — показываем как есть
        self.content_edit.setPlainText(plain)

        # Категория
        for i in range(self.cat_combo.count()):
            if self.cat_combo.itemData(i) == cat_id:
                self.cat_combo.setCurrentIndex(i)
                break

        if color:
            self._pick_preset(color)

    # ──────────────── Сохранение ────────────────

    def _on_save(self):
        title   = self.title_edit.text().strip()
        content = self.content_edit.toPlainText().strip()

        if not title:
            QMessageBox.warning(self, "Ошибка", "Введите заголовок заметки.")
            return
        if not content:
            QMessageBox.warning(self, "Ошибка", "Текст заметки не может быть пустым.")
            return

        cipher_id = self.cipher_combo.currentData()
        key       = self.key_edit.text()
        cat_id    = self.cat_combo.currentData()

        # content сейчас всегда plaintext — шифруем один раз
        try:
            saved_content = encrypt(content, cipher_id, key)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка шифрования", str(e))
            return

        q = QSqlQuery()
        if self.is_edit:
            q.prepare("""
                UPDATE notes
                SET title=?, content=?, cipher=?, category_id=?, color=?
                WHERE id=?
            """)
            for v in (title, saved_content, cipher_id, cat_id, self.selected_color, self.note_id):
                q.addBindValue(v)
        else:
            q.prepare("""
                INSERT INTO notes (user_id, category_id, title, content, cipher, color)
                VALUES (?,?,?,?,?,?)
            """)
            for v in (self.user_id, cat_id, title, saved_content, cipher_id, self.selected_color):
                q.addBindValue(v)

        if q.exec():
            self.accept()
        else:
            QMessageBox.critical(self, "Ошибка БД", q.lastError().text())
