"""
Простая авторизация: хэш пароля через hashlib.
"""

import hashlib
from PyQt6.QtSql import QSqlQuery


def _hash(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def register_user(name: str, password: str) -> tuple[bool, str]:
    """
    Регистрирует нового пользователя.
    Возвращает (успех, сообщение).
    """
    query = QSqlQuery()
    query.prepare("SELECT id FROM users WHERE name = ?")
    query.addBindValue(name)
    query.exec()
    if query.next():
        return False, "Пользователь с таким именем уже существует."

    query.prepare("INSERT INTO users (name, pass_hash) VALUES (?, ?)")
    query.addBindValue(name)
    query.addBindValue(_hash(password))
    if query.exec():
        return True, "Регистрация прошла успешно!"
    return False, query.lastError().text()


def login_user(name: str, password: str) -> tuple[bool, int]:
    """
    Проверяет логин/пароль.
    Возвращает (успех, user_id) — user_id = -1 при неудаче.
    """
    query = QSqlQuery()
    query.prepare("SELECT id FROM users WHERE name = ? AND pass_hash = ?")
    query.addBindValue(name)
    query.addBindValue(_hash(password))
    query.exec()
    if query.next():
        return True, query.value(0)
    return False, -1
