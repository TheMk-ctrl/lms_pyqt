<p align="center">
  <h1 align="center">🔐 CryptoNotes</h1>
  <p align="center">Менеджер зашифрованных заметок на PyQt6 + SQLite</p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.14+-blue?logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/PyQt6-6.4+-green?logo=qt&logoColor=white" />
  <img src="https://img.shields.io/badge/SQLite-3-lightblue?logo=sqlite&logoColor=white" />
  <img src="https://img.shields.io/badge/Шифрование-Caesar%20%7C%20XOR%20%7C%20Base64-orange" />
</p>

---

## О проекте

**CryptoNotes** — десктопное приложение для хранения личных заметок с поддержкой шифрования. Каждая заметка перед сохранением шифруется выбранным алгоритмом, что делает данные нечитаемыми при прямом доступе к файлу базы данных. Поддерживается многопользовательский режим: у каждого пользователя своё пространство заметок, защищённое паролем.

Проект выполнен в рамках учебного курса по PyQt6. Реализована модульная архитектура: логика приложения разделена на слои `core` (логика) и `ui` (интерфейс).

---

## Возможности

### Авторизация
- Регистрация и вход по имени пользователя и паролю
- Пароль никогда не хранится в открытом виде — только SHA-256 хэш
- Каждый пользователь видит только свои заметки

### Заметки
- Создание заметок с заголовком, текстом и категорией
- Выбор **цвета карточки** из палитры или произвольного цвета через `QColorDialog`
- Просмотр заметки с автоматической расшифровкой
- Редактирование — текст загружается в расшифрованном виде, шифруется заново только при сохранении
- Удаление с подтверждением через `QMessageBox`

### Шифрование
| Алгоритм | Как работает |
|:---------|:-------------|
| **Без шифрования** | Текст хранится как есть |
| **Шифр Цезаря** | Каждая латинская буква сдвигается на 3 позиции в алфавите. `hello → khoor` |
| **XOR** | Каждый байт текста XOR-ится с байтом ключа циклически. Результат кодируется в Base64 для хранения в БД |
| **Base64** | Кодирование строки. Не является шифрованием в строгом смысле, но скрывает текст от беглого взгляда |

Демо-окно позволяет ввести произвольный текст и сравнить результат всех алгоритмов в реальном времени.

### Интерфейс
- Главный экран — **сетка цветных карточек** с заголовком, категорией, типом шифра и датой
- Поиск по заголовку заметки через параметризованный SQL-запрос (`prepare` / `bindValue`)
- Фильтр по категории
- Счётчик заметок с правильным склонением
- Сетка автоматически перестраивается при изменении ширины окна

### Стикеры на рабочем столе
- Любую заметку можно открыть как **перетаскиваемый стикер** поверх всех окон
- Стикер отображается в цвете заметки, текст редактируется прямо на нём
- Позиция запоминается в БД и восстанавливается при следующем открытии
- Размер меняется за угловой grip
- Стикеры остаются на экране даже после закрытия панели управления

### Экспорт
- Все заметки пользователя экспортируются в `.txt` через стандартный диалог `QFileDialog`

---

## Структура проекта

```
crypto_notes/
├── main.py                       # Точка входа, запуск QApplication
├── requirements.txt              # Зависимости
├── core/
│   ├── __init__.py
│   ├── database.py               # Подключение к SQLite, создание таблиц, миграции
│   ├── auth.py                   # Регистрация и вход, SHA-256 хэширование
│   └── cipher.py                 # Алгоритмы шифрования: Caesar, XOR, Base64
└── ui/
    ├── __init__.py
    ├── login_window.py           # Окно входа и регистрации (QTabWidget)
    ├── main_window.py            # Главное окно: сетка карточек, поиск, фильтр
    ├── note_dialog.py            # Диалог создания / редактирования заметки
    ├── view_note_dialog.py       # Диалог просмотра с расшифровкой
    ├── cipher_demo_window.py     # Демонстрация алгоритмов шифрования
    ├── sticker_board.py          # Панель управления стикерами
    └── sticker_widget.py         # Один стикер — перетаскиваемое окно без рамки
```

---

## База данных

Три таблицы, связанные внешними ключами:

```sql
users (
    id        INTEGER PRIMARY KEY,
    name      TEXT UNIQUE NOT NULL,
    pass_hash TEXT NOT NULL          -- SHA-256 хэш пароля
)

categories (
    id    INTEGER PRIMARY KEY,
    title TEXT UNIQUE NOT NULL
)

notes (
    id          INTEGER PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users(id),
    category_id INTEGER REFERENCES categories(id),
    title       TEXT NOT NULL,
    content     TEXT NOT NULL,       -- хранится в зашифрованном виде
    cipher      TEXT NOT NULL,       -- 'none' | 'caesar' | 'xor' | 'base64'
    color       TEXT NOT NULL,       -- hex-цвет карточки, напр. '#FFFACD'
    sticker_x   INTEGER,             -- позиция стикера на экране
    sticker_y   INTEGER,
    created_at  TEXT NOT NULL        -- datetime('now','localtime')
)
```

При выборке используется `LEFT JOIN` чтобы отображать название категории вместо её ID:

```sql
SELECT n.id, n.title, COALESCE(c.title, '—') AS category, n.cipher, n.color, n.created_at
FROM notes n
LEFT JOIN categories c ON c.id = n.category_id
WHERE n.user_id = :user_id AND n.title LIKE :search
```

Все пользовательские данные передаются через `prepare()` / `bindValue()` — защита от SQL-инъекций.

---

## Установка и запуск

```bash
# 1. Клонировать репозиторий
git clone https://github.com/your-username/cryptonotes.git
cd cryptonotes

# 2. Установить зависимости
pip install -r requirements.txt

# 3. Запустить
python main.py
```

**Требования:** Python 3.14+, PyQt6 ≥ 6.4.0

---

## Сборка в .exe

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name CryptoNotes main.py
```

Готовый файл появится в `dist/CryptoNotes.exe`.

---

## Технологии

| Компонент | Технология |
|:----------|:-----------|
| GUI | PyQt6 |
| База данных | SQLite через `QSqlQuery` / `QSqlQueryModel` |
| Шифрование | Собственная реализация (`core/cipher.py`) |
| Хэширование паролей | `hashlib.sha256` (стандартная библиотека) |
| Кодирование | `base64` (стандартная библиотека) |
| Сборка | PyInstaller |

---

## Применённые виджеты и технологии PyQt6

`QMainWindow` · `QDialog` · `QWidget` · `QToolBar` · `QStatusBar` ·
`QScrollArea` · `QGridLayout` · `QTabWidget` · `QTableView` ·
`QTextEdit` · `QLineEdit` · `QComboBox` · `QPushButton` · `QCheckBox` ·
`QLabel` · `QFrame` · `QSizeGrip` · `QSplitter` ·
`QMessageBox` · `QFileDialog` · `QColorDialog` ·
`QSqlQuery` · `QSqlQueryModel` · `QSqlDatabase` ·
`QThread` · `pyqtSignal` · `QPainter`

---

## Автор

**Сидоров Максим** — учебный проект по курсу PyQt6
