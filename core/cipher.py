"""
Модуль шифрования.
Реализованы три алгоритма: Цезарь, XOR, Base64.
"""

import base64


# ─────────────────────── Шифр Цезаря ───────────────────────

def caesar_encrypt(text: str, shift: int = 3) -> str:
    """Шифр Цезаря — сдвиг каждого символа на shift позиций."""
    result = []
    for ch in text:
        if ch.isalpha():
            # Определяем базу: 'a' или 'A'
            base = ord('a') if ch.islower() else ord('A')
            result.append(chr((ord(ch) - base + shift) % 26 + base))
        else:
            result.append(ch)
    return "".join(result)


def caesar_decrypt(text: str, shift: int = 3) -> str:
    """Обратный шифр Цезаря."""
    return caesar_encrypt(text, -shift)


# ─────────────────────── XOR-шифр ───────────────────────────

def xor_encrypt(text: str, key: str = "secret") -> str:
    """
    XOR-шифрование: каждый байт текста XOR-ится с байтом ключа.
    Результат кодируется в Base64, чтобы хранить как строку.
    """
    key_bytes = key.encode("utf-8")
    text_bytes = text.encode("utf-8")
    xored = bytes(b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(text_bytes))
    return base64.b64encode(xored).decode("utf-8")


def xor_decrypt(encoded: str, key: str = "secret") -> str:
    """Обратный XOR (XOR симметричен, достаточно повторить операцию)."""
    key_bytes = key.encode("utf-8")
    xored = base64.b64decode(encoded.encode("utf-8"))
    text_bytes = bytes(b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(xored))
    return text_bytes.decode("utf-8")


# ─────────────────────── Base64 ─────────────────────────────

def b64_encrypt(text: str) -> str:
    """Кодирование в Base64 (не шифрование, но скрывает текст)."""
    return base64.b64encode(text.encode("utf-8")).decode("utf-8")


def b64_decrypt(encoded: str) -> str:
    """Декодирование из Base64."""
    return base64.b64decode(encoded.encode("utf-8")).decode("utf-8")


# ─────────────────────── Диспетчер ──────────────────────────

CIPHERS = {
    "none":   ("Без шифрования",  lambda t, k: t,              lambda t, k: t),
    "caesar": ("Шифр Цезаря",     lambda t, k: caesar_encrypt(t), lambda t, k: caesar_decrypt(t)),
    "xor":    ("XOR",             lambda t, k: xor_encrypt(t, k), lambda t, k: xor_decrypt(t, k)),
    "base64": ("Base64",          lambda t, k: b64_encrypt(t),    lambda t, k: b64_decrypt(t)),
}


def encrypt(text: str, cipher_id: str, key: str = "secret") -> str:
    """Зашифровать текст выбранным алгоритмом."""
    _, enc, _ = CIPHERS.get(cipher_id, CIPHERS["none"])
    return enc(text, key)


def decrypt(text: str, cipher_id: str, key: str = "secret") -> str:
    """Расшифровать текст выбранным алгоритмом."""
    _, _, dec = CIPHERS.get(cipher_id, CIPHERS["none"])
    return dec(text, key)


def cipher_names() -> dict:
    """Возвращает {id: название} для заполнения QComboBox."""
    return {k: v[0] for k, v in CIPHERS.items()}
