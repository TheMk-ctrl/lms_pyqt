"""
Синхронизация с Яндекс.Диском через REST API.
Загружает и скачивает файл notes.db.
"""

import requests

YADISK_API = "https://cloud-api.yandex.net/v1/disk/resources"
REMOTE_PATH = "/CryptoNotes/notes.db"


def _headers(token: str) -> dict:
    return {"Authorization": f"OAuth {token}"}


def upload_db(token: str, local_path: str = "notes.db") -> tuple[bool, str]:
    """Загружает notes.db на Яндекс.Диск. Возвращает (успех, сообщение)."""
    try:
        # 1. Создаём папку CryptoNotes если её нет
        requests.put(
            f"{YADISK_API}?path=/CryptoNotes",
            headers=_headers(token),
            timeout=10
        )

        # 2. Получаем URL для загрузки
        resp = requests.get(
            f"{YADISK_API}/upload?path={REMOTE_PATH}&overwrite=true",
            headers=_headers(token),
            timeout=10
        )
        if resp.status_code != 200:
            return False, f"Ошибка получения URL загрузки: {resp.status_code}\n{resp.text}"

        upload_url = resp.json()["href"]

        # 3. Загружаем файл
        with open(local_path, "rb") as f:
            put_resp = requests.put(upload_url, data=f, timeout=30)

        if put_resp.status_code in (200, 201):
            return True, "Файл успешно загружен на Яндекс.Диск!\nПуть: /CryptoNotes/notes.db"
        else:
            return False, f"Ошибка загрузки файла: {put_resp.status_code}"

    except FileNotFoundError:
        return False, f"Файл {local_path} не найден."
    except requests.exceptions.ConnectionError:
        return False, "Нет подключения к интернету."
    except requests.exceptions.Timeout:
        return False, "Превышено время ожидания ответа от сервера."
    except Exception as e:
        return False, f"Неожиданная ошибка: {e}"


def download_db(token: str, local_path: str = "notes.db") -> tuple[bool, str]:
    """Скачивает notes.db с Яндекс.Диска. Возвращает (успех, сообщение)."""
    try:
        # Получаем ссылку на скачивание
        resp = requests.get(
            f"{YADISK_API}/download?path={REMOTE_PATH}",
            headers=_headers(token),
            timeout=10
        )
        if resp.status_code == 404:
            return False, "Файл на Яндекс.Диске не найден.\nСначала загрузите резервную копию."
        if resp.status_code != 200:
            return False, f"Ошибка: {resp.status_code}\n{resp.text}"

        download_url = resp.json()["href"]

        # Скачиваем
        file_resp = requests.get(download_url, timeout=30)
        if file_resp.status_code == 200:
            with open(local_path, "wb") as f:
                f.write(file_resp.content)
            return True, "База данных успешно восстановлена с Яндекс.Диска!\nПерезапустите приложение."
        else:
            return False, f"Ошибка скачивания: {file_resp.status_code}"

    except requests.exceptions.ConnectionError:
        return False, "Нет подключения к интернету."
    except requests.exceptions.Timeout:
        return False, "Превышено время ожидания ответа от сервера."
    except Exception as e:
        return False, f"Неожиданная ошибка: {e}"


def check_token(token: str) -> tuple[bool, str]:
    """Проверяет, действителен ли токен. Возвращает (валиден, имя пользователя или ошибка)."""
    try:
        resp = requests.get(
            "https://cloud-api.yandex.net/v1/disk/",
            headers=_headers(token),
            timeout=10
        )
        if resp.status_code == 200:
            data = resp.json()
            login = data.get("user", {}).get("login", "неизвестно")
            return True, login
        elif resp.status_code == 401:
            return False, "Неверный токен. Проверьте правильность и попробуйте снова."
        else:
            return False, f"Ошибка проверки токена: {resp.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "Нет подключения к интернету."
    except Exception as e:
        return False, str(e)
