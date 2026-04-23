import tkinter as tk
from tkinter import messagebox
from database import Database

class LoginApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Авторизация")
        self.db = Database()

        # Элементы интерфейса
        tk.Label(root, text="Логин:").grid(row=0, column=0, padx=10, pady=5)
        self.username_entry = tk.Entry(root)
        self.username_entry.grid(row=0, column=1, padx=10, pady=5)

        tk.Label(root, text="Пароль:").grid(row=1, column=0, padx=10, pady=5)
        self.password_entry = tk.Entry(root, show="*")
        self.password_entry.grid(row=1, column=1, padx=10, pady=5)

        # Кнопки
        tk.Button(root, text="Войти", command=self.login).grid(row=2, column=0, pady=10)
        tk.Button(root, text="Зарегистрироваться", command=self.register).grid(row=2, column=1, pady=10)

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        user_id = self.db.check_credentials(username, password)
        if user_id:
            self.db.log_login(user_id)  # Записываем время входа
            messagebox.showinfo("Успех", "Вход выполнен успешно!")
            self.show_history(user_id)
        else:
            messagebox.showerror("Ошибка", "Неверные логин или пароль")

    def register(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if self.db.add_user(username, password):
            messagebox.showinfo("Успех", "Пользователь зарегистрирован!")
        else:
            messagebox.showerror("Ошибка", "Пользователь уже существует")

    def show_history(self, user_id):
        # Создаём новое окно для отображения истории
        history_window = tk.Toplevel(self.root)
        history_window.title("История входов")

        history = self.db.get_login_history(user_id)

        tk.Label(history_window, text="История входов:").pack(pady=10)
        for i, (login_time,) in enumerate(history):
            tk.Label(history_window, text=login_time).pack()

# Запуск приложения
if __name__ == "__main__":
    root = tk.Tk()
    app = LoginApp(root)
    root.mainloop()
