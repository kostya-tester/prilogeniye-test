import tkinter as tk
from tkinter import ttk, messagebox
import json
from database import Database


class StandsMonitor:
    def __init__(self):
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


class MainApplication:
    def __init__(self, root):
        self.root = root
        self.root.title("Мониторинг стендов")
        self.root.geometry("1200x800")

        self.db = Database()
        self.stands_monitor = StandsMonitor()
        self.current_user_id = None

        # Показываем окно авторизации
        self.show_login()

    def show_login(self):
        # Очищаем главное окно
        for widget in self.root.winfo_children():
            widget.destroy()

        # Создаем фрейм для авторизации
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
        password = self.password_entry.get()

        user_id = self.db.check_credentials(username, password)
        if user_id:
            self.current_user_id = user_id
            self.db.log_login(user_id)
            messagebox.showinfo("Успех", "Вход выполнен успешно!")
            self.show_main_interface()
        else:
            messagebox.showerror("Ошибка", "Неверные логин или пароль")

    def register(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if self.db.add_user(username, password):
            messagebox.showinfo("Успех", "Пользователь зарегистрирован!")
        else:
            messagebox.showerror("Ошибка", "Пользователь уже существует")

    def show_main_interface(self):
        # Очищаем главное окно
        for widget in self.root.winfo_children():
            widget.destroy()

        # Создаем панель инструментов
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        ttk.Button(toolbar, text="История входов", command=self.show_history).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Выйти", command=self.logout).pack(side=tk.RIGHT, padx=5)

        # Создаем Notebook для вкладок
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Создаем вкладки для каждого стенда
        self.create_stand_tab(notebook, "192.168.243.248", "ГОЗ")
        self.create_stand_tab(notebook, "192.168.243.249", "Арктика")
        self.create_stand_tab(notebook, "192.168.243.254", "С1М")

        # Создаем общую вкладку с системами и режимами
        self.create_systems_tab(notebook)

    def create_stand_tab(self, notebook, ip, name):
        stand_data = self.stands_monitor.stands[ip]
        frame = ttk.Frame(notebook)
        notebook.add(frame, text=f"{name} ({ip})")

        # Заголовок
        ttk.Label(frame, text=f"Стенд {name}", font=("Arial", 14, "bold")).pack(pady=10)
        ttk.Label(frame, text=f"IP: {ip}").pack()

        # Связанные устройства
        if stand_data["devices"]:
            devices_frame = ttk.LabelFrame(frame, text="Связанные устройства", padding=10)
            devices_frame.pack(fill=tk.X, padx=10, pady=5)

            devices_text = ", ".join(stand_data["devices"])
            ttk.Label(devices_frame, text=devices_text).pack(anchor=tk.W)

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
                   command=lambda s=name: self.configure_stand(s)).pack(pady=10)

    def create_systems_tab(self, notebook):
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
        messagebox.showinfo("Конфигурация", f"Конфигурация стенда {stand_name}")

    def configure_bm(self):
        messagebox.showinfo("Конфигурация", "Конфигурация БМ")

    def show_history(self):
        if self.current_user_id:
            history_window = tk.Toplevel(self.root)
            history_window.title("История входов")
            history_window.geometry("400x300")

            history = self.db.get_login_history(self.current_user_id)

            ttk.Label(history_window, text="История входов:", font=("Arial", 12)).pack(pady=10)

            frame = ttk.Frame(history_window)
            frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

            for i, (login_time,) in enumerate(history):
                ttk.Label(frame, text=f"{i + 1}. {login_time}").pack(anchor=tk.W, pady=2)

    def logout(self):
        self.current_user_id = None
        self.show_login()


# Запуск приложения
if __name__ == "__main__":
    root = tk.Tk()
    app = MainApplication(root)
    root.mainloop()