import tkinter as tk
from tkinter import ttk, messagebox
import json
import sys
import os
from datetime import datetime
from database import Database
from cvs_manager import CVSManager, CVSControlPanel
from orangepi_module import OrangePiDetector, OrangePiFrame

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

class StandsMonitor:
    def __init__(self):
        log_to_file("Инициализация StandsMonitor")
        self.stands = {
            "192.168.243.248": {
                "name": "ГОЗ",
                "abbr": "ГОЗ",
                "devices": ["С1М", "АРКТИКА"],
                "components": {
                    "EPBA": ["v0020-28", "v0020"],
                    "KC": ["1465b3ed", "mpo_mzur"]
                },
                "directory": ["EPBA", "CVS", "mpo", "KC", "SA", "72v6", "INI"]
            },
            "192.168.243.249": {
                "name": "Арктика",
                "abbr": "АРКТИКА",
                "devices": ["ГОЗ", "С1М"],
                "components": {
                    "EPBA": ["v0020"],
                    "KC": ["mpo_mzur"]
                },
                "directory": ["EPBA", "CVS", "mpo", "KC", "SA", "72v6", "INI"]
            },
            "192.168.243.254": {
                "name": "С1М",
                "abbr": "С1М",
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
        log_to_file("StandsMonitor инициализирован успешно")

class MainApplication:
    def __init__(self, root):
        log_to_file("=" * 50)
        log_to_file("Запуск приложения")
        
        self.root = root
        self.root.title("Мониторинг стендов")
        self.root.geometry("1200x800")
        
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
        self.cvs_manager = CVSManager(ssh_user="pkrv", ssh_password="zxcv")
        
        # Показываем окно авторизации
        self.show_login()
    
    def show_login(self):
        log_to_file("Отображение окна авторизации")
        for widget in self.root.winfo_children():
            widget.destroy()
        
        login_frame = ttk.Frame(self.root, padding="20")
        login_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        ttk.Label(login_frame, text="Авторизация", font=("Arial", 16)).grid(row=0, column=0, columnspan=2, pady=10)
        
        ttk.Label(login_frame, text="Логин:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
        self.username_entry = ttk.Entry(login_frame, width=30)
        self.username_entry.grid(row=1, column=1, padx=10, pady=5)
        
        ttk.Label(login_frame, text="Пароль:").grid(row=2, column=0, padx=10, pady=5, sticky="e")
        self.password_entry = ttk.Entry(login_frame, show="*", width=30)
        self.password_entry.grid(row=2, column=1, padx=10, pady=5)
        
        ttk.Button(login_frame, text="Войти", command=self.login).grid(row=3, column=0, pady=10)
        ttk.Button(login_frame, text="Зарегистрироваться", command=self.register).grid(row=3, column=1, pady=10)
    
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
                messagebox.showinfo("Успех", "Вход выполнен успешно!")
                self.show_main_interface()
            else:
                log_to_file(f"Неудачная попытка входа: '{username}' - неверные учетные данные")
                messagebox.showerror("Ошибка", "Неверные логин или пароль")
        except Exception as e:
            log_to_file(f"ОШИБКА при входе: {e}")
            messagebox.showerror("Ошибка", f"Произошла ошибка при входе:\n{e}")
    
    def register(self):
        username = self.username_entry.get()
        log_to_file(f"Попытка регистрации: '{username}'")
        password = self.password_entry.get()
        
        try:
            if self.db.add_user(username, password):
                log_to_file(f"Успешная регистрация: '{username}'")
                messagebox.showinfo("Успех", "Пользователь зарегистрирован!")
            else:
                log_to_file(f"Ошибка регистрации: пользователь '{username}' уже существует")
                messagebox.showerror("Ошибка", "Пользователь уже существует")
        except Exception as e:
            log_to_file(f"ОШИБКА при регистрации: {e}")
            messagebox.showerror("Ошибка", f"Произошла ошибка при регистрации:\n{e}")
    
    def show_main_interface(self):
        log_to_file("Отображение главного интерфейса")
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Панель инструментов
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        ttk.Button(toolbar, text="История входов", command=self.show_history).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Выйти", command=self.logout).pack(side=tk.RIGHT, padx=5)
        
        # Notebook для вкладок
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Вкладки для стендов
        self.create_stand_tab(notebook, "192.168.243.248", "ГОЗ")
        self.create_stand_tab(notebook, "192.168.243.249", "Арктика")
        self.create_stand_tab(notebook, "192.168.243.254", "С1М")
        
        # Вкладка систем и режимов
        self.create_systems_tab(notebook)
        
        # Вкладка Orange Pi
        orangepi_frame = OrangePiFrame(notebook)
        notebook.add(orangepi_frame, text="🍊 Orange Pi")
        
        log_to_file("Главный интерфейс отображен успешно")
    
    def create_stand_tab(self, notebook, ip, name):
        log_to_file(f"Создание вкладки стенда: {name} ({ip})")
        stand_data = self.stands_monitor.stands[ip]
        
        # Основной фрейм с прокруткой
        canvas = tk.Canvas(notebook)
        scrollbar = ttk.Scrollbar(notebook, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        notebook.add(canvas, text=f"{name} ({ip})")
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Заголовок
        ttk.Label(scrollable_frame, text=f"Стенд {name}", font=("Arial", 14, "bold")).pack(pady=10)
        ttk.Label(scrollable_frame, text=f"IP: {ip}").pack()
        
        # Связанные устройства
        if stand_data["devices"]:
            devices_frame = ttk.LabelFrame(scrollable_frame, text="Связанные устройства", padding=10)
            devices_frame.pack(fill=tk.X, padx=10, pady=5)
            
            devices_text = ", ".join(stand_data["devices"])
            ttk.Label(devices_frame, text=devices_text).pack(anchor=tk.W)
        
        # Компоненты
        if stand_data["components"]:
            components_frame = ttk.LabelFrame(scrollable_frame, text="Компоненты", padding=10)
            components_frame.pack(fill=tk.X, padx=10, pady=5)
            
            for component, versions in stand_data["components"].items():
                versions_text = ", ".join(versions)
                ttk.Label(components_frame, text=f"{component}: {versions_text}").pack(anchor=tk.W)
        
        # Директория
        if stand_data["directory"]:
            dir_frame = ttk.LabelFrame(scrollable_frame, text="Директория бинарников", padding=10)
            dir_frame.pack(fill=tk.X, padx=10, pady=5)
            
            dir_text = " → ".join(stand_data["directory"])
            ttk.Label(dir_frame, text=dir_text).pack(anchor=tk.W)
        
        # Блок управления ЦВС
        cvs_panel = CVSControlPanel(scrollable_frame, self.cvs_manager, ip, name)
        cvs_panel.pack(fill=tk.X, padx=10, pady=10)
        
        # Кнопка конфигурации
        ttk.Button(scrollable_frame, text="СКОНФИГУРИРОВАТЬ СТЕНД", 
                  command=lambda s=name: self.configure_stand(s)).pack(pady=10)
    
    def create_systems_tab(self, notebook):
        log_to_file("Создание вкладки систем и режимов")
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Системы и режимы")
        
        # Левая часть - системы
        left_frame = ttk.LabelFrame(frame, text="Системы", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        for system in self.stands_monitor.systems:
            ttk.Label(left_frame, text=f"• {system}").pack(anchor=tk.W, pady=2)
        
        # Средняя часть - режимы
        middle_frame = ttk.LabelFrame(frame, text="Режимы", padding=10)
        middle_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        for mode in self.stands_monitor.modes:
            ttk.Label(middle_frame, text=f"• {mode}").pack(anchor=tk.W, pady=2)
        
        # Правая часть - протоколы
        right_frame = ttk.LabelFrame(frame, text="Протоколы и ВКП", padding=10)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        for protocol in self.stands_monitor.protocols:
            ttk.Label(right_frame, text=f"• {protocol}").pack(anchor=tk.W, pady=2)
        
        # Кнопка конфигурации БМ
        ttk.Button(frame, text="СКОНФИГУРИРОВАТЬ БМ", 
                  command=self.configure_bm).pack(pady=10)
    
    def configure_stand(self, stand_name):
        log_to_file(f"Нажата кнопка конфигурации стенда: {stand_name}")
        messagebox.showinfo("Конфигурация", f"Конфигурация стенда {stand_name}")
    
    def configure_bm(self):
        log_to_file("Нажата кнопка конфигурации БМ")
        messagebox.showinfo("Конфигурация", "Конфигурация БМ")
    
    def show_history(self):
        if self.current_user_id:
            log_to_file(f"Просмотр истории входов для пользователя ID: {self.current_user_id}")
            history_window = tk.Toplevel(self.root)
            history_window.title("История входов")
            history_window.geometry("400x300")
            
            history = self.db.get_login_history(self.current_user_id)
            
            ttk.Label(history_window, text="История входов:", font=("Arial", 12)).pack(pady=10)
            
            frame = ttk.Frame(history_window)
            frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            for i, (login_time,) in enumerate(history):
                ttk.Label(frame, text=f"{i+1}. {login_time}").pack(anchor=tk.W, pady=2)
    
    def logout(self):
        log_to_file("Выход из системы")
        self.current_user_id = None
        self.show_login()

# Запуск приложения
if __name__ == "__main__":
    try:
        log_to_file("=" * 50)
        log_to_file("ЗАПУСК ПРИЛОЖЕНИЯ")
        log_to_file(f"Python версия: {sys.version}")
        log_to_file(f"Рабочая директория: {os.getcwd()}")
        
        root = tk.Tk()
        app = MainApplication(root)
        log_to_file("Приложение запущено, вход в mainloop")
        root.mainloop()
        log_to_file("Приложение закрыто нормально")
        
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
