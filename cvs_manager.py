"""
Модуль управления процессом ЦВС
Управление процессом 1po2_1n на стендах
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
from datetime import datetime

class CVSManager:
    """Класс для управления процессом ЦВС"""
    
    def __init__(self, ssh_user="pkrv", ssh_password="zxcv"):
        self.ssh_user = ssh_user
        self.ssh_password = ssh_password
        self.cvs_process = "1po2_1n"
        self.cvs_path = "/home/pkrv/CVS"
        self.status_labels = {}
    
    def log_to_file(self, message, log_file="1.txt"):
        """Запись логов"""
        try:
            log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), log_file)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] [ЦВС] {message}\n")
        except:
            pass
    
    def stop_cvs(self, ip, stand_name):
        """
        Остановка процесса ЦВС
        Команда: cd /home/pkrv/CVS && slay 1po2_1n
        """
        self.log_to_file(f"Остановка ЦВС на стенде {stand_name} ({ip})")
        
        if not messagebox.askyesno("Подтверждение", 
            f"Вы уверены, что хотите ВЫКЛЮЧИТЬ ЦВС на стенде {stand_name}?\n\n"
            f"Будет выполнена команда:\n"
            f"cd {self.cvs_path} && slay {self.cvs_process}"):
            return False
        
        try:
            import paramiko
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(ip, username=self.ssh_user, password=self.ssh_password, timeout=5)
            
            # Выполняем остановку процесса
            command = f"cd {self.cvs_path} && slay {self.cvs_process}"
            self.log_to_file(f"Выполнение: {command}")
            
            stdin, stdout, stderr = ssh.exec_command(command)
            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()
            
            if output:
                self.log_to_file(f"Вывод: {output}")
            if error:
                self.log_to_file(f"Ошибка: {error}")
            
            ssh.close()
            
            self.log_to_file(f"ЦВС остановлен на стенде {stand_name}")
            messagebox.showinfo("ЦВС остановлен", 
                f"Процесс ЦВС успешно остановлен на стенде {stand_name}\n"
                f"Команда: slay {self.cvs_process}")
            return True
            
        except ImportError:
            self.log_to_file("Ошибка: модуль paramiko не установлен")
            messagebox.showerror("Ошибка", "Модуль paramiko не установлен.\nУстановите: pip install paramiko")
            return False
        except Exception as e:
            self.log_to_file(f"Ошибка остановки ЦВС: {e}")
            messagebox.showerror("Ошибка", f"Не удалось остановить ЦВС:\n{e}")
            return False
    
    def start_cvs(self, ip, stand_name):
        """
        Запуск процесса ЦВС
        Команда: cd /home/pkrv/CVS && ./1po2_1n &
        """
        self.log_to_file(f"Запуск ЦВС на стенде {stand_name} ({ip})")
        
        if not messagebox.askyesno("Подтверждение", 
            f"Вы уверены, что хотите ЗАПУСТИТЬ ЦВС на стенде {stand_name}?\n\n"
            f"Будет выполнена команда:\n"
            f"cd {self.cvs_path} && ./{self.cvs_process} &"):
            return False
        
        try:
            import paramiko
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(ip, username=self.ssh_user, password=self.ssh_password, timeout=5)
            
            # Запускаем процесс в фоновом режиме
            command = f"cd {self.cvs_path} && ./{self.cvs_process} &"
            self.log_to_file(f"Выполнение: {command}")
            
            stdin, stdout, stderr = ssh.exec_command(command)
            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()
            
            if output:
                self.log_to_file(f"Вывод: {output}")
            if error:
                self.log_to_file(f"Ошибка: {error}")
            
            ssh.close()
            
            self.log_to_file(f"ЦВС запущен на стенде {stand_name}")
            messagebox.showinfo("ЦВС запущен", 
                f"Процесс ЦВС успешно запущен на стенде {stand_name}\n"
                f"Команда: ./{self.cvs_process} &")
            return True
            
        except ImportError:
            self.log_to_file("Ошибка: модуль paramiko не установлен")
            messagebox.showerror("Ошибка", "Модуль paramiko не установлен.\nУстановите: pip install paramiko")
            return False
        except Exception as e:
            self.log_to_file(f"Ошибка запуска ЦВС: {e}")
            messagebox.showerror("Ошибка", f"Не удалось запустить ЦВС:\n{e}")
            return False
    
    def restart_cvs(self, ip, stand_name):
        """
        Перезапуск процесса ЦВС
        Останавливает и запускает процесс заново
        """
        self.log_to_file(f"Перезапуск ЦВС на стенде {stand_name} ({ip})")
        
        if not messagebox.askyesno("Подтверждение", 
            f"Вы уверены, что хотите ПЕРЕЗАПУСТИТЬ ЦВС на стенде {stand_name}?\n\n"
            f"Будут выполнены команды:\n"
            f"1. cd {self.cvs_path} && slay {self.cvs_process}\n"
            f"2. cd {self.cvs_path} && ./{self.cvs_process} &"):
            return False
        
        try:
            import paramiko
            import time
            
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(ip, username=self.ssh_user, password=self.ssh_password, timeout=5)
            
            # Шаг 1: Остановка
            self.log_to_file("Шаг 1: Остановка ЦВС")
            stop_cmd = f"cd {self.cvs_path} && slay {self.cvs_process}"
            stdin, stdout, stderr = ssh.exec_command(stop_cmd)
            
            # Пауза
            time.sleep(1)
            
            # Шаг 2: Запуск
            self.log_to_file("Шаг 2: Запуск ЦВС")
            start_cmd = f"cd {self.cvs_path} && ./{self.cvs_process} &"
            stdin, stdout, stderr = ssh.exec_command(start_cmd)
            
            ssh.close()
            
            self.log_to_file(f"ЦВС перезапущен на стенде {stand_name}")
            messagebox.showinfo("ЦВС перезапущен", 
                f"Процесс ЦВС успешно перезапущен на стенде {stand_name}")
            return True
            
        except ImportError:
            self.log_to_file("Ошибка: модуль paramiko не установлен")
            messagebox.showerror("Ошибка", "Модуль paramiko не установлен.\nУстановите: pip install paramiko")
            return False
        except Exception as e:
            self.log_to_file(f"Ошибка перезапуска ЦВС: {e}")
            messagebox.showerror("Ошибка", f"Не удалось перезапустить ЦВС:\n{e}")
            return False
    
    def check_status(self, ip, stand_name):
        """
        Проверка статуса процесса ЦВС
        Команда: ps aux | grep 1po2_1n | grep -v grep
        """
        self.log_to_file(f"Проверка статуса ЦВС на стенде {stand_name} ({ip})")
        
        try:
            import paramiko
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(ip, username=self.ssh_user, password=self.ssh_password, timeout=5)
            
            # Проверяем процесс
            check_cmd = f"ps aux | grep {self.cvs_process} | grep -v grep"
            stdin, stdout, stderr = ssh.exec_command(check_cmd)
            output = stdout.read().decode().strip()
            
            ssh.close()
            
            if output:
                self.log_to_file(f"ЦВС запущен на {stand_name}")
                return True, "🟢 ЦВС ЗАПУЩЕН", output
            else:
                self.log_to_file(f"ЦВС остановлен на {stand_name}")
                return False, "🔴 ЦВС ОСТАНОВЛЕН", "Процесс не найден"
                
        except ImportError:
            return None, "⚠️ Ошибка", "Модуль paramiko не установлен"
        except Exception as e:
            self.log_to_file(f"Ошибка проверки статуса: {e}")
            return None, "⚠️ Нет соединения", str(e)
    
    def kill_cvs(self, ip, stand_name):
        """
        Принудительное завершение процесса ЦВС (kill -9)
        """
        self.log_to_file(f"Принудительное завершение ЦВС на стенде {stand_name} ({ip})")
        
        if not messagebox.askyesno("ПОДТВЕРЖДЕНИЕ", 
            f"⚠️ ВНИМАНИЕ! Принудительное завершение процесса!\n\n"
            f"Вы уверены, что хотите принудительно завершить ЦВС на стенде {stand_name}?\n\n"
            f"Будет выполнена команда:\n"
            f"cd {self.cvs_path} && slay {self.cvs_process}"):
            return False
        
        try:
            import paramiko
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(ip, username=self.ssh_user, password=self.ssh_password, timeout=5)
            
            command = f"cd {self.cvs_path} && slay {self.cvs_process}"
            stdin, stdout, stderr = ssh.exec_command(command)
            
            ssh.close()
            
            self.log_to_file(f"ЦВС принудительно завершен на {stand_name}")
            messagebox.showinfo("Успех", f"Процесс ЦВС принудительно завершен на стенде {stand_name}")
            return True
            
        except Exception as e:
            self.log_to_file(f"Ошибка: {e}")
            messagebox.showerror("Ошибка", str(e))
            return False


class CVSControlPanel(ttk.LabelFrame):
    """GUI панель управления ЦВС"""
    
    def __init__(self, parent, manager, ip, stand_name, **kwargs):
        super().__init__(parent, text="Управление процессом ЦВС", padding=10, **kwargs)
        
        self.manager = manager
        self.ip = ip
        self.stand_name = stand_name
        
        self.create_widgets()
    
    def create_widgets(self):
        # Статус процесса
        status_frame = ttk.Frame(self)
        status_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(status_frame, text="Статус:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        
        self.status_label = ttk.Label(status_frame, text="Не проверен", font=("Arial", 10))
        self.status_label.pack(side=tk.LEFT, padx=10)
        
        # Кнопки управления в две строки
        # Первая строка кнопок
        buttons_row1 = ttk.Frame(self)
        buttons_row1.pack(fill=tk.X, pady=5)
        
        # Кнопка ПРОВЕРИТЬ СТАТУС
        tk.Button(buttons_row1, text="🔍 Проверить статус",
                 bg="#2196F3", fg="white", font=("Arial", 9, "bold"),
                 command=self.check_status
                 ).pack(side=tk.LEFT, padx=3)
        
        # Кнопка ЗАПУСТИТЬ (зеленая)
        tk.Button(buttons_row1, text="▶ ЗАПУСТИТЬ ЦВС",
                 bg="#4CAF50", fg="white", font=("Arial", 9, "bold"),
                 command=self.start_cvs
                 ).pack(side=tk.LEFT, padx=3)
        
        # Кнопка ОСТАНОВИТЬ (красная)
        tk.Button(buttons_row1, text="⏹ ВЫКЛЮЧИТЬ ЦВС",
                 bg="#f44336", fg="white", font=("Arial", 9, "bold"),
                 command=self.stop_cvs
                 ).pack(side=tk.LEFT, padx=3)
        
        # Вторая строка кнопок
        buttons_row2 = ttk.Frame(self)
        buttons_row2.pack(fill=tk.X, pady=5)
        
        # Кнопка ПЕРЕЗАПУСТИТЬ (оранжевая)
        tk.Button(buttons_row2, text="🔄 ПЕРЕЗАПУСТИТЬ ЦВС",
                 bg="#FF9800", fg="white", font=("Arial", 9, "bold"),
                 command=self.restart_cvs
                 ).pack(side=tk.LEFT, padx=3)
        
        # Кнопка ПРИНУДИТЕЛЬНО ЗАВЕРШИТЬ (тёмно-красная)
        tk.Button(buttons_row2, text="⚠️ Принудительно завершить",
                 bg="#b71c1c", fg="white", font=("Arial", 9, "bold"),
                 command=self.kill_cvs
                 ).pack(side=tk.LEFT, padx=3)
        
        # Разделитель
        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # Информация о командах
        info_frame = ttk.LabelFrame(self, text="Выполняемые команды", padding=5)
        info_frame.pack(fill=tk.X, pady=5)
        
        commands_text = f"""
Путь: {self.manager.cvs_path}
Процесс: {self.manager.cvs_process}

▶ Запуск:      cd {self.manager.cvs_path} && ./{self.manager.cvs_process} &
⏹ Остановка:   cd {self.manager.cvs_path} && slay {self.manager.cvs_process}
🔄 Перезапуск:  slay → пауза 1с → ./{self.manager.cvs_process} &
        """
        
        ttk.Label(info_frame, text=commands_text, 
                 font=("Courier", 8), justify=tk.LEFT).pack(anchor=tk.W, padx=5, pady=5)
        
        # SSH информация
        ssh_frame = ttk.LabelFrame(self, text="SSH подключение", padding=5)
        ssh_frame.pack(fill=tk.X, pady=5)
        
        ssh_text = f"Пользователь: {self.manager.ssh_user}\nIP: {self.ip}"
        ttk.Label(ssh_frame, text=ssh_text, font=("Arial", 9)).pack(anchor=tk.W, padx=5)
    
    def update_status_label(self, is_running, status_text, details=""):
        """Обновление метки статуса"""
        if is_running:
            self.status_label.config(text=status_text, foreground="green")
        elif is_running is None:
            self.status_label.config(text=status_text, foreground="orange")
        else:
            self.status_label.config(text=status_text, foreground="red")
    
    def check_status(self):
        """Проверить статус ЦВС"""
        is_running, status_text, details = self.manager.check_status(self.ip, self.stand_name)
        self.update_status_label(is_running, status_text, details)
        
        if is_running:
            messagebox.showinfo("Статус ЦВС", 
                f"🟢 ЦВС ЗАПУЩЕН на стенде {self.stand_name}\n\n{details}")
        elif is_running is False:
            messagebox.showinfo("Статус ЦВС", 
                f"🔴 ЦВС ОСТАНОВЛЕН на стенде {self.stand_name}")
        else:
            messagebox.showwarning("Статус ЦВС", 
                f"⚠️ Не удалось проверить статус на стенде {self.stand_name}\n{status_text}")
    
    def start_cvs(self):
        """Запустить ЦВС"""
        if self.manager.start_cvs(self.ip, self.stand_name):
            self.root.after(1000, self.check_status)
    
    def stop_cvs(self):
        """Остановить ЦВС"""
        if self.manager.stop_cvs(self.ip, self.stand_name):
            self.root.after(1000, self.check_status)
    
    def restart_cvs(self):
        """Перезапустить ЦВС"""
        if self.manager.restart_cvs(self.ip, self.stand_name):
            self.root.after(2000, self.check_status)
    
    def kill_cvs(self):
        """Принудительно завершить ЦВС"""
        if self.manager.kill_cvs(self.ip, self.stand_name):
            self.root.after(1000, self.check_status)
