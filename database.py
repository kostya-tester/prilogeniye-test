import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_name="users.db"):
        self.conn = sqlite3.connect(db_name)
        self.create_tables()

    def create_tables(self):
        # Таблица пользователей (логин и пароль)
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')

        # Таблица логов входа (кто и когда зашёл)
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS login_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                login_time TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        self.conn.commit()

    def add_user(self, username, password):
        try:
            self.conn.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False  # Пользователь уже существует

    def check_credentials(self, username, password):
        cursor = self.conn.execute(
            "SELECT id FROM users WHERE username = ? AND password = ?",
            (username, password)
        )
        user = cursor.fetchone()
        return user[0] if user else None

    def log_login(self, user_id):
        login_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.conn.execute(
            "INSERT INTO login_logs (user_id, login_time) VALUES (?, ?)",
            (user_id, login_time)
        )
        self.conn.commit()

    def get_login_history(self, user_id):
        cursor = self.conn.execute(
            "SELECT login_time FROM login_logs WHERE user_id = ? ORDER BY login_time DESC",
            (user_id,)
        )
        return cursor.fetchall()
