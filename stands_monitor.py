import tkinter as tk
from tkinter import ttk, messagebox
import json
import sys
import os
from datetime import datetime
from database import Database
from cvs_manager import CVSManager, CVSControlPanel
from orangepi_module import OrangePiDetector, OrangePiFrame
from email_notifier import EmailNotifier
from statistics_module import StatisticsManager, ChecksumCalculator

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
        self.root.title("Мониторинг стендов — НПО ПКРВ")
        self.root.geometry("1200x800")
        
        # Применяем тёмную тему
        self.apply_dark_theme()
        
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
        self.current_username = None
        self.cvs_manager = CVSManager(ssh_user="pkrv", ssh_password="zxcv")
        
        # Инициализация почтовых уведомлений
        self.email = EmailNotifier()
        
        # Инициализация статистики
        self.stats = StatisticsManager()
        self.checksum_calc = ChecksumCalculator()
        
        # Показываем окно авторизации
        self.show_login()
    
    def apply_dark_theme(self):
        """Применение тёмной темы"""
        style = ttk.Style()
        style.theme_use('clam')
        
        bg_dark = '#1a1a2e'
        bg_medium = '#16213e'
        bg_light = '#0f3460'
        fg_light = '#e0e0e0'
        fg_accent = '#e94560'
        bg_button = '#0f3460'
        
        style.configure('.',
            background=bg_dark,
            foreground=fg_light,
            fieldbackground=bg_medium,
            borderwidth=1
        )
        
        style.configure('TLabel',
            background=bg_dark,
            foreground=fg_light,
            font=('Arial', 10)
        )
        
        style.configure('Header.TLabel',
            background=bg_dark,
            foreground=fg_accent,
            font=('Arial', 14, 'bold')
        )
        
        style.configure('TFrame', background=bg_dark)
        
        style.configure('TLabelframe',
            background=bg_dark,
            foreground=fg_light,
            borderwidth=1
        )
        
        style.configure('TLabelframe.Label',
            background=bg_dark,
            foreground=fg_accent,
            font=('Arial', 10, 'bold')
        )
        
        style.configure('TButton',
            background=bg_button,
            foreground=fg_light,
            font=('Arial', 9),
            borderwidth=1,
            padding=5
        )
        
        style.map('TButton',
            background=[('active', fg_accent), ('pressed', bg_light)],
            foreground=[('active', 'white')]
        )
        
        style.configure('TNotebook', background=bg_dark, borderwidth=0)
        
        style.configure('TNotebook.Tab',
            background=bg_medium,
            foreground=fg_light,
            padding=[10, 5],
            font=('Arial', 9)
        )
        
        style.map('TNotebook.Tab',
            background=[('selected', bg_light), ('active', fg_accent)],
            foreground=[('selected', 'white')]
        )
        
        style.configure('TEntry',
            fieldbackground=bg_medium,
            foreground=fg_light,
            insertcolor=fg_light
        )
        
        style.configure('Treeview',
            background=bg_medium,
            foreground=fg_light,
            fieldbackground=bg_medium,
            rowheight=25
        )
        
        style.configure('Treeview.Heading',
            background=bg_light,
            foreground=fg_light,
            font=('Arial', 9, 'bold')
        )
        
        style.map('Treeview',
            background=[('selected', fg_accent)],
            foreground=[('selected', 'white')]
        )
        
        self.root.configure(bg=bg_dark)
        
        self.colors = {
            'bg_dark': bg_dark,
            'bg_medium': bg_medium,
            'bg_light': bg_light,
            'fg_light': fg_light,
            'fg_accent': fg_accent,
            'bg_button': bg_button,
            'success': '#4CAF50',
            'warning': '#FF9800',
            'error': '#f44336',
            'info': '#2196F3'
        }
    
    def show_login(self):
        log_to_file("Отображение окна авторизации")
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Центральный контейнер
        container = ttk.Frame(self.root)
        container.place(relx=0.5, rely=0.5, anchor="center")
        
        # Заголовок НПО ПКРВ
        ttk.Label(container, text="НПО ПКРВ", 
                 font=("Arial", 28, "bold"), 
                 foreground=self.colors['fg_accent']).pack(pady=10)
        
        ttk.Label(container, text="Система мониторинга стендов", 
                 font=("Arial", 12),
                 foreground=self.colors['fg_light']).pack(pady=5)
        
        # Фрейм авторизации
        login_frame = ttk.LabelFrame(container, text="Авторизация", padding=20)
        login_frame.pack(pady=20, fill=tk.X)
        
        ttk.Label(login_frame, text="Логин:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
        self.username_entry = ttk.Entry(login_frame, width=30, font=("Arial", 11))
        self.username_entry.grid(row=0, column=1, padx=10, pady=5)
        self.username_entry.focus()
        
        ttk.Label(login_frame, text="Пароль:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
        self.password_entry = ttk.Entry(login_frame, show="*", width=30, font=("Arial", 11))
        self.password_entry.grid(row=1, column=1, padx=10, pady=5)
        self.password_entry.bind("<Return>", lambda e: self.login())
        
        btn_frame = ttk.Frame(login_frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=15)
        
        ttk.Button(btn_frame, text="Войти", command=self.login).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Зарегистрироваться", command=self.register).pack(side=tk.LEFT, padx=5)
    
    def login(self):
        username = self.username_entry.get()
        log_to_file(f"Попытка входа: пользователь '{username}'")
        password = self.password_entry.get()
        
        try:
            user_id = self.db.check_credentials(username, password)
            if user_id:
                self.current_user_id = user_id
                self.current_username = username
                self.db.log_login(user_id)
                log_to_file(f"Успешный вход: '{username}' (ID: {user_id})")
                
                # Отправляем уведомление на почту
                self.email.notify_stand_online(
                    "Система мониторинга",
                    f"Пользователь {username} вошёл в систему"
                )
                
                # Записываем в статистику
                self.stats.add_user_action(username, "Вход в систему")
                
                messagebox.showinfo("Успех", f"Добро пожаловать, {username}!")
                self.show_main_interface()
            else:
                log_to_file(f"Неудачная попытка входа: '{username}'")
                messagebox.showerror("Ошибка", "Неверные логин или пароль")
        except Exception as e:
            log_to_file(f"ОШИБКА при входе: {e}")
            messagebox.showerror("Ошибка", f"Произошла ошибка при входе:\n{e}")
    
    def register(self):
        username = self.username_entry.get()
        log_to_file(f"Попытка регистрации: '{username}'")
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror("Ошибка", "Введите логин и пароль")
            return
        
        try:
            if self.db.add_user(username, password):
                log_to_file(f"Успешная регистрация: '{username}'")
                self.stats.add_user_action(username, "Регистрация")
                messagebox.showinfo("Успех", "Пользователь зарегистрирован!")
            else:
                log_to_file(f"Ошибка регистрации: '{username}' уже существует")
                messagebox.showerror("Ошибка", "Пользователь уже существует")
        except Exception as e:
            log_to_file(f"ОШИБКА при регистрации: {e}")
            messagebox.showerror("Ошибка", f"Произошла ошибка при регистрации:\n{e}")
    
    def show_main_interface(self):
        log_to_file("Отображение главного интерфейса")
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Верхняя панель инструментов
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        # Логотип в тулбаре
        ttk.Label(toolbar, text="НПО ПКРВ", 
                 font=("Arial", 12, "bold"),
                 foreground=self.colors['fg_accent']).pack(side=tk.LEFT, padx=10)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        ttk.Button(toolbar, text="📊 Отчёт", command=self.show_report).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="📧 Почта", command=self.configure_email).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="📋 История", command=self.show_history).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🔑 Выйти", command=self.logout).pack(side=tk.RIGHT, padx=5)
        
        # Notebook для вкладок
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Вкладки стендов
        self.create_stand_tab(notebook, "192.168.243.248", "ГОЗ")
        self.create_stand_tab(notebook, "192.168.243.249", "Арктика")
        self.create_stand_tab(notebook, "192.168.243.254", "С1М")
        
        # Вкладка систем и режимов
        self.create_systems_tab(notebook)
        
        # Вкладка Orange Pi
        orangepi_frame = OrangePiFrame(notebook)
        notebook.add(orangepi_frame, text="🍊 Orange Pi")
        
        # Строка состояния внизу
        status_bar = ttk.Frame(self.root)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        ttk.Label(status_bar, text=f"👤 {self.current_username}", 
                 foreground=self.colors['fg_light']).pack(side=tk.LEFT, padx=10)
        
        ttk.Label(status_bar, text="🟢 Система работает", 
                 foreground="green").pack(side=tk.RIGHT, padx=10)
        
        log_to_file("Главный интерфейс отображен успешно")
    
    def create_stand_tab(self, notebook, ip, name):
        log_to_file(f"Создание вкладки стенда: {name} ({ip})")
        stand_data = self.stands_monitor.stands[ip]
        
        canvas = tk.Canvas(notebook, bg=self.colors['bg_dark'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(notebook, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        notebook.add(canvas, text=f"📡 {name}")
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Заголовок
        ttk.Label(scrollable_frame, text=f"Стенд {name}", 
                 font=("Arial", 14, "bold"), foreground=self.colors['fg_accent']).pack(pady=10)
        ttk.Label(scrollable_frame, text=f"IP: {ip}").pack()
        
        # Связанные устройства
        if stand_data["devices"]:
            devices_frame = ttk.LabelFrame(scrollable_frame, text="Связанные устройства", padding=10)
            devices_frame.pack(fill=tk.X, padx=10, pady=5)
            devices_text = ", ".join(stand_data["devices"])
            ttk.Label(devices_frame, text=devices_text, font=("Arial", 11)).pack(anchor=tk.W)
        
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
        
        # Кнопки
        btn_frame = ttk.Frame(scrollable_frame)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="⚙️ Конфигурировать стенд", 
                  command=lambda s=name: self.configure_stand(s)).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="📊 Статистика стенда", 
                  command=lambda n=name, i=ip: self.show_stand_stats(n, i)).pack(side=tk.LEFT, padx=5)
    
    def create_systems_tab(self, notebook):
        log_to_file("Создание вкладки систем и режимов")
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="⚙️ Системы")
        
        # Левая часть - системы
        left_frame = ttk.LabelFrame(frame, text="Системы", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        for system in self.stands_monitor.systems:
            ttk.Label(left_frame, text=f"• {system}", font=("Arial", 10)).pack(anchor=tk.W, pady=3)
        
        # Средняя часть - режимы
        middle_frame = ttk.LabelFrame(frame, text="Режимы", padding=10)
        middle_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        for mode in self.stands_monitor.modes:
            ttk.Label(middle_frame, text=f"• {mode}", font=("Arial", 10)).pack(anchor=tk.W, pady=3)
        
        # Правая часть - протоколы
        right_frame = ttk.LabelFrame(frame, text="Протоколы и ВКП", padding=10)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        for protocol in self.stands_monitor.protocols:
            ttk.Label(right_frame, text=f"• {protocol}", font=("Arial", 10)).pack(anchor=tk.W, pady=3)
        
        ttk.Button(frame, text="СКОНФИГУРИРОВАТЬ БМ", 
                  command=self.configure_bm).pack(pady=15)
    
    def configure_stand(self, stand_name):
        log_to_file(f"Конфигурация стенда: {stand_name}")
        self.stats.add_user_action(self.current_username, f"Конфигурация стенда {stand_name}")
        messagebox.showinfo("Конфигурация", f"Конфигурация стенда {stand_name}")
    
    def configure_bm(self):
        log_to_file("Конфигурация БМ")
        self.stats.add_user_action(self.current_username, "Конфигурация БМ")
        messagebox.showinfo("Конфигурация", "Конфигурация БМ")
    
    def show_history(self):
        if self.current_user_id:
            log_to_file(f"Просмотр истории для ID: {self.current_user_id}")
            history_window = tk.Toplevel(self.root)
            history_window.title("История входов")
            history_window.geometry("400x300")
            history_window.configure(bg=self.colors['bg_dark'])
            
            history = self.db.get_login_history(self.current_user_id)
            
            ttk.Label(history_window, text="История входов:", font=("Arial", 12, "bold")).pack(pady=10)
            
            frame = ttk.Frame(history_window)
            frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            for i, (login_time,) in enumerate(history):
                ttk.Label(frame, text=f"{i+1}. {login_time}").pack(anchor=tk.W, pady=2)
    
    def show_report(self):
        """Показать отчёт"""
        report = self.stats.generate_report()
        
        report_window = tk.Toplevel(self.root)
        report_window.title("📊 Отчёт о работе стендов")
        report_window.geometry("700x600")
        report_window.configure(bg=self.colors['bg_dark'])
        
        text_frame = ttk.Frame(report_window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        text = tk.Text(text_frame, wrap=tk.WORD, bg=self.colors['bg_medium'], 
                      fg=self.colors['fg_light'], font=("Courier", 10),
                      insertbackground=self.colors['fg_light'])
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(text_frame, command=text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text.config(yscrollcommand=scrollbar.set)
        
        text.insert("1.0", report)
        text.config(state="disabled")
        
        # Кнопка отправки на почту
        ttk.Button(report_window, text="📧 Отправить на почту", 
                  command=lambda: self.email.notify_daily_report(report)
                  ).pack(pady=10)
    
    def show_stand_stats(self, stand_name, ip):
        """Показать статистику конкретного стенда"""
        uptime = self.stats.get_uptime_stats()
        flash = self.stats.get_flash_stats()
        errors = self.stats.get_error_stats()
        
        stats_text = f"=== Статистика стенда {stand_name} ===\n\n"
        
        # Uptime
        if stand_name in uptime:
            u = uptime[stand_name]
            stats_text += f"Время работы: {u['uptime_percent']}%\n"
            stats_text += f"Всего проверок: {u['total_checks']}\n\n"
        
        messagebox.showinfo(f"Статистика {stand_name}", stats_text)
    
    def configure_email(self):
        """Окно настройки почтовых уведомлений"""
        config_window = tk.Toplevel(self.root)
        config_window.title("Настройка почтовых уведомлений")
        config_window.geometry("500x450")
        config_window.configure(bg=self.colors['bg_dark'])
        
        frame = ttk.Frame(config_window, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Настройка Email-уведомлений", 
                 font=("Arial", 14, "bold")).pack(pady=10)
        
        ttk.Label(frame, text="SMTP сервер:").pack(anchor=tk.W)
        smtp_entry = ttk.Entry(frame, width=50)
        smtp_entry.insert(0, self.email.smtp_server)
        smtp_entry.pack(fill=tk.X, pady=2)
        
        ttk.Label(frame, text="Порт:").pack(anchor=tk.W)
        port_entry = ttk.Entry(frame, width=10)
        port_entry.insert(0, str(self.email.smtp_port))
        port_entry.pack(anchor=tk.W, pady=2)
        
        ttk.Label(frame, text="Логин:").pack(anchor=tk.W)
        user_entry = ttk.Entry(frame, width=50)
        user_entry.insert(0, self.email.smtp_user)
        user_entry.pack(fill=tk.X, pady=2)
        
        ttk.Label(frame, text="Пароль (пароль приложения):").pack(anchor=tk.W)
        pass_entry = ttk.Entry(frame, width=50, show="*")
        pass_entry.insert(0, self.email.smtp_password)
        pass_entry.pack(fill=tk.X, pady=2)
        
        ttk.Label(frame, text="Отправитель:").pack(anchor=tk.W)
        from_entry = ttk.Entry(frame, width=50)
        from_entry.insert(0, self.email.from_email)
        from_entry.pack(fill=tk.X, pady=2)
        
        ttk.Label(frame, text="Получатель:").pack(anchor=tk.W)
        to_entry = ttk.Entry(frame, width=50)
        to_entry.insert(0, self.email.to_email)
        to_entry.pack(fill=tk.X, pady=2)
        
        enabled_var = tk.BooleanVar(value=self.email.enabled)
        ttk.Checkbutton(frame, text="Включить уведомления", 
                       variable=enabled_var).pack(anchor=tk.W, pady=10)
        
        def save():
            self.email.smtp_server = smtp_entry.get()
            self.email.smtp_port = int(port_entry.get())
            self.email.smtp_user = user_entry.get()
            self.email.smtp_password = pass_entry.get()
            self.email.from_email = from_entry.get()
            self.email.to_email = to_entry.get()
            self.email.enabled = enabled_var.get()
            self.email.save_settings()
            
            success, msg = self.email.test_connection()
            if success:
                messagebox.showinfo("Успех", f"Настройки сохранены!\n{msg}")
            else:
                messagebox.showwarning("Предупреждение", 
                    f"Настройки сохранены, но подключение не удалось:\n{msg}")
            config_window.destroy()
        
        def test():
            self.email.smtp_server = smtp_entry.get()
            self.email.smtp_port = int(port_entry.get())
            self.email.smtp_user = user_entry.get()
            self.email.smtp_password = pass_entry.get()
            
            success, msg = self.email.test_connection()
            if success:
                messagebox.showinfo("Тест", msg)
            else:
                messagebox.showerror("Ошибка", msg)
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="Тест подключения", command=test).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Сохранить", command=save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Отмена", command=config_window.destroy).pack(side=tk.LEFT, padx=5)
    
    def logout(self):
        log_to_file("Выход из системы")
        self.stats.add_user_action(self.current_username, "Выход из системы")
        self.current_user_id = None
        self.current_username = None
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
