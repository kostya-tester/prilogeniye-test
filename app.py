"""
Модуль для работы с прошивками и папкой CVS
Обеспечивает прошивку выбранных стендов
"""

import os
import logging
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class FirmwareFlasher:
    """Класс для управления прошивками стендов"""
    
    def __init__(self, firmware_path: str = "/home/pkrv/CVS"):
        self.firmware_path = Path(firmware_path)
        
    def list_available_firmwares(self, extensions: List[str] = None) -> List[Dict]:
        """
        Получить список доступных прошивок из папки CVS
        extensions: список расширений файлов (по умолчанию: bin, hex, elf, img)
        """
        if not self.firmware_path.exists():
            raise FileNotFoundError(f"Папка {self.firmware_path} не существует")
        
        if extensions is None:
            extensions = ['bin', 'hex', 'elf', 'img']
        
        firmware_files = []
        for ext in extensions:
            pattern = f"*.{ext}"
            firmware_files.extend(self.firmware_path.glob(pattern))
        
        result = []
        for f in firmware_files:
            stat = f.stat()
            result.append({
                'name': f.name,
                'path': str(f),
                'size_bytes': stat.st_size,
                'size_kb': round(stat.st_size / 1024, 2),
                'modified_timestamp': stat.st_mtime,
                'modified_date': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'extension': f.suffix[1:],
                'is_ready': self._check_firmware_validity(f)
            })
        
        return sorted(result, key=lambda x: x['modified_timestamp'], reverse=True)
    
    def get_firmware_info(self, filename: str) -> Optional[Dict]:
        """Получить детальную информацию о конкретном файле прошивки"""
        filepath = self.firmware_path / filename
        
        if not filepath.exists():
            return None
        
        stat = filepath.stat()
        return {
            'name': filepath.name,
            'path': str(filepath),
            'size_bytes': stat.st_size,
            'size_kb': round(stat.st_size / 1024, 2),
            'size_mb': round(stat.st_size / (1024 * 1024), 2),
            'modified_date': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'extension': filepath.suffix[1:],
            'is_valid': self._check_firmware_validity(filepath)
        }
    
    def _check_firmware_validity(self, filepath: Path) -> bool:
        """Проверить валидность файла прошивки (базовая проверка)"""
        try:
            # Проверяем, что файл не пустой
            if filepath.stat().st_size == 0:
                return False
            
            # Проверка магических чисел для бинарных файлов
            with open(filepath, 'rb') as f:
                header = f.read(8)
                # Проверка на ELF файл
                if header[:4] == b'\x7fELF':
                    return True
                # Проверка на HEX файл
                if header[:1] == b':':
                    return True
            
            return True
        except Exception as e:
            logger.error(f"Ошибка проверки файла {filepath}: {e}")
            return False
    
    def list_stands_for_flashing(self) -> Dict:
        """Получить список стендов, доступных для прошивки"""
        # Здесь должна быть логика определения доступных стендов
        # В текущей реализации используем данные из stands_monitor
        try:
            from stands_monitor import StandsMonitor
            monitor = StandsMonitor(db=None)  # Упрощенно для примера
            return monitor.get_all_status()
        except Exception as e:
            logger.error(f"Ошибка получения списка стендов: {e}")
            # Возвращаем заглушку с тестовыми данными
            return {
                "stand_1": {"ip": "192.168.1.101", "status": "online", "type": "test"},
                "stand_2": {"ip": "192.168.1.102", "status": "online", "type": "production"},
                "stand_3": {"ip": "192.168.1.103", "status": "offline", "type": "test"}
            }
    
    def flash_stand(self, stand_id: str, firmware_file: str) -> Dict:
        """
        Прошить выбранный стенд выбранной прошивкой
        """
        # Проверяем существование файла прошивки
        firmware_full_path = self.firmware_path / firmware_file
        if not firmware_full_path.exists():
            return {
                "success": False, 
                "error": f"Файл прошивки {firmware_file} не найден в {self.firmware_path}"
            }
        
        # Получаем информацию о стенде
        stands = self.list_stands_for_flashing()
        if stand_id not in stands:
            return {"success": False, "error": f"Стенд {stand_id} не найден"}
        
        stand_info = stands[stand_id]
        if stand_info.get('status') != 'online':
            return {"success": False, "error": f"Стенд {stand_id} недоступен (статус: {stand_info.get('status')})"}
        
        # Логика прошивки (замените под ваше оборудование)
        logger.info(f"Начало прошивки стенда {stand_id} файлом {firmware_file}")
        
        try:
            # ВАРИАНТ 1: Прошивка через SSH (если на стенде Linux)
            # result = self._flash_via_ssh(stand_info['ip'], firmware_full_path)
            
            # ВАРИАНТ 2: Прошивка через HTTP POST
            # result = self._flash_via_http(stand_info['ip'], firmware_full_path)
            
            # ВАРИАНТ 3: Прошивка через копирование на флешку
            # result = self._flash_via_usb(stand_info['ip'], firmware_full_path)
            
            # ВРЕМЕННАЯ ЗАГЛУШКА (замените на реальную логику)
            logger.warning("Используется тестовая прошивка (замените на реальную логику)")
            result = {
                "success": True,
                "output": f"Тестовая прошивка стенда {stand_id} файлом {firmware_file}\nРазмер: {firmware_full_path.stat().st_size} байт"
            }
            
            if result['success']:
                logger.info(f"Стенд {stand_id} успешно прошит")
                return result
            else:
                return {"success": False, "error": result.get('error', 'Неизвестная ошибка прошивки')}
                
        except Exception as e:
            logger.error(f"Ошибка прошивки: {e}")
            return {"success": False, "error": str(e)}
    
    def _flash_via_ssh(self, ip: str, firmware_path: Path) -> Dict:
        """Прошивка через SSH (пример)"""
        try:
            import paramiko
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Подключение (замените пароль/ключ)
            ssh.connect(ip, username='root', password='password', timeout=10)
            
            # Загрузка файла прошивки
            sftp = ssh.open_sftp()
            remote_path = f'/tmp/{firmware_path.name}'
            sftp.put(str(firmware_path), remote_path)
            sftp.close()
            
            # Запуск прошивки
            stdin, stdout, stderr = ssh.exec_command(f'/usr/local/bin/flash.sh {remote_path}')
            output = stdout.read().decode()
            error = stderr.read().decode()
            ssh.close()
            
            if error:
                return {"success": False, "error": error}
            return {"success": True, "output": output}
            
        except ImportError:
            logger.error("Модуль paramiko не установлен. Установите: pip install paramiko")
            return {"success": False, "error": "SSH модуль не доступен"}
        except Exception as e:
            return {"success": False, "error": str(e)}
