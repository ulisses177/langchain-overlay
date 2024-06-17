import sys
import speech_recognition as sr
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QWidget, QLineEdit, QSystemTrayIcon, QMenu, QAction, QTextEdit, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QCursor
from backend import ChatBotBackend

class OverlayWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.backend = ChatBotBackend()
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
        
        self.input_layout.addWidget(self.input_field)
        self.input_layout.addWidget(self.speech_button)

        self.layout.addWidget(self.chat_history)
        self.layout.addLayout(self.input_layout)
        self.setLayout(self.layout)
        self.resize(600, 400)

        self.setWindowOpacity(0.9)
        self.hide()

        # Set the position to the top right corner
        screen_geometry = QApplication.desktop().screenGeometry()
        self.move(screen_geometry.width() - self.width(), 0)

        # Timer to check mouse position
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
            self.input_field.setFocus()  # Ensure input field gets focus when shown
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
                QApplication.processEvents()  # Ensure the UI updates to show "Listening..."
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

    def load_chat_history(self):
        full_history = self.backend.get_full_chat_history()
        self.chat_history.setText(full_history)

class SystemTrayIcon(QSystemTrayIcon):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setIcon(QIcon("icon.png"))  # Make sure to replace with the path to your icon

        self.menu = QMenu(parent)
        self.exit_action = QAction("Exit", self)
        self.exit_action.triggered.connect(self.exit)
        self.menu.addAction(self.exit_action)
        self.setContextMenu(self.menu)

    def exit(self):
        QApplication.quit()

if __name__ == '__main__':
    app = QApplication(sys.argv)

    tray_icon = SystemTrayIcon()
    tray_icon.show()

    overlay = OverlayWindow()

    sys.exit(app.exec_())
