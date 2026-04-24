"""
Модуль для отправки уведомлений на почту
Использует SMTP для отправки писем
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime


class EmailNotifier:
    """Класс для отправки уведомлений на почту"""
    
    def __init__(self):
        # Настройки SMTP (Яндекс почта как пример)
        self.smtp_server = "smtp.yandex.ru"
        self.smtp_port = 587
        self.smtp_user = ""  # Логин от почты-отправителя
        self.smtp_password = ""  # Пароль приложения
        self.from_email = ""  # Адрес отправителя
        
        # Получатели
        self.to_email = "k.kanarejkin@npo-pkrv.ru"
        self.cc_emails = []  # Копии
        self.enabled = False
        
        # Загружаем настройки
        self.load_settings()
    
    def load_settings(self):
        """Загрузка настроек из файла"""
        try:
            settings_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "email_config.txt")
            if os.path.exists(settings_path):
                with open(settings_path, 'r', encoding='utf-8') as f:
                    for line in f.readlines():
                        if '=' in line:
                            key, value = line.strip().split('=', 1)
                            if key == 'smtp_server':
                                self.smtp_server = value
                            elif key == 'smtp_port':
                                self.smtp_port = int(value)
                            elif key == 'smtp_user':
                                self.smtp_user = value
                            elif key == 'smtp_password':
                                self.smtp_password = value
                            elif key == 'from_email':
                                self.from_email = value
                            elif key == 'to_email':
                                self.to_email = value
                            elif key == 'enabled':
                                self.enabled = value.lower() == 'true'
        except Exception as e:
            print(f"Ошибка загрузки настроек почты: {e}")
    
    def save_settings(self):
        """Сохранение настроек в файл"""
        try:
            settings_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "email_config.txt")
            with open(settings_path, 'w', encoding='utf-8') as f:
                f.write(f"smtp_server={self.smtp_server}\n")
                f.write(f"smtp_port={self.smtp_port}\n")
                f.write(f"smtp_user={self.smtp_user}\n")
                f.write(f"smtp_password={self.smtp_password}\n")
                f.write(f"from_email={self.from_email}\n")
                f.write(f"to_email={self.to_email}\n")
                f.write(f"enabled={self.enabled}\n")
        except Exception as e:
            print(f"Ошибка сохранения настроек почты: {e}")
    
    def send_email(self, subject, body, attachments=None, is_html=True):
        """Отправить письмо"""
        if not self.enabled:
            print("[Email] Отправка отключена")
            return False
        
        if not self.smtp_user or not self.smtp_password:
            print("[Email] Не настроены учётные данные SMTP")
            return False
        
        try:
            # Создаём письмо
            msg = MIMEMultipart()
            msg['From'] = self.from_email or self.smtp_user
            msg['To'] = self.to_email
            msg['Subject'] = subject
            
            # Добавляем копии
            if self.cc_emails:
                msg['Cc'] = ', '.join(self.cc_emails)
            
            # Тело письма
            content_type = 'html' if is_html else 'plain'
            msg.attach(MIMEText(body, content_type, 'utf-8'))
            
            # Прикрепляем файлы
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        with open(file_path, 'rb') as attachment:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(attachment.read())
                            encoders.encode_base64(part)
                            filename = os.path.basename(file_path)
                            part.add_header(
                                'Content-Disposition',
                                f'attachment; filename="{filename}"'
                            )
                            msg.attach(part)
            
            # Отправляем
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            print(f"[Email] Письмо отправлено: {subject}")
            return True
            
        except Exception as e:
            print(f"[Email] Ошибка отправки: {e}")
            return False
    
    def send_alert(self, title, message, level="info", attachments=None):
        """Отправить форматированное уведомление"""
        
        # Цвета для разных уровней
        colors = {
            "info": "#2196F3",
            "warning": "#FF9800",
            "error": "#f44336",
            "success": "#4CAF50",
            "critical": "#9C27B0"
        }
        
        # Иконки
        icons = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "🚨",
            "success": "✅",
            "critical": "🔴"
        }
        
        color = colors.get(level, "#2196F3")
        icon = icons.get(level, "ℹ️")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # HTML шаблон письма
        html_body = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #f5f5f5;
                    margin: 0;
                    padding: 20px;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: #ffffff;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .header {{
                    background-color: {color};
                    color: white;
                    padding: 20px;
                    border-radius: 10px 10px 0 0;
                    font-size: 18px;
                    font-weight: bold;
                }}
                .body {{
                    padding: 20px;
                    color: #333333;
                    line-height: 1.6;
                }}
                .footer {{
                    padding: 15px 20px;
                    background-color: #f8f9fa;
                    border-radius: 0 0 10px 10px;
                    font-size: 12px;
                    color: #666666;
                    border-top: 1px solid #e0e0e0;
                }}
                .stand-name {{
                    color: {color};
                    font-weight: bold;
                }}
                .timestamp {{
                    color: #999999;
                    font-size: 12px;
                }}
                pre {{
                    background-color: #f4f4f4;
                    padding: 10px;
                    border-radius: 5px;
                    border-left: 3px solid {color};
                    overflow-x: auto;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    {icon} {title}
                </div>
                <div class="body">
                    {message}
                </div>
                <div class="footer">
                    <strong>НПО ПКРВ</strong> — Система мониторинга стендов<br>
                    <span class="timestamp">📅 {timestamp}</span><br>
                    <span class="timestamp">📧 Отправлено автоматически</span>
                </div>
            </div>
        </body>
        </html>
        """
        
        subject = f"[ПКРВ] {icon} {title}"
        return self.send_email(subject, html_body, attachments)
    
    # ===== СПЕЦИАЛИЗИРОВАННЫЕ УВЕДОМЛЕНИЯ =====
    
    def notify_stand_online(self, stand_name, ip):
        """Уведомление: стенд в сети"""
        self.send_alert(
            f"Стенд {stand_name} в сети",
            f"""
            <p>Стенд <span class="stand-name">{stand_name}</span> доступен.</p>
            <p>📡 IP адрес: <code>{ip}</code></p>
            <p>✅ Все системы работают нормально.</p>
            """,
            "success"
        )
    
    def notify_stand_offline(self, stand_name, ip):
        """Уведомление: стенд не в сети"""
        self.send_alert(
            f"Стенд {stand_name} НЕ В СЕТИ!",
            f"""
            <p>⚠️ Стенд <span class="stand-name">{stand_name}</span> недоступен!</p>
            <p>📡 IP адрес: <code>{ip}</code></p>
            <p>🔴 <b>Требуется немедленная проверка!</b></p>
            <p>Возможные причины:</p>
            <ul>
                <li>Стенд выключен</li>
                <li>Проблемы с сетью</li>
                <li>Аппаратный сбой</li>
            </ul>
            """,
            "critical"
        )
    
    def notify_cvs_started(self, stand_name, ip):
        """Уведомление: ЦВС запущен"""
        self.send_alert(
            f"ЦВС запущен — {stand_name}",
            f"""
            <p>▶ Процесс ЦВС успешно запущен на стенде <span class="stand-name">{stand_name}</span>.</p>
            <p>📡 IP: <code>{ip}</code></p>
            <p>🟢 Статус: <b>Работает</b></p>
            """,
            "success"
        )
    
    def notify_cvs_stopped(self, stand_name, ip):
        """Уведомление: ЦВС остановлен"""
        self.send_alert(
            f"ЦВС остановлен — {stand_name}",
            f"""
            <p>⏹ Процесс ЦВС остановлен на стенде <span class="stand-name">{stand_name}</span>.</p>
            <p>📡 IP: <code>{ip}</code></p>
            <p>🟡 Статус: <b>Остановлен</b></p>
            """,
            "warning"
        )
    
    def notify_cvs_error(self, stand_name, ip, error_details):
        """Уведомление: ошибка ЦВС"""
        self.send_alert(
            f"Ошибка ЦВС — {stand_name}",
            f"""
            <p>🚨 Ошибка при работе с ЦВС на стенде <span class="stand-name">{stand_name}</span>!</p>
            <p>📡 IP: <code>{ip}</code></p>
            <p>Детали ошибки:</p>
            <pre>{error_details}</pre>
            """,
            "error"
        )
    
    def notify_flash_complete(self, stand_name, ip, file_name, success=True):
        """Уведомление о прошивке"""
        if success:
            self.send_alert(
                f"Прошивка завершена — {stand_name}",
                f"""
                <p>✅ Прошивка успешно выполнена на стенде <span class="stand-name">{stand_name}</span>.</p>
                <p>📡 IP: <code>{ip}</code></p>
                <p>📁 Файл: <code>{file_name}</code></p>
                """,
                "success"
            )
        else:
            self.send_alert(
                f"Ошибка прошивки — {stand_name}",
                f"""
                <p>❌ Ошибка прошивки на стенде <span class="stand-name">{stand_name}</span>!</p>
                <p>📡 IP: <code>{ip}</code></p>
                <p>📁 Файл: <code>{file_name}</code></p>
                <p>⚠️ Требуется проверить логи!</p>
                """,
                "error"
            )
    
    def notify_orangepi_found(self, ip, model, os_info):
        """Уведомление о найденном Orange Pi"""
        self.send_alert(
            f"Найден Orange Pi — {ip}",
            f"""
            <p>🍊 Обнаружено новое устройство Orange Pi!</p>
            <p>📡 IP: <code>{ip}</code></p>
            <p>🖥 Модель: <b>{model}</b></p>
            <p>💿 ОС: {os_info}</p>
            """,
            "info"
        )
    
    def notify_daily_report(self, report_text):
        """Отправка ежедневного отчёта"""
        self.send_alert(
            "Ежедневный отчёт мониторинга",
            report_text.replace('\n', '<br>').replace(' ', '&nbsp;'),
            "info"
        )
    
    def notify_error_general(self, error_type, details, stand_name=None):
        """Общее уведомление об ошибке"""
        stand_info = f"Стенд: <span class=\"stand-name\">{stand_name}</span><br>" if stand_name else ""
        
        self.send_alert(
            f"Ошибка: {error_type}",
            f"""
            <p>🚨 Произошла ошибка в системе мониторинга!</p>
            {stand_info}
            <p>Тип ошибки: <b>{error_type}</b></p>
            <p>Детали:</p>
            <pre>{details}</pre>
            <p>📅 Время: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            """,
            "error"
        )
    
    def test_connection(self):
        """Проверка подключения к почтовому серверу"""
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=5) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                return True, "Подключение успешно"
        except Exception as e:
            return False, str(e)
