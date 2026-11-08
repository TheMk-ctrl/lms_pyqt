"""
Окно входа / регистрации.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QTabWidget, QFrame
)
from PyQt6.QtCore import Qt

from core.database import init_db
from core.auth import login_user, register_user


STYLE = """
QWidget {
    background: #f0f2f5;
    font-family: "Segoe UI", Arial, sans-serif;
}
QTabWidget::pane {
    border: none;
    background: white;
    border-radius: 0 0 12px 12px;
}
QTabBar::tab {
    background: #e8eaf0;
    color: #666;
    padding: 9px 28px;
    font-size: 13px;
    border: none;
}
QTabBar::tab:selected {
    background: white;
    color: #1a1a2e;
    font-weight: bold;
}
QLineEdit {
    border: 1.5px solid #d8dce8;
    border-radius: 8px;
    padding: 9px 12px;
    font-size: 13px;
    background: #fafbfc;
    color: #222;
}
QLineEdit:focus {
    border: 1.5px solid #4a90d9;
    background: white;
}
QPushButton {
    border-radius: 8px;
    padding: 9px;
    font-size: 13px;
    font-weight: bold;
    border: none;
}
"""


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CryptoNotes")
        self.setFixedSize(380, 420)
        self.setStyleSheet(STYLE)

        if not init_db():
            QMessageBox.critical(self, "Ошибка", "Не удалось подключиться к базе данных.")

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Шапка
        header = QFrame()
        header.setFixedHeight(110)
        header.setStyleSheet("background: #1a1a2e; border-radius: 0;")
        h_layout = QVBoxLayout(header)
        h_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("CryptoNotes")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: white; font-size: 26px; font-weight: bold; letter-spacing: 1px;")
        h_layout.addWidget(title)

        sub = QLabel("Защищённые заметки")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet("color: #7a8aaa; font-size: 12px;")
        h_layout.addWidget(sub)

        layout.addWidget(header)

        # Вкладки
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("QTabWidget { background: white; }")
        layout.addWidget(self.tabs)

        self.tabs.addTab(self._build_login_tab(), "Вход")
        self.tabs.addTab(self._build_register_tab(), "Регистрация")

    def _build_login_tab(self):
        w = QWidget()
        w.setStyleSheet("background: white;")
        vbox = QVBoxLayout(w)
        vbox.setContentsMargins(28, 20, 28, 24)
        vbox.setSpacing(10)

        vbox.addWidget(QLabel("Имя пользователя"))
        self.login_name = QLineEdit()
        self.login_name.setPlaceholderText("Введите имя...")
        vbox.addWidget(self.login_name)

        vbox.addWidget(QLabel("Пароль"))
        self.login_pass = QLineEdit()
        self.login_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.login_pass.setPlaceholderText("Введите пароль...")
        self.login_pass.returnPressed.connect(self._on_login)
        vbox.addWidget(self.login_pass)

        vbox.addSpacing(6)
        btn = QPushButton("Войти")
        btn.setStyleSheet("background: #4a90d9; color: white;")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(self._on_login)
        vbox.addWidget(btn)
        vbox.addStretch()
        return w

    def _build_register_tab(self):
        w = QWidget()
        w.setStyleSheet("background: white;")
        vbox = QVBoxLayout(w)
        vbox.setContentsMargins(28, 20, 28, 24)
        vbox.setSpacing(8)

        vbox.addWidget(QLabel("Имя пользователя"))
        self.reg_name = QLineEdit()
        self.reg_name.setPlaceholderText("Придумайте имя...")
        vbox.addWidget(self.reg_name)

        vbox.addWidget(QLabel("Пароль"))
        self.reg_pass = QLineEdit()
        self.reg_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.reg_pass.setPlaceholderText("Придумайте пароль...")
        vbox.addWidget(self.reg_pass)

        vbox.addWidget(QLabel("Повторите пароль"))
        self.reg_pass2 = QLineEdit()
        self.reg_pass2.setEchoMode(QLineEdit.EchoMode.Password)
        self.reg_pass2.setPlaceholderText("Повторите пароль...")
        self.reg_pass2.returnPressed.connect(self._on_register)
        vbox.addWidget(self.reg_pass2)

        vbox.addSpacing(4)
        btn = QPushButton("Зарегистрироваться")
        btn.setStyleSheet("background: #27ae60; color: white;")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(self._on_register)
        vbox.addWidget(btn)
        vbox.addStretch()
        return w

    def _on_login(self):
        name = self.login_name.text().strip()
        password = self.login_pass.text()
        if not name or not password:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля.")
            return
        ok, user_id = login_user(name, password)
        if ok:
            self._open_main(user_id, name)
        else:
            QMessageBox.critical(self, "Ошибка", "Неверное имя или пароль.")

    def _on_register(self):
        name = self.reg_name.text().strip()
        password = self.reg_pass.text()
        password2 = self.reg_pass2.text()
        if not name or not password:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля.")
            return
        if password != password2:
            QMessageBox.warning(self, "Ошибка", "Пароли не совпадают.")
            return
        ok, msg = register_user(name, password)
        if ok:
            QMessageBox.information(self, "Успех", msg + "\nТеперь войдите.")
            self.tabs.setCurrentIndex(0)
            self.login_name.setText(name)
        else:
            QMessageBox.critical(self, "Ошибка", msg)

    def _open_main(self, user_id, username):
        from ui.main_window import MainWindow
        self.main_win = MainWindow(user_id, username)
        self.main_win.show()
        self.close()
