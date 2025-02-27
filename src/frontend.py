from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QLabel, 
                            QPushButton, QComboBox, QHBoxLayout, QGroupBox, 
                            QTextEdit, QFrame)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QIcon
from datetime import datetime
import os
from src.styles import *

class StyleFrame(QFrame):
    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(QFrameStyle)

class TranscriptionSignals(QObject):
    mic_transcription_ready = pyqtSignal(str)
    mix_transcription_ready = pyqtSignal(str)

class MainWindow(QMainWindow):
    def __init__(self, audio_recorder, signals):
        super().__init__()
        self.audio_recorder = audio_recorder
        self.signals = signals
        self.signals.mic_transcription_ready.connect(self.update_mic_transcript)
        self.signals.mix_transcription_ready.connect(self.update_mix_transcript)
        self.last_prefix = None
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Call Recorder")
        self.setGeometry(100, 100, 1000, 800)
        self.setStyleSheet(UIStyle)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)

        self.setup_icon()
        self.setup_header(main_layout)
        self.setup_device_section(main_layout)
        self.setup_controls(main_layout)
        self.setup_transcription(main_layout)
        
        # Timer for updating recording duration
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_duration)
        self.recording_start_time = None

    def setup_icon(self):
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'icon.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

            if os.name == 'nt':  # Windows OS special case to handle app icon
                import ctypes
                myappid = 'mycompany.callrecorder.app.1'
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    def setup_header(self, layout):
        header_label = QLabel("Voice Recording & Transcription")
        header_label.setStyleSheet(HeaderStyle)
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header_label)

    def setup_device_section(self, layout):
        device_frame = StyleFrame()
        device_layout = QVBoxLayout(device_frame)
        
        mic_group = QGroupBox("Audio Input Selection")
        mic_layout = QVBoxLayout()
        mic_layout.setSpacing(10)
        
        self.mic_combo = QComboBox()
        for device in self.audio_recorder.mic_devices:
            self.mic_combo.addItem(device['name'])
        self.mic_combo.currentIndexChanged.connect(self.audio_recorder.update_mic)
        mic_layout.addWidget(self.mic_combo)
        mic_group.setLayout(mic_layout)
        device_layout.addWidget(mic_group)
        layout.addWidget(device_frame)

    def setup_controls(self, layout):
        controls_frame = StyleFrame()
        controls_layout = QHBoxLayout(controls_frame)
        controls_layout.setSpacing(20)
        
        self.status_label = QLabel("Ready to record")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet(StatusStyle)
        
        self.record_button = QPushButton("Start Recording")
        self.record_button.clicked.connect(self.toggle_recording)
        self.record_button.setMinimumWidth(150)
        
        controls_layout.addWidget(self.status_label)
        controls_layout.addWidget(self.record_button)
        layout.addWidget(controls_frame)

    def setup_transcription(self, layout):
        transcript_frame = StyleFrame()
        transcript_layout = QVBoxLayout(transcript_frame)
        
        transcript_label = QLabel("Live Transcription")
        transcript_label.setStyleSheet(TranscriptLabelStyle)
        transcript_layout.addWidget(transcript_label)
        
        self.transcript_area = QTextEdit()
        self.transcript_area.setReadOnly(True)
        self.transcript_area.setPlaceholderText("Transcription will appear here in real-time...")
        self.transcript_area.setMinimumHeight(400)  
        self.transcript_area.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse | 
            Qt.TextInteractionFlag.TextSelectableByKeyboard
        )
        self.transcript_area.setStyleSheet(TranscriptAreaStyle)
        transcript_layout.addWidget(self.transcript_area)
        layout.addWidget(transcript_frame)

    def toggle_recording(self):
        if not self.audio_recorder.is_recording:
            self.audio_recorder.start_recording()
            self.recording_start_time = datetime.now()
            self.record_button.setText("Stop Recording")
            self.record_button.setStyleSheet(RecordingButtonStyle)
            self.timer.start(1000)  # Update every second
            self.status_label.setText("Recording... 00:00")
        else:
            self.stop_recording()

    def stop_recording(self):
        if self.audio_recorder.is_recording:
            transcript = self.transcript_area.toPlainText()
            message = self.audio_recorder.stop_recording(transcript)
            self.status_label.setText(message)
            self.record_button.setText("Start Recording")
            self.record_button.setStyleSheet("")
            self.timer.stop()
            self.recording_start_time = None
            self.status_label.setText("Ready to record")

    def update_mic_transcript(self, text):
        if text.strip():
            self._update_transcript_area("Input", text.strip())

    def update_mix_transcript(self, text):
        if text.strip():
            self._update_transcript_area("Output", text.strip())

    def _update_transcript_area(self, prefix, content):
        cursor = self.transcript_area.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        
        # Get current text and determine if we need a new line
        current_text = self.transcript_area.toPlainText().strip()
        
        if current_text:
            if prefix == self.last_prefix:
                cursor.insertText(f" {content}")
            else:
                cursor.insertText(f"\n{prefix}: {content}")
        else:
            cursor.insertText(f"{prefix}: {content}")
        
        self.last_prefix = prefix
        
        # Update scroll position
        self.transcript_area.setTextCursor(cursor)
        self.transcript_area.verticalScrollBar().setValue(
            self.transcript_area.verticalScrollBar().maximum()
        )

    def update_duration(self):
        if self.recording_start_time:
            duration = datetime.now() - self.recording_start_time
            seconds = duration.total_seconds()
            minutes = int(seconds // 60)
            seconds = int(seconds % 60)
            self.status_label.setText(f"Recording... {minutes:02d}:{seconds:02d}")