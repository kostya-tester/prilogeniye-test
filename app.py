import tkinter as tk
from tkinter import ttk, messagebox
import json
import sys
import os
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
        log_to_file("Запуск MainApplication")
        
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
        
        # Сразу показываем главный интерфейс со вкладками
        self.show_main_interface()
    
    def show_login(self):
        """Показать окно авторизации (если нужно)"""
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
                self.show_main_interface()  # ← Открываем ГЛАВНЫЙ интерфейс
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
        
        # Очищаем окно
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Верхняя панель с кнопками
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        ttk.Label(toolbar, text="МОНИТОРИНГ СТЕНДОВ", font=("Arial", 12, "bold")).pack(side=tk.LEFT, padx=10)
        ttk.Button(toolbar, text="История входов", command=self.show_history).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Выйти", command=self.logout).pack(side=tk.RIGHT, padx=5)
        
        # Вкладки стендов
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Создаем вкладки
        self.create_stand_tab(notebook, "192.168.243.248", "ГОЗ")
        self.create_stand_tab(notebook, "192.168.243.249", "Арктика")
        self.create_stand_tab(notebook, "192.168.243.254", "С1М")
        self.create_systems_tab(notebook)
        
        log_to_file("Главный интерфейс отображен")
    
    def create_stand_tab(self, notebook, ip, name):
        log_to_file(f"Создание вкладки: {name} ({ip})")
        stand_data = self.stands_monitor.stands[ip]
        frame = ttk.Frame(notebook)
        notebook.add(frame, text=f"{name} ({ip})")
        
        # Заголовок
        header_frame = ttk.Frame(frame)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(header_frame, text=f"Стенд: {name}", font=("Arial", 16, "bold")).pack()
        ttk.Label(header_frame, text=f"IP: {ip}", font=("Arial", 10)).pack()
        
        # Связанные устройства
        if stand_data["devices"]:
            devices_frame = ttk.LabelFrame(frame, text="Связанные устройства", padding=10)
            devices_frame.pack(fill=tk.X, padx=10, pady=5)
            devices_text = ", ".join(stand_data["devices"])
            ttk.Label(devices_frame, text=devices_text, font=("Arial", 11)).pack(anchor=tk.W)
        
        # Компоненты
        if stand_data["components"]:
            components_frame = ttk.LabelFrame(frame, text="Компоненты", padding=10)
            components_frame.pack(fill=tk.X, padx=10, pady=5)
            for component, versions in stand_data["components"].items():
                versions_text = ", ".join(versions)
                ttk.Label(components_frame, text=f"{component}: {versions_text}").pack(anchor=tk.W)
        
        # Директория
        if stand_data["directory"]:
            dir_frame = ttk.LabelFrame(frame, text="Директория бинарников", padding=10)
            dir_frame.pack(fill=tk.X, padx=10, pady=5)
            dir_text = " → ".join(stand_data["directory"])
            ttk.Label(dir_frame, text=dir_text).pack(anchor=tk.W)
        
        # Кнопка конфигурации
        ttk.Button(frame, text="СКОНФИГУРИРОВАТЬ СТЕНД", 
                  command=lambda s=name: self.configure_stand(s)).pack(pady=15)
    
    def create_systems_tab(self, notebook):
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
            history_window.title("История входов")
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
