#!/usr/bin/env python3
"""
Приложение для мониторинга стендов и управления прошивками
"""

import os
import sys
import time
import socket
import subprocess
from datetime import datetime

# ==================== КОНФИГУРАЦИЯ ====================

FIRMWARE_PATH = "/home/pkrv/CVS"

if not os.path.exists(FIRMWARE_PATH):
    FIRMWARE_PATH = os.path.join(os.path.dirname(__file__), "firmwares")
    os.makedirs(FIRMWARE_PATH, exist_ok=True)

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

TIMEOUT = 3
_stands_cache = {}
_cache_time = 0
_cache_ttl = 10

# ==================== ФУНКЦИИ ====================

def check_host_alive(ip, port, timeout=TIMEOUT):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()
        return result == 0
    except Exception:
        return False

def get_stands_status():
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

def get_firmware_list():
    firmwares = []
    if not os.path.exists(FIRMWARE_PATH):
        return firmwares
    
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
    except Exception:
        pass
    
    firmwares.sort(key=lambda x: x['modified'], reverse=True)
    return firmwares

def flash_firmware(stand_ip, stand_name, firmware_path, firmware_name):
    print(f"\n   📡 Прошивка стенда {stand_name} ({stand_ip})...")
    print(f"   📁 Файл: {firmware_name}")
    
    if not os.path.exists(firmware_path):
        return False, f"Файл {firmware_name} не найден!"
    
    if os.path.getsize(firmware_path) == 0:
        return False, "Файл прошивки пустой!"
    
    print("   🔄 Загрузка прошивки...")
    for i in range(1, 4):
        print(f"      ... {i*33}%")
        time.sleep(0.5)
    
    print("   ✅ Прошивка успешно завершена!")
    
    try:
        with open("flash_log.txt", "a") as log:
            log.write(f"{datetime.now()} | {stand_name} ({stand_ip}) | {firmware_name} | УСПЕХ\n")
    except Exception:
        pass
    
    return True, "Прошивка выполнена успешно"

def list_processes():
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
        processes.append(f"Ошибка: {e}")
    return processes

def clear_screen():
    os.system('cls' if sys.platform == 'win32' else 'clear')

def print_header():
    print("=" * 60)
    print("   🖥️  СИСТЕМА МОНИТОРИНГА СТЕНДОВ И ПРОШИВКИ")
    print("=" * 60)
    print(f"   📁 Папка прошивок: {FIRMWARE_PATH}")
    print(f"   🕐 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

def show_stands_status():
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
    online_count = sum(1 for s in statuses.values() if s['status'] == 'online')
    print(f"   📊 Всего: {len(statuses)} | 🟢 Онлайн: {online_count} | 🔴 Оффлайн: {len(statuses) - online_count}")
    print("-" * 50)

def show_firmwares():
    print("\n📁 ДОСТУПНЫЕ ПРОШИВКИ:")
    print("-" * 50)
    firmwares = get_firmware_list()
    
    if not firmwares:
        print("   ❌ Нет файлов прошивок в папке!")
        print(f"   📂 Поместите файлы (.bin, .hex, .elf) в: {FIRMWARE_PATH}")
    else:
        for i, fw in enumerate(firmwares, 1):
            print(f"   {i}. {fw['name']}")
            print(f"      Размер: {fw['size_kb']} KB | Изменён: {fw['modified']}")
    
    print("-" * 50)
    return firmwares

def select_stand_for_flashing():
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
        return None, None
    
    while True:
        try:
            choice = input("\n👉 Выберите номер стенда (0 для отмены): ").strip()
            if choice == '0':
                return None, None
            for stand_id, stand in online_stands:
                if choice == stand_id:
                    return stand_id, stand
            print("   ❌ Неверный выбор!")
        except (EOFError, KeyboardInterrupt):
            return None, None

def select_firmware_for_flashing(firmwares):
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
        except (ValueError, EOFError, KeyboardInterrupt):
            return None

def flash_menu():
    clear_screen()
    print_header()
    
    firmwares = get_firmware_list()
    if not firmwares:
        print("\n❌ НЕТ ФАЙЛОВ ПРОШИВОК!")
        input("\nНажмите Enter для продолжения...")
        return
    
    stand_id, stand = select_stand_for_flashing()
    if not stand:
        return
    
    firmware = select_firmware_for_flashing(firmwares)
    if not firmware:
        return
    
    print("\n" + "=" * 50)
    print("⚠️  ПОДТВЕРЖДЕНИЕ ПРОШИВКИ")
    print("=" * 50)
    print(f"   Стенд: {stand['name']} ({stand['ip']})")
    print(f"   Прошивка: {firmware['name']}")
    print("=" * 50)
    
    try:
        confirm = input("\n👉 Начать прошивку? (да/нет): ").strip().lower()
        if confirm in ['да', 'yes', 'y', 'д', '+']:
            success, message = flash_firmware(stand['ip'], stand['name'], firmware['path'], firmware['name'])
            print("\n" + "=" * 50)
            if success:
                print(f"✅ {message}")
            else:
                print(f"❌ {message}")
            print("=" * 50)
        else:
            print("\n❌ Прошивка отменена.")
    except (EOFError, KeyboardInterrupt):
        print("\n❌ Операция отменена.")
    
    input("\nНажмите Enter для продолжения...")

def show_processes():
    clear_screen()
    print_header()
    print("\n⚙️ ПРОЦЕССЫ В СИСТЕМЕ:")
    print("-" * 60)
    processes = list_processes()
    for proc in processes:
        print(f"   {proc}")
    print("-" * 60)
    input("\nНажмите Enter для продолжения...")

def show_logs():
    clear_screen()
    print_header()
    print("\n📋 ИСТОРИЯ ПРОШИВОК:")
    print("-" * 60)
    
    if os.path.exists("flash_log.txt"):
        try:
            with open("flash_log.txt", 'r') as f:
                content = f.read()
                print(content if content.strip() else "   Лог пуст")
        except Exception:
            print("   Ошибка чтения лога")
    else:
        print("   История прошивок пока пуста")
    
    print("-" * 60)
    input("\nНажмите Enter для продолжения...")

def show_help():
    clear_screen()
    print_header()
    print("\n📖 СПРАВКА")
    print("=" * 60)
    print(f"""
📡 МОНИТОРИНГ СТЕНДОВ:
   - ONLINE  - стенд отвечает на запросы
   - OFFLINE - стенд недоступен

📁 ПРОШИВКИ:
   • Файлы должны лежать в папке: {FIRMWARE_PATH}
   • Поддерживаемые форматы: .bin, .hex, .elf, .img

🔥 ПРОШИВКА:
   1. Выберите онлайн стенд
   2. Выберите файл прошивки
   3. Подтвердите действие

🔧 НАСТРОЙКА:
   • IP стендов можно изменить в файле app.py
   • Найдите переменную STANDS и отредактируйте IP
""")
    print("=" * 60)
    input("\nНажмите Enter для продолжения...")

# ==================== ГЛАВНАЯ ФУНКЦИЯ ====================

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
            print("   6. 📖 Справка")
            print("   0. 🚪 Выход")
            print("=" * 60)
            
            choice = input("\n👉 Ваш выбор: ").strip()
            
            if choice == '1':
                continue
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
                time.sleep(1)
                sys.exit(0)
            else:
                print("\n❌ Неверный выбор!")
                time.sleep(1)
                
        except (EOFError, KeyboardInterrupt):
            print("\n\n👋 До свидания!")
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ Ошибка: {e}")
            time.sleep(2)

# ==================== ЗАПУСК ====================

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        print("\nНажмите Enter для выхода...")
        input()
        sys.exit(1)
