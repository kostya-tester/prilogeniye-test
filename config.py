"""
Конфигурационный файл для приложения мониторинга стендов
Все настройки вынесены в отдельный файл для удобства изменения
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

# Директория для временных файлов
TEMP_DIR = BASE_DIR / "temp"

# ==================== ПУТЬ К ПРОШИВКАМ (CVS) ====================

# Путь к папке CVS с прошивками (основной путь для вашей задачи)
FIRMWARE_PATH = "/home/pkrv/CVS"

# Альтернативный вариант: можно использовать относительный путь
# FIRMWARE_PATH = BASE_DIR / "firmwares"

# Допустимые расширения файлов прошивок
ALLOWED_FIRMWARE_EXTENSIONS = ["bin", "hex", "elf", "img", "s19", "mot"]

# Максимальный размер файла прошивки в МБ (50 МБ по умолчанию)
MAX_FIRMWARE_SIZE_MB = 50

# ==================== НАСТРОЙКИ СТЕНДОВ ====================

# Конфигурация стендов (замените на реальные IP и порты)
STANDS = {
    "stand_1": {
        "name": "Тестовый стенд 1",
        "ip": "192.168.1.101",
        "port": 80,
        "enabled": True,
        "type": "test",
        "ssh_port": 22,
        "ssh_user": "root",
        "ssh_password": "your_password_here"
    },
    "stand_2": {
        "name": "Тестовый стенд 2",
        "ip": "192.168.1.102",
        "port": 80,
        "enabled": True,
        "type": "production",
        "ssh_port": 22,
        "ssh_user": "root",
        "ssh_password": "your_password_here"
    },
    "stand_3": {
        "name": "Тестовый стенд 3",
        "ip": "192.168.1.103",
        "port": 80,
        "enabled": True,
        "type": "test",
        "ssh_port": 22,
        "ssh_user": "root",
        "ssh_password": "your_password_here"
    },
}

# Настройки мониторинга стендов
MONITOR_INTERVAL = 30  # секунд между проверками статуса
STANDS_TIMEOUT = 5  # таймаут для сетевых запросов к стендам (секунды)
STANDS_RETRY_COUNT = 3  # количество попыток при неудаче
STANDS_RETRY_DELAY = 1  # задержка между попытками (секунды)

# ==================== НАСТРОЙКИ ORANGE PI ====================

# Конфигурация платы Orange Pi (если используется)
ORANGE_PI_CONFIG = {
    "ip": "192.168.1.200",
    "port": 22,
    "username": "pi",
    "password": "raspberry",  # замените на реальный пароль
    "key_path": str(BASE_DIR / "keys" / "id_rsa"),  # опционально: путь к SSH ключу
    "use_key_auth": False,  # использовать ключ вместо пароля
}

# ==================== НАСТРОЙКИ ПРОЦЕССОВ ====================

# Список процессов для мониторинга и управления
PROCESSES_TO_MONITOR = [
    {
        "name": "stands_monitor",
        "command": "python3 stands_monitor.py",
        "auto_restart": True,
        "working_dir": str(BASE_DIR)
    },
    {
        "name": "webserver",
        "command": "python3 app.py",
        "auto_restart": True,
        "working_dir": str(BASE_DIR)
    },
    # Добавьте свои процессы здесь
]

# Настройки управления процессами
PROCESS_MANAGER_CONFIG = {
    "check_interval": 10,  # интервал проверки статуса процессов (секунды)
    "stop_timeout": 10,  # таймаут остановки процесса (секунды)
    "start_delay": 2,  # задержка перед запуском (секунды)
}

# ==================== EMAIL УВЕДОМЛЕНИЯ ====================

# Настройки SMTP для отправки email уведомлений
EMAIL_CONFIG = {
    "enabled": False,  # включить/выключить отправку уведомлений
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "your_email@gmail.com",
    "sender_password": "your_app_password",  # используйте пароль приложения Gmail
    "receiver_email": "admin@example.com",
    "subject_prefix": "[Stands Monitor]",
    "send_on_firmware_complete": True,  # уведомлять об успешной прошивке
    "send_on_stand_failure": True,  # уведомлять о падении стенда
}

# ==================== НАСТРОЙКИ ВЕБ-ИНТЕРФЕЙСА ====================

# Flask настройки
SECRET_KEY = "your-secret-key-here-change-in-production-12345"  # СМЕНИТЕ на случайную строку!
DEBUG = False  # Включите True только для отладки
HOST = "0.0.0.0"  # Слушать все интерфейсы (для доступа из сети)
PORT = 5000

# Настройки безопасности
CSRF_ENABLED = True
SESSION_COOKIE_SECURE = True if not DEBUG else False
SESSION_COOKIE_HTTPONLY = True
PERMANENT_SESSION_LIFETIME = 3600  # секунды (1 час)

# ==================== НАСТРОЙКИ ЛОГИРОВАНИЯ ====================

# Уровень логирования: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL = "INFO"

# Формат логов
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Формат даты в логах
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Максимальный размер файла лога в байтах (10 МБ)
LOG_MAX_BYTES = 10 * 1024 * 1024

# Количество сохраняемых файлов логов
LOG_BACKUP_COUNT = 5

# ==================== НАСТРОЙКИ БАЗЫ ДАННЫХ ====================

# Тип базы данных: sqlite, postgresql, mysql
DATABASE_TYPE = "sqlite"

# Настройки для SQLite (используется по умолчанию)
SQLITE_CONFIG = {
    "database": str(DATABASE_PATH),
    "timeout": 10,  # таймаут блокировки в секундах
}

# Настройки для PostgreSQL (если понадобится)
POSTGRESQL_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "stands_monitor",
    "user": "postgres",
    "password": "password",
}

# Настройки для MySQL (если понадобится)
MYSQL_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "database": "stands_monitor",
    "user": "root",
    "password": "password",
}

# ==================== НАСТРОЙКИ ЭКСПОРТА ДАННЫХ ====================

# Директория для экспорта CSV/отчетов
EXPORT_DIR = BASE_DIR / "exports"

# Формат экспорта: csv, json, excel
EXPORT_FORMAT = "csv"

# Разделитель для CSV файлов
CSV_DELIMITER = ","

# Кодировка для экспорта
EXPORT_ENCODING = "utf-8"

# ==================== НАСТРОЙКИ СТАТИСТИКИ ====================

# Периоды для сбора статистики (в днях)
STATISTICS_PERIODS = {
    "day": 1,
    "week": 7,
    "month": 30,
    "year": 365,
}

# Включить сбор детальной статистики
DETAILED_STATISTICS = True

# Хранить историю статусов (в днях)
HISTORY_RETENTION_DAYS = 90

# ==================== СИСТЕМНЫЕ НАСТРОЙКИ ====================

# Автоматически создавать необходимые директории
AUTO_CREATE_DIRS = True

# Включить режим совместимости с Windows (если запускаете на Windows)
WINDOWS_COMPATIBILITY = False

# Количество потоков для параллельных проверок
THREAD_POOL_SIZE = 5

# Таймаут операций (секунды)
DEFAULT_TIMEOUT = 30

# ==================== ФУНКЦИИ ДЛЯ ПРОВЕРКИ КОНФИГУРАЦИИ ====================

def validate_config():
    """Проверка корректности конфигурации"""
    errors = []
    
    # Проверяем путь к прошивкам
    if not os.path.exists(FIRMWARE_PATH):
        errors.append(f"Папка с прошивками не найдена: {FIRMWARE_PATH}")
    
    # Проверяем секретный ключ
    if SECRET_KEY == "your-secret-key-here-change-in-production-12345" and not DEBUG:
        errors.append("WARNING: Используется стандартный SECRET_KEY! Смените его!")
    
    # Проверяем email настройки если включены
    if EMAIL_CONFIG["enabled"]:
        if EMAIL_CONFIG["sender_password"] == "your_app_password":
            errors.append("EMAIL: Не указан пароль для отправки уведомлений")
    
    # Создаем необходимые директории
    if AUTO_CREATE_DIRS:
        for dir_path in [LOGS_DIR, TEMP_DIR, EXPORT_DIR]:
            dir_path.mkdir(exist_ok=True)
    
    return errors

# ==================== ЗАГРУЗКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ ====================

def load_env_variables():
    """Загрузка конфигурации из переменных окружения (переопределяет настройки)"""
    # Можно переопределить секретный ключ
    global SECRET_KEY
    if os.getenv('STANDS_SECRET_KEY'):
        SECRET_KEY = os.getenv('STANDS_SECRET_KEY')
    
    # Можно переопределить путь к прошивкам
    global FIRMWARE_PATH
    if os.getenv('STANDS_FIRMWARE_PATH'):
        FIRMWARE_PATH = os.getenv('STANDS_FIRMWARE_PATH')
    
    # Можно переопределить режим отладки
    global DEBUG
    if os.getenv('STANDS_DEBUG'):
        DEBUG = os.getenv('STANDS_DEBUG').lower() == 'true'

# Загружаем переменные окружения (раскомментируйте если нужно)
# load_env_variables()

# ==================== ИНИЦИАЛИЗАЦИЯ ====================

# Выводим предупреждения о конфигурации
config_errors = validate_config()
for error in config_errors:
    print(f"[CONFIG] {error}")

# Создаем необходимые директории
if AUTO_CREATE_DIRS:
    LOGS_DIR.mkdir(exist_ok=True)
    TEMP_DIR.mkdir(exist_ok=True)
    EXPORT_DIR.mkdir(exist_ok=True)

# Итоговая информация
print(f"[CONFIG] Конфигурация загружена")
print(f"[CONFIG] Режим DEBUG: {DEBUG}")
print(f"[CONFIG] Путь к прошивкам: {FIRMWARE_PATH}")
print(f"[CONFIG] База данных: {DATABASE_PATH}")
print(f"[CONFIG] Логи: {LOGS_DIR}")
