"""
Окно-демонстратор алгоритмов шифрования.
Позволяет ввести текст и увидеть результат каждого алгоритма в реальном времени.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QPushButton, QComboBox, QLineEdit,
    QGroupBox, QSplitter
)
from PyQt6.QtCore import Qt

from core.cipher import encrypt, decrypt, cipher_names, CIPHERS


class CipherDemoWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔬 Демонстрация шифрования")
        self.setMinimumSize(700, 500)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # Заголовок
        lbl = QLabel("Введите текст — и посмотрите, как работают алгоритмы шифрования")
        lbl.setWordWrap(True)
        lbl.setStyleSheet("font-size: 13px; margin-bottom: 6px;")
        layout.addWidget(lbl)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        # Левая панель — ввод
        left = QGroupBox("Исходный текст")
        left_l = QVBoxLayout(left)

        self.input_edit = QTextEdit()
        self.input_edit.setPlaceholderText("Введите любой текст...")
        self.input_edit.textChanged.connect(self._on_text_changed)
        left_l.addWidget(self.input_edit)

        row = QHBoxLayout()
        row.addWidget(QLabel("XOR-ключ:"))
        self.key_edit = QLineEdit("secret")
        self.key_edit.textChanged.connect(self._on_text_changed)
        row.addWidget(self.key_edit)
        left_l.addLayout(row)

        splitter.addWidget(left)

        # Правая панель — результаты
        right = QGroupBox("Зашифрованный / расшифрованный текст")
        right_l = QVBoxLayout(right)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Алгоритм:"))
        self.cipher_combo = QComboBox()
        for cid, cname in cipher_names().items():
            self.cipher_combo.addItem(cname, cid)
        self.cipher_combo.currentIndexChanged.connect(self._on_text_changed)
        row2.addWidget(self.cipher_combo)
        row2.addStretch()
        right_l.addLayout(row2)

        right_l.addWidget(QLabel("Зашифровано:"))
        self.encrypted_edit = QTextEdit()
        self.encrypted_edit.setReadOnly(True)
        self.encrypted_edit.setStyleSheet("background:#f5f5f5;")
        right_l.addWidget(self.encrypted_edit)

        right_l.addWidget(QLabel("Расшифровано обратно:"))
        self.decrypted_edit = QTextEdit()
        self.decrypted_edit.setReadOnly(True)
        self.decrypted_edit.setStyleSheet("background:#f0fff0;")
        right_l.addWidget(self.decrypted_edit)

        splitter.addWidget(right)

        # Кнопка «Показать все»
        btn = QPushButton("Показать все алгоритмы сразу")
        btn.clicked.connect(self._show_all)
        layout.addWidget(btn)

        self.all_label = QLabel("")
        self.all_label.setWordWrap(True)
        self.all_label.setStyleSheet("font-family: monospace; font-size: 11px;")
        layout.addWidget(self.all_label)

    def _on_text_changed(self):
        text = self.input_edit.toPlainText()
        cipher_id = self.cipher_combo.currentData()
        key = self.key_edit.text() or "secret"

        if not text:
            self.encrypted_edit.clear()
            self.decrypted_edit.clear()
            return

        try:
            enc = encrypt(text, cipher_id, key)
            dec = decrypt(enc, cipher_id, key)
            self.encrypted_edit.setPlainText(enc)
            self.decrypted_edit.setPlainText(dec)
        except Exception as e:
            self.encrypted_edit.setPlainText(f"Ошибка: {e}")
            self.decrypted_edit.clear()

    def _show_all(self):
        text = self.input_edit.toPlainText()
        key = self.key_edit.text() or "secret"
        if not text:
            self.all_label.setText("Введите текст слева, чтобы увидеть результаты.")
            return

        lines = []
        for cid, (cname, enc_fn, _) in CIPHERS.items():
            try:
                result = enc_fn(text, key)
            except Exception as e:
                result = f"[ошибка: {e}]"
            lines.append(f"<b>{cname}:</b> {result}")

        self.all_label.setText("<br>".join(lines))
