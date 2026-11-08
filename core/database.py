"""
Модуль для работы с базой данных через QtSql
"""

from PyQt6.QtSql import QSqlDatabase, QSqlQuery


DB_PATH = "notes.db"


def init_db() -> bool:
    """Создаёт подключение к БД и все таблицы, если их нет."""
    db = QSqlDatabase.addDatabase("QSQLITE")
    db.setDatabaseName(DB_PATH)

    if not db.open():
        print("Ошибка подключения к БД:", db.lastError().text())
        return False

    query = QSqlQuery()

    # Таблица пользователей
    query.exec("""
        CREATE TABLE IF NOT EXISTS users (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            pass_hash TEXT NOT NULL
        )
    """)

    # Таблица категорий
    query.exec("""
        CREATE TABLE IF NOT EXISTS categories (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL UNIQUE
        )
    """)

    # Таблица заметок
    query.exec("""
        CREATE TABLE IF NOT EXISTS notes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            category_id INTEGER,
            title       TEXT    NOT NULL,
            content     TEXT    NOT NULL,
            cipher      TEXT    NOT NULL DEFAULT 'none',
            color       TEXT    NOT NULL DEFAULT '#FFFACD',
            sticker_x   INTEGER DEFAULT NULL,
            sticker_y   INTEGER DEFAULT NULL,
            created_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (user_id)     REFERENCES users(id),
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    """)
    # Миграция для существующих БД — добавляем колонки если их нет
    for col, definition in [
        ("color",     "TEXT NOT NULL DEFAULT '#FFFACD'"),
        ("sticker_x", "INTEGER DEFAULT NULL"),
        ("sticker_y", "INTEGER DEFAULT NULL"),
    ]:
        query.exec(f"ALTER TABLE notes ADD COLUMN {col} {definition}")

    # Предзаполним пару категорий
    for cat in ("Личное", "Работа", "Пароли", "Разное"):
        query.prepare("INSERT OR IGNORE INTO categories (title) VALUES (?)")
        query.addBindValue(cat)
        query.exec()

    return True


def get_db() -> QSqlDatabase:
    return QSqlDatabase.database()
