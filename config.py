"""
Конфигурационный файл для приложения мониторинга стендов
"""

import os
from pathlib import Path

# ==================== БАЗОВЫЕ ПУТИ ====================

# Базовая директория проекта
BASE_DIR = Path(__file__).parent

# Путь к базе данных
DATABASE_PATH = BASE_DIR / "stands_monitor.db"

# Директория для логов
LOGS_DIR = BASE_DIR / "logs"

# ==================== ПУТЬ К ПРОШИВКАМ (CVS) ====================

# Путь к папке CVS с прошивками
FIRMWARE_PATH = "/home/pkrv/CVS"

# Если папки нет, используем локальную папку firmwares
if not os.path.exists(FIRMWARE_PATH):
    FIRMWARE_PATH = str(BASE_DIR / "firmwares")
    # Создаём локальную папку если её нет
    os.makedirs(FIRMWARE_PATH, exist_ok=True)

# Допустимые расширения файлов прошивок
ALLOWED_FIRMWARE_EXTENSIONS = ["bin", "hex", "elf", "img"]

# ==================== НАСТРОЙКИ СТЕНДОВ ====================

# Конфигурация стендов (замените на реальные IP)
STANDS = {
    "stand_1": {
        "name": "Стенд 1",
        "ip": "192.168.1.101",
        "port": 80,
        "enabled": True
    },
    "stand_2": {
        "name": "Стенд 2",
        "ip": "192.168.1.102",
        "port": 80,
        "enabled": True
    },
    "stand_3": {
        "name": "Стенд 3",
        "ip": "192.168.1.103",
        "port": 80,
        "enabled": True
    },
}

# Настройки мониторинга
MONITOR_INTERVAL = 30
STANDS_TIMEOUT = 5

# ==================== НАСТРОЙКИ ВЕБ-ИНТЕРФЕЙСА ====================

SECRET_KEY = "dev-key-change-in-production-12345"
DEBUG = True  # Включаем для отладки
HOST = "0.0.0.0"
PORT = 5000

# ==================== НАСТРОЙКИ ЛОГИРОВАНИЯ ====================

LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

# ==================== EMAIL (опционально) ====================

EMAIL_CONFIG = {
    "enabled": False,
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "",
    "sender_password": "",
    "receiver_email": ""
}

# Создаём необходимые директории
LOGS_DIR.mkdir(exist_ok=True)
