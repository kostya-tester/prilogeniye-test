"""
Модуль для обнаружения и работы с Orange Pi
Автоматически находит Orange Pi в сети
Подключение: root / orangepi
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import subprocess
import platform
import os
import threading
from datetime import datetime


class OrangePiDetector:
    """Класс для обнаружения и взаимодействия с Orange Pi"""
    
    def __init__(self):
        self.ssh_user = "root"
        self.ssh_password = "orangepi"
        self.found_devices = []
        self.scanning = False
    
    def log(self, message):
        """Запись в лог"""
        try:
            log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "1.txt")
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] [OrangePi] {message}\n")
        except:
            pass
    
    def ping_device(self, ip, timeout=1):
        """Проверка доступности устройства по ping"""
        try:
            param = '-n' if platform.system().lower() == 'windows' else '-c'
            command = ['ping', param, '1', '-w', str(timeout * 1000), ip]
            return subprocess.call(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            ) == 0
        except:
            return False
    
    def check_is_orange_pi(self, ip):
        """Проверка, является ли устройство Orange Pi"""
        try:
            import paramiko
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(ip, username=self.ssh_user, password=self.ssh_password, timeout=3)
            
            # Проверяем характерные признаки Orange Pi
            stdin, stdout, stderr = ssh.exec_command(
                "cat /proc/cpuinfo 2>/dev/null | grep -iE 'sunxi|rockchip|allwinner|orange' || "
                "cat /proc/device-tree/model 2>/dev/null || "
                "uname -a 2>/dev/null"
            )
            output = stdout.read().decode().lower()
            ssh.close()
            
            return any(kw in output for kw in ['sunxi', 'rockchip', 'allwinner', 'orange', 'armv7', 'aarch64'])
        except:
            return False
    
    def scan_network(self, subnet="192.168.243", callback=None):
        """Сканирование сети на наличие Orange Pi"""
        self.log(f"Сканирование сети {subnet}.0/24")
        self.found_devices = []
        self.scanning = True
        
        for i in range(1, 255):
            if not self.scanning:
                break
            
            ip = f"{subnet}.{i}"
            
            if callback:
                callback(f"Проверка {ip}...", i)
            
            if self.ping_device(ip):
                self.log(f"Устройство отвечает: {ip}")
                
                if callback:
                    callback(f"Найдено устройство: {ip}, проверка Orange Pi...", i)
                
                if self.check_is_orange_pi(ip):
                    device_info = self.get_device_info(ip)
                    self.found_devices.append({
                        "ip": ip,
                        "name": device_info.get("model", "Orange Pi"),
                        "status": "Доступен",
                        "details": device_info
                    })
                    self.log(f"Orange Pi подтверждён: {ip}")
                    
                    if callback:
                        callback(f"✓ Orange Pi найден: {ip}", i)
        
        self.scanning = False
        self.log(f"Сканирование завершено. Найдено Orange Pi: {len(self.found_devices)}")
        return self.found_devices
    
    def scan_network_threaded(self, subnet, progress_callback, finish_callback):
        """Сканирование в отдельном потоке"""
        def scan():
            self.scan_network(subnet, progress_callback)
            if finish_callback:
                finish_callback(self.found_devices)
        
        thread = threading.Thread(target=scan, daemon=True)
        thread.start()
    
    def get_device_info(self, ip):
        """Получение подробной информации об устройстве"""
        info = {
            "model": "Orange Pi",
            "os": "Неизвестно",
            "kernel": "Неизвестно",
            "temperature": "N/A",
            "ip": ip,
            "memory": "N/A",
            "disk": "N/A"
        }
        
        try:
            import paramiko
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(ip, username=self.ssh_user, password=self.ssh_password, timeout=5)
            
            # Модель
            stdin, stdout, stderr = ssh.exec_command(
                "cat /proc/device-tree/model 2>/dev/null | tr -d '\\0' || "
                "cat /proc/cpuinfo | grep 'Hardware' | cut -d: -f2 | xargs || "
                "cat /proc/cpuinfo | grep 'Model' | cut -d: -f2 | xargs"
            )
            info["model"] = stdout.read().decode().strip() or "Orange Pi"
            
            # ОС
            stdin, stdout, stderr = ssh.exec_command(
                "cat /etc/os-release 2>/dev/null | grep PRETTY_NAME | cut -d= -f2 | tr -d '\"' || "
                "cat /etc/armbian-release 2>/dev/null | grep BOARD_NAME | cut -d= -f2"
            )
            info["os"] = stdout.read().decode().strip() or "Linux"
            
            # Ядро
            stdin, stdout, stderr = ssh.exec_command("uname -r")
            info["kernel"] = stdout.read().decode().strip()
            
            # Температура
            stdin, stdout, stderr = ssh.exec_command(
                "cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null | awk '{printf \"%.1f°C\", $1/1000}' || "
                "cat /sys/class/hwmon/hwmon0/temp1_input 2>/dev/null | awk '{printf \"%.1f°C\", $1/1000}' || "
                "echo 'N/A'"
            )
            info["temperature"] = stdout.read().decode().strip()
            
            # Память
            stdin, stdout, stderr = ssh.exec_command("free -h | grep Mem | awk '{print $3\"/\"$2}'")
            info["memory"] = stdout.read().decode().strip()
            
            # Диск
            stdin, stdout, stderr = ssh.exec_command("df -h / | tail -1 | awk '{print $3\"/\"$2 \" (\"$5\")\"}'")
            info["disk"] = stdout.read().decode().strip()
            
            ssh.close()
        except Exception as e:
            self.log(f"Ошибка получения информации: {e}")
        
        return info
    
    def execute_command(self, ip, command):
        """Выполнить команду на устройстве"""
        try:
            import paramiko
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(ip, username=self.ssh_user, password=self.ssh_password, timeout=5)
            
            stdin, stdout, stderr = ssh.exec_command(command)
            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()
            
            ssh.close()
            
            if error:
                self.log(f"Ошибка выполнения '{command}': {error}")
            
            return output or error
        except Exception as e:
            self.log(f"Ошибка SSH: {e}")
            return f"Ошибка: {e}"
    
    def upload_file(self, ip, local_path, remote_path="/root/"):
        """Загрузить файл на устройство"""
        try:
            import paramiko
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(ip, username=self.ssh_user, password=self.ssh_password, timeout=5)
            
            sftp = ssh.open_sftp()
            filename = os.path.basename(local_path)
            remote_full = os.path.join(remote_path, filename).replace("\\", "/")
            sftp.put(local_path, remote_full)
            
            sftp.close()
            ssh.close()
            
            self.log(f"Файл {filename} загружен на {ip}:{remote_full}")
            return True, remote_full
        except Exception as e:
            self.log(f"Ошибка загрузки: {e}")
            return False, str(e)
    
    def download_file(self, ip, remote_path, local_path):
        """Скачать файл с устройства"""
        try:
            import paramiko
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(ip, username=self.ssh_user, password=self.ssh_password, timeout=5)
            
            sftp = ssh.open_sftp()
            sftp.get(remote_path, local_path)
            
            sftp.close()
            ssh.close()
            
            self.log(f"Файл {remote_path} скачан с {ip}")
            return True
        except Exception as e:
            self.log(f"Ошибка скачивания: {e}")
            return False
    
    def get_files_list(self, ip, path="/root"):
        """Получить список файлов"""
        return self.execute_command(ip, f"ls -lh {path}")
    
    def get_processes(self, ip):
        """Получить список процессов"""
        return self.execute_command(ip, "ps aux --sort=-%mem | head -30")
    
    def get_memory_info(self, ip):
        """Получить информацию о памяти"""
        return self.execute_command(ip, "free -h")
    
    def get_disk_info(self, ip):
        """Получить информацию о дисках"""
        return self.execute_command(ip, "df -h")
    
    def get_network_info(self, ip):
        """Получить сетевую информацию"""
        return self.execute_command(ip, "ip addr show | grep 'inet ' | grep -v 127.0.0.1")
    
    def reboot(self, ip):
        """Перезагрузить устройство"""
        self.log(f"Отправка команды перезагрузки на {ip}")
        return self.execute_command(ip, "reboot")
    
    def shutdown(self, ip):
        """Выключить устройство"""
        self.log(f"Отправка команды выключения на {ip}")
        return self.execute_command(ip, "shutdown -h now")
    
    def stop_scan(self):
        """Остановить сканирование"""
        self.scanning = False
        self.log("Сканирование остановлено")


class OrangePiFrame(ttk.LabelFrame):
    """GUI компонент для работы с Orange Pi"""
    
    def __init__(self, parent, detector=None, **kwargs):
        super().__init__(parent, text="Orange Pi — Поиск и управление", padding=10, **kwargs)
        
        self.detector = detector or OrangePiDetector()
        self.found_devices = []
        self.create_widgets()
        
        # Автосканирование при создании
        self.after(500, self.auto_scan)
    
    def create_widgets(self):
        # === ВЕРХНЯЯ ПАНЕЛЬ ===
        top_frame = ttk.Frame(self)
        top_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(top_frame, text="🔍 Поиск Orange Pi в сети", 
                 font=("Arial", 12, "bold")).pack(side=tk.LEFT)
        
        self.scan_button = ttk.Button(top_frame, text="Сканировать сеть", 
                                      command=self.scan_network)
        self.scan_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(top_frame, text="Стоп", 
                                      command=self.stop_scan, state="disabled")
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # === НАСТРОЙКИ ПОДКЛЮЧЕНИЯ ===
        settings_frame = ttk.LabelFrame(self, text="Параметры подключения", padding=5)
        settings_frame.pack(fill=tk.X, pady=5)
        
        row1 = ttk.Frame(settings_frame)
        row1.pack(fill=tk.X, pady=2)
        
        ttk.Label(row1, text="Подсеть:").pack(side=tk.LEFT)
        self.subnet_entry = ttk.Entry(row1, width=15)
        self.subnet_entry.pack(side=tk.LEFT, padx=5)
        self.subnet_entry.insert(0, "192.168.243")
        
        ttk.Label(row1, text="Логин:").pack(side=tk.LEFT, padx=(10, 0))
        self.user_entry = ttk.Entry(row1, width=12)
        self.user_entry.pack(side=tk.LEFT, padx=5)
        self.user_entry.insert(0, "root")
        
        ttk.Label(row1, text="Пароль:").pack(side=tk.LEFT, padx=(10, 0))
        self.pass_entry = ttk.Entry(row1, show="*", width=12)
        self.pass_entry.pack(side=tk.LEFT, padx=5)
        self.pass_entry.insert(0, "orangepi")
        
        ttk.Button(row1, text="Применить", 
                  command=self.apply_settings).pack(side=tk.LEFT, padx=10)
        
        # === ПРОГРЕСС СКАНИРОВАНИЯ ===
        self.progress_frame = ttk.Frame(self)
        self.progress_frame.pack(fill=tk.X, pady=2)
        
        self.progress_label = ttk.Label(self.progress_frame, text="Готов к сканированию", 
                                        foreground="gray")
        self.progress_label.pack(side=tk.LEFT)
        
        self.progress_bar = ttk.Progressbar(self.progress_frame, mode="determinate", length=200)
        self.progress_bar.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=10)
        
        # === ТАБЛИЦА УСТРОЙСТВ ===
        table_frame = ttk.Frame(self)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        columns = ("ip", "name", "status", "model", "os")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=6)
        
        self.tree.heading("ip", text="IP адрес")
        self.tree.heading("name", text="Имя")
        self.tree.heading("status", text="Статус")
        self.tree.heading("model", text="Модель")
        self.tree.heading("os", text="ОС")
        
        self.tree.column("ip", width=140)
        self.tree.column("name", width=100)
        self.tree.column("status", width=90)
        self.tree.column("model", width=180)
        self.tree.column("os", width=250)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.bind("<<TreeviewSelect>>", self.on_device_select)
        
        # === КНОПКИ ДЕЙСТВИЙ ===
        actions_frame = ttk.LabelFrame(self, text="Действия с устройством", padding=5)
        actions_frame.pack(fill=tk.X, pady=5)
        
        btn_frame1 = ttk.Frame(actions_frame)
        btn_frame1.pack(fill=tk.X, pady=2)
        
        ttk.Button(btn_frame1, text="📋 Информация", 
                  command=self.show_info).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame1, text="📂 Файлы", 
                  command=self.show_files).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame1, text="📊 Процессы", 
                  command=self.show_processes).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame1, text="💾 Память", 
                  command=self.show_memory).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame1, text="💿 Диски", 
                  command=self.show_disks).pack(side=tk.LEFT, padx=2)
        
        btn_frame2 = ttk.Frame(actions_frame)
        btn_frame2.pack(fill=tk.X, pady=2)
        
        ttk.Button(btn_frame2, text="📤 Загрузить файл", 
                  command=self.upload_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame2, text="🔄 Перезагрузить", 
                  command=self.reboot_device).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame2, text="⏻ Выключить", 
                  command=self.shutdown_device).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame2, text="🗑 Удалить", 
                  command=self.remove_device).pack(side=tk.LEFT, padx=2)
        
        # === КОНСОЛЬ ===
        console_frame = ttk.LabelFrame(self, text="Консоль (выполнить команду)", padding=5)
        console_frame.pack(fill=tk.X, pady=5)
        
        cmd_frame = ttk.Frame(console_frame)
        cmd_frame.pack(fill=tk.X)
        
        self.cmd_entry = ttk.Entry(cmd_frame)
        self.cmd_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.cmd_entry.bind("<Return>", lambda e: self.execute_custom_command())
        
        ttk.Button(cmd_frame, text="Выполнить", 
                  command=self.execute_custom_command).pack(side=tk.RIGHT, padx=5)
        
        # === ИНФО ПАНЕЛЬ ===
        self.info_text = scrolledtext.ScrolledText(self, height=6, wrap=tk.WORD, 
                                                    font=("Courier", 9))
        self.info_text.pack(fill=tk.BOTH, expand=True, pady=5)
        self.info_text.insert("1.0", "Выполните сканирование для поиска Orange Pi...")
    
    def apply_settings(self):
        """Применить настройки подключения"""
        self.detector.ssh_user = self.user_entry.get()
        self.detector.ssh_password = self.pass_entry.get()
        self.info_text.insert("end", f"\n✓ Настройки применены: {self.detector.ssh_user}@{self.subnet_entry.get()}.0/24\n")
    
    def auto_scan(self):
        """Автоматическое сканирование при запуске"""
        self.scan_network()
    
    def scan_network(self):
        """Запуск сканирования"""
        subnet = self.subnet_entry.get().strip()
        self.detector.ssh_user = self.user_entry.get()
        self.detector.ssh_password = self.pass_entry.get()
        
        self.scan_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.progress_bar["value"] = 0
        self.progress_bar["maximum"] = 254
        
        self.tree.delete(*self.tree.get_children())
        self.info_text.delete("1.0", "end")
        self.info_text.insert("end", f"🔍 Сканирование сети {subnet}.0/24...\n")
        self.info_text.insert("end", f"   Логин: {self.detector.ssh_user}\n")
        self.info_text.insert("end", "   Поиск Orange Pi...\n\n")
        
        def progress_callback(msg, progress):
            self.progress_label.config(text=msg)
            self.progress_bar["value"] = progress
            self.update_idletasks()
        
        def finish_callback(devices):
            self.found_devices = devices
            self.tree.delete(*self.tree.get_children())
            
            for device in devices:
                details = device.get("details", {})
                self.tree.insert("", "end", values=(
                    device["ip"],
                    "Orange Pi",
                    "✓ Доступен",
                    details.get("model", ""),
                    details.get("os", "")
                ))
            
            self.scan_button.config(state="normal")
            self.stop_button.config(state="disabled")
            self.progress_label.config(text=f"Готово. Найдено Orange Pi: {len(devices)}", 
                                       foreground="green")
            
            self.info_text.insert("end", f"\n✓ Сканирование завершено\n")
            self.info_text.insert("end", f"  Найдено устройств Orange Pi: {len(devices)}\n")
            
            for d in devices:
                self.info_text.insert("end", f"  • {d['ip']} - {d['name']}\n")
        
        self.detector.scan_network_threaded(subnet, progress_callback, finish_callback)
    
    def stop_scan(self):
        """Остановить сканирование"""
        self.detector.stop_scan()
        self.scan_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.progress_label.config(text="Сканирование остановлено", foreground="orange")
        self.info_text.insert("end", "\n⏹ Сканирование остановлено пользователем\n")
    
    def on_device_select(self, event):
        """Обработчик выбора устройства"""
        selection = self.tree.selection()
        if selection:
            ip = self.tree.item(selection[0])["values"][0]
            self.cmd_entry.delete(0, "end")
            self.cmd_entry.insert(0, f"ssh {self.detector.ssh_user}@{ip}")
    
    def get_selected_ip(self):
        """Получить IP выбранного устройства"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите устройство в списке")
            return None
        
        return self.tree.item(selection[0])["values"][0]
    
    def show_info(self):
        """Показать информацию об устройстве"""
        ip = self.get_selected_ip()
        if not ip:
            return
        
        info = self.detector.get_device_info(ip)
        
        text = f"""
╔══════════════════════════════════════╗
║     ИНФОРМАЦИЯ ОБ ORANGE PI        ║
╚══════════════════════════════════════╝

  IP адрес:     {info.get('ip', 'N/A')}
  Модель:       {info.get('model', 'N/A')}
  ОС:           {info.get('os', 'N/A')}
  Ядро:         {info.get('kernel', 'N/A')}
  Температура:  {info.get('temperature', 'N/A')}
  Память (исп.): {info.get('memory', 'N/A')}
  Диск (исп.):  {info.get('disk', 'N/A')}
"""
        self.info_text.delete("1.0", "end")
        self.info_text.insert("1.0", text)
    
    def show_files(self):
        """Показать список файлов"""
        ip = self.get_selected_ip()
        if not ip:
            return
        
        files = self.detector.get_files_list(ip)
        self._show_in_window(f"Файлы на {ip}", files)
    
    def show_processes(self):
        """Показать процессы"""
        ip = self.get_selected_ip()
        if not ip:
            return
        
        processes = self.detector.get_processes(ip)
        self._show_in_window(f"Процессы на {ip}", processes)
    
    def show_memory(self):
        """Показать информацию о памяти"""
        ip = self.get_selected_ip()
        if not ip:
            return
        
        memory = self.detector.get_memory_info(ip)
        self._show_in_window(f"Память на {ip}", memory)
    
    def show_disks(self):
        """Показать информацию о дисках"""
        ip = self.get_selected_ip()
        if not ip:
            return
        
        disks = self.detector.get_disk_info(ip)
        self._show_in_window(f"Диски на {ip}", disks)
    
    def _show_in_window(self, title, content):
        """Показать содержимое в новом окне"""
        window = tk.Toplevel(self)
        window.title(title)
        window.geometry("700x500")
        
        text = scrolledtext.ScrolledText(window, wrap=tk.NONE, font=("Courier", 10))
        text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        text.insert("1.0", content)
        text.config(state="disabled")
    
    def upload_file(self):
        """Загрузить файл на устройство"""
        ip = self.get_selected_ip()
        if not ip:
            return
        
        file_path = filedialog.askopenfilename(title="Выберите файл для загрузки")
        if file_path:
            success, result = self.detector.upload_file(ip, file_path)
            if success:
                messagebox.showinfo("Успех", f"Файл загружен:\n{result}")
            else:
                messagebox.showerror("Ошибка", f"Не удалось загрузить:\n{result}")
    
    def reboot_device(self):
        """Перезагрузить устройство"""
        ip = self.get_selected_ip()
        if not ip:
            return
        
        if messagebox.askyesno("Подтверждение", f"Перезагрузить Orange Pi ({ip})?"):
            self.detector.reboot(ip)
            messagebox.showinfo("Успех", f"Команда перезагрузки отправлена на {ip}")
    
    def shutdown_device(self):
        """Выключить устройство"""
        ip = self.get_selected_ip()
        if not ip:
            return
        
        if messagebox.askyesno("⚠️ Подтверждение", 
                               f"ВЫКЛЮЧИТЬ Orange Pi ({ip})?\n\n"
                               "Устройство будет недоступно до физического включения!"):
            self.detector.shutdown(ip)
            messagebox.showinfo("Успех", f"Команда выключения отправлена на {ip}")
    
    def remove_device(self):
        """Удалить устройство из списка"""
        selection = self.tree.selection()
        if selection:
            self.tree.delete(selection[0])
    
    def execute_custom_command(self):
        """Выполнить произвольную команду"""
        ip = self.get_selected_ip()
        if not ip:
            return
        
        command = self.cmd_entry.get().strip()
        if not command:
            return
        
        self.info_text.insert("end", f"\n$ {command}\n")
        output = self.detector.execute_command(ip, command)
        self.info_text.insert("end", f"{output}\n")
        self.info_text.see("end")
