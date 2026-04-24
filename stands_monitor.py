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
                "components": {"EPBA": ["v0020-28", "v0020"], "KC": ["1465b3ed", "mpo_mzur"]},
                "directory": ["EPBA", "CVS", "mpo", "KC", "SA", "72v6", "INI"]
            },
            "192.168.243.249": {
                "name": "Арктика",
                "abbr": "АРКТИКА",
                "devices": ["ГОЗ", "С1М"],
                "components": {"EPBA": ["v0020"], "KC": ["mpo_mzur"]},
                "directory": ["EPBA", "CVS", "mpo", "KC", "SA", "72v6", "INI"]
            },
            "192.168.243.254": {
                "name": "С1М",
                "abbr": "С1М",
                "devices": ["ГОЗ", "АРКТИКА"],
                "components": {"EPBA": ["v0020"], "KC": ["mpo_mzur"]},
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

        # Сразу красим фон
        self.root.configure(bg='#1a1a2e')

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
        self.email = EmailNotifier()
        self.stats = StatisticsManager()
        self.checksum_calc = ChecksumCalculator()

        self.show_login()

    def apply_dark_theme(self):
        """Тёмная тема в стиле мониторинга"""
        style = ttk.Style()
        style.theme_use('clam')

        bg_dark = '#1a1a2e'
        bg_medium = '#16213e'
        bg_light = '#0f3460'
        fg_light = '#e0e0e0'
        fg_accent = '#e94560'
        bg_button = '#0f3460'

        style.configure('.', background=bg_dark, foreground=fg_light, fieldbackground=bg_medium, borderwidth=1)
        style.configure('TLabel', background=bg_dark, foreground=fg_light, font=('Arial', 10))
        style.configure('Header.TLabel', background=bg_dark, foreground=fg_accent, font=('Arial', 14, 'bold'))
        style.configure('TFrame', background=bg_dark)
        style.configure('TLabelframe', background=bg_dark, foreground=fg_light, borderwidth=1)
        style.configure('TLabelframe.Label', background=bg_dark, foreground=fg_accent, font=('Arial', 10, 'bold'))
        style.configure('TButton', background=bg_button, foreground=fg_light, font=('Arial', 9), borderwidth=1, padding=5)
        style.map('TButton', background=[('active', fg_accent), ('pressed', bg_light)], foreground=[('active', 'white')])
        style.configure('TNotebook', background=bg_dark, borderwidth=0)
        style.configure('TNotebook.Tab', background=bg_medium, foreground=fg_light, padding=[10, 5], font=('Arial', 9))
        style.map('TNotebook.Tab', background=[('selected', bg_light), ('active', fg_accent)], foreground=[('selected', 'white')])
        style.configure('TEntry', fieldbackground=bg_medium, foreground=fg_light, insertcolor=fg_light)
        style.configure('Treeview', background=bg_medium, foreground=fg_light, fieldbackground=bg_medium, rowheight=25)
        style.configure('Treeview.Heading', background=bg_light, foreground=fg_light, font=('Arial', 9, 'bold'))
        style.map('Treeview', background=[('selected', fg_accent)], foreground=[('selected', 'white')])
        style.configure('TSeparator', background=fg_accent)

        self.root.configure(bg=bg_dark)

        self.colors = {
            'bg_dark': bg_dark, 'bg_medium': bg_medium, 'bg_light': bg_light,
            'fg_light': fg_light, 'fg_accent': fg_accent, 'bg_button': bg_button,
            'success': '#4CAF50', 'warning': '#FF9800', 'error': '#f44336', 'info': '#2196F3'
        }

    # ==================== АВТОРИЗАЦИЯ ====================

    def show_login(self):
        log_to_file("Отображение окна авторизации")
        for widget in self.root.winfo_children():
            widget.destroy()

        self.root.configure(bg=self.colors['bg_dark'])

        container = ttk.Frame(self.root)
        container.place(relx=0.5, rely=0.5, anchor="center")

        ttk.Label(container, text="НПО ПКРВ", font=("Arial", 28, "bold"),
                 foreground=self.colors['fg_accent']).pack(pady=10)
        ttk.Label(container, text="Система мониторинга стендов",
                 font=("Arial", 12), foreground=self.colors['fg_light']).pack(pady=5)

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
        ttk.Button(btn_frame, text="🔑 Войти", command=self.login).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="📝 Регистрация", command=self.register).pack(side=tk.LEFT, padx=5)

    def login(self):
        username = self.username_entry.get()
        log_to_file(f"Попытка входа: '{username}'")
        password = self.password_entry.get()
        try:
            user_id = self.db.check_credentials(username, password)
            if user_id:
                self.current_user_id = user_id
                self.current_username = username
                self.db.log_login(user_id)
                log_to_file(f"Успешный вход: '{username}'")
                self.email.notify_stand_online("Система мониторинга", f"Пользователь {username} вошёл в систему")
                self.stats.add_user_action(username, "Вход в систему")
                messagebox.showinfo("Успех", f"Добро пожаловать, {username}!")
                self.show_main_interface()
            else:
                log_to_file(f"Неверные данные: '{username}'")
                messagebox.showerror("Ошибка", "Неверные логин или пароль")
        except Exception as e:
            log_to_file(f"ОШИБКА входа: {e}")
            messagebox.showerror("Ошибка", str(e))

    def register(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        if not username or not password:
            messagebox.showerror("Ошибка", "Введите логин и пароль")
            return
        try:
            if self.db.add_user(username, password):
                log_to_file(f"Регистрация: '{username}'")
                self.stats.add_user_action(username, "Регистрация")
                messagebox.showinfo("Успех", "Пользователь зарегистрирован!")
            else:
                messagebox.showerror("Ошибка", "Пользователь уже существует")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def logout(self):
        log_to_file("Выход из системы")
        self.stats.add_user_action(self.current_username, "Выход из системы")
        self.current_user_id = None
        self.current_username = None
        self.show_login()

    # ==================== ГЛАВНЫЙ ИНТЕРФЕЙС ====================

    def show_main_interface(self):
        log_to_file("Отображение главного интерфейса")
        for widget in self.root.winfo_children():
            widget.destroy()

        self.root.configure(bg=self.colors['bg_dark'])

        # Тулбар
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        ttk.Label(toolbar, text="НПО ПКРВ", font=("Arial", 12, "bold"),
                 foreground=self.colors['fg_accent']).pack(side=tk.LEFT, padx=10)
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)

        for text, cmd in [("📊 Отчёт", self.show_report), ("📧 Почта", self.configure_email),
                          ("📋 История", self.show_history)]:
            ttk.Button(toolbar, text=text, command=cmd).pack(side=tk.LEFT, padx=2)

        ttk.Button(toolbar, text="🔑 Выйти", command=self.logout).pack(side=tk.RIGHT, padx=5)

        # Вкладки
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.create_stand_tab(notebook, "192.168.243.248", "ГОЗ")
        self.create_stand_tab(notebook, "192.168.243.249", "Арктика")
        self.create_stand_tab(notebook, "192.168.243.254", "С1М")
        self.create_systems_tab(notebook)

        orangepi_frame = OrangePiFrame(notebook)
        notebook.add(orangepi_frame, text="🍊 Orange Pi")

        # Статус-бар
        status_bar = ttk.Frame(self.root)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        ttk.Label(status_bar, text=f"👤 {self.current_username}",
                 foreground=self.colors['fg_light']).pack(side=tk.LEFT, padx=10)
        ttk.Label(status_bar, text="🟢 Система работает",
                 foreground="green").pack(side=tk.RIGHT, padx=10)

        log_to_file("Главный интерфейс отображен")

    def create_stand_tab(self, notebook, ip, name):
        log_to_file(f"Создание вкладки: {name} ({ip})")
        stand_data = self.stands_monitor.stands[ip]

        # Внешний фрейм
        outer_frame = ttk.Frame(notebook)
        notebook.add(outer_frame, text=f"📡 {name}")

        # Canvas с правильным фоном
        canvas = tk.Canvas(outer_frame, bg=self.colors['bg_dark'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(outer_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        def on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)

        canvas.bind("<Configure>", on_canvas_configure)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Колесо мыши
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", on_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        # Содержимое
        ttk.Label(scrollable_frame, text=f"Стенд {name}", font=("Arial", 14, "bold"),
                 foreground=self.colors['fg_accent']).pack(pady=10)
        ttk.Label(scrollable_frame, text=f"IP: {ip}", font=("Arial", 11)).pack()

        ttk.Separator(scrollable_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=5)

        if stand_data["devices"]:
            f = ttk.LabelFrame(scrollable_frame, text="Связанные устройства", padding=10)
            f.pack(fill=tk.X, padx=10, pady=5)
            ttk.Label(f, text=", ".join(stand_data["devices"]), font=("Arial", 11)).pack(anchor=tk.W)

        if stand_data["components"]:
            f = ttk.LabelFrame(scrollable_frame, text="Компоненты", padding=10)
            f.pack(fill=tk.X, padx=10, pady=5)
            for c, v in stand_data["components"].items():
                ttk.Label(f, text=f"● {c}: {', '.join(v)}").pack(anchor=tk.W, pady=2)

        if stand_data["directory"]:
            f = ttk.LabelFrame(scrollable_frame, text="Директория бинарников", padding=10)
            f.pack(fill=tk.X, padx=10, pady=5)
            ttk.Label(f, text=" → ".join(stand_data["directory"]), font=("Courier", 9)).pack(anchor=tk.W)

        # ЦВС
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
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="⚙️ Системы")

        for title, items in [("Системы", self.stands_monitor.systems),
                             ("Режимы", self.stands_monitor.modes),
                             ("Протоколы и ВКП", self.stands_monitor.protocols)]:
            f = ttk.LabelFrame(frame, text=title, padding=10)
            f.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
            for item in items:
                ttk.Label(f, text=f"• {item}", font=("Arial", 10)).pack(anchor=tk.W, pady=3)

        ttk.Button(frame, text="СКОНФИГУРИРОВАТЬ БМ", command=self.configure_bm).pack(pady=15)

    # ==================== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ====================

    def configure_stand(self, stand_name):
        self.stats.add_user_action(self.current_username, f"Конфигурация стенда {stand_name}")
        messagebox.showinfo("Конфигурация", f"Конфигурация стенда {stand_name}")

    def configure_bm(self):
        self.stats.add_user_action(self.current_username, "Конфигурация БМ")
        messagebox.showinfo("Конфигурация", "Конфигурация БМ")

    def show_history(self):
        if not self.current_user_id:
            return
        hw = tk.Toplevel(self.root)
        hw.title("История входов")
        hw.geometry("400x300")
        hw.configure(bg=self.colors['bg_dark'])
        ttk.Label(hw, text="История входов:", font=("Arial", 12, "bold")).pack(pady=10)
        f = ttk.Frame(hw)
        f.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        for i, (t,) in enumerate(self.db.get_login_history(self.current_user_id)):
            ttk.Label(f, text=f"{i+1}. {t}").pack(anchor=tk.W, pady=2)

    def show_report(self):
        report = self.stats.generate_report()
        rw = tk.Toplevel(self.root)
        rw.title("📊 Отчёт")
        rw.geometry("700x600")
        rw.configure(bg=self.colors['bg_dark'])
        tf = ttk.Frame(rw)
        tf.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        txt = tk.Text(tf, wrap=tk.WORD, bg=self.colors['bg_medium'], fg=self.colors['fg_light'],
                      font=("Courier", 10), insertbackground=self.colors['fg_light'])
        txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb = ttk.Scrollbar(tf, command=txt.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        txt.config(yscrollcommand=sb.set)
        txt.insert("1.0", report)
        txt.config(state="disabled")
        ttk.Button(rw, text="📧 Отправить на почту", command=lambda: self.email.notify_daily_report(report)).pack(pady=10)

    def show_stand_stats(self, stand_name, ip):
        uptime = self.stats.get_uptime_stats()
        txt = f"=== Статистика стенда {stand_name} ===\n\n"
        if stand_name in uptime:
            u = uptime[stand_name]
            txt += f"Время работы: {u['uptime_percent']}%\nВсего проверок: {u['total_checks']}\n"
        messagebox.showinfo(f"Статистика {stand_name}", txt)

    def configure_email(self):
        cw = tk.Toplevel(self.root)
        cw.title("Настройка почты")
        cw.geometry("500x450")
        cw.configure(bg=self.colors['bg_dark'])
        f = ttk.Frame(cw, padding=20)
        f.pack(fill=tk.BOTH, expand=True)
        ttk.Label(f, text="Настройка Email-уведомлений", font=("Arial", 14, "bold")).pack(pady=10)

        entries = {}
        for label, key, show in [("SMTP сервер:", "smtp_server", False), ("Порт:", "smtp_port", False),
                                  ("Логин:", "smtp_user", False), ("Пароль:", "smtp_password", True),
                                  ("Отправитель:", "from_email", False), ("Получатель:", "to_email", False)]:
            ttk.Label(f, text=label).pack(anchor=tk.W)
            e = ttk.Entry(f, width=50, show="*" if show else "")
            e.insert(0, str(getattr(self.email, key)))
            e.pack(fill=tk.X, pady=2)
            entries[key] = e

        enabled_var = tk.BooleanVar(value=self.email.enabled)
        ttk.Checkbutton(f, text="Включить уведомления", variable=enabled_var).pack(anchor=tk.W, pady=10)

        def save():
            for k, e in entries.items():
                setattr(self.email, k, e.get() if k != 'smtp_port' else int(e.get()))
            self.email.enabled = enabled_var.get()
            self.email.save_settings()
            ok, msg = self.email.test_connection()
            (messagebox.showinfo if ok else messagebox.showwarning)("Результат", msg)
            cw.destroy()

        def test():
            for k, e in entries.items():
                setattr(self.email, k, e.get() if k != 'smtp_port' else int(e.get()))
            ok, msg = self.email.test_connection()
            (messagebox.showinfo if ok else messagebox.showerror)("Тест", msg)

        bf = ttk.Frame(f)
        bf.pack(pady=10)
        ttk.Button(bf, text="Тест", command=test).pack(side=tk.LEFT, padx=5)
        ttk.Button(bf, text="Сохранить", command=save).pack(side=tk.LEFT, padx=5)
        ttk.Button(bf, text="Отмена", command=cw.destroy).pack(side=tk.LEFT, padx=5)


# ==================== ЗАПУСК ====================
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
            messagebox.showerror("Ошибка", f"{e}\n\nПодробности в 1.txt")
        except:
            pass
        input("\nНажмите Enter...")
