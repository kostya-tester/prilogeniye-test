"""
Модуль расширенной статистики
Время работы, прошивки, ошибки, отчёты
"""

import os
import json
import hashlib
from datetime import datetime, timedelta
from collections import Counter

class StatisticsManager:
    """Класс для сбора и отображения статистики"""
    
    def __init__(self):
        self.stats_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "statistics.json")
        self.stats_data = self.load_stats()
    
    def load_stats(self):
        """Загрузка статистики из файла"""
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        # Начальная структура
        return {
            "uptime": {},           # Время работы стендов
            "flash_history": [],    # История прошивок
            "cvs_actions": [],      # Действия с ЦВС
            "errors": [],           # Ошибки
            "checksums": {},        # Контрольные суммы
            "user_actions": []      # Действия пользователей
        }
    
    def save_stats(self):
        """Сохранение статистики"""
        try:
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Ошибка сохранения статистики: {e}")
    
    def add_uptime(self, stand_name, ip, is_online):
        """Добавить запись о времени работы"""
        today = datetime.now().strftime("%Y-%m-%d")
        hour = datetime.now().strftime("%H:%M")
        
        key = f"{stand_name}_{ip}"
        if key not in self.stats_data["uptime"]:
            self.stats_data["uptime"][key] = {
                "name": stand_name,
                "ip": ip,
                "daily": {}
            }
        
        if today not in self.stats_data["uptime"][key]["daily"]:
            self.stats_data["uptime"][key]["daily"][today] = []
        
        self.stats_data["uptime"][key]["daily"][today].append({
            "hour": hour,
            "status": "online" if is_online else "offline"
        })
        
        self.save_stats()
    
    def add_flash_action(self, stand_name, ip, action, file_name=None, success=True):
        """Добавить запись о прошивке"""
        self.stats_data["flash_history"].append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "stand": stand_name,
            "ip": ip,
            "action": action,
            "file": file_name,
            "success": success
        })
        self.save_stats()
    
    def add_cvs_action(self, stand_name, ip, action, success=True):
        """Добавить запись о действии с ЦВС"""
        self.stats_data["cvs_actions"].append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "stand": stand_name,
            "ip": ip,
            "action": action,
            "success": success
        })
        self.save_stats()
    
    def add_error(self, error_type, stand_name, details):
        """Добавить запись об ошибке"""
        self.stats_data["errors"].append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": error_type,
            "stand": stand_name,
            "details": str(details)
        })
        self.save_stats()
    
    def add_user_action(self, username, action, stand_name=None):
        """Добавить запись о действии пользователя"""
        self.stats_data["user_actions"].append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user": username,
            "action": action,
            "stand": stand_name
        })
        self.save_stats()
    
    def save_checksum(self, file_path, checksum, stand_name):
        """Сохранить контрольную сумму файла"""
        file_name = os.path.basename(file_path)
        key = f"{stand_name}_{file_name}"
        
        self.stats_data["checksums"][key] = {
            "file": file_name,
            "stand": stand_name,
            "checksum": checksum,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.save_stats()
    
    def get_uptime_stats(self, days=7):
        """Получить статистику времени работы за последние N дней"""
        result = {}
        today = datetime.now()
        
        for key, data in self.stats_data["uptime"].items():
            stand_name = data["name"]
            total_hours = 0
            online_hours = 0
            
            for i in range(days):
                date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
                if date in data["daily"]:
                    records = data["daily"][date]
                    total_hours += len(records)
                    online_hours += sum(1 for r in records if r["status"] == "online")
            
            if total_hours > 0:
                uptime_percent = (online_hours / total_hours) * 100
            else:
                uptime_percent = 0
            
            result[stand_name] = {
                "ip": data["ip"],
                "uptime_percent": round(uptime_percent, 1),
                "total_checks": total_hours,
                "online_checks": online_hours
            }
        
        return result
    
    def get_flash_stats(self, days=30):
        """Получить статистику прошивок"""
        today = datetime.now()
        cutoff = today - timedelta(days=days)
        
        recent = [
            f for f in self.stats_data["flash_history"]
            if datetime.strptime(f["timestamp"], "%Y-%m-%d %H:%M:%S") > cutoff
        ]
        
        total = len(recent)
        successful = sum(1 for f in recent if f.get("success", True))
        by_stand = Counter(f["stand"] for f in recent)
        
        return {
            "total": total,
            "successful": successful,
            "failed": total - successful,
            "by_stand": dict(by_stand)
        }
    
    def get_cvs_stats(self, days=30):
        """Получить статистику ЦВС"""
        today = datetime.now()
        cutoff = today - timedelta(days=days)
        
        recent = [
            a for a in self.stats_data["cvs_actions"]
            if datetime.strptime(a["timestamp"], "%Y-%m-%d %H:%M:%S") > cutoff
        ]
        
        by_action = Counter(a["action"] for a in recent)
        by_stand = Counter(a["stand"] for a in recent)
        
        return {
            "total_actions": len(recent),
            "by_action": dict(by_action),
            "by_stand": dict(by_stand)
        }
    
    def get_error_stats(self, days=30):
        """Получить статистику ошибок"""
        today = datetime.now()
        cutoff = today - timedelta(days=days)
        
        recent = [
            e for e in self.stats_data["errors"]
            if datetime.strptime(e["timestamp"], "%Y-%m-%d %H:%M:%S") > cutoff
        ]
        
        by_type = Counter(e["type"] for e in recent)
        by_stand = Counter(e["stand"] for e in recent)
        
        return {
            "total_errors": len(recent),
            "by_type": dict(by_type),
            "by_stand": dict(by_stand)
        }
    
    def generate_report(self):
        """Сгенерировать полный отчёт"""
        uptime = self.get_uptime_stats()
        flash = self.get_flash_stats()
        cvs = self.get_cvs_stats()
        errors = self.get_error_stats()
        
        report = f"""
╔══════════════════════════════════════════════╗
║       ОТЧЁТ О РАБОТЕ СТЕНДОВ               ║
║       {datetime.now().strftime("%Y-%m-%d %H:%M")}               ║
╚══════════════════════════════════════════════╝

📊 ВРЕМЯ РАБОТЫ СТЕНДОВ (за 7 дней):
"""
        for stand, data in uptime.items():
            color = "🟢" if data["uptime_percent"] > 95 else "🟡" if data["uptime_percent"] > 80 else "🔴"
            report += f"  {color} {stand}: {data['uptime_percent']}% uptime\n"
        
        report += f"""
📱 ПРОШИВКИ (за 30 дней):
  Всего: {flash['total']}
  Успешно: {flash['successful']} | Ошибок: {flash['failed']}
"""
        for stand, count in flash.get("by_stand", {}).items():
            report += f"  • {stand}: {count} прошивок\n"
        
        report += f"""
⚙️ ДЕЙСТВИЯ С ЦВС (за 30 дней):
  Всего: {cvs['total_actions']}
"""
        for action, count in cvs.get("by_action", {}).items():
            report += f"  • {action}: {count} раз\n"
        
        report += f"""
❌ ОШИБКИ (за 30 дней):
  Всего: {errors['total_errors']}
"""
        for etype, count in errors.get("by_type", {}).items():
            report += f"  • {etype}: {count}\n"
        
        return report


class ChecksumCalculator:
    """Класс для расчёта контрольных сумм файлов"""
    
    @staticmethod
    def calculate_md5(file_path):
        """Вычислить MD5 файла"""
        md5_hash = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    md5_hash.update(chunk)
            return md5_hash.hexdigest()
        except Exception as e:
            return f"Ошибка: {e}"
    
    @staticmethod
    def calculate_sha256(file_path):
        """Вычислить SHA256 файла"""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception as e:
            return f"Ошибка: {e}"
    
    @staticmethod
    def calculate_crc32(file_path):
        """Вычислить CRC32 файла"""
        try:
            with open(file_path, "rb") as f:
                content = f.read()
            return format(hashlib.crc32(content) & 0xFFFFFFFF, '08x')
        except Exception as e:
            return f"Ошибка: {e}"
    
    @staticmethod
    def remote_checksum(ssh, file_path, algorithm="md5sum"):
        """Вычислить контрольную сумму файла на удалённом сервере"""
        try:
            command = f"{algorithm} {file_path}"
            stdin, stdout, stderr = ssh.exec_command(command)
            output = stdout.read().decode().strip()
            return output.split()[0] if output else "Ошибка"
        except Exception as e:
            return f"Ошибка: {e}"
    
    @staticmethod
    def get_directory_checksums(ssh, directory="/home/pkrv/CVS"):
        """Получить контрольные суммы всех файлов в директории"""
        try:
            # Получаем список файлов
            command = f"ls -1 {directory}"
            stdin, stdout, stderr = ssh.exec_command(command)
            files = stdout.read().decode().strip().split('\n')
            
            results = {}
            for filename in files:
                if filename:
                    filepath = f"{directory}/{filename}"
                    md5 = ChecksumCalculator.remote_checksum(ssh, filepath, "md5sum")
                    sha256 = ChecksumCalculator.remote_checksum(ssh, filepath, "sha256sum")
                    
                    results[filename] = {
                        "path": filepath,
                        "md5": md5,
                        "sha256": sha256,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
            
            return results
        except Exception as e:
            return {"error": str(e)}
