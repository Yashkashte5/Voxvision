import sys
import cv2
import os
from deepface import DeepFace
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap, QFont
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox, QInputDialog  # <-- Added QInputDialog import


class VideoCaptureThread(QThread):
    change_pixmap_signal = pyqtSignal(QImage)

    def __init__(self, user_name, parent=None):
        super().__init__(parent)
        self.user_name = user_name
        self.running = False

    def run(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return

        self.running = True
        while self.running:
            ret, frame = cap.read()
            if not ret:
                break
            # Convert frame to RGB for display in Qt
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_frame.shape
            bytes_per_line = ch * w
            qt_img = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            self.change_pixmap_signal.emit(qt_img)

        cap.release()

    def stop(self):
        self.running = False
        self.quit()


class FaceRegistrationApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("VoxVision Face Registration")
        self.setGeometry(100, 100, 600, 400)
        self.setStyleSheet("background-color: #F1F1F1; color: #333;")
        self.setFont(QFont("Arial", 12))

        self.layout = QVBoxLayout()

        # Header Label
        self.header_label = QLabel("Welcome to the VoxVision Face Registration", self)
        self.header_label.setAlignment(Qt.AlignCenter)
        self.header_label.setFont(QFont("Arial", 16, QFont.Bold))
        self.header_label.setStyleSheet("color: #4CAF50;")
        self.layout.addWidget(self.header_label)


        # Start Registration Button
        self.start_registration_button = QPushButton("Start Registration", self)
        self.start_registration_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 12px; border-radius: 5px;")
        self.start_registration_button.clicked.connect(self.start_registration)
        self.layout.addWidget(self.start_registration_button)

        # Video feed label
        self.video_label = QLabel(self)
        self.layout.addWidget(self.video_label)

        # Capture button
        self.capture_button = QPushButton("Capture Face", self)
        self.capture_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px; border-radius: 5px;")
        self.capture_button.setEnabled(False)
        self.capture_button.clicked.connect(self.capture_face)
        self.layout.addWidget(self.capture_button)

        # Cancel button
        self.cancel_button = QPushButton("Cancel", self)
        self.cancel_button.setStyleSheet("background-color: #FF5722; color: white; font-weight: bold; padding: 10px; border-radius: 5px;")
        self.cancel_button.clicked.connect(self.cancel_registration)
        self.layout.addWidget(self.cancel_button)

        # Status label
        self.status_label = QLabel("Status: Waiting for user to click 'Start Registration'.", self)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.status_label)

        self.setLayout(self.layout)

        self.video_thread = None
        self.user_name = None

    def start_registration(self):
        self.user_name = self.get_user_name()
        if self.user_name:
            self.status_label.setText("Status: Capturing face... Please look at the camera.")
            self.capture_button.setEnabled(True)
            self.start_registration_button.setEnabled(False)

    def capture_face(self):
        self.status_label.setText("Status: Capturing face... Please look at the camera.")
        self.capture_button.setEnabled(False)
        self.video_thread = VideoCaptureThread(self.user_name)
        self.video_thread.change_pixmap_signal.connect(self.update_video_frame)
        self.video_thread.start()

        self.capture_button.setText("Capture Face (Press Space to Capture)")
        self.capture_button.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold; padding: 10px; border-radius: 5px;")

        # Wait for the user to press space to capture
        self.capture_button.clicked.connect(self.on_capture_click)

    def on_capture_click(self):
        self.capture_image(self.user_name)
        self.status_label.setText("Status: Saving image and generating embedding...")
        self.video_thread.stop()
        self.capture_button.setEnabled(False)

    def update_video_frame(self, qt_img):
        self.video_label.setPixmap(QPixmap.fromImage(qt_img))

    def get_user_name(self):
        # Direct input for username
        user_name, ok = QInputDialog.getText(self, "User Name", "Enter your name for registration:")
        if ok and user_name:
            return user_name
        else:
            QMessageBox.warning(self, "Input Error", "Name is required for registration.")
            return None

    def capture_image(self, user_name):
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        if ret:
            image_path = f'registered_users/{user_name}.jpg'
            cv2.imwrite(image_path, frame)
            self.status_label.setText("Status: Generating facial embedding...")
            user_embedding = DeepFace.represent(image_path, model_name="VGG-Face")
            self.save_embedding(user_name, user_embedding)
        cap.release()

    def save_embedding(self, user_name, embedding):
        embedding_file = f'registered_users/{user_name}_embedding.txt'
        with open(embedding_file, 'w') as f:
            f.write(str(embedding))
        self.status_label.setText(f"Status: Registration complete for {user_name}.")
        QMessageBox.information(self, "Registration Successful", f"Registration complete for {user_name}. The face has been registered successfully!")

    def cancel_registration(self):
        if self.video_thread:
            self.video_thread.stop()
        self.status_label.setText("Status: Registration canceled.")
        self.capture_button.setEnabled(False)
        self.start_registration_button.setEnabled(True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FaceRegistrationApp()
    window.show()
    sys.exit(app.exec_())
