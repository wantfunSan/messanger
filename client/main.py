import sys
import os
import time
import subprocess
import zipfile
import requests
import threading
from datetime import datetime
from pathlib import Path
from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread

from cryptography.fernet import Fernet

from PyQt6.QtWidgets import (
	QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
	QListWidget, QListWidgetItem, QTextEdit, QLineEdit, QPushButton,
	QDialog, QDialogButtonBox, QFormLayout, QLabel, QFileDialog,
	QMenuBar, QMenu, QMessageBox, QComboBox, QGridLayout,
	QGraphicsOpacityEffect, QSystemTrayIcon, QStackedWidget, QFrame, QProgressDialog, QProgressBar
)
from PyQt6.QtCore import Qt, QUrl, QPropertyAnimation, QEasingCurve, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import (
	QPixmap, QTextCursor, QIcon, QDesktopServices, QAction,
	QPainter, QBrush, QPen, QFont
)

# ========================== ШИФРОВАНИЕ ==========================
# (из shifratory.py)
key = Fernet.generate_key()
cipher_suite = Fernet(key)

shifratory = {
	'key': key,
	'cipher_suite': cipher_suite
}

def update_key():
	global key, cipher_suite, shifratory
	key = Fernet.generate_key()
	cipher_suite = Fernet(key)
	shifratory['key'] = key
	shifratory['cipher_suite'] = cipher_suite

# ========================== ОКНО ВХОДА ==========================
class LoginWindow(QDialog):
	def __init__(self):
		super().__init__()
		self.setWindowTitle("Nebula — Вход")
		self.setFixedSize(440, 520)
		self.current_user = None
		self.current_phone = None
		self.right_password = None

		# Градиент через стиль
		self.setStyleSheet("""
			QDialog {
				background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
					stop:0 #4a90e2, stop:1 #7c3aed);
			}
		""")

		# Карточка
		self.card = QFrame(self)
		self.card.setGeometry(35, 75, 370, 370)
		self.card.setStyleSheet("""
			QFrame {
				background-color: white;
				border-radius: 10px;
				border: 1px solid #d0d0d0;
			}
		""")
		self.shadow = QFrame(self)
		self.shadow.setGeometry(38, 78, 370, 370)
		self.shadow.setStyleSheet("background-color: #d0d0d0; border-radius: 10px;")
		self.shadow.lower()

		# Заголовок
		title = QLabel("✨ Добро пожаловать!", self.card)
		title.setGeometry(0, 15, 370, 30)
		title.setAlignment(Qt.AlignmentFlag.AlignCenter)
		title.setStyleSheet("font-size: 18px; font-weight: bold; color: #a855f7;")

		# Кнопки вкладок
		self.btn_login = QPushButton("Вход", self.card)
		self.btn_login.setGeometry(20, 60, 165, 40)
		self.btn_login.setStyleSheet("""
			QPushButton {
				background-color: #0088cc;
				color: white;
				border: none;
				border-radius: 5px;
				font-weight: bold;
			}
			QPushButton:hover {
				background-color: #0077b3;
			}
		""")
		self.btn_login.clicked.connect(lambda: self.stack.setCurrentIndex(0))

		self.btn_register = QPushButton("Регистрация", self.card)
		self.btn_register.setGeometry(185, 60, 165, 40)
		self.btn_register.setStyleSheet("""
			QPushButton {
				background-color: #e2e8f0;
				color: #222222;
				border: none;
				border-radius: 5px;
				font-weight: bold;
			}
			QPushButton:hover {
				background-color: #cbd5e1;
			}
		""")
		self.btn_register.clicked.connect(lambda: self.stack.setCurrentIndex(1))

		# Стек
		self.stack = QStackedWidget(self.card)
		self.stack.setGeometry(20, 110, 330, 240)

		# Страница входа
		login_widget = QWidget()
		login_layout = QVBoxLayout(login_widget)
		login_layout.setSpacing(10)
		login_layout.setContentsMargins(0, 10, 0, 10)

		self.login_phone = QLineEdit()
		self.login_phone.setPlaceholderText("Номер телефона")
		self.login_phone.setStyleSheet("padding: 8px; border: 1px solid #ccc; border-radius: 5px;")
		self.login_password = QLineEdit()
		self.login_password.setPlaceholderText("Пароль")
		self.login_password.setEchoMode(QLineEdit.EchoMode.Password)
		self.login_password.setStyleSheet("padding: 8px; border: 1px solid #ccc; border-radius: 5px;")

		login_btn = QPushButton("Войти")
		login_btn.setStyleSheet("""
			QPushButton {
				background-color: #0088cc;
				color: white;
				border: none;
				padding: 10px;
				border-radius: 5px;
				font-weight: bold;
			}
			QPushButton:hover {
				background-color: #0077b3;
			}
		""")
		login_btn.clicked.connect(self.do_login)

		switch_to_register = QPushButton("Нет аккаунта? Зарегистрироваться")
		switch_to_register.setFlat(True)
		switch_to_register.setStyleSheet("color: #0088cc; text-decoration: underline;")
		switch_to_register.clicked.connect(lambda: self.stack.setCurrentIndex(1))

		login_layout.addWidget(self.login_phone)
		login_layout.addWidget(self.login_password)
		login_layout.addWidget(login_btn)
		login_layout.addWidget(switch_to_register)
		login_layout.addStretch()
		self.stack.addWidget(login_widget)

		# Страница регистрации
		register_widget = QWidget()
		register_layout = QVBoxLayout(register_widget)
		register_layout.setSpacing(10)
		register_layout.setContentsMargins(0, 10, 0, 10)

		self.reg_phone = QLineEdit()
		self.reg_phone.setPlaceholderText("Номер телефона")
		self.reg_phone.setStyleSheet("padding: 8px; border: 1px solid #ccc; border-radius: 5px;")
		self.reg_username = QLineEdit()
		self.reg_username.setPlaceholderText("Имя пользователя")
		self.reg_username.setStyleSheet("padding: 8px; border: 1px solid #ccc; border-radius: 5px;")
		self.reg_password = QLineEdit()
		self.reg_password.setPlaceholderText("Пароль")
		self.reg_password.setEchoMode(QLineEdit.EchoMode.Password)
		self.reg_password.setStyleSheet("padding: 8px; border: 1px solid #ccc; border-radius: 5px;")
		self.reg_confirm = QLineEdit()
		self.reg_confirm.setPlaceholderText("Подтверждение пароля")
		self.reg_confirm.setEchoMode(QLineEdit.EchoMode.Password)
		self.reg_confirm.setStyleSheet("padding: 8px; border: 1px solid #ccc; border-radius: 5px;")

		register_btn = QPushButton("Зарегистрироваться")
		register_btn.setStyleSheet("""
			QPushButton {
				background-color: #0088cc;
				color: white;
				border: none;
				padding: 10px;
				border-radius: 5px;
				font-weight: bold;
			}
			QPushButton:hover {
				background-color: #0077b3;
			}
		""")
		register_btn.clicked.connect(self.do_register)

		switch_to_login = QPushButton("Уже есть аккаунт? Войти")
		switch_to_login.setFlat(True)
		switch_to_login.setStyleSheet("color: #0088cc; text-decoration: underline;")
		switch_to_login.clicked.connect(lambda: self.stack.setCurrentIndex(0))

		register_layout.addWidget(self.reg_phone)
		register_layout.addWidget(self.reg_username)
		register_layout.addWidget(self.reg_password)
		register_layout.addWidget(self.reg_confirm)
		register_layout.addWidget(register_btn)
		register_layout.addWidget(switch_to_login)
		register_layout.addStretch()
		self.stack.addWidget(register_widget)

		# Ошибка
		self.error_label = QLabel(self.card)
		self.error_label.setGeometry(20, 350, 330, 30)
		self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
		self.error_label.setStyleSheet("color: red;")

		self.stack.setCurrentIndex(0)
		self.update_tab_style()

		# Enter
		self.login_phone.returnPressed.connect(self.do_login)
		self.login_password.returnPressed.connect(self.do_login)
		self.reg_phone.returnPressed.connect(self.do_register)
		self.reg_username.returnPressed.connect(self.do_register)
		self.reg_password.returnPressed.connect(self.do_register)
		self.reg_confirm.returnPressed.connect(self.do_register)

	def update_tab_style(self):
		if self.stack.currentIndex() == 0:
			self.btn_login.setStyleSheet("""
				QPushButton {
					background-color: #0088cc;
					color: white;
					border: none;
					border-radius: 5px;
					font-weight: bold;
				}
				QPushButton:hover { background-color: #0077b3; }
			""")
			self.btn_register.setStyleSheet("""
				QPushButton {
					background-color: #e2e8f0;
					color: #222222;
					border: none;
					border-radius: 5px;
					font-weight: bold;
				}
				QPushButton:hover { background-color: #cbd5e1; }
			""")
		else:
			self.btn_login.setStyleSheet("""
				QPushButton {
					background-color: #e2e8f0;
					color: #222222;
					border: none;
					border-radius: 5px;
					font-weight: bold;
				}
				QPushButton:hover { background-color: #cbd5e1; }
			""")
			self.btn_register.setStyleSheet("""
				QPushButton {
					background-color: #0088cc;
					color: white;
					border: none;
					border-radius: 5px;
					font-weight: bold;
				}
				QPushButton:hover { background-color: #0077b3; }
			""")

	def do_login(self):
		phone = self.login_phone.text().strip()
		password = self.login_password.text().strip()
		if not phone or not password:
			self.error_label.setText("⚠️ Заполните все поля")
			return

		try:
			HOST = 'vlahouse.ru'
			PORT = 12345
			BUFSIZ = 1024
			ADDR = (HOST, PORT)
			client_socket = socket(AF_INET, SOCK_STREAM)
			client_socket.connect(ADDR)

			data2send = f'func=log phone={phone} password={password} _ver_'
			data2send = shifratory['cipher_suite'].encrypt(bytes(data2send, 'utf8'))
			client_socket.send(data2send)

			res = client_socket.recv(BUFSIZ).decode("utf8")
			key = res.encode()
			res = bytes(res, 'utf8')
			cipher_suite = Fernet(key)
			res = cipher_suite.decrypt(res).decode('utf-8')

			if 'open ' in res:
				try:
					username = res.split(' ')[1]
					with open('SocialNet_Data/data.ini', 'w+', encoding='utf8') as f:
						f.write(f'phone={phone}\npass={password}\nuse={username}\n')
					client_socket.close()
					self.current_user = username
					self.current_phone = phone
					self.right_password = password
					self.accept()
				except Exception as e:
					print(e)
			elif res == 'closed pass':
				self.error_label.setText("❌ Неверный пароль")
				return
			elif res == 'closed no':
				self.error_label.setText("❌ Пользователь не найден")
				return
			else:
				self.error_label.setText("❌ Ошибка сервера")
				return
		except Exception as e:
			self.error_label.setText(f"❌ Ошибка: {e}")
		finally:
			try:
				client_socket.close()
			except:
				pass
			update_key()

	def do_register(self):
		phone = self.reg_phone.text().strip()
		username = self.reg_username.text().strip()
		password = self.reg_password.text().strip()
		confirm = self.reg_confirm.text().strip()
		if not phone or not username or not password or not confirm:
			self.error_label.setText("⚠️ Заполните все поля")
			return
		if password != confirm:
			self.error_label.setText("❌ Пароли не совпадают")
			return
		if ' ' in phone or ' ' in username or ' ' in password:
			self.error_label.setText("❌ Не должно быть пробелов")
			return

		try:
			HOST = 'vlahouse.ru'
			PORT = 12345
			BUFSIZ = 1024
			ADDR = (HOST, PORT)
			client_socket = socket(AF_INET, SOCK_STREAM)
			client_socket.connect(ADDR)

			data2send = f'func=reg phone={phone} username={username} password={password} _ver_'
			data2send = shifratory['cipher_suite'].encrypt(bytes(data2send, 'utf8'))
			client_socket.send(data2send)

			res = client_socket.recv(BUFSIZ).decode("utf8")
			key = res.encode()
			res = bytes(res, 'utf8')
			cipher_suite = Fernet(key)
			res = cipher_suite.decrypt(res).decode('utf-8')

			if res == 'open':
				with open('SocialNet_Data/data.ini', 'w+', encoding='utf8') as f:
					f.write(f'phone={phone}\npass={password}\nuse={username}\n')
				client_socket.close()
				self.current_user = username
				self.current_phone = phone
				self.accept()
			elif res == 'closed yes':
				self.error_label.setText("❌ Номер уже зарегистрирован")
			else:
				self.error_label.setText("❌ Ошибка сервера")
		except Exception as e:
			self.error_label.setText(f"❌ Ошибка: {e}")
		finally:
			try:
				client_socket.close()
			except:
				pass
			update_key()


# ========================== ОКНО ЧАТОВ ==========================
class AddContactDialog(QDialog):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.setWindowTitle("Добавить контакт")
		self.setFixedSize(300, 120)
		layout = QFormLayout(self)
		self.name_edit = QLineEdit()
		self.name_edit.setPlaceholderText("Введите номер телефона")
		layout.addRow("Телефон:", self.name_edit)
		buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
		buttons.accepted.connect(self.accept)
		buttons.rejected.connect(self.reject)
		layout.addRow(buttons)
		self.name_edit.setFocus()

	def get_contact_phone(self):
		return self.name_edit.text().strip()


class SettingsDialog(QDialog):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.setWindowTitle("Настройки")
		self.setFixedSize(500, 350)
		layout = QVBoxLayout(self)

		theme_layout = QHBoxLayout()
		theme_label = QLabel("Тема:")
		self.theme_combo = QComboBox()
		self.theme_combo.addItems(["Тёмная фиолетовая", "Тёмная синяя", "Светлая", "Ночная"])
		theme_layout.addWidget(theme_label)
		theme_layout.addWidget(self.theme_combo)
		layout.addLayout(theme_layout)

		wallpaper_layout = QHBoxLayout()
		self.wallpaper_label = QLabel("Не выбрано")
		self.wallpaper_label.setWordWrap(True)
		choose_btn = QPushButton("Выбрать изображение")
		choose_btn.clicked.connect(self.choose_wallpaper)
		clear_btn = QPushButton("Сбросить обои")
		clear_btn.clicked.connect(self.clear_wallpaper)
		wallpaper_layout.addWidget(QLabel("Обои:"))
		wallpaper_layout.addWidget(self.wallpaper_label, 1)
		wallpaper_layout.addWidget(choose_btn)
		wallpaper_layout.addWidget(clear_btn)
		layout.addLayout(wallpaper_layout)

		discord_layout = QHBoxLayout()
		discord_label = QLabel("Discord сервер:")
		discord_btn = QPushButton("Присоединиться")
		discord_btn.setStyleSheet("background-color: #5865F2; color: white; font-weight: bold; border-radius: 5px;")
		discord_btn.clicked.connect(self.open_discord)
		discord_layout.addWidget(discord_label)
		discord_layout.addWidget(discord_btn)
		discord_layout.addStretch()
		layout.addLayout(discord_layout)

		buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
		buttons.accepted.connect(self.accept)
		buttons.rejected.connect(self.reject)
		layout.addWidget(buttons)

		self.wallpaper_path = None
		self.load_settings()

	def load_settings(self):
		main = self.parent()
		if main:
			theme_map = {"dark_purple": 0, "dark_blue": 1, "light": 2, "night": 3}
			idx = theme_map.get(main.current_theme, 0)
			self.theme_combo.setCurrentIndex(idx)
			if main.wallpaper_path:
				self.wallpaper_path = main.wallpaper_path
				self.wallpaper_label.setText(os.path.basename(main.wallpaper_path))

	def choose_wallpaper(self):
		file_path, _ = QFileDialog.getOpenFileName(
			self, "Выберите изображение", "",
			"Images (*.png *.jpg *.jpeg *.bmp *.gif)"
		)
		if file_path:
			self.wallpaper_path = file_path
			self.wallpaper_label.setText(os.path.basename(file_path))

	def clear_wallpaper(self):
		self.wallpaper_path = None
		self.wallpaper_label.setText("Не выбрано")

	def get_settings(self):
		theme_map = {0: "dark_purple", 1: "dark_blue", 2: "light", 3: "night"}
		theme = theme_map[self.theme_combo.currentIndex()]
		return theme, self.wallpaper_path

	def open_discord(self):
		QDesktopServices.openUrl(QUrl("https://discord.gg/5PzDUgV8sm"))

class UpdateThread(QThread):
	progress = pyqtSignal(int, str)	  # процент, статус
	finished = pyqtSignal(bool, str)	 # успех, сообщение/путь

	def __init__(self, latest):
		super().__init__()
		self.url = 'http://vlahouse.ru/assets/apps/Social Network.zip'
		self.downloads_path = str(Path.home() / "Downloads") + "\\Social Network.zip"
		self.latest = latest

	def run(self):
		response = requests.get(self.url, stream=True)
		new_folder1 = str(Path.home() / "Downloads")
		new_folder2 = str(Path.home() / "Downloads") + f"\\Social Network-{self.latest}"
								
		if response.status_code == 200:
			response = requests.get(self.url, stream=True)
			total_size = int(response.headers.get('content-length', 0))
			block_size = 8192
			downloaded = 0
			with open(self.downloads_path, 'wb') as f:
				for chunk in response.iter_content(chunk_size=block_size):
					if chunk:
						f.write(chunk)
						downloaded += len(chunk)
						if total_size > 0:
							percent = int(downloaded * 100 / total_size)
							self.progress.emit(percent, f"Загружено {downloaded // 1024} КБ из {total_size // 1024} КБ")
			self.progress.emit(0, f"Подготовка к распаковке..")
						
			try:
				with zipfile.ZipFile(self.downloads_path, 'r') as zip_ref:
					file_list = zip_ref.namelist()
					total_files = len(file_list)
					for i, file_name in enumerate(file_list):
						percent = int((i + 1) * 100 / total_files)
						self.progress.emit(percent, f"Распаковка: {file_name}")
						zip_ref.extract(file_name, new_folder1)
				self.progress.emit(0, f"Удаляю временные файлы...") 
				os.remove(self.downloads_path)
				
										
				with zipfile.ZipFile(new_folder1 + "\\Social Network(no pswd).zip") as zip_ref2:
					file_list = zip_ref2.namelist()
					total_files = len(file_list)
					for i, file_name in enumerate(file_list):
						zip_ref2.extract(file_name, new_folder1)
						percent = int((i + 1) * 100 / total_files)
						self.progress.emit(percent, f"Распаковка: {file_name}")
				
				self.progress.emit(100, f"Удаляю временные файлы...")				
				os.remove(new_folder1 + "\\Social Network(no pswd).zip")
				print(new_folder2)
				self.finished.emit(True, new_folder2)
			except Exception as err:
				#QMessageBox.critical(self, "Ошибка", "Не удалось загрузить обновление.")
				self.finished.emit(False, str(err))

class UpdateDialog(QDialog):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.setWindowTitle("Обновление")
		self.setModal(True)
		self.setFixedSize(400, 150)
		layout = QVBoxLayout(self)

		self.status_label = QLabel("Подготовка к загрузке...")
		self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
		layout.addWidget(self.status_label)

		self.progress_bar = QProgressBar()
		self.progress_bar.setRange(0, 100)
		self.progress_bar.setValue(0)
		layout.addWidget(self.progress_bar)

		self.cancel_btn = QPushButton("Отмена")
		self.cancel_btn.clicked.connect(self.reject)
		layout.addWidget(self.cancel_btn)

		self.thread = None

	def start_download(self, latest):
		self.thread = UpdateThread(latest)
		self.thread.progress.connect(self.update_progress)
		self.thread.finished.connect(self.download_finished)
		self.thread.start()
		self.timer = QTimer()
		self.timer.timeout.connect(lambda: QApplication.processEvents())
		self.timer.start(1)

	def update_progress(self, percent, status):
		self.progress_bar.setValue(percent)
		self.status_label.setText(status)
		QApplication.processEvents()

	def download_finished(self, success, message):
		if success:
			print('finished')
			QMessageBox.information(self, "Обновлено", "Перед запуском новой версии, не забудьте удалить старую!")
			subprocess.Popen(r'explorer /select,"' + message + '\\Social Network.exe"')
			sys.exit()
		else:
			QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить обновление: {message}")
			self.reject()

	def closeEvent(self, event):
		if self.thread and self.thread.isRunning():
			self.thread.terminate()
			self.thread.wait()
		event.accept()


class ChatApp(QMainWindow):
	message_received = pyqtSignal(str, str, str)  # contact, sender, text
	new_chat_created = pyqtSignal(str)
	def __init__(self, current_user, phone_number, right_password):
		super().__init__()
		self.current_user = current_user
		self.phone_number = phone_number
		self.right_password = right_password
		self.current_contact = None
		self.wallpaper_path = None
		self.current_theme = "dark_purple"
		self.colors = self.get_theme_colors(self.current_theme)
		self.chats = []
		self.messages = {}

		self.tray_icon = None
		self.create_tray_icon()

		self.check_update()
		self.fetch_chats()

		self.init_ui()
		self.apply_theme()
		self.update_wallpaper()

		self.message_received.connect(self.on_message_received)

		self.receive_thread = Thread(target=self.receive2, daemon=True)
		self.receive_thread.start()

	# ------------------ Сетевая логика ------------------

	def check_update(self):
		try:
			HOST = 'vlahouse.ru'
			PORT = 12345
			BUFSIZ = 1024
			ADDR = (HOST, PORT)

			client_socket = socket(AF_INET, SOCK_STREAM)
			client_socket.connect(ADDR)
			data2send = shifratory['cipher_suite'].encrypt(b'version=beta_1.0.1')
			client_socket.send(data2send)
			res = client_socket.recv(BUFSIZ).decode("utf8")
			key = res.encode()
			res = bytes(res, 'utf8')
			cipher_suite = Fernet(key)
			res = cipher_suite.decrypt(res).decode('utf-8')
			if 'outdated' in res:
				reply = QMessageBox.question(self, "Обновление", "Версия устарела. Обновить?",
											 QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
				if reply == QMessageBox.StandardButton.Yes:
					latest = res.split('=')[1]
					dialog = UpdateDialog(self)
					dialog.show()
					dialog.start_download(latest)
				else:
					sys.exit()
			client_socket.close()
		except Exception as e:
			print(f"Ошибка обновления: {e}")

	def fetch_chats(self):
		try:
			HOST = 'vlahouse.ru'
			PORT = 12345
			BUFSIZ = 1024
			ADDR = (HOST, PORT)
			client_socket = socket(AF_INET, SOCK_STREAM)
			client_socket.connect(ADDR)
			data2send = shifratory['cipher_suite'].encrypt(bytes(f'func=chat phone={self.phone_number} password={self.right_password} _ver_', 'utf8'))
			client_socket.send(data2send)
			res = client_socket.recv(BUFSIZ).decode("utf8")
			key = res.encode()
			res = bytes(res, 'utf8')
			cipher_suite = Fernet(key)
			res = cipher_suite.decrypt(res).decode('utf-8')
			if 'open ' in res:
				chats_str = res.replace('open ', '')
				if chats_str == 'None':
					self.chats = []
				else:
					self.chats = chats_str.split(' ')
			else:
				self.chats = []
			client_socket.close()
		except Exception as e:
			print(f"Ошибка получения чатов: {e}")
			self.chats = []
		for chat in self.chats:
			if chat not in self.messages:
				self.messages[chat] = []

	def receive2(self):
		while True:
			try:
				HOST = 'vlahouse.ru'
				PORT = 12345
				BUFSIZ = 1024
				ADDR = (HOST, PORT)
				client_socket = socket(AF_INET, SOCK_STREAM)
				client_socket.connect(ADDR)
				data2send = shifratory['cipher_suite'].encrypt(bytes(f'update2 {self.phone_number} _ver_', 'utf8'))
				client_socket.send(data2send)
				msg = client_socket.recv(BUFSIZ).decode("utf8")
				key = msg.encode()
				msg = bytes(msg, 'utf8')
				cipher_suite = Fernet(key)
				msg = cipher_suite.decrypt(msg).decode('utf-8')
				if 'make' in msg:
					new_chat = msg.split(' ')[1]
					if new_chat not in self.chats:
						self.chats.append(new_chat)
						self.messages[new_chat] = []
						self.contact_list.addItem(new_chat)
						self.show_notification("🆕 Новый чат", f"Добавлен чат с {new_chat}")
			except Exception as e:
				print(f"Receive2 error: {e}")
			time.sleep(5)
			update_key()

	def receive_messages(self, chat_name):
		try:
			HOST = 'vlahouse.ru'
			PORT = 12345
			BUFSIZ = 1024
			ADDR = (HOST, PORT)
			client_socket = socket(AF_INET, SOCK_STREAM)
			client_socket.connect(ADDR)
			data2send = shifratory['cipher_suite'].encrypt(bytes(f'update {self.phone_number} _ver_', 'utf8'))
			client_socket.send(data2send)
			while True:
				msg = client_socket.recv(BUFSIZ).decode("utf8")
				key = msg.encode()
				msg = bytes(msg, 'utf8')
				cipher_suite = Fernet(key)
				msg = cipher_suite.decrypt(msg).decode('utf-8')
				msg = msg.split(' ')
				if msg[0] == chat_name:
					data2send = shifratory['cipher_suite'].encrypt(b'ok _ver_')
					client_socket.send(data2send)
					msg_text = client_socket.recv(BUFSIZ).decode("utf8")
					key = msg_text.encode()
					msg_text = bytes(msg_text, 'utf8')
					cipher_suite = Fernet(key)
					msg_text = cipher_suite.decrypt(msg_text).decode('utf-8')
					self.message_received.emit(chat_name, chat_name, msg_text)
				else:
					data2send = shifratory['cipher_suite'].encrypt(b'not need chat _ver_')
					client_socket.send(data2send)
		except Exception as e:
			print(f"Receive messages error: {e}")
		update_key()

	def send_message_to_server(self, chat_name, msg):
		try:
			HOST = 'vlahouse.ru'
			PORT = 12345
			BUFSIZ = 1024
			ADDR = (HOST, PORT)

			client_socket = socket(AF_INET, SOCK_STREAM)
			client_socket.connect(ADDR)
			data2send = shifratory['cipher_suite'].encrypt(bytes(f'{msg} @{chat_name} @{self.current_user} _ver_', "utf8"))
			client_socket.send(data2send)
			resp = client_socket.recv(BUFSIZ).decode("utf8")
			key = resp.encode()
			resp = bytes(resp, 'utf8')
			cipher_suite = Fernet(key)
			resp = cipher_suite.decrypt(resp).decode('utf-8')
			if resp == 'sended':
				now = datetime.now().strftime("%H:%M")
				self.messages[chat_name].append({"user": self.current_user, "text": msg, "time": now})
				self.load_messages()
			elif resp == 'non active':
				QMessageBox.warning(self, "Ошибка", "Пользователь не в сети")
			elif resp == 'not need chat':
				QMessageBox.warning(self, "Ошибка", "Пользователь в другом чате")
			client_socket.close()
		except Exception as e:
			print(f"Send error: {e}")
		update_key()

	def on_message_received(self, contact, sender, text):
		"""Обработчик получения нового сообщения (выполняется в главном потоке)."""
		if contact not in self.messages:
			self.messages[contact] = []
		now = datetime.now().strftime("%H:%M")
		self.messages[contact].append({"user": sender, "text": text, "time": now})
		if self.current_contact == contact:
			self.load_messages()
		if not self.isActiveWindow() or self.isMinimized():
			self.show_notification(f"📩 {sender}", text[:80])

	# ------------------ UI и стили ------------------
	def get_theme_colors(self, theme_name):
		themes = {
			"dark_purple": {
				"bg": "#12121a",
				"sidebar": "#1a1a2e",
				"card": "#22223b",
				"accent": "#a855f7",
				"input_bg": "#2d2d44",
				"text": "#f1f5f9",
				"text_secondary": "#94a3b8",
				"msg_mine": "#7c3aed",
				"msg_other": "#2d2d44",
			},
			"dark_blue": {
				"bg": "#0f172a",
				"sidebar": "#1e293b",
				"card": "#1e293b",
				"accent": "#3b82f6",
				"input_bg": "#334155",
				"text": "#f8fafc",
				"text_secondary": "#94a3b8",
				"msg_mine": "#3b82f6",
				"msg_other": "#334155",
			},
			"light": {
				"bg": "#f1f5f9",
				"sidebar": "#ffffff",
				"card": "#ffffff",
				"accent": "#6366f1",
				"input_bg": "#e2e8f0",
				"text": "#0f172a",
				"text_secondary": "#475569",
				"msg_mine": "#6366f1",
				"msg_other": "#e2e8f0",
			},
			"night": {
				"bg": "#0a0a0a",
				"sidebar": "#1a1a1a",
				"card": "#1c1c1c",
				"accent": "#64b5f6",
				"input_bg": "#2a2a2a",
				"text": "#e6e6e6",
				"text_secondary": "#808080",
				"msg_mine": "#64b5f6",
				"msg_other": "#2a2a2a",
			},
		}
		return themes.get(theme_name, themes["dark_purple"])

	def apply_hover_animation(self, button):
		effect = QGraphicsOpacityEffect()
		button.setGraphicsEffect(effect)
		button._animation = QPropertyAnimation(effect, b"opacity")
		button._animation.setDuration(150)
		button._animation.setEasingCurve(QEasingCurve.Type.OutCubic)

		def enter_event(event):
			button._animation.stop()
			button._animation.setEndValue(0.8)
			button._animation.start()
			event.accept()

		def leave_event(event):
			button._animation.stop()
			button._animation.setEndValue(1.0)
			button._animation.start()
			event.accept()

		button.enterEvent = enter_event
		button.leaveEvent = leave_event

	def create_tray_icon(self):
		self.tray_icon = QSystemTrayIcon(self)
		pixmap = QPixmap(64, 64)
		pixmap.fill(Qt.GlobalColor.transparent)
		painter = QPainter(pixmap)
		painter.setBrush(QBrush(Qt.GlobalColor.blue))
		painter.setPen(QPen(Qt.GlobalColor.blue))
		painter.drawEllipse(8, 8, 48, 48)
		painter.end()
		icon = QIcon(pixmap)
		self.tray_icon.setIcon(icon)
		self.tray_icon.setToolTip("Nebula")
		tray_menu = QMenu()
		show_action = QAction("Показать", self)
		show_action.triggered.connect(self.show_window)
		tray_menu.addAction(show_action)
		quit_action = QAction("Выйти", self)
		quit_action.triggered.connect(self.quit_application)
		tray_menu.addAction(quit_action)
		self.tray_icon.setContextMenu(tray_menu)
		self.tray_icon.activated.connect(self.tray_icon_activated)
		self.tray_icon.show()

	def tray_icon_activated(self, reason):
		if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
			self.show_window()

	def show_window(self):
		self.show()
		self.activateWindow()
		self.raise_()

	def quit_application(self):
		self.tray_icon.hide()
		QApplication.quit()

	def closeEvent(self, event):
		event.ignore()
		self.hide()
		self.tray_icon.showMessage("Nebula", "Приложение свёрнуто в трей.", QSystemTrayIcon.MessageIcon.Information, 2000)

	def show_notification(self, title, message):
		if self.tray_icon:
			self.tray_icon.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 5000)

	def init_ui(self):
		self.setWindowTitle(f"wf_message — {self.current_user}")
		self.setMinimumSize(900, 600)
		self.setGeometry(100, 100, 1000, 700)

		central_widget = QWidget()
		self.setCentralWidget(central_widget)
		main_layout = QHBoxLayout(central_widget)
		main_layout.setContentsMargins(0, 0, 0, 0)
		main_layout.setSpacing(0)

		# Левая панель
		self.sidebar = QWidget()
		self.sidebar.setFixedWidth(260)
		self.sidebar.setObjectName("sidebar")
		sidebar_layout = QVBoxLayout(self.sidebar)
		sidebar_layout.setContentsMargins(10, 10, 10, 10)
		sidebar_layout.setSpacing(5)

		title = QLabel("✨ Чаты")
		title.setAlignment(Qt.AlignmentFlag.AlignCenter)
		title.setObjectName("title")
		sidebar_layout.addWidget(title)

		self.contact_list = QListWidget()
		self.contact_list.setObjectName("contact_list")
		for chat in self.chats:
			self.contact_list.addItem(chat)
		self.contact_list.itemClicked.connect(self.select_contact)
		sidebar_layout.addWidget(self.contact_list)

		add_btn = QPushButton("➕ Добавить чат")
		add_btn.setObjectName("add_btn")
		add_btn.clicked.connect(self.add_contact_dialog)
		self.apply_hover_animation(add_btn)

		settings_btn = QPushButton("⚙️ Настройки")
		settings_btn.setObjectName("settings_btn")
		settings_btn.clicked.connect(self.open_settings_dialog)
		self.apply_hover_animation(settings_btn)

		sidebar_layout.addWidget(add_btn)
		sidebar_layout.addWidget(settings_btn)

		# Правая панель
		self.chat_panel = QWidget()
		self.chat_panel.setObjectName("chat_panel")
		chat_panel_layout = QVBoxLayout(self.chat_panel)
		chat_panel_layout.setContentsMargins(0, 0, 0, 0)
		chat_panel_layout.setSpacing(0)

		self.chat_header = QLabel("Выберите контакт")
		self.chat_header.setObjectName("chat_header")
		self.chat_header.setFixedHeight(50)
		self.chat_header.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
		self.chat_header.setIndent(20)
		chat_panel_layout.addWidget(self.chat_header)

		self.chat_container = QWidget()
		self.chat_container.setObjectName("chat_container")
		container_layout = QGridLayout(self.chat_container)
		container_layout.setContentsMargins(0, 0, 0, 0)
		container_layout.setSpacing(0)

		self.wallpaper_label = QLabel()
		self.wallpaper_label.setScaledContents(True)
		self.wallpaper_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
		container_layout.addWidget(self.wallpaper_label, 0, 0, 1, 1)

		self.chat_area = QTextEdit()
		self.chat_area.setObjectName("chat_area")
		self.chat_area.setReadOnly(True)
		self.chat_area.document().setDocumentMargin(10)
		self.chat_area.setStyleSheet("QTextEdit#chat_area { background-color: transparent; }")
		container_layout.addWidget(self.chat_area, 0, 0, 1, 1)

		chat_panel_layout.addWidget(self.chat_container)

		input_panel = QWidget()
		input_panel.setObjectName("input_panel")
		input_panel.setFixedHeight(60)
		input_layout = QHBoxLayout(input_panel)
		input_layout.setContentsMargins(10, 10, 10, 10)
		self.message_input = QLineEdit()
		self.message_input.setPlaceholderText("Введите сообщение...")
		self.message_input.returnPressed.connect(self.send_message)

		self.send_btn = QPushButton("✈")
		self.send_btn.setFixedSize(40, 40)
		self.send_btn.setStyleSheet("""
			QPushButton {
				background-color: #a855f7;
				color: white;
				border: none;
				border-radius: 20px;
				font-size: 18px;
				font-weight: bold;
			}
			QPushButton:hover {
				background-color: #7c3aed;
			}
		""")
		self.send_btn.clicked.connect(self.send_message)
		self.apply_hover_animation(self.send_btn)

		input_layout.addWidget(self.message_input)
		input_layout.addWidget(self.send_btn)
		chat_panel_layout.addWidget(input_panel)

		main_layout.addWidget(self.sidebar)
		main_layout.addWidget(self.chat_panel)

		if self.chats:
			self.contact_list.setCurrentRow(0)
			self.select_contact(self.contact_list.item(0))

		file = open('SocialNet_Data/data.ini', 'r+', encoding='utf8')
		data = file.read()
		file.close()

		splitted_log_data = data.split('\n')
		print(splitted_log_data)

		if len(splitted_log_data) > 3:
			theme = None
			bg = None
			try:	
				if 'theme' in splitted_log_data[3] or 'theme' in splitted_log_data[4]:
					if 'theme' in splitted_log_data[3]:
						theme = splitted_log_data[3][splitted_log_data[3].find('=')+1:]
						print(theme)
					elif 'theme' in splitted_log_data[4]:
						theme = splitted_log_data[4][splitted_log_data[4].find('=')+1:]
						print(theme)
					print(theme)
					self.current_theme = theme
					self.colors = self.get_theme_colors(theme)
			except IndexError:
				pass

			try:	
				if 'bg' in splitted_log_data[3] or 'bg' in splitted_log_data[4]:
					if 'bg' in splitted_log_data[3]:
						bg = splitted_log_data[3][splitted_log_data[3].find('=')+1:]
					elif 'bg' in splitted_log_data[4]:
						bg = splitted_log_data[4][splitted_log_data[4].find('=')+1:]

				self.wallpaper_path = bg
			except IndexError:
				pass

		self.apply_theme()
		self.update_wallpaper()

	def select_contact(self, item):
		contact = item.text()
		self.current_contact = contact
		self.chat_header.setText(contact)
		self.load_messages()
		Thread(target=self.receive_messages, args=(contact,), daemon=True).start()

	def load_messages(self):
		self.chat_area.clear()
		if self.current_contact is None:
			self.chat_area.setPlainText("Выберите контакт")
			return
		msgs = self.messages.get(self.current_contact, [])
		if not msgs:
			self.chat_area.setPlainText("Нет сообщений. Напишите что-нибудь!")
			return

		html_parts = []
		for msg in msgs:
			is_mine = msg["user"] == self.current_user
			align = "right" if is_mine else "left"
			bg_color = self.colors["msg_mine"] if is_mine else self.colors["msg_other"]
			text_color = "white" if is_mine else self.colors["text"]
			time_str = msg.get("time", "")
			safe_text = msg["text"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
			html = f'''
			<table align="{align}" style="border-collapse: collapse; margin: 4px 0; max-width: 60%;">
			<tr>
				<td style="background-color: {bg_color}; border-radius: 14px; padding: 6px 12px; color: {text_color}; word-wrap: break-word;">
					<span style="font-size: 14px;">{safe_text}</span>
					<span style="font-size: 10px; color: #a0a0a0; opacity: 0.6; margin-left: 8px;">{time_str}</span>
				</td>
			</tr>
			</table>
			'''
			html_parts.append(html)

		full_html = "<html><body style='margin: 0;'>" + "".join(html_parts) + "</body></html>"
		self.chat_area.setHtml(full_html)
		self.chat_area.moveCursor(QTextCursor.MoveOperation.End)

	def send_message(self):
		if self.current_contact is None:
			QMessageBox.warning(self, "Ошибка", "Сначала выберите контакт!")
			return
		text = self.message_input.text().strip()
		if not text:
			return
		self.send_message_to_server(self.current_contact, text)
		self.message_input.clear()

	def add_contact_dialog(self):
		dialog = AddContactDialog(self)
		if dialog.exec() == QDialog.DialogCode.Accepted:
			phone = dialog.get_contact_phone()
			if not phone:
				return
			try:
				HOST = 'vlahouse.ru'
				PORT = 12345
				BUFSIZ = 1024
				ADDR = (HOST, PORT)
				client_socket = socket(AF_INET, SOCK_STREAM)
				client_socket.connect(ADDR)
				data2send = shifratory['cipher_suite'].encrypt(bytes(f'add_chat phone={phone} my_phone={self.phone_number} _ver_', 'utf8'))
				client_socket.send(data2send)
				res = client_socket.recv(BUFSIZ).decode("utf8")
				key = res.encode()
				res = bytes(res, 'utf8')
				cipher_suite = Fernet(key)
				res = cipher_suite.decrypt(res).decode('utf-8')
				if res == 'find':
					if phone not in self.chats:
						self.chats.append(phone)
						self.messages[phone] = []
						self.contact_list.addItem(phone)
						QMessageBox.information(self, "Успех", "Чат добавлен!")
					else:
						QMessageBox.warning(self, "Внимание", "Чат уже существует")
				elif res == 'not found':
					QMessageBox.warning(self, "Ошибка", "Пользователь не найден")
				client_socket.close()
			except Exception as e:
				QMessageBox.critical(self, "Ошибка", str(e))
			update_key()

	def open_settings_dialog(self):
		dialog = SettingsDialog(self)
		if dialog.exec() == QDialog.DialogCode.Accepted:
			theme, wallpaper = dialog.get_settings()
			if theme != self.current_theme:
				self.current_theme = theme
				self.colors = self.get_theme_colors(theme)
				file = open('SocialNet_Data/data.ini', 'r+', encoding='utf8')
				data = file.read()
				file.close()

				splitted = data.split('\n')

				last_theme = None
				try:	
					if 'theme' in splitted[3]:
						last_theme = splitted[3][splitted[3].find('=')+1:]
					elif 'theme' in splitted[4]:
						last_theme = splitted[4][splitted[4].find('=')+1:]
				except IndexError:
					pass

				if last_theme == None:
					file = open('SocialNet_Data/data.ini', 'w+', encoding='utf8')
					file.write(data+f'\ntheme={theme}')
					file.close()
				else:
					data = data.replace(last_theme, f'{theme}')

					file = open('SocialNet_Data/data.ini', 'w+', encoding='utf8')
					file.write(data)
					file.close()

				self.apply_theme()
			if wallpaper != self.wallpaper_path:
				self.wallpaper_path = wallpaper
				file = open('SocialNet_Data/data.ini', 'r+', encoding='utf8')
				data = file.read()
				file.close()

				splitted = data.split('\n')

				bg = None
				try:	
					if 'bg' in splitted[3]:
						bg = splitted[3][splitted[3].find('=')+1:]
					elif 'bg' in splitted[4]:
						bg = splitted[4][splitted[4].find('=')+1:]
				except IndexError:
					pass

				if bg == None:
					file = open('SocialNet_Data/data.ini', 'w+', encoding='utf8')
					file.write(data+f'\nbg={wallpaper}')
					file.close()
				else:
					data = data.replace(bg, f'{wallpaper}')

					file = open('SocialNet_Data/data.ini', 'w+', encoding='utf8')
					file.write(data)
					file.close()
				self.update_wallpaper()

	def change_theme(self, theme_name):
		if theme_name != self.current_theme:
			self.current_theme = theme_name
			self.colors = self.get_theme_colors(theme_name)
			self.apply_theme()

	def apply_theme(self):
		t = self.colors
		self.setStyleSheet(f"""
			QWidget#sidebar {{
				background-color: {t["sidebar"]};
			}}
			QLabel#title {{
				background-color: {t["accent"]};
				color: white;
				padding: 10px;
				border-radius: 10px;
				font-size: 16px;
				font-weight: bold;
			}}
			QListWidget#contact_list {{
				background-color: {t["sidebar"]};
				color: {t["text"]};
				border: none;
				font-size: 14px;
				outline: none;
			}}
			QListWidget#contact_list::item {{
				padding: 8px;
				border-radius: 8px;
			}}
			QListWidget#contact_list::item:selected {{
				background-color: {t["accent"]};
				color: white;
			}}
			QPushButton#add_btn, QPushButton#settings_btn {{
				background-color: {t["accent"]};
				color: white;
				border: none;
				padding: 8px;
				border-radius: 5px;
				font-weight: bold;
			}}
			QPushButton#add_btn:hover, QPushButton#settings_btn:hover {{
				background-color: {t["accent"]}cc;
			}}
			QWidget#chat_panel {{
				background-color: {t["bg"]};
			}}
			QLabel#chat_header {{
				background-color: {t["card"]};
				color: {t["text"]};
				font-size: 16px;
				font-weight: bold;
			}}
			QWidget#chat_container {{
				background-color: {t["bg"]};
			}}
			QTextEdit#chat_area {{
				color: {t["text"]};
				border: none;
				font-size: 14px;
			}}
			QWidget#input_panel {{
				background-color: {t["card"]};
			}}
			QLineEdit {{
				background-color: {t["input_bg"]};
				color: {t["text"]};
				border: 1px solid {t["accent"]};
				border-radius: 5px;
				padding: 8px;
				font-size: 14px;
			}}
			QPushButton {{
				background-color: {t["accent"]};
				color: white;
				border: none;
				padding: 8px 16px;
				border-radius: 5px;
				font-weight: bold;
			}}
			QPushButton:hover {{
				background-color: {t["accent"]}cc;
			}}
			QMenuBar {{
				background-color: {t["card"]};
				color: {t["text"]};
			}}
			QMenuBar::item:selected {{
				background-color: {t["accent"]};
			}}
			QMenu {{
				background-color: {t["card"]};
				color: {t["text"]};
			}}
			QMenu::item:selected {{
				background-color: {t["accent"]};
			}}
		""")
		self.send_btn.setStyleSheet(f"""
			QPushButton {{
				background-color: {t["accent"]};
				color: white;
				border: none;
				border-radius: 20px;
				font-size: 18px;
				font-weight: bold;
			}}
			QPushButton:hover {{
				background-color: {t["accent"]}cc;
			}}
		""")
		if not self.wallpaper_path:
			self.chat_container.setStyleSheet(f"background-color: {t['bg']};")
		else:
			self.chat_container.setStyleSheet("background-color: transparent;")
		self.load_messages()

	def update_wallpaper(self):
		if self.wallpaper_path and os.path.exists(self.wallpaper_path):
			pixmap = QPixmap(self.wallpaper_path)
			if not pixmap.isNull():
				container_size = self.chat_container.size()
				if container_size.width() > 0 and container_size.height() > 0:
					pixmap = pixmap.scaled(
						container_size,
						Qt.AspectRatioMode.KeepAspectRatioByExpanding,
						Qt.TransformationMode.SmoothTransformation
					)
				self.wallpaper_label.setPixmap(pixmap)
				self.wallpaper_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
				self.chat_container.setStyleSheet("background-color: transparent;")
				return
		self.wallpaper_label.clear()
		self.apply_theme()

	def resizeEvent(self, event):
		super().resizeEvent(event)
		if self.wallpaper_path:
			self.update_wallpaper()

# ========================== ЗАПУСК ==========================
if __name__ == "__main__":
	app = QApplication(sys.argv)
	app.setQuitOnLastWindowClosed(False)
	
	file = open('SocialNet_Data/data.ini', 'r+', encoding='utf8')
	phone_num_n_pswd = file.read()
	file.close()
	if phone_num_n_pswd == '':
		login = LoginWindow()
		if login.exec() == QDialog.DialogCode.Accepted:
			window = ChatApp(login.current_user, login.current_phone, login.right_password)
			window.show()
			sys.exit(app.exec())
		else:
			sys.exit()

	if phone_num_n_pswd != '':
		splitted_log_data = phone_num_n_pswd.split('\n')
		phone_number = splitted_log_data[0][splitted_log_data[0].find('=')+1:]
		pswd = splitted_log_data[1][splitted_log_data[1].find('=')+1:]
		username = splitted_log_data[2][splitted_log_data[2].find('=')+1:]

		try:
			HOST = 'vlahouse.ru'
			PORT = 12345
			BUFSIZ = 1024
			ADDR = (HOST, PORT)
			client_socket = socket(AF_INET, SOCK_STREAM)
			client_socket.connect(ADDR)

			data2send = f'func=log phone={phone_number} password={pswd} _ver_'
			data2send = shifratory['cipher_suite'].encrypt(bytes(data2send, 'utf8'))
			client_socket.send(data2send)

			res = client_socket.recv(BUFSIZ).decode("utf8")
			key = res.encode()
			res = bytes(res, 'utf8')
			cipher_suite = Fernet(key)
			res = cipher_suite.decrypt(res).decode('utf-8')

			if 'open ' in res:
				try:
					client_socket.close()
					window = ChatApp(username, phone_number, pswd)
					window.show()
					sys.exit(app.exec())
				except Exception as e:
					print(e)
			elif res == 'closed pass':
				login = LoginWindow()
				if login.exec() == QDialog.DialogCode.Accepted:
					window = ChatApp(login.current_user, login.current_phone, login.right_password)
					window.show()
					sys.exit(app.exec())
				else:
					sys.exit()
			elif res == 'closed no':
				login = LoginWindow()
				if login.exec() == QDialog.DialogCode.Accepted:
					window = ChatApp(login.current_user, login.current_phone, login.right_password)
					window.show()
					sys.exit(app.exec())
				else:
					sys.exit()
			else:
				login = LoginWindow()
				if login.exec() == QDialog.DialogCode.Accepted:
					window = ChatApp(login.current_user, login.current_phone, login.right_password)
					window.show()
					sys.exit(app.exec())
				else:
					sys.exit()
		except Exception as e:
			self.error_label.setText(f"❌ Ошибка: {e}")
		finally:
			try:
				client_socket.close()
			except:
				pass
			update_key()