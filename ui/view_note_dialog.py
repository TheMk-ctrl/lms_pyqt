"""
Диалог просмотра заметки (только чтение, с расшифровкой).
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QPushButton, QLineEdit, QFrame
)
from PyQt6.QtSql import QSqlQuery
from core.cipher import decrypt, cipher_names


class ViewNoteDialog(QDialog):
    def __init__(self, note_id: int, parent=None):
        super().__init__(parent)
        self.note_id = note_id
        self.setWindowTitle("Просмотр заметки")
        self.setMinimumWidth(500)
        self.setMinimumHeight(380)

        self._note_data = {}
        self._load_note()
        self._build_ui()

    def _load_note(self):
        query = QSqlQuery()
        query.prepare("""
            SELECT n.title, n.content, n.cipher, c.title, n.created_at
            FROM notes n
            LEFT JOIN categories c ON c.id = n.category_id
            WHERE n.id = ?
        """)
        query.addBindValue(self.note_id)
        query.exec()
        if query.next():
            self._note_data = {
                "title":    query.value(0),
                "content":  query.value(1),
                "cipher":   query.value(2),
                "category": query.value(3) or "—",
                "created":  query.value(4),
            }

    def _build_ui(self):
        layout = QVBoxLayout(self)

        title_lbl = QLabel(self._note_data.get("title", ""))
        title_lbl.setStyleSheet("font-size: 16px; font-weight: bold;")
        title_lbl.setWordWrap(True)
        layout.addWidget(title_lbl)

        cipher_id = self._note_data.get("cipher", "none")
        cipher_label = cipher_names().get(cipher_id, cipher_id)
        meta = QLabel(
            f"Категория: {self._note_data.get('category')}   |   "
            f"Шифр: {cipher_label}   |   "
            f"Создано: {self._note_data.get('created')}"
        )
        meta.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(meta)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #ddd;")
        layout.addWidget(line)

        # Поле ключа — показываем для XOR
        self.key_edit = None
        if cipher_id == "xor":
            key_row = QHBoxLayout()
            key_row.addWidget(QLabel("XOR-ключ:"))
            self.key_edit = QLineEdit("secret")
            key_row.addWidget(self.key_edit)
            btn_dec = QPushButton("Расшифровать")
            btn_dec.clicked.connect(self._do_decrypt)
            key_row.addWidget(btn_dec)
            layout.addLayout(key_row)

        self.content_view = QTextEdit()
        self.content_view.setReadOnly(True)
        self.content_view.setStyleSheet("background: #fafafa; font-size: 13px;")
        layout.addWidget(self.content_view)

        # Расшифровываем сразу при открытии
        self._do_decrypt()

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        edit_btn = QPushButton("Редактировать")
        edit_btn.clicked.connect(self._open_edit)
        btn_row.addWidget(edit_btn)

        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    def _do_decrypt(self):
        content = self._note_data.get("content", "")
        cipher_id = self._note_data.get("cipher", "none")
        key = self.key_edit.text() if self.key_edit else "secret"
        try:
            plain = decrypt(content, cipher_id, key)
            self.content_view.setPlainText(plain)
        except Exception as e:
            self.content_view.setPlainText(
                f"[Не удалось расшифровать: {e}]\n\nЗашифрованный текст:\n{content}"
            )

    def _open_edit(self):
        from ui.note_dialog import NoteDialog
        # Получаем user_id из БД по note_id
        query = QSqlQuery()
        query.prepare("SELECT user_id FROM notes WHERE id = ?")
        query.addBindValue(self.note_id)
        query.exec()
        if query.next():
            user_id = query.value(0)
            from ui.note_dialog import NoteDialog
            dlg = NoteDialog(user_id, note_id=self.note_id, parent=self)
            if dlg.exec():
                # Перезагружаем данные и обновляем просмотр
                self._load_note()
                self._do_decrypt()
                # Обновляем заголовок
                title_lbl = self.findChild(QLabel)
                if title_lbl:
                    title_lbl.setText(self._note_data.get("title", ""))
