import sys
import os
import shutil
import subprocess
import speech_recognition as sr
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QWidget, QLineEdit, QSystemTrayIcon, QMenu, QAction, QTextEdit, QPushButton, QHBoxLayout, QFileDialog
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QCursor, QTextDocument, QTextCursor
from backend import ChatBotBackend

class OverlayWindow(QWidget):
    def __init__(self, log_file="chat_log.md"):
        super().__init__()

        self.backend = ChatBotBackend(log_file=log_file)
        self.recognizer = sr.Recognizer()
        self.initUI()
        self.load_chat_history()

    def initUI(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.X11BypassWindowManagerHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)

        self.layout = QVBoxLayout()

        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setStyleSheet("color: white; font-size: 18px; background: rgba(0, 0, 0, 0.7);")

        self.input_layout = QHBoxLayout()

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type your message or use speech...")
        self.input_field.setStyleSheet("color: white; font-size: 18px; background: rgba(0, 0, 0, 0.7);")
        self.input_field.setFocusPolicy(Qt.StrongFocus)
        self.input_field.returnPressed.connect(self.handle_user_input)

        self.speech_button = QPushButton("🎤")
        self.speech_button.setStyleSheet("color: white; font-size: 18px; background: rgba(0, 0, 0, 0.7);")
        self.speech_button.clicked.connect(self.handle_speech_input)
        
        self.image_button = QPushButton("🖼️")
        self.image_button.setStyleSheet("color: white; font-size: 18px; background: rgba(0, 0, 0, 0.7);")
        self.image_button.clicked.connect(self.handle_image_input)
        
        self.input_layout.addWidget(self.input_field)
        self.input_layout.addWidget(self.speech_button)
        self.input_layout.addWidget(self.image_button)

        self.layout.addWidget(self.chat_history)
        self.layout.addLayout(self.input_layout)
        self.setLayout(self.layout)
        self.resize(600, 400)

        self.setWindowOpacity(0.9)
        self.hide()

        screen_geometry = QApplication.desktop().screenGeometry()
        self.move(screen_geometry.width() - self.width(), 0)

        self.timer = QTimer()
        self.timer.timeout.connect(self.check_mouse_position)
        self.timer.start(100)

    def check_mouse_position(self):
        pos = QCursor.pos()
        screen_geometry = QApplication.desktop().screenGeometry()
        if pos.x() > screen_geometry.width() - 10 and pos.y() < 10:
            self.show()
            self.raise_()
            self.activateWindow()
            self.input_field.setFocus()
        else:
            if pos.x() > screen_geometry.width() - 600 and pos.y() > 400:
                self.hide()

    def handle_user_input(self):
        user_input = self.input_field.text().strip()
        if user_input:
            self.chat_history.append(f"<b>You:</b> {user_input}")
            self.input_field.clear()
            QApplication.processEvents()

            response = self.backend.generate_response(user_input)
            self.chat_history.append(f"<b>Bot:</b> {response}")

    def handle_speech_input(self):
        try:
            with sr.Microphone() as source:
                self.chat_history.append("<b>Listening...</b>")
                QApplication.processEvents()
                audio = self.recognizer.listen(source)

            user_input = self.recognizer.recognize_google(audio).strip()
            self.chat_history.append(f"<b>You (speech):</b> {user_input}")

            response = self.backend.generate_response(user_input)
            self.chat_history.append(f"<b>Bot:</b> {response}")
        except sr.UnknownValueError:
            self.chat_history.append("<b>Could not understand the audio</b>")
        except sr.RequestError as e:
            self.chat_history.append(f"<b>Could not request results; {e}</b>")
        except Exception as e:
            self.chat_history.append(f"<b>Speech recognition error: {e}</b>")

    def handle_image_input(self):
        image_path, _ = QFileDialog.getOpenFileName(self, "Select Image", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if image_path:
            saved_image_path = os.path.join(self.backend.saved_images_dir, os.path.basename(image_path))
            self.chat_history.append(f'<img src="{saved_image_path}" width="200">')
            image_description = self.backend.save_image(image_path)
            self.chat_history.append(f"<b>Bot:</b> {image_description}")

    def load_chat_history(self):
        full_history = self.backend.get_full_chat_history()
        self.chat_history.clear()
        html_content = ""
        for line in full_history.split('\n'):
            if line.startswith("![Image]"):
                image_path = line.split('(')[-1].strip(')')
                html_content += f'<img src="{image_path}" width="200"><br>'
            else:
                html_content += f'{line}<br>'
        self.chat_history.setHtml(html_content)

    def save_chat_history(self):
        self.backend.save_chat_history(self.backend.log_file)
        self.restart_application(self.backend.log_file)

    def save_as_chat_history(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save As", "", "Markdown Files (*.md);;All Files (*)")
        if file_path:
            self.backend.save_chat_history(file_path)
            self.restart_application(file_path)

    def load_chat_history_from_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Load Chat History", "", "Markdown Files (*.md);;All Files (*)")
        if file_path:
            self.restart_application(file_path)

    def restart_application(self, log_file):
        QApplication.quit()
        subprocess.Popen([sys.executable, __file__, log_file])

class SystemTrayIcon(QSystemTrayIcon):
    def __init__(self, parent=None, overlay_window=None):
        super().__init__(parent)
        self.overlay_window = overlay_window

        self.setIcon(QIcon("icon.png"))

        self.menu = QMenu(parent)

        self.save_action = QAction("Save", self)
        self.save_action.triggered.connect(self.save_chat_history)
        self.menu.addAction(self.save_action)

        self.save_as_action = QAction("Save As", self)
        self.save_as_action.triggered.connect(self.save_as_chat_history)
        self.menu.addAction(self.save_as_action)

        self.load_action = QAction("Load", self)
        self.load_action.triggered.connect(self.load_chat_history)
        self.menu.addAction(self.load_action)

        self.exit_action = QAction("Exit", self)
        self.exit_action.triggered.connect(self.exit)
        self.menu.addAction(self.exit_action)

        self.setContextMenu(self.menu)

    def save_chat_history(self):
        if self.overlay_window:
            self.overlay_window.save_chat_history()

    def save_as_chat_history(self):
        if self.overlay_window:
            self.overlay_window.save_as_chat_history()

    def load_chat_history(self):
        if self.overlay_window:
            self.overlay_window.load_chat_history_from_file()

    def exit(self):
        QApplication.quit()

if __name__ == '__main__':
    log_file = "chat_log.md"
    if len(sys.argv) > 1:
        log_file = sys.argv[1]

    app = QApplication(sys.argv)

    overlay = OverlayWindow(log_file=log_file)
    tray_icon = SystemTrayIcon(parent=None, overlay_window=overlay)
    tray_icon.show()

    sys.exit(app.exec_())
