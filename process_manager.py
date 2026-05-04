"""
Модуль для управления системными процессами
Позволяет останавливать, запускать и перезапускать процессы
"""

import subprocess
import logging
import signal
import psutil
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class ProcessManager:
    """Класс для управления процессами в системе"""
    
    def __init__(self):
        self._process_cache = {}
    
    def find_process_by_name(self, process_name: str) -> Optional[psutil.Process]:
        """Найти процесс по имени"""
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if process_name.lower() in proc.info['name'].lower() or \
                   any(process_name.lower() in cmd.lower() for cmd in proc.info['cmdline'] or []):
                    return proc
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return None
    
    def stop_process(self, process_name: str) -> bool:
        """Остановить процесс"""
        proc = self.find_process_by_name(process_name)
        if proc:
            try:
                proc.terminate()  # мягкое завершение
                proc.wait(timeout=5)
                logger.info(f"Процесс {process_name} (PID: {proc.pid}) остановлен")
                return True
            except psutil.TimeoutExpired:
                proc.kill()  # принудительно
                logger.warning(f"Процесс {process_name} не отвечал, убит принудительно")
                return True
            except Exception as e:
                logger.error(f"Ошибка остановки процесса {process_name}: {e}")
                return False
        logger.warning(f"Процесс {process_name} не найден")
        return False
    
    def start_process(self, command: str, args: List[str] = None) -> bool:
        """Запустить новый процесс по команде"""
        try:
            cmd = [command] + (args or [])
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            logger.info(f"Запущен процесс {command} с PID: {process.pid}")
            return True
        except Exception as e:
            logger.error(f"Ошибка запуска процесса {command}: {e}")
            return False
    
    def restart_process(self, process_name: str, start_command: str = None) -> bool:
        """
        Перезапустить процесс
        process_name: имя процесса для остановки
        start_command: команда для запуска (если не указана, используется имя процесса)
        """
        if not self.stop_process(process_name):
            logger.warning(f"Не удалось остановить {process_name}, попытка принудительного завершения")
        
        cmd_to_start = start_command or process_name
        return self.start_process(cmd_to_start)
    
    def list_all_processes(self) -> List[Dict]:
        """Получить список всех процессов с информацией"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return processes
