import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import platform
import os
import json
from datetime import datetime

class OrangePiDetector:
    """Модуль для обнаружения и работы с Orange Pi"""
    
    def __init__(self):
        self.orange_pi_info = {
            "name": "Orange Pi",
            "default_ip": "192.168.1.100",
            "ssh_user": "orangepi",
            "ssh_password": "orangepi",
            "models": [
                "Orange Pi Zero",
                "Orange Pi Zero 2",
                "Orange Pi One",
                "Orange Pi Lite",
                "Orange Pi PC",
                "Orange Pi PC Plus",
                "Orange Pi Plus",
                "Orange Pi 3",
                "Orange Pi 4",
                "Orange Pi 5"
            ]
        }
        
    def scan_network(self, subnet="192.168.243"):
        """Сканирование сети на наличие Orange Pi"""
        found_devices = []
        
        for i in range(1, 255):
            ip = f"{subnet}.{i}"
            if self.ping_device(ip):
                if self.check_orange_pi(ip):
                    found_devices.append({
                        "ip": ip,
                        "name": "Orange Pi",
                        "status": "Доступен"
                    })
        
        return found_devices
    
    def ping_device(self, ip, timeout=1):
        """Проверка доступности устройства по ping"""
        try:
            param = '-n' if platform.system().lower() == 'windows' else '-c'
            command = ['ping', param, '1', '-w', str(timeout * 1000), ip]
            return subprocess.call(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0
        except:
            return False
    
    def check_orange_pi(self, ip):
        """Проверка, является ли устройство Orange Pi"""
        try:
            import paramiko
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(ip, username=self.orange_pi_info["ssh_user"], 
                       password=self.orange_pi_info["ssh_password"], timeout=3)
            
            stdin, stdout, stderr = ssh.exec_command("cat /proc/cpuinfo | grep -i 'sunxi\|rockchip\|allwinner'")
            output = stdout.read().decode().lower()
            ssh.close()
            
            return any(keyword in output for keyword in ['sunxi', 'rockchip', 'allwinner', 'orange'])
        except:
            return False
    
    def get_orange_pi_details(self, ip):
        """Получение информации о Orange Pi"""
        try:
            import paramiko
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(ip, username=self.orange_pi_info["ssh_user"], 
                       password=self.orange_pi_info["ssh_password"], timeout=5)
            
            details = {}
            
            # Модель
            stdin, stdout, stderr = ssh.exec_command("cat /proc/cpuinfo | grep 'Hardware' | cut -d ':' -f2")
            details["hardware"] = stdout.read().decode().strip()
            
            # Версия ОС
            stdin, stdout, stderr = ssh.exec_command("cat /etc/os-release | grep PRETTY_NAME | cut -d '=' -f2")
            details["os"] = stdout.read().decode().strip().replace('"', '')
            
            # Версия ядра
            stdin, stdout, stderr = ssh.exec_command("uname -r")
            details["kernel"] = stdout.read().decode().strip()
            
            # Температура
            stdin, stdout, stderr = ssh.exec_command("cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null || echo 'N/A'")
            temp = stdout.read().decode().strip()
            if temp != 'N/A':
                details["temperature"] = f"{int(temp) / 1000:.1f}°C"
            else:
                details["temperature"] = "N/A"
            
            # IP адрес
            stdin, stdout, stderr = ssh.exec_command("hostname -I | awk '{print $1}'")
            details["ip"] = stdout.read().decode().strip()
            
            ssh.close()
            return details
        except:
            return None

class OrangePiFrame(ttk.LabelFrame):
    """GUI компонент для отображения Orange Pi"""
    
    def __init__(self, parent, detector, **kwargs):
        super().__init__(parent, text="Orange Pi", padding=10, **kwargs)
        self.detector = detector
        self.devices = []
        self.create_widgets()
    
    def create_widgets(self):
        # Верхняя панель
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, pady=5)
        
        ttk.Label(toolbar, text="Поиск платы Orange Pi", font=("Arial", 12, "bold")).pack(side=tk.LEFT)
        
        ttk.Button(toolbar, text="Сканировать сеть", 
                  command=self.scan_network).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(toolbar, text="Подключиться по SSH", 
                  command=self.connect_ssh).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(toolbar, text="Добавить вручную", 
                  command=self.add_manual).pack(side=tk.LEFT, padx=5)
        
        # Поле для ввода IP вручную
        self.ip_frame = ttk.Frame(self)
        self.ip_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(self.ip_frame, text="IP адрес:").pack(side=tk.LEFT, padx=5)
        self.ip_entry = ttk.Entry(self.ip_frame, width=20)
        self.ip_entry.pack(side=tk.LEFT, padx=5)
        self.ip_entry.insert(0, "192.168.243.")
        
        ttk.Button(self.ip_frame, text="Проверить", 
                  command=self.check_ip).pack(side=tk.LEFT, padx=5)
        
        # Список найденных устройств
        self.tree_frame = ttk.Frame(self)
        self.tree_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        columns = ("ip", "name", "status", "details")
        self.tree = ttk.Treeview(self.tree_frame, columns=columns, show="headings", height=8)
        
        self.tree.heading("ip", text="IP адрес")
        self.tree.heading("name", text="Название")
        self.tree.heading("status", text="Статус")
        self.tree.heading("details", text="Детали")
        
        self.tree.column("ip", width=150)
        self.tree.column("name", width=150)
        self.tree.column("status", width=100)
        self.tree.column("details", width=300)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Скроллбар
        scrollbar = ttk.Scrollbar(self.tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Кнопки действий
        action_frame = ttk.Frame(self)
        action_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(action_frame, text="Загрузить прошивку", 
                  command=self.upload_firmware).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(action_frame, text="Перезагрузить", 
                  command=self.reboot_device).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(action_frame, text="Удалить из списка", 
                  command=self.remove_device).pack(side=tk.LEFT, padx=5)
        
        # Информационная панель
        self.info_frame = ttk.LabelFrame(self, text="Информация о плате", padding=10)
        self.info_frame.pack(fill=tk.X, pady=5)
        self.info_label = ttk.Label(self.info_frame, text="Выберите устройство для просмотра информации")
        self.info_label.pack()
    
    def scan_network(self):
        """Сканирование сети"""
        self.info_label.config(text="Сканирование сети...")
        self.update()
        
        subnet = self.ip_entry.get().rsplit('.', 1)[0]
        devices = self.detector.scan_network(subnet)
        
        self.tree.delete(*self.tree.get_children())
        self.devices = devices
        
        for device in devices:
            self.tree.insert("", "end", values=(
                device["ip"],
                device["name"],
                device["status"],
                "Найден при сканировании"
            ))
        
        self.info_label.config(text=f"Найдено устройств: {len(devices)}")
    
    def check_ip(self):
        """Проверка конкретного IP"""
        ip = self.ip_entry.get()
        if self.detector.ping_device(ip):
            if self.detector.check_orange_pi(ip):
                self.tree.insert("", "end", values=(ip, "Orange Pi", "Доступен", "Проверен вручную"))
                self.info_label.config(text=f"Orange Pi найден по адресу {ip}")
            else:
                self.info_label.config(text=f"Устройство {ip} доступно, но не является Orange Pi")
                messagebox.showinfo("Информация", f"Устройство {ip} доступно, но не определено как Orange Pi")
        else:
            self.info_label.config(text=f"Устройство {ip} недоступно")
            messagebox.showerror("Ошибка", f"Устройство {ip} недоступно")
    
    def connect_ssh(self):
        """Подключение по SSH к выбранному устройству"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите устройство в списке")
            return
        
        ip = self.tree.item(selected[0])["values"][0]
        details = self.detector.get_orange_pi_details(ip)
        
        if details:
            info_text = f"""
=== Информация о Orange Pi ===
Модель: {details.get('hardware', 'N/A')}
ОС: {details.get('os', 'N/A')}
Ядро: {details.get('kernel', 'N/A')}
Температура: {details.get('temperature', 'N/A')}
IP: {details.get('ip', 'N/A')}
=============================
            """
            self.info_label.config(text=info_text)
            messagebox.showinfo("Информация", info_text)
        else:
            messagebox.showerror("Ошибка", "Не удалось получить информацию об устройстве")
    
    def add_manual(self):
        """Добавление устройства вручную"""
        ip = self.ip_entry.get()
        if ip:
            self.check_ip()
    
    def upload_firmware(self):
        """Загрузка прошивки на Orange Pi"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите устройство в списке")
            return
        
        ip = self.tree.item(selected[0])["values"][0]
        from tkinter import filedialog
        file_path = filedialog.askopenfilename(title="Выберите файл прошивки")
        
        if file_path:
            try:
                import paramiko
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(ip, username=self.detector.orange_pi_info["ssh_user"],
                           password=self.detector.orange_pi_info["ssh_password"])

                sftp = ssh.open_sftp()
                filename = os.path.basename(file_path)
                sftp.put(file_path, f"/home/orangepi/{filename}")
                sftp.close()
                ssh.close()
                
                messagebox.showinfo("Успех", f"Файл {filename} загружен на Orange Pi")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить файл: {e}")
    
    def reboot_device(self):
        """Перезагрузка Orange Pi"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите устройство в списке")
            return
        
        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите перезагрузить Orange Pi?"):
            ip = self.tree.item(selected[0])["values"][0]
            try:
                import paramiko
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(ip, username=self.detector.orange_pi_info["ssh_user"],
                           password=self.detector.orange_pi_info["ssh_password"])
                ssh.exec_command("sudo reboot")
                ssh.close()
                messagebox.showinfo("Успех", "Команда перезагрузки отправлена")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка: {e}")
    
    def remove_device(self):
        """Удаление устройства из списка"""
        selected = self.tree.selection()
        if selected:
            self.tree.delete(selected[0])
            self.info_label.config(text="Устройство удалено из списка")
