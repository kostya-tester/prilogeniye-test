#!/usr/bin/env python3
"""
Приложение для мониторинга стендов и управления прошивками
Работает только на стандартной библиотеке Python (без Flask, requests и т.д.)
"""

import os
import sys
import json
import time
import socket
import subprocess
from pathlib import Path
from datetime import datetime
from threading import Thread

# ==================== КОНФИГУРАЦИЯ ====================

# Путь к папке CVS с прошивками
FIRMWARE_PATH = "/home/pkrv/CVS"

# Если папки нет, используем локальную
if not os.path.exists(FIRMWARE_PATH):
    FIRMWARE_PATH = os.path.join(os.path.dirname(__file__), "firmwares")
    os.makedirs(FIRMWARE_PATH, exist_ok=True)

# Конфигурация стендов (укажите свои IP)
STANDS = {
    "1": {
        "name": "Стенд 1",
        "ip": "192.168.1.101",
        "port": 80,
        "enabled": True
    },
    "2": {
        "name": "Стенд 2",
        "ip": "192.168.1.102",
        "port": 80,
        "enabled": True
    },
    "3": {
        "name": "Стенд 3",
        "ip": "192.168.1.103",
        "port": 80,
        "enabled": True
    },
}

# Таймаут проверки стендов (секунды)
TIMEOUT = 3

# ==================== ФУНКЦИИ ДЛЯ РАБОТЫ С СЕТЬЮ ====================

def check_host_alive(ip, port, timeout=TIMEOUT):
    """Проверка доступности хоста через TCP соединение"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()
        return result == 0
    except Exception:
        return False

def ping_host(ip):
    """Проверка доступности через ping (опционально)"""
    try:
        param = '-n' if sys.platform == 'win32' else '-c'
        result = subprocess.run(
            ['ping', param, '1', ip],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=TIMEOUT
        )
        return result.returncode == 0
    except Exception:
        return False

# ==================== ФУНКЦИИ ДЛЯ РАБОТЫ С ПРОШИВКАМИ ====================

def get_firmware_list():
    """Получить список файлов прошивок из папки CVS"""
    firmwares = []
    
    if not os.path.exists(FIRMWARE_PATH):
        return firmwares
    
    # Расширения файлов прошивок
    extensions = ['.bin', '.hex', '.elf', '.img', '.s19', '.mot']
    
    for file in os.listdir(FIRMWARE_PATH):
        file_path = os.path.join(FIRMWARE_PATH, file)
        if os.path.isfile(file_path):
            ext = os.path.splitext(file)[1].lower()
            if ext in extensions:
                stat = os.stat(file_path)
                firmwares.append({
                    'name': file,
                    'path': file_path,
                    'size': stat.st_size,
                    'size_kb': round(stat.st_size / 1024, 1),
                    'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                })
    
    # Сортируем по дате изменения (новые сверху)
    firmwares.sort(key=lambda x: x['modified'], reverse=True)
    return firmwares

def flash_firmware(stand_ip, firmware_path):
    """Прошить стенд (реальная реализация зависит от оборудования)"""
    print(f"\n📡 Прошивка стенда {stand_ip}...")
    print(f"📁 Файл: {firmware_path}")
    
    # Здесь должна быть логика прошивки
    # Вариант 1: Копирование через SSH (если есть доступ)
    # Вариант 2: Отправка через HTTP
    # Вариант 3: Копирование на флешку
    
    # Для примера - симуляция прошивки
    print("🔄 Загрузка прошивки...")
    time.sleep(2)
    
    # Проверяем, что файл не пустой
    if os.path.getsize(firmware_path) == 0:
        return False, "Файл прошивки пустой!"
    
    # Симуляция успеха
    print("✅ Прошивка успешно завершена!")
    return True, "Прошивка выполнена успешно"

# ==================== ФУНКЦИИ ДЛЯ РАБОТЫ С ПРОЦЕССАМИ ====================

def list_processes():
    """Список процессов (упрощённая версия)"""
    processes = []
    try:
        if sys.platform == 'win32':
            result = subprocess.run(['tasklist'], capture_output=True, text=True)
        else:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        
        lines = result.stdout.split('\n')
        for i, line in enumerate(lines[:20]):  # Показываем первые 20
            if i > 0 and line.strip():
                processes.append(line.strip())
    except Exception as e:
        processes.append(f"Ошибка: {e}")
    
    return processes

# ==================== ОСНОВНОЕ МЕНЮ ====================

def clear_screen():
    """Очистка экрана"""
    os.system('cls' if sys.platform == 'win32' else 'clear')

def print_header():
    """Вывод заголовка"""
    print("=" * 60)
    print("   🖥️  СИСТЕМА МОНИТОРИНГА СТЕНДОВ И ПРОШИВКИ")
    print("=" * 60)
    print(f"   📁 Папка прошивок: {FIRMWARE_PATH}")
    print(f"   🕐 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

def show_stands_status():
    """Показать статус всех стендов"""
    print("\n📡 СТАТУС СТЕНДОВ:")
    print("-" * 50)
    
    for stand_id, stand in STANDS.items():
        if not stand.get('enabled', True):
            status = "⚪ ОТКЛЮЧЁН"
            status_color = "⚪"
        else:
            ip = stand['ip']
            port = stand['port']
            
            print(f"   Проверка {stand['name']} ({ip}:{port})...", end=" ")
            sys.stdout.flush()
            
            alive = check_host_alive(ip, port)
            
            if alive:
                status = "✅ ONLINE"
                status_color = "🟢"
            else:
                status = "❌ OFFLINE"
                status_color = "🔴"
            
            # Возврат каретки и перезапись строки
            print("\r", end="")
        
        print(f"   {status_color} {stand['name']}: {status}")
        if status == "✅ ONLINE":
            print(f"      IP: {stand['ip']}:{stand['port']}")
    
    print("-" * 50)

def show_firmwares():
    """Показать список прошивок"""
    print("\n📁 ДОСТУПНЫЕ ПРОШИВКИ:")
    print("-" * 50)
    
    firmwares = get_firmware_list()
    
    if not firmwares:
        print("   ❌ Нет файлов прошивок в папке!")
        print(f"   📂 Поместите файлы (.bin, .hex, .elf) в: {FIRMWARE_PATH}")
        return []
    
    for i, fw in enumerate(firmwares, 1):
        print(f"   {i}. {fw['name']}")
        print(f"      Размер: {fw['size_kb']} KB | Изменён: {fw['modified']}")
    
    print("-" * 50)
    return firmwares

def select_stand_for_flashing():
    """Выбор стенда для прошивки"""
    print("\n🎯 ВЫБОР СТЕНДА ДЛЯ ПРОШИВКИ:")
    print("-" * 50)
    
    online_stands = []
    for stand_id, stand in STANDS.items():
        if stand.get('enabled', True):
            ip = stand['ip']
            port = stand['port']
            alive = check_host_alive(ip, port)
            status = "🟢 ONLINE" if alive else "🔴 OFFLINE"
            if alive:
                online_stands.append((stand_id, stand))
            print(f"   {stand_id}. {stand['name']} ({ip}) - {status}")
    
    print("-" * 50)
    
    if not online_stands:
        print("   ❌ Нет доступных стендов для прошивки!")
        return None, None
    
    while True:
        choice = input("\n👉 Выберите номер стенда (0 для отмены): ").strip()
        if choice == '0':
            return None, None
        
        if choice in [s[0] for s in online_stands]:
            stand = next(s for s in online_stands if s[0] == choice)
            return choice, stand[1]
        else:
            print("   ❌ Неверный выбор! Попробуйте снова.")

def select_firmware_for_flashing(firmwares):
    """Выбор прошивки"""
    print("\n📁 ВЫБОР ПРОШИВКИ:")
    print("-" * 50)
    
    for i, fw in enumerate(firmwares, 1):
        print(f"   {i}. {fw['name']} ({fw['size_kb']} KB)")
    
    print("-" * 50)
    
    while True:
        try:
            choice = input("\n👉 Выберите номер прошивки (0 для отмены): ").strip()
            if choice == '0':
                return None
            
            idx = int(choice) - 1
            if 0 <= idx < len(firmwares):
                return firmwares[idx]
            else:
                print("   ❌ Неверный номер! Попробуйте снова.")
        except ValueError:
            print("   ❌ Введите число!")

def flash_menu():
    """Меню прошивки"""
    print_header()
    
    # Проверяем наличие прошивок
    firmwares = get_firmware_list()
    if not firmwares:
        print("\n❌ НЕТ ФАЙЛОВ ПРОШИВОК!")
        print(f"📂 Поместите файлы прошивок в папку: {FIRMWARE_PATH}")
        input("\nНажмите Enter для продолжения...")
        return
    
    # Выбираем стенд
    stand_id, stand = select_stand_for_flashing()
    if not stand:
        return
    
    # Выбираем прошивку
    firmware = select_firmware_for_flashing(firmwares)
    if not firmware:
        return
    
    # Подтверждение
    print("\n" + "=" * 50)
    print("⚠️  ПОДТВЕРЖДЕНИЕ ПРОШИВКИ")
    print(f"   Стенд: {stand['name']} ({stand['ip']})")
    print(f"   Прошивка: {firmware['name']}")
    print("=" * 50)
    
    confirm = input("\n👉 Начать прошивку? (да/нет): ").strip().lower()
    if confirm in ['да', 'yes', 'y', 'д']:
        success, message = flash_firmware(stand['ip'], firmware['path'])
        
        print("\n" + "=" * 50)
        if success:
            print(f"✅ {message}")
            # Логируем успешную прошивку
            with open("flash_log.txt", "a") as log:
                log.write(f"{datetime.now()} - {stand['name']} - {firmware['name']} - УСПЕХ\n")
        else:
            print(f"❌ {message}")
        print("=" * 50)
    else:
        print("\n❌ Прошивка отменена.")
    
    input("\nНажмите Enter для продолжения...")

def show_processes():
    """Показать процессы"""
    print_header()
    print("\n⚙️ СПИСОК ПРОЦЕССОВ (первые 20):")
    print("-" * 60)
    
    processes = list_processes()
    for proc in processes:
        print(f"   {proc}")
    
    print("-" * 60)
    print("\n💡 Управление процессами:")
    print("   1. Для полного управления используйте системные команды")
    print("   2. Например: kill <PID> или taskkill /PID <PID>")
    
    input("\nНажмите Enter для продолжения...")

def show_logs():
    """Показать логи прошивок"""
    print_header()
    print("\n📋 ИСТОРИЯ ПРОШИВОК:")
    print("-" * 60)
    
    log_file = "flash_log.txt"
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            content = f.read()
            if content:
                print(content)
            else:
                print("   Лог пуст")
    else:
        print("   История прошивок пока пуста")
    
    print("-" * 60)
    input("\nНажмите Enter для продолжения...")

def show_help():
    """Помощь"""
    print_header()
    print("\n📖 СПРАВКА:")
    print("-" * 60)
    print("""
    📡 Мониторинг стендов:
       - Приложение проверяет доступность стендов по TCP порту
       - ONLINE - стенд отвечает на запросы
       - OFFLINE - стенд недоступен
    
    📁 Прошивки:
       - Файлы прошивок должны лежать в папке: """ + FIRMWARE_PATH + """
       - Поддерживаемые форматы: .bin, .hex, .elf, .img, .s19, .mot
       - Для добавления новой прошивки просто скопируйте файл в папку
    
    🔧 Прошивка стенда:
       1. Выберите стенд из списка доступных
       2. Выберите файл прошивки
       3. Подтвердите действие
    
    ⚙️ Процессы:
       - Для управления процессами используйте системные команды
       - Linux: kill, pkill, systemctl
       - Windows: taskkill, task manager
    
    📂 Папка CVS: """ + FIRMWARE_PATH)
    print("-" * 60)
    input("\nНажмите Enter для продолжения...")

def auto_monitor_loop():
    """Автоматический мониторинг в фоне"""
    def monitor():
        while True:
            time.sleep(30)  # Каждые 30 секунд
            # Здесь можно добавить фоновый мониторинг
            pass
    
    thread = Thread(target=monitor, daemon=True)
    thread.start()

# ==================== ГЛАВНОЕ МЕНЮ ====================

def main():
    """Главное меню приложения"""
    auto_monitor_loop()
    
    while True:
        clear_screen()
        print_header()
        show_stands_status()
        
        print("\n" + "=" * 60)
        print("📋 МЕНЮ:")
        print("=" * 60)
        print("   1. 🔄 Обновить статус стендов")
        print("   2. 📁 Показать прошивки (CVS)")
        print("   3. 🔥 Прошить стенд")
        print("   4. ⚙️ Управление процессами")
        print("   5. 📋 История прошивок")
        print("   6. 📖 Справка")
        print("   0. 🚪 Выход")
        print("=" * 60)
        
        choice = input("\n👉 Ваш выбор: ").strip()
        
        if choice == '1':
            continue  # Просто обновим экран
        elif choice == '2':
            clear_screen()
            print_header()
            show_firmwares()
            input("\nНажмите Enter для продолжения...")
        elif choice == '3':
            flash_menu()
        elif choice == '4':
            show_processes()
        elif choice == '5':
            show_logs()
        elif choice == '6':
            show_help()
        elif choice == '0':
            print("\n👋 До свидания!")
            sys.exit(0)
        else:
            print("\n❌ Неверный выбор!")
            time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Прерывание работы...")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        input("\nНажмите Enter для выхода...")
        sys.exit(1)
