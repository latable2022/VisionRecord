import sys
import cv2
import numpy as np
import pyautogui
import sounddevice as sd
import wave
import threading
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QCheckBox
from PyQt5.QtCore import QTimer

class ScreenRecorder(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Screen & Audio Recorder with Camera Overlay")
        self.setGeometry(100, 100, 300, 150)
        self.is_recording = False
        self.show_camera = False  # Variable pour contrôler l'affichage de la caméra

        # Boutons
        self.start_button = QPushButton("Start Recording")
        self.start_button.clicked.connect(self.start_recording)

        self.stop_button = QPushButton("Stop Recording")
        self.stop_button.clicked.connect(self.stop_recording)
        self.stop_button.setEnabled(False)

        # Case à cocher pour activer/désactiver la caméra
        self.camera_checkbox = QCheckBox("Show Camera")
        self.camera_checkbox.stateChanged.connect(self.toggle_camera)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        layout.addWidget(self.camera_checkbox)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Timer pour la capture d'écran
        self.timer = QTimer()
        self.timer.timeout.connect(self.record_screen)

        # Paramètres d'enregistrement
        self.video_writer = None
        self.audio_frames = []
        self.camera_capture = None

    def toggle_camera(self, state):
        self.show_camera = state == 2

    def start_recording(self):
        self.is_recording = True
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.timer.start(30)  # Capture toutes les 30 ms

        # Initialisation du writer vidéo
        screen_size = pyautogui.size()
        fourcc = cv2.VideoWriter_fourcc(*"XVID")
        self.video_writer = cv2.VideoWriter("screen_recording.avi", fourcc, 20.0, screen_size)

        # Démarrage de la caméra si activée
        if self.show_camera:
            self.camera_capture = cv2.VideoCapture(0)

        # Démarrage de l'enregistrement audio sur un thread séparé
        self.audio_frames = []
        self.audio_thread = threading.Thread(target=self.record_audio)
        self.audio_thread.start()

    def stop_recording(self):
        self.is_recording = False
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.timer.stop()

        # Libération des ressources vidéo et caméra
        if self.video_writer:
            self.video_writer.release()
        if self.camera_capture:
            self.camera_capture.release()

        # Arrêt de l'enregistrement audio
        self.audio_thread.join()
        self.save_audio()

    def record_screen(self):
        # Capture de l'écran
        img = pyautogui.screenshot()
        frame = np.array(img)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Ajout du flux de la caméra en haut à droite si activé
        if self.show_camera and self.camera_capture.isOpened():
            ret, camera_frame = self.camera_capture.read()
            if ret:
                # Redimensionner la caméra pour l'incrustation
                camera_frame = cv2.resize(camera_frame, (150, 100))
                # Convertir en RGB pour correspondre au frame principal
                camera_frame = cv2.cvtColor(camera_frame, cv2.COLOR_BGR2RGB)
                # Incruster la caméra en haut à droite du frame principal
                frame[10:110, -160:-10] = camera_frame

        # Enregistrement du frame dans le fichier vidéo
        if self.video_writer:
            self.video_writer.write(frame)

    def record_audio(self):
        # Configuration audio
        samplerate = 44100
        channels = 1
        with sd.InputStream(samplerate=samplerate, channels=channels) as stream:
            while self.is_recording:
                audio_data, _ = stream.read(1024)
                self.audio_frames.append(audio_data)

    def save_audio(self):
        # Enregistre l'audio dans un fichier WAV
        with wave.open("audio_recording.wav", 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16 bits
            wf.setframerate(44100)
            for frame in self.audio_frames:
                wf.writeframes(frame)

    def closeEvent(self, event):
        # Libère les ressources lors de la fermeture
        if self.video_writer:
            self.video_writer.release()
        if self.camera_capture:
            self.camera_capture.release()

app = QApplication(sys.argv)
window = ScreenRecorder()
window.show()
sys.exit(app.exec_())
