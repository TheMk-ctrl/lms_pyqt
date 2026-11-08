"""
Менеджер зашифрованных заметок
Автор: студент
Технологии: PyQt6, SQLite (QSqlTableModel), шифрование (Цезарь, XOR, Base64)
"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from ui.login_window import LoginWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("CryptoNotes")
    app.setStyle("Fusion")

    window = LoginWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
