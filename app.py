import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import sys
import os
import socket
import paramiko
from datetime import datetime
from database import Database

# Функция для логирования
def log_to_file(message):
    """Запись сообщения в файл 1.txt"""
    try:
        log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "1.txt")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
    except Exception as e:
        print(f"Ошибка записи в лог: {e}")

class StandInfo:
    """Класс для хранения информации о стенде"""
    def __init__(self, ip, name, devices, components, directory):
        self.ip = ip
        self.name = name
        self.devices = devices
        self.components = components
        self.directory = directory
        self.ssh = None
        self.sftp = None

class StandsMonitor:
    def __init__(self):
        log_to_file("Инициализация StandsMonitor")
        self.stands_data = {
            "192.168.243.248": {
                "name": "ГОЗ",
                "devices": ["С1М", "АРКТИКА"],
                "components": {
                    "EPBA": ["v0020-28", "v0020"],
                    "KC": ["1465b3ed", "mpo_mzur"]
                },
                "directory": ["EPBA", "CVS", "mpo", "KC", "SA", "72v6", "INI"]
            },
            "192.168.243.249": {
                "name": "Арктика",
                "devices": ["ГОЗ", "С1М"],
                "components": {
                    "EPBA": ["v0020"],
                    "KC": ["mpo_mzur"]
                },
                "directory": ["EPBA", "CVS", "mpo", "KC", "SA", "72v6", "INI"]
            },
            "192.168.243.254": {
                "name": "С1М",
                "devices": ["ГОЗ", "АРКТИКА"],
                "components": {
                    "EPBA": ["v0020"],
                    "KC": ["mpo_mzur"]
                },
                "directory": ["EPBA", "CVS", "mpo_mzur", "SA", "72v6", "INI", "Dev1", "Dev2", "Dev3"]
            }
        }
        
        self.systems = ["СОЦ", "МРЛС", "АКСС", "и т.д."]
        self.modes = ["Море", "КББ", "и т.д."]
        self.protocols = ["ВБП", "ВКП", "С400", "С400 IP", "СКВП", "ЦВО", "ЦВО IP", "РЛС", "Протокол ТМ 23"]
        
        # SSH данные
        self.ssh_user = "pkrv"
        self.ssh_password = "zxcv"
        log_to_file("StandsMonitor инициализирован успешно")
    
    def check_stand_availability(self, ip, port=22, timeout=2):
        """Проверка доступности стенда по SSH"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((ip, port))
            sock.close()
            return result == 0
        except Exception as e:
            log_to_file(f"Ошибка проверки доступности {ip}: {e}")
            return False
    
    def connect_ssh(self, ip):
        """Подключение к стенду по SSH"""
        try:
            log_to_file(f"Подключение SSH к {ip} с логином {self.ssh_user}")
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(ip, username=self.ssh_user, password=self.ssh_password, timeout=5)
            sftp = ssh.open_sftp()
            log_to_file(f"SSH подключение к {ip} успешно")
            return ssh, sftp
        except Exception as e:
            log_to_file(f"Ошибка SSH подключения к {ip}: {e}")
            return None, None
    
    def upload_file(self, sftp, local_path, remote_path="/home/pkrv/CVS/"):
        """Загрузка файла на стенд"""
        try:
            filename = os.path.basename(local_path)
            remote_full_path = os.path.join(remote_path, filename).replace("\\", "/")
            log_to_file(f"Загрузка файла {filename} на {remote_full_path}")
            sftp.put(local_path, remote_full_path)
            log_to_file(f"Файл {filename} успешно загружен")
            return True, remote_full_path
        except Exception as e:
            log_to_file(f"Ошибка загрузки файла: {e}")
            return False, str(e)
    
    def execute_flash_commands(self, ssh, remote_path=""):
        """Выполнение команд прошивки"""
        try:
            commands = [
                "cd /home/pkrv/CVS",
                "ln -sf mpo 1po2_1n"
            ]
            if remote_path:
                commands.append(f"ln -sf {os.path.basename(remote_path)} mpo")
            
            for cmd in commands:
                log_to_file(f"Выполнение команды: {cmd}")
                stdin, stdout, stderr = ssh.exec_command(cmd)
                output = stdout.read().decode()
                error = stderr.read().decode()
                if output:
                    log_to_file(f"Вывод: {output}")
                if error:
                    log_to_file(f"Ошибка: {error}")
            
            return True
        except Exception as e:
            log_to_file(f"Ошибка выполнения команд прошивки: {e}")
            return False

class MainApplication:
    def __init__(self, root):
        log_to_file("=" * 50)
        log_to_file("Запуск MainApplication")
        
        self.root = root
        self.root.title("Мониторинг стендов - НПО ПКРВ")
        self.root.geometry("1200x800")
        
        # Добавляем иконку/лого (если есть файл)
        try:
            logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")
            if os.path.exists(logo_path):
                self.logo_img = tk.PhotoImage(file=logo_path)
                self.root.iconphoto(True, self.logo_img)
        except:
            pass
        
        try:
            log_to_file("Подключение к базе данных...")
            self.db = Database()
            log_to_file("База данных подключена успешно")
        except Exception as e:
            log_to_file(f"ОШИБКА подключения к БД: {e}")
            messagebox.showerror("Ошибка", f"Не удалось подключиться к базе данных:\n{e}")
            raise
        
        self.stands_monitor = StandsMonitor()
        self.current_user_id = None
        self.active_ssh_connections = {}
        
        # Показываем окно авторизации
        self.show_login()
    
    def show_login(self):
        """Показать окно авторизации"""
        log_to_file("Отображение окна авторизации")
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Основной контейнер
        main_frame = ttk.Frame(self.root)
        main_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # Логотип НПО ПКРВ
        logo_frame = ttk.Frame(main_frame)
        logo_frame.pack(pady=20)
        
        ttk.Label(logo_frame, text="НПО ПКРВ", font=("Arial", 24, "bold"), foreground="darkblue").pack()
        ttk.Label(logo_frame, text="Научно-производственное объединение", font=("Arial", 10)).pack()
        ttk.Label(logo_frame, text="_______________________", font=("Arial", 8)).pack(pady=5)
        
        # Фрейм для авторизации
        login_frame = ttk.LabelFrame(main_frame, text="Авторизация", padding=20)
        login_frame.pack(pady=20)
        
        ttk.Label(login_frame, text="Логин:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
        self.username_entry = ttk.Entry(login_frame, width=30)
        self.username_entry.grid(row=0, column=1, padx=10, pady=5)
        
        ttk.Label(login_frame, text="Пароль:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
        self.password_entry = ttk.Entry(login_frame, show="*", width=30)
        self.password_entry.grid(row=1, column=1, padx=10, pady=5)
        
        buttons_frame = ttk.Frame(login_frame)
        buttons_frame.grid(row=2, column=0, columnspan=2, pady=20)
        
        ttk.Button(buttons_frame, text="Войти", command=self.login).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Зарегистрироваться", command=self.register).pack(side=tk.LEFT, padx=5)
    
    def login(self):
        username = self.username_entry.get()
        log_to_file(f"Попытка входа: пользователь '{username}'")
        password = self.password_entry.get()
        
        try:
            user_id = self.db.check_credentials(username, password)
            if user_id:
                self.current_user_id = user_id
                self.db.log_login(user_id)
                log_to_file(f"Успешный вход: пользователь '{username}' (ID: {user_id})")
                messagebox.showinfo("Успех", f"Добро пожаловать, {username}!")
                self.show_main_interface()
            else:
                log_to_file(f"Неудачная попытка входа: '{username}'")
                messagebox.showerror("Ошибка", "Неверные логин или пароль")
        except Exception as e:
            log_to_file(f"ОШИБКА при входе: {e}")
            messagebox.showerror("Ошибка", f"Произошла ошибка:\n{e}")
    
    def register(self):
        username = self.username_entry.get()
        log_to_file(f"Попытка регистрации: '{username}'")
        password = self.password_entry.get()
        
        try:
            if self.db.add_user(username, password):
                log_to_file(f"Успешная регистрация: '{username}'")
                messagebox.showinfo("Успех", "Пользователь зарегистрирован!")
            else:
                log_to_file(f"Ошибка регистрации: '{username}' уже существует")
                messagebox.showerror("Ошибка", "Пользователь уже существует")
        except Exception as e:
            log_to_file(f"ОШИБКА при регистрации: {e}")
            messagebox.showerror("Ошибка", f"Произошла ошибка:\n{e}")
    
    def show_main_interface(self):
        """Показать главный интерфейс с вкладками стендов"""
        log_to_file("Отображение главного интерфейса со стендами")
        
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Верхняя панель
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        # Лого в тулбаре
        ttk.Label(toolbar, text="НПО ПКРВ", font=("Arial", 12, "bold"), 
                 foreground="darkblue").pack(side=tk.LEFT, padx=10)
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        ttk.Label(toolbar, text="МОНИТОРИНГ СТЕНДОВ", font=("Arial", 12, "bold")).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(toolbar, text="История входов", command=self.show_history).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Выйти", command=self.logout).pack(side=tk.RIGHT, padx=5)
        
        # Вкладки стендов
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Проверяем доступность стендов и создаем вкладки
        available_stands = self.check_all_stands()
        
        if not available_stands:
            # Если нет доступных стендов
            empty_frame = ttk.Frame(notebook)
            notebook.add(empty_frame, text="Стенды")
            ttk.Label(empty_frame, text="Нет доступных стендов", 
                     font=("Arial", 14)).pack(expand=True)
            ttk.Label(empty_frame, text="Включите стенды и перезапустите приложение", 
                     font=("Arial", 12), foreground="red").pack(pady=10)
        
        for ip, data in available_stands.items():
            self.create_stand_tab(notebook, ip, data)
        
        # Вкладка систем и режимов
        self.create_systems_tab(notebook)
        
        log_to_file("Главный интерфейс отображен")
    
    def check_all_stands(self):
        """Проверка доступности всех стендов"""
        available = {}
        for ip, data in self.stands_monitor.stands_data.items():
            if self.stands_monitor.check_stand_availability(ip):
                available[ip] = data
                log_to_file(f"Стенд {data['name']} ({ip}) доступен")
            else:
                log_to_file(f"Стенд {data['name']} ({ip}) недоступен")
        return available
    
    def create_stand_tab(self, notebook, ip, data):
        """Создание вкладки стенда"""
        name = data["name"]
        log_to_file(f"Создание вкладки: {name} ({ip})")
        
        frame = ttk.Frame(notebook)
        notebook.add(frame, text=f"{name} ({ip})")
        
        # Заголовок
        header_frame = ttk.Frame(frame)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(header_frame, text=f"Стенд: {name}", font=("Arial", 16, "bold")).pack()
        ttk.Label(header_frame, text=f"IP: {ip}", font=("Arial", 10)).pack()
        
        # Статус подключения
        status_frame = ttk.Frame(header_frame)
        status_frame.pack(pady=5)
        
        status_label = ttk.Label(status_frame, text="● Подключен", foreground="green", font=("Arial", 10))
        status_label.pack()
        
        # Связанные устройства
        if data.get("devices"):
            devices_frame = ttk.LabelFrame(frame, text="Связанные устройства", padding=10)
            devices_frame.pack(fill=tk.X, padx=10, pady=5)
            devices_text = ", ".join(data["devices"])
            ttk.Label(devices_frame, text=devices_text, font=("Arial", 11)).pack(anchor=tk.W)
        
        # Компоненты
        if data.get("components"):
            components_frame = ttk.LabelFrame(frame, text="Компоненты", padding=10)
            components_frame.pack(fill=tk.X, padx=10, pady=5)
            for component, versions in data["components"].items():
                versions_text = ", ".join(versions)
                ttk.Label(components_frame, text=f"{component}: {versions_text}").pack(anchor=tk.W)
        
        # Директория
        if data.get("directory"):
            dir_frame = ttk.LabelFrame(frame, text="Директория бинарников", padding=10)
            dir_frame.pack(fill=tk.X, padx=10, pady=5)
            dir_text = " → ".join(data["directory"])
            ttk.Label(dir_frame, text=dir_text).pack(anchor=tk.W)
        
        # SSH управление файлами
        ssh_frame = ttk.LabelFrame(frame, text="Управление файлами (SSH)", padding=10)
        ssh_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(ssh_frame, text=f"SSH: pkrv@{ip}").pack(anchor=tk.W)
        ttk.Label(ssh_frame, text="Директория: /home/pkrv/CVS").pack(anchor=tk.W)
        
        # Кнопки управления
        buttons_frame = ttk.Frame(ssh_frame)
        buttons_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(buttons_frame, text="Загрузить файл", 
                  command=lambda: self.upload_file_to_stand(ip, name)).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(buttons_frame, text="Прошить (ln -sf mpo 1po2_1n)", 
                  command=lambda: self.flash_stand(ip, name)).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(buttons_frame, text="Выбрать файл и прошить", 
                  command=lambda: self.select_and_flash(ip, name)).pack(side=tk.LEFT, padx=5)
        
        # Кнопка конфигурации стенда
        ttk.Button(frame, text="СКОНФИГУРИРОВАТЬ СТЕНД", 
                  command=lambda s=name: self.configure_stand(s)).pack(pady=15)
    
    def upload_file_to_stand(self, ip, stand_name):
        """Загрузка файла на стенд"""
        log_to_file(f"Загрузка файла на стенд {stand_name} ({ip})")
        
        # Выбор файла
        file_path = filedialog.askopenfilename(
            title=f"Выберите файл для загрузки на {stand_name}",
            filetypes=[("Все файлы", "*.*"), ("Бинарные файлы", "*.bin"), ("Прошивки", "*.fw")]
        )
        
        if not file_path:
            return
        
        # Подключение SSH
        ssh, sftp = self.stands_monitor.connect_ssh(ip)
        if not ssh or not sftp:
            messagebox.showerror("Ошибка", f"Не удалось подключиться к стенду {stand_name}")
            return
        
        # Загрузка файла
        success, result = self.stands_monitor.upload_file(sftp, file_path)
        
        if success:
            messagebox.showinfo("Успех", f"Файл успешно загружен на стенд {stand_name}")
        else:
            messagebox.showerror("Ошибка", f"Ошибка загрузки файла:\n{result}")
        
        # Закрытие подключения
        sftp.close()
        ssh.close()
    
    def flash_stand(self, ip, stand_name):
        """Прошивка стенда"""
        log_to_file(f"Прошивка стенда {stand_name} ({ip})")
        
        # Подключение SSH
        ssh, sftp = self.stands_monitor.connect_ssh(ip)
        if not ssh or not sftp:
            messagebox.showerror("Ошибка", f"Не удалось подключиться к стенду {stand_name}")
            return
        
        # Выполнение команд прошивки
        if self.stands_monitor.execute_flash_commands(ssh):
            messagebox.showinfo("Успех", f"Команды прошивки выполнены на стенде {stand_name}\nln -sf mpo 1po2_1n")
        else:
            messagebox.showerror("Ошибка", "Ошибка выполнения команд прошивки")
        
        # Закрытие подключения
        sftp.close()
        ssh.close()
    
    def select_and_flash(self, ip, stand_name):
        """Выбор файла и прошивка"""
        log_to_file(f"Выбор файла и прошивка стенда {stand_name} ({ip})")
        
        # Выбор файла
        file_path = filedialog.askopenfilename(
            title=f"Выберите файл для загрузки и прошивки {stand_name}",
            filetypes=[("Все файлы", "*.*"), ("Бинарные файлы", "*.bin"), ("Прошивки", "*.fw")]
        )
        
        if not file_path:
            return
        
        # Подключение SSH
        ssh, sftp = self.stands_monitor.connect_ssh(ip)
        if not ssh or not sftp:
            messagebox.showerror("Ошибка", f"Не удалось подключиться к стенду {stand_name}")
            return
        
        # Загрузка файла
        success, result = self.stands_monitor.upload_file(sftp, file_path)
        
        if not success:
            messagebox.showerror("Ошибка", f"Ошибка загрузки файла:\n{result}")
            sftp.close()
            ssh.close()
            return
        
        # Выполнение команд прошивки
        if self.stands_monitor.execute_flash_commands(ssh, file_path):
            messagebox.showinfo("Успех", 
                f"Файл загружен и команды прошивки выполнены на стенде {stand_name}\nln -sf mpo 1po2_1n")
        else:
            messagebox.showerror("Ошибка", "Файл загружен, но ошибка выполнения команд прошивки")
        
        # Закрытие подключения
        sftp.close()
        ssh.close()
    
    def create_systems_tab(self, notebook):
        """Создание вкладки систем и режимов"""
        log_to_file("Создание вкладки Системы и режимы")
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Системы и режимы")
        
        # Левая колонка - Системы
        left_frame = ttk.LabelFrame(frame, text="Системы", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        for system in self.stands_monitor.systems:
            ttk.Label(left_frame, text=f"• {system}", font=("Arial", 10)).pack(anchor=tk.W, pady=3)
        
        # Средняя колонка - Режимы
        middle_frame = ttk.LabelFrame(frame, text="Режимы", padding=10)
        middle_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        for mode in self.stands_monitor.modes:
            ttk.Label(middle_frame, text=f"• {mode}", font=("Arial", 10)).pack(anchor=tk.W, pady=3)
        
        # Правая колонка - Протоколы
        right_frame = ttk.LabelFrame(frame, text="Протоколы и ВКП", padding=10)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        for protocol in self.stands_monitor.protocols:
            ttk.Label(right_frame, text=f"• {protocol}", font=("Arial", 10)).pack(anchor=tk.W, pady=3)
        
        # Кнопка конфигурации БМ
        ttk.Button(frame, text="СКОНФИГУРИРОВАТЬ БМ", 
                  command=self.configure_bm).pack(pady=15)
    
    def configure_stand(self, stand_name):
        log_to_file(f"Конфигурация стенда: {stand_name}")
        messagebox.showinfo("Конфигурация", f"Запуск конфигурации стенда {stand_name}")
    
    def configure_bm(self):
        log_to_file("Конфигурация БМ")
        messagebox.showinfo("Конфигурация", "Запуск конфигурации БМ")
    
    def show_history(self):
        if self.current_user_id:
            log_to_file(f"Просмотр истории для ID: {self.current_user_id}")
            history_window = tk.Toplevel(self.root)
            history_window.title("История входов - НПО ПКРВ")
            history_window.geometry("400x300")
            
            history = self.db.get_login_history(self.current_user_id)
            
            ttk.Label(history_window, text="История входов:", font=("Arial", 12, "bold")).pack(pady=10)
            frame = ttk.Frame(history_window)
            frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            for i, (login_time,) in enumerate(history):
                ttk.Label(frame, text=f"{i+1}. {login_time}").pack(anchor=tk.W, pady=2)
    
    def logout(self):
        log_to_file("Выход из системы")
        self.current_user_id = None
        # Закрываем все SSH подключения
        for ip, (ssh, sftp) in self.active_ssh_connections.items():
            try:
                sftp.close()
                ssh.close()
                log_to_file(f"SSH подключение к {ip} закрыто")
            except:
                pass
        self.active_ssh_connections.clear()
        self.show_login()

# Запуск приложения
if __name__ == "__main__":
    try:
        log_to_file("=" * 50)
        log_to_file("ЗАПУСК ПРИЛОЖЕНИЯ")
        log_to_file(f"Python версия: {sys.version}")
        log_to_file(f"Рабочая директория: {os.getcwd()}")
        
        # Проверка наличия paramiko
        try:
            import paramiko
            log_to_file("Paramiko доступен")
        except ImportError:
            log_to_file("Paramiko не установлен!")
            print("Ошибка: модуль paramiko не установлен!")
            print("Установите: pip install paramiko")
            input("\nНажмите Enter для выхода...")
            sys.exit(1)
        
        root = tk.Tk()
        app = MainApplication(root)
        log_to_file("Приложение запущено")
        root.mainloop()
        log_to_file("Приложение закрыто")
        
    except Exception as e:
        import traceback
        error_msg = f"КРИТИЧЕСКАЯ ОШИБКА: {e}\n{traceback.format_exc()}"
        log_to_file(error_msg)
        print(error_msg)
        try:
            from tkinter import messagebox
            messagebox.showerror("Критическая ошибка", f"Произошла ошибка:\n\n{e}\n\nПодробности в файле 1.txt")
        except:
            pass
        input("\nНажмите Enter для выхода...")
