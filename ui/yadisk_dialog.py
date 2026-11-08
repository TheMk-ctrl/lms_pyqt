"""
Диалог синхронизации с Яндекс.Диском.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTextEdit, QGroupBox,
    QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtCore import QUrl

from core.yadisk_sync import upload_db, download_db, check_token


# ──────────────── Фоновый поток для запросов ────────────────

class SyncWorker(QThread):
    """Выполняет загрузку/скачивание в отдельном потоке, чтобы не замораживать UI."""
    finished = pyqtSignal(bool, str)  # (успех, сообщение)

    def __init__(self, action: str, token: str):
        super().__init__()
        self.action = action  # "upload" или "download"
        self.token = token

    def run(self):
        if self.action == "upload":
            ok, msg = upload_db(self.token)
        elif self.action == "download":
            ok, msg = download_db(self.token)
        elif self.action == "check":
            ok, msg = check_token(self.token)
        else:
            ok, msg = False, "Неизвестное действие"
        self.finished.emit(ok, msg)


# ──────────────── Диалог ────────────────

class YaDiskDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Синхронизация с Яндекс.Диском")
        self.setMinimumWidth(520)
        self.worker = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # Инструкция
        info = QLabel(
            "Для синхронизации нужен OAuth-токен Яндекс.Диска.\n"
            "Нажмите кнопку ниже, чтобы получить его на сайте Яндекса."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #555;")
        layout.addWidget(info)

        # Кнопка получить токен
        link_btn = QPushButton("Открыть страницу получения токена")
        link_btn.setStyleSheet("color: #c0392b; text-decoration: underline;")
        link_btn.setFlat(True)
        link_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        link_btn.clicked.connect(self._open_token_page)
        layout.addWidget(link_btn)

        # Поле токена
        token_group = QGroupBox("OAuth-токен")
        token_layout = QHBoxLayout(token_group)

        self.token_edit = QLineEdit()
        self.token_edit.setPlaceholderText("Вставьте токен сюда...")
        self.token_edit.setEchoMode(QLineEdit.EchoMode.Password)
        token_layout.addWidget(self.token_edit)

        show_btn = QPushButton("Показать")
        show_btn.setCheckable(True)
        show_btn.toggled.connect(self._toggle_echo)
        show_btn.setMaximumWidth(80)
        token_layout.addWidget(show_btn)

        check_btn = QPushButton("Проверить")
        check_btn.setMaximumWidth(80)
        check_btn.clicked.connect(self._on_check)
        token_layout.addWidget(check_btn)

        layout.addWidget(token_group)

        # Кнопки синхронизации
        sync_group = QGroupBox("Действия")
        sync_layout = QHBoxLayout(sync_group)

        self.upload_btn = QPushButton("Загрузить на диск")
        self.upload_btn.setStyleSheet(
            "background: #27ae60; color: white; padding: 8px; border-radius: 4px;"
        )
        self.upload_btn.clicked.connect(self._on_upload)
        sync_layout.addWidget(self.upload_btn)

        self.download_btn = QPushButton("Скачать с диска")
        self.download_btn.setStyleSheet(
            "background: #2980b9; color: white; padding: 8px; border-radius: 4px;"
        )
        self.download_btn.clicked.connect(self._on_download)
        sync_layout.addWidget(self.download_btn)

        layout.addWidget(sync_group)

        # Лог
        layout.addWidget(QLabel("Журнал:"))
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(100)
        self.log.setStyleSheet("background: #f5f5f5; font-family: monospace; font-size: 11px;")
        layout.addWidget(self.log)

        # Закрыть
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    # ──────────────── Вспомогательные ────────────────

    def _open_token_page(self):
        QDesktopServices.openUrl(
            QUrl("https://oauth.yandex.ru/authorize?response_type=token&client_id=d09c2efb19a3480591e84fe2eec1f1e8")
        )
        self._log("Открываю браузер. Войдите в Яндекс, разрешите доступ и скопируйте токен из адресной строки.")

    def _toggle_echo(self, checked: bool):
        mode = QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        self.token_edit.setEchoMode(mode)

    def _get_token(self) -> str | None:
        token = self.token_edit.text().strip()
        if not token:
            QMessageBox.warning(self, "Токен не введён", "Вставьте OAuth-токен в поле выше.")
            return None
        return token

    def _log(self, msg: str):
        self.log.append(msg)

    def _set_busy(self, busy: bool):
        self.upload_btn.setEnabled(not busy)
        self.download_btn.setEnabled(not busy)
        if busy:
            self._log("Выполняется запрос...")

    # ──────────────── Действия ────────────────

    def _on_check(self):
        token = self._get_token()
        if not token:
            return
        self._set_busy(True)
        self.worker = SyncWorker("check", token)
        self.worker.finished.connect(self._on_check_done)
        self.worker.start()

    def _on_check_done(self, ok: bool, msg: str):
        self._set_busy(False)
        if ok:
            self._log(f"Токен действителен. Пользователь: {msg}")
        else:
            self._log(f"Ошибка: {msg}")

    def _on_upload(self):
        token = self._get_token()
        if not token:
            return
        self._set_busy(True)
        self.worker = SyncWorker("upload", token)
        self.worker.finished.connect(self._on_sync_done)
        self.worker.start()

    def _on_download(self):
        token = self._get_token()
        if not token:
            return

        reply = QMessageBox.warning(
            self, "Подтверждение",
            "Текущая база данных будет ЗАМЕНЕНА файлом с Яндекс.Диска.\n"
            "Несохранённые данные будут потеряны. Продолжить?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self._set_busy(True)
        self.worker = SyncWorker("download", token)
        self.worker.finished.connect(self._on_sync_done)
        self.worker.start()

    def _on_sync_done(self, ok: bool, msg: str):
        self._set_busy(False)
        self._log(msg)
        if ok:
            QMessageBox.information(self, "Готово", msg)
        else:
            QMessageBox.critical(self, "Ошибка", msg)
