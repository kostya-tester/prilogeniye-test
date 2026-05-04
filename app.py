"""
Главный модуль приложения для мониторинга стендов и управления прошивками
"""

import logging
import os
import json
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template_string, jsonify, request

from config import (
    SECRET_KEY, DEBUG, HOST, PORT, LOG_LEVEL,
    LOG_FORMAT, LOGS_DIR, FIRMWARE_PATH, STANDS,
    STANDS_TIMEOUT, ALLOWED_FIRMWARE_EXTENSIONS
)

# ==================== НАСТРОЙКА ЛОГИРОВАНИЯ ====================
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler(LOGS_DIR / "app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ==================== ИНИЦИАЛИЗАЦИЯ FLASK ====================
app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['DEBUG'] = DEBUG

# ==================== КЛАССЫ-ЗАГЛУШКИ (для работы без других модулей) ====================

class StandsMonitor:
    """Класс для мониторинга стендов"""
    def __init__(self, db=None):
        self.db = db
        
    def get_all_status(self):
        """Получить статус всех стендов"""
        import requests
        statuses = {}
        for stand_id, stand_config in STANDS.items():
            if not stand_config.get('enabled', True):
                statuses[stand_id] = {
                    'name': stand_config['name'],
                    'ip': stand_config['ip'],
                    'status': 'disabled',
                    'response_time': 0
                }
                continue
                
            try:
                start_time = datetime.now()
                response = requests.get(f"http://{stand_config['ip']}:{stand_config['port']}", 
                                      timeout=STANDS_TIMEOUT)
                response_time = (datetime.now() - start_time).total_seconds()
                
                if response.status_code == 200:
                    statuses[stand_id] = {
                        'name': stand_config['name'],
                        'ip': stand_config['ip'],
                        'status': 'online',
                        'response_time': round(response_time, 3),
                        'http_code': response.status_code
                    }
                else:
                    statuses[stand_id] = {
                        'name': stand_config['name'],
                        'ip': stand_config['ip'],
                        'status': 'error',
                        'response_time': round(response_time, 3),
                        'http_code': response.status_code
                    }
            except Exception as e:
                statuses[stand_id] = {
                    'name': stand_config['name'],
                    'ip': stand_config['ip'],
                    'status': 'offline',
                    'error': str(e),
                    'response_time': 0
                }
        return statuses
    
    def get_stand_status(self, stand_id):
        """Получить статус конкретного стенда"""
        statuses = self.get_all_status()
        return statuses.get(stand_id)
    
    def get_history(self, stand_id=None, start_date=None, end_date=None):
        """Получить историю (заглушка)"""
        return []


class ProcessManager:
    """Класс для управления процессами"""
    
    def stop_process(self, process_name):
        """Остановить процесс"""
        logger.info(f"Остановка процесса: {process_name}")
        return True
    
    def start_process(self, command, args=None):
        """Запустить процесс"""
        logger.info(f"Запуск процесса: {command}")
        return True
    
    def restart_process(self, process_name, command=None):
        """Перезапустить процесс"""
        logger.info(f"Перезапуск процесса: {process_name}")
        return True
    
    def list_all_processes(self):
        """Список процессов"""
        return [{'pid': 1, 'name': 'system', 'cpu': 0, 'memory': 0}]


class FirmwareFlasher:
    """Класс для работы с прошивками"""
    
    def __init__(self, firmware_path):
        self.firmware_path = Path(firmware_path)
        
    def list_available_firmwares(self, extensions=None):
        """Список доступных прошивок"""
        if extensions is None:
            extensions = ALLOWED_FIRMWARE_EXTENSIONS
        
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
                'modified_date': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'extension': f.suffix[1:]
            })
        
        return sorted(result, key=lambda x: x['modified_date'], reverse=True)
    
    def get_firmware_info(self, filename):
        """Информация о прошивке"""
        filepath = self.firmware_path / filename
        if not filepath.exists():
            return None
        
        stat = filepath.stat()
        return {
            'name': filepath.name,
            'path': str(filepath),
            'size_bytes': stat.st_size,
            'size_kb': round(stat.st_size / 1024, 2),
            'modified_date': datetime.fromtimestamp(stat.st_mtime).isoformat()
        }
    
    def list_stands_for_flashing(self):
        """Список стендов для прошивки"""
        statuses = StandsMonitor().get_all_status()
        stands_list = []
        for stand_id, info in statuses.items():
            stands_list.append({
                'id': stand_id,
                'name': info.get('name', stand_id),
                'ip': info.get('ip'),
                'status': info.get('status'),
                'available': info.get('status') == 'online'
            })
        return stands_list
    
    def flash_stand(self, stand_id, firmware_file):
        """Прошить стенд"""
        # Проверяем существование файла
        firmware_path = self.firmware_path / firmware_file
        if not firmware_path.exists():
            return {"success": False, "error": f"Файл {firmware_file} не найден"}
        
        # Получаем информацию о стенде
        stands = self.list_stands_for_flashing()
        stand_info = next((s for s in stands if s['id'] == stand_id), None)
        
        if not stand_info:
            return {"success": False, "error": f"Стенд {stand_id} не найден"}
        
        if stand_info['status'] != 'online':
            return {"success": False, "error": f"Стенд {stand_id} недоступен"}
        
        # Симуляция прошивки
        logger.info(f"Прошивка стенда {stand_id} файлом {firmware_file}")
        
        return {
            "success": True,
            "output": f"Стенд {stand_id} успешно прошит файлом {firmware_file}\nРазмер: {firmware_path.stat().st_size} байт\nВремя: {datetime.now()}"
        }


# ==================== ВЕБ-ИНТЕРФЕЙС (HTML) ====================

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Мониторинг стендов</title>
    <meta charset="utf-8">
    <style>
        * { box-sizing: border-box; }
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f0f0f0; }
        h1 { color: #333; }
        .container { max-width: 1200px; margin: 0 auto; }
        .card { background: white; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .stands-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; margin-top: 20px; }
        .stand-card { border: 2px solid #ddd; border-radius: 8px; padding: 15px; background: white; }
        .stand-card.online { border-color: #4CAF50; background: #e8f5e9; }
        .stand-card.offline { border-color: #f44336; background: #ffebee; }
        .stand-card.disabled { border-color: #999; background: #f5f5f5; }
        .stand-title { font-size: 18px; font-weight: bold; margin-bottom: 10px; }
        .stand-ip { color: #666; font-size: 12px; margin-bottom: 10px; }
        .status { display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
        .status.online { background: #4CAF50; color: white; }
        .status.offline { background: #f44336; color: white; }
        .response-time { margin-top: 10px; font-size: 12px; color: #666; }
        button { background: #2196F3; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; margin-top: 10px; margin-right: 5px; }
        button:hover { background: #0b7dda; }
        .firmware-list { margin-top: 20px; }
        .firmware-item { padding: 8px; margin: 5px 0; background: #f9f9f9; border-radius: 4px; cursor: pointer; }
        .firmware-item:hover { background: #e0e0e0; }
        .firmware-item.selected { background: #2196F3; color: white; }
        select, input { padding: 8px; margin: 5px; border-radius: 4px; border: 1px solid #ddd; }
        .flash-result { margin-top: 10px; padding: 10px; border-radius: 4px; }
        .flash-result.success { background: #d4edda; color: #155724; }
        .flash-result.error { background: #f8d7da; color: #721c24; }
        .nav-buttons { margin-bottom: 20px; }
        .nav-btn { background: #607D8B; margin-right: 10px; }
        .nav-btn.active { background: #2196F3; }
        .hidden { display: none; }
        pre { background: #f4f4f4; padding: 10px; overflow-x: auto; border-radius: 4px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🖥️ Мониторинг стендов и прошивка</h1>
        
        <div class="nav-buttons">
            <button class="nav-btn active" onclick="showSection('stands')">📡 Статус стендов</button>
            <button class="nav-btn" onclick="showSection('firmware')">📁 Прошивки (CVS)</button>
            <button class="nav-btn" onclick="showSection('processes')">⚙️ Процессы</button>
        </div>
        
        <!-- Секция стендов -->
        <div id="stands-section" class="card">
            <h2>Статус стендов</h2>
            <div id="stands-container" class="stands-grid">Загрузка...</div>
            <button onclick="refreshStands()">🔄 Обновить</button>
        </div>
        
        <!-- Секция прошивок -->
        <div id="firmware-section" class="card hidden">
            <h2>📁 Прошивки из папки: <span id="firmware-path"></span></h2>
            <div>
                <select id="stand-select" style="width: 200px;">
                    <option value="">Выберите стенд...</option>
                </select>
                <div id="firmware-list" class="firmware-list">Загрузка...</div>
                <button onclick="flashSelected()">🔥 Прошить выбранный стенд</button>
                <div id="flash-result"></div>
            </div>
        </div>
        
        <!-- Секция процессов -->
        <div id="processes-section" class="card hidden">
            <h2>⚙️ Управление процессами</h2>
            <div id="processes-container">Загрузка...</div>
        </div>
    </div>
    
    <script>
        let selectedStand = null;
        let selectedFirmware = null;
        
        function showSection(section) {
            document.getElementById('stands-section').classList.add('hidden');
            document.getElementById('firmware-section').classList.add('hidden');
            document.getElementById('processes-section').classList.add('hidden');
            
            document.getElementById(section + '-section').classList.remove('hidden');
            
            document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            
            if (section === 'stands') refreshStands();
            if (section === 'firmware') { loadStandsForFirmware(); loadFirmwares(); }
            if (section === 'processes') loadProcesses();
        }
        
        async function refreshStands() {
            const container = document.getElementById('stands-container');
            container.innerHTML = 'Загрузка...';
            
            try {
                const response = await fetch('/api/stands');
                const data = await response.json();
                
                if (data.success) {
                    container.innerHTML = '';
                    for (const [id, stand] of Object.entries(data.data)) {
                        const statusClass = stand.status === 'online' ? 'online' : (stand.status === 'disabled' ? 'disabled' : 'offline');
                        container.innerHTML += `
                            <div class="stand-card ${statusClass}">
                                <div class="stand-title">${stand.name || id}</div>
                                <div class="stand-ip">IP: ${stand.ip}</div>
                                <div><span class="status ${stand.status}">${stand.status.toUpperCase()}</span></div>
                                ${stand.response_time ? `<div class="response-time">⏱️ ${stand.response_time}с</div>` : ''}
                                ${stand.error ? `<div class="response-time" style="color:red;">❌ ${stand.error}</div>` : ''}
                            </div>
                        `;
                    }
                } else {
                    container.innerHTML = `<p style="color:red;">Ошибка: ${data.error}</p>`;
                }
            } catch (e) {
                container.innerHTML = `<p style="color:red;">Ошибка подключения: ${e.message}</p>`;
            }
        }
        
        async function loadStandsForFirmware() {
            const response = await fetch('/api/firmware/stands');
            const data = await response.json();
            const select = document.getElementById('stand-select');
            
            if (data.success) {
                select.innerHTML = '<option value="">Выберите стенд...</option>';
                data.stands.forEach(stand => {
                    select.innerHTML += `<option value="${stand.id}" ${!stand.available ? 'disabled' : ''}>${stand.name} (${stand.ip}) - ${stand.status}</option>`;
                });
                select.onchange = () => { selectedStand = select.value; };
            }
        }
        
        async function loadFirmwares() {
            const container = document.getElementById('firmware-list');
            container.innerHTML = 'Загрузка...';
            
            const response = await fetch('/api/firmware/list');
            const data = await response.json();
            
            if (data.success) {
                document.getElementById('firmware-path').innerText = data.firmware_path || 'не указан';
                if (data.firmwares.length === 0) {
                    container.innerHTML = '<p>📂 Нет файлов прошивок. Поместите .bin/.hex файлы в папку.</p>';
                } else {
                    container.innerHTML = '<h3>Доступные прошивки:</h3>';
                    data.firmwares.forEach(fw => {
                        container.innerHTML += `
                            <div class="firmware-item" onclick="selectFirmware('${fw.name}')" id="fw-${fw.name}">
                                <strong>${fw.name}</strong> - ${fw.size_kb} KB (${new Date(fw.modified_date).toLocaleString()})
                            </div>
                        `;
                    });
                }
            } else {
                container.innerHTML = `<p style="color:red;">Ошибка: ${data.error}</p>`;
            }
        }
        
        function selectFirmware(name) {
            selectedFirmware = name;
            document.querySelectorAll('.firmware-item').forEach(el => el.classList.remove('selected'));
            document.getElementById(`fw-${name}`).classList.add('selected');
        }
        
        async function flashSelected() {
            if (!selectedStand) {
                alert('Выберите стенд!');
                return;
            }
            if (!selectedFirmware) {
                alert('Выберите прошивку!');
                return;
            }
            
            const resultDiv = document.getElementById('flash-result');
            resultDiv.innerHTML = '🔄 Прошивка...';
            
            const response = await fetch('/api/firmware/flash', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    stand_id: selectedStand,
                    firmware_file: selectedFirmware
                })
            });
            
            const data = await response.json();
            if (data.success) {
                resultDiv.innerHTML = `<div class="flash-result success">✅ ${data.message || 'Успешно!'}<br><pre>${data.output || ''}</pre></div>`;
            } else {
                resultDiv.innerHTML = `<div class="flash-result error">❌ Ошибка: ${data.error}</div>`;
            }
        }
        
        async function loadProcesses() {
            const container = document.getElementById('processes-container');
            container.innerHTML = 'Загрузка...';
            
            const response = await fetch('/api/processes/list');
            const data = await response.json();
            
            if (data.success) {
                container.innerHTML = '<pre>' + JSON.stringify(data.processes, null, 2) + '</pre>';
            } else {
                container.innerHTML = `<p style="color:red;">Ошибка: ${data.error}</p>`;
            }
        }
        
        // Загружаем при старте
        refreshStands();
    </script>
</body>
</html>
'''

# ==================== МАРШРУТЫ (ROUTES) ====================

# Инициализация компонентов
stands_monitor = StandsMonitor()
process_manager = ProcessManager()
firmware_flasher = FirmwareFlasher(FIRMWARE_PATH)

@app.route('/')
def index():
    """Главная страница"""
    return render_template_string(HTML_TEMPLATE)

# API: Стенды
@app.route('/api/stands', methods=['GET'])
def get_stands_status():
    try:
        status = stands_monitor.get_all_status()
        return jsonify({'success': True, 'data': status})
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# API: Список прошивок
@app.route('/api/firmware/list', methods=['GET'])
def list_firmwares():
    try:
        extensions = request.args.get('extensions', '').split(',')
        extensions = [ext for ext in extensions if ext] or ALLOWED_FIRMWARE_EXTENSIONS
        firmwares = firmware_flasher.list_available_firmwares(extensions)
        return jsonify({
            'success': True,
            'firmwares': firmwares,
            'firmware_path': FIRMWARE_PATH
        })
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# API: Список стендов для прошивки
@app.route('/api/firmware/stands', methods=['GET'])
def get_available_stands():
    try:
        stands = firmware_flasher.list_stands_for_flashing()
        return jsonify({'success': True, 'stands': stands})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# API: Прошивка
@app.route('/api/firmware/flash', methods=['POST'])
def flash_firmware():
    try:
        data = request.json
        stand_id = data.get('stand_id')
        firmware_file = data.get('firmware_file')
        
        if not stand_id:
            return jsonify({'success': False, 'error': 'Не указан стенд'}), 400
        if not firmware_file:
            return jsonify({'success': False, 'error': 'Не указана прошивка'}), 400
        
        result = firmware_flasher.flash_stand(stand_id, firmware_file)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Ошибка прошивки: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# API: Список процессов
@app.route('/api/processes/list', methods=['GET'])
def list_processes():
    try:
        processes = process_manager.list_all_processes()
        return jsonify({'success': True, 'processes': processes})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# API: Управление процессами
@app.route('/api/processes/<process_name>/<action>', methods=['POST'])
def manage_process(process_name, action):
    if action not in ['start', 'stop', 'restart']:
        return jsonify({'success': False, 'error': 'Invalid action'}), 400
    
    try:
        if action == 'stop':
            result = process_manager.stop_process(process_name)
        elif action == 'start':
            result = process_manager.start_process(process_name)
        else:
            result = process_manager.restart_process(process_name)
        
        return jsonify({'success': result, 'message': f'Process {action}ed'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# API: Health check
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'firmware_path': FIRMWARE_PATH,
        'firmware_path_exists': os.path.exists(FIRMWARE_PATH)
    })

# ==================== ЗАПУСК ====================

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 Запуск приложения мониторинга стендов")
    print(f"📁 Путь к прошивкам: {FIRMWARE_PATH}")
    print(f"🌐 Сервер: http://{HOST}:{PORT}")
    print("=" * 50)
    
    # Создаём папку для прошивок если её нет
    if not os.path.exists(FIRMWARE_PATH):
        os.makedirs(FIRMWARE_PATH, exist_ok=True)
        print(f"📁 Создана папка для прошивок: {FIRMWARE_PATH}")
        print("   Поместите файлы прошивок (.bin, .hex) в эту папку")
    
    app.run(host=HOST, port=PORT, debug=DEBUG)
