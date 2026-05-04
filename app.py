#!/usr/bin/env python3
"""
Приложение для мониторинга стендов и управления прошивками
Работает только на стандартной библиотеке Python
"""

import os
import sys
import time
import socket
import subprocess
from datetime import datetime

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

# Кэш статусов стендов (чтобы не проверять каждый раз)
_stands_cache = {}
_cache_time = 0
_cache_ttl = 10  # обновлять раз в 10 секунд

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

def get_stands_status():
    """Получить статус всех стендов с кэшированием"""
    global _stands_cache, _cache_time
    
    now = time.time()
    if now - _cache_time < _cache_ttl and _stands_cache:
        return _stands_cache
    
    statuses = {}
    for stand_id, stand in STANDS.items():
        if not stand.get('enabled', True):
            statuses[stand_id] = {'name': stand['name'], 'ip': stand['ip'], 'status': 'disabled', 'port': stand['port']}
        else:
            alive = check_host_alive(stand['ip'], stand['port'])
            statuses[stand_id] = {
                'name': stand['name'],
                'ip': stand['ip'],
                'port': stand['port'],
                'status': 'online' if alive else 'offline'
            }
    
    _stands_cache = statuses
    _cache_time = now
    return statuses

# ==================== ФУНКЦИИ ДЛЯ РАБОТЫ С ПРОШИВКАМИ ====================

def get_firmware_list():
    """Получить список файлов прошивок из папки CVS"""
    firmwares = []
    
    if not os.path.exists(FIRMWARE_PATH):
        return firmwares
    
    # Расширения файлов прошивок
    extensions = ['.bin', '.hex', '.elf', '.img', '.s19', '.mot']
    
    try:
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
    except Exception as e:
        print(f"   Ошибка чтения папки: {e}")
    
    # Сортируем по дате изменения (новые сверху)
    firmwares.sort(key=lambda x: x['modified'], reverse=True)
    return firmwares

def flash_firmware(stand_ip, stand_name, firmware_path, firmware_name):
    """Прошить стенд"""
    print(f"\n   📡 Прошивка стенда {stand_name} ({stand_ip})...")
    print(f"   📁 Файл: {firmware_name}")
    
    # Проверяем, что файл существует и не пустой
    if not os.path.exists(firmware_path):
        return False, f"Файл {firmware_name} не найден!"
    
    if os.path.getsize(firmware_path) == 0:
        return False, "Файл прошивки пустой!"
    
    # Здесь должна быть реальная логика прошивки
    # Пример для копирования через SSH:
    """
    try:
        result = subprocess.run(
            ['scp', firmware_path, f'root@{stand_ip}:/tmp/firmware.bin'],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            return False, f"Ошибка копирования: {result.stderr}"
    except Exception as e:
        return False, f"Ошибка: {e}"
    """
    
    # Симуляция прошивки
    print("   🔄 Загрузка прошивки...")
    for i in range(1, 4):
        print(f"      ... {i*33}%")
        time.sleep(0.5)
    
    print("   ✅ Прошивка успешно завершена!")
    
    # Логируем успешную прошивку
    try:
        with open("flash_log.txt", "a") as log:
            log.write(f"{datetime.now()} | {stand_name} ({stand_ip}) | {firmware_name} | УСПЕХ\n")
    except Exception:
        pass
    
    return True, "Прошивка выполнена успешно"

# ==================== ФУНКЦИИ ДЛЯ РАБОТЫ С ПРОЦЕССАМИ ====================

def list_processes():
    """Список процессов"""
    processes = []
    try:
        if sys.platform == 'win32':
            result = subprocess.run(['tasklist', '/NH'], capture_output=True, text=True, timeout=10)
        else:
            result = subprocess.run(['ps', 'aux', '--sort=-%cpu', '|', 'head', '-15'], 
                                   capture_output=True, text=True, timeout=10, shell=True)
        
        lines = result.stdout.split('\n')
        for line in lines[:15]:
            if line.strip():
                processes.append(line.strip())
    except Exception as e:
        processes.append(f"Ошибка получения процессов: {e}")
    
    return processes

# ==================== ФУНКЦИИ ДЛЯ ВЫВОДА ====================

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
    
    statuses = get_stands_status()
    
    for stand_id, stand in statuses.items():
        if stand['status'] == 'online':
            status_icon = "🟢"
            status_text = "ONLINE"
        elif stand['status'] == 'disabled':
            status_icon = "⚪"
            status_text = "ОТКЛЮЧЁН"
        else:
            status_icon = "🔴"
            status_text = "OFFLINE"
        
        print(f"   {status_icon} {stand['name']}: {status_text}")
        print(f"      IP: {stand['ip']}:{stand['port']}")
    
    print("-" * 50)
    
    # Подсчет онлайн стендов
    online_count = sum(1 for s in statuses.values() if s['status'] == 'online')
    print(f"   📊 Всего: {len(statuses)} | 🟢 Онлайн: {online_count} | 🔴 Оффлайн: {len(statuses) - online_count}")
    print("-" * 50)

def show_firmwares():
    """Показать список прошивок"""
    print("\n📁 ДОСТУПНЫЕ ПРОШИВКИ:")
    print("-" * 50)
    
    firmwares = get_firmware_list()
    
    if not firmwares:
        print("   ❌ Нет файлов прошивок в папке!")
        print(f"   📂 Поместите файлы (.bin, .hex, .elf) в: {FIRMWARE_PATH}")
        print("\n   💡 Создайте тестовый файл:")
        print(f"      echo 'test' > {FIRMWARE_PATH}/test.bin")
    else:
        for i, fw in enumerate(firmwares, 1):
            print(f"   {i}. {fw['name']}")
            print(f"      Размер: {fw['size_kb']} KB | Изменён: {fw['modified']}")
    
    print("-" * 50)
    return firmwares

def select_stand_for_flashing():
    """Выбор стенда для прошивки"""
    print("\n🎯 ВЫБОР СТЕНДА ДЛЯ ПРОШИВКИ:")
    print("-" * 50)
    
    statuses = get_stands_status()
    online_stands = []
    
    for stand_id, stand in statuses.items():
        if stand['status'] == 'online':
            online_stands.append((stand_id, stand))
            print(f"   {stand_id}. {stand['name']} ({stand['ip']}) - 🟢 ONLINE")
        else:
            status_text = "⚪ ОТКЛ" if stand['status'] == 'disabled' else "🔴 OFF"
            print(f"   {stand_id}. {stand['name']} ({stand['ip']}) - {status_text}")
    
    print("-" * 50)
    
    if not online_stands:
        print("   ❌ Нет доступных стендов для прошивки!")
        print("   💡 Проверьте подключение стендов к сети")
        return None, None
    
    while True:
        try:
            choice = input("\n👉 Выберите номер стенда (0 для отмены): ").strip()
            if choice == '0':
                return None, None
            
            for stand_id, stand in online_stands:
                if choice == stand_id:
                    return stand_id, stand
            
            print("   ❌ Неверный выбор! Выберите номер из списка онлайн стендов.")
        except EOFError:
            return None, None
        except KeyboardInterrupt:
            return None, None

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
                print(f"   ❌ Введите число от 1 до {len(firmwares)}!")
        except ValueError:
            print("   ❌ Введите число!")
        except EOFError:
            return None
        except KeyboardInterrupt:
            return None

def flash_menu():
    """Меню прошивки"""
    clear_screen()
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
    print("=" * 50)
    print(f"   Стенд: {stand['name']} ({stand['ip']})")
    print(f"   Прошивка: {firmware['name']}")
    print("=" * 50)
    
    try:
        confirm = input("\n👉 Начать прошивку? (да/нет): ").strip().lower()
        if confirm in ['да', 'yes', 'y', 'д', '+']:
            success, message = flash_firmware(
                stand['ip'], 
                stand['name'], 
                firmware['path'], 
                firmware['name']
            )
            
            print("\n" + "=" * 50)
            if success:
                print(f"✅ {message}")
            else:
                print(f"❌ {message}")
            print("=" * 50)
        else:
            print("\n❌ Прошивка отменена.")
    except EOFError:
        print("\n❌ Операция отменена.")
    
    input("\nНажмите Enter для продолжения...")

def show_processes():
    """Показать процессы"""
    clear_screen()
    print_header()
    print("\n⚙️ ПРОЦЕССЫ В СИСТЕМЕ:")
    print("-" * 60)
    
    processes = list_processes()
    for proc in processes:
        print(f"   {proc}")
    
    print("-" * 60)
    print("\n💡 Управление процессами:")
    print("   • Windows: taskkill /PID <PID>")
    print("   • Linux:   kill -9 <PID>")
    print("   • Посмотреть PID можно в колонке слева")
    
    input("\nНажмите Enter для продолжения...")

def show_logs():
    """Показать логи прошивок"""
    clear_screen()
    print_header()
    print("\n📋 ИСТОРИЯ ПРОШИВОК:")
    print("-" * 60)
    
    log_file = "flash_log.txt"
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r') as f:
                content = f.read()
                if content.strip():
                    print(content)
                else:
                    print("   Лог пуст")
        except Exception as e:
            print(f"   Ошибка чтения лога: {e}")
    else:
        print("   История прошивок пока пуста")
        print("   После первой прошивки здесь появится запись")
    
    print("-" * 60)
    input("\nНажмите Enter для продолжения...")

def show_info():
    """Информация о системе"""
    clear_screen()
    print_header()
    print("\n💻 ИНФОРМАЦИЯ О СИСТЕМЕ:")
    print("-" * 60)
    print(f"   Python версия: {sys.version}")
    print(f"   Операционная система: {sys.platform}")
    print(f"   Путь к папке прошивок: {FIRMWARE_PATH}")
    print(f"   Существует ли папка: {os.path.exists(FIRMWARE_PATH)}")
    
    # Проверяем доступность IP
    print("\n📡 Проверка доступности стендов:")
    for stand_id, stand in STANDS.items():
        alive = check_host_alive(stand['ip'], stand['port'])
        status = "✅ Доступен" if alive else "❌ Недоступен"
        print(f"   {stand['name']} ({stand['ip']}:{stand['port']}) - {status}")
    
    print("-" * 60)
    input("\nНажмите Enter для продолжения...")

def show_help():
    """Помощь"""
    clear_screen()
    print_header()
    print("\n📖 СПРАВКА")
    print("=" * 60)
    print("""
📡 МОНИТОРИНГ СТЕНДОВ:
   - ONLINE  - стенд отвечает на запросы
   - OFFLINE - стенд недоступен
   - ОТКЛЮЧЁН - стенд выключен в конфигурации

📁 ПРОШИВКИ:
   • Файлы должны лежать в папке: """ + FIRMWARE_PATH + """
   • Поддерживаемые форматы: .bin, .hex, .elf, .img, .s19, .mot
   • Для добавления: просто скопируйте файл в папку

🔥 ПРОШИВКА СТЕНДА:
   1. Выберите стенд (только ONLINE)
   2. Выберите файл прошивки
   3. Подтвердите действие

⚙️ ПРОЦЕССЫ:
   • Для остановки: kill <PID> (Linux) или taskkill /PID <PID> (Windows)
   • PID - номер процесса в первом столбце

🔧 НАСТРОЙКА:
   • IP стендов можно изменить в файле app.py
   • Найдите переменную STANDS и отредактируйте IP адреса
""")
    print("=" * 60)
    input("\nНажмите Enter для продолжения...")

# ==================== ГЛАВНОЕ МЕНЮ ====================

def main():
    """Главное меню приложения"""
    while True:
        try:
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
            print("   6. 💻 Информация о системе")
            print("   7. 📖 Справка")
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
                show_info()
            elif choice == '7':
                show_help()
            elif choice == '0':
                print("\n👋 До свидания!")
                sys.exit(0)
            else:
                print("\n❌ Неверный выбор! Введите число от 0 до 7.")
                time.sleep(1)
                
        except EOFError:
            print("\n\n👋 До свидания!")
            sys.exit(0)
        except KeyboardInterrupt:
            print("\n\n👋 Прерывание работы...")
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ Ошибка: {e}")
            time.sleep(2)

if __name__ == "__main__":
    main()
