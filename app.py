from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QLabel, QFrame, QPushButton
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import *
import sys
import cv2
from hand import HandGestureMIDIController  # Assuming the hand.py file is in the same directory


class MappingThread(QThread):
    def __init__(self, controller, finger):
        super().__init__()
        self.controller = controller
        self.finger = finger

    def run(self):
        while(self.controller.getMode()):
            if(not self.finger == ""):
                self.controller.send_finger(self.finger)

    def stop(self):
        self.controller.disableMode()
        self.quit()

    def updateFinger(self,finger):
        self.finger = finger

class VideoThread(QThread):
    ImageUpdate = pyqtSignal(QImage)

    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.ThreadActive = True

    def run(self):
        Capture = cv2.VideoCapture(0)
        while self.ThreadActive:
            if(not self.controller.getMode()):
                ret, frame = Capture.read()
                if ret:
                    frame = cv2.flip(frame, 1)
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frame = self.controller.capture_frame(frame)
                    height, width, channel = frame.shape
                    bytesPerLine = 3 * width
                    qImg = QImage(frame.data, width, height, bytesPerLine, QImage.Format.Format_RGB888)

                    # Scale the image to the new dimensions
                    pic = qImg.scaled(680, 480, Qt.AspectRatioMode.KeepAspectRatio)
                    self.ImageUpdate.emit(pic)

    def stop(self):
        self.ThreadActive = False
        self.quit()


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("MIDI Controller")
        self.setGeometry(100, 100, 1000, 700)

        # Shared HandGestureMIDIController instance
        self.controller = HandGestureMIDIController()

        self.mapping_mode = False
        self.mapping_thread = None

        # Main container widget
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(50, 50, 50, 50)
        main_layout.setSpacing(20)

        # Top section (CTRL text, line, and Settings button)
        ctrl_label = QLabel("CTRL")
        ctrl_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        ctrl_label.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")

        settings_label = QLabel("Settings")
        settings_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        settings_label.setStyleSheet("font-size: 14px; color: gray;")

        ctrl_line = QFrame()
        ctrl_line.setFrameShape(QFrame.Shape.HLine)
        ctrl_line.setFrameShadow(QFrame.Shadow.Sunken)
        ctrl_line.setStyleSheet("color: gray;")

        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(40, 0, 40, 0)
        top_layout.addWidget(ctrl_label)
        top_layout.addWidget(settings_label)

        top_container = QVBoxLayout()
        top_container.addLayout(top_layout)
        top_container.addWidget(ctrl_line)

        # Middle section (HStack Layout)
        h_stack_layout = QHBoxLayout()
        h_stack_layout.setContentsMargins(40, 0, 40, 0)
        h_stack_layout.setSpacing(40)

        # Left 30% - Mapping Config Text
        left_layout = QVBoxLayout()
        left_layout.setSpacing(5)  # Reduced spacing between items
        left_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center the items

        mapping_label = QLabel("Mapping Config")
        mapping_label.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")

        self.mappings = {
            "Index": "CC20",
            "Middle": "CC21",
            "Ring": "CC22",
            "Pinky": "CC23",
            "Depth": "CC24"
        }
        self.mapping_labels = []
        for key, value in self.mappings.items():
            mapping_container = QWidget()
            mapping_layout = QHBoxLayout()
            mapping_layout.setContentsMargins(5, 5, 5, 5)
            mapping_layout.setSpacing(5)
            mapping_text = QLabel(f"{key}\t{value}")
            mapping_text.setStyleSheet("font-size: 14px; color: white;")
            mapping_layout.addWidget(mapping_text)
            mapping_container.setLayout(mapping_layout)
            mapping_container.setStyleSheet("background-color: transparent; border-radius: 5px;")
            mapping_container.mousePressEvent = lambda event, container=mapping_container, finger=key: self.mapping_clicked(container, finger)
            self.mapping_labels.append(mapping_container)
            left_layout.addWidget(mapping_container)

        left_container = QWidget()
        left_container.setLayout(left_layout)
        left_container.setFixedWidth(240)

        self.VideoThread = VideoThread(self.controller)
        self.VideoThread.start()
        self.VideoThread.ImageUpdate.connect(self.ImageUpdateSlot)

        # Center 30% - Video frame (Webcam feed)
        center_layout = QVBoxLayout()
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        midi_label = QLabel("MIDI Device 1")
        midi_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        midi_label.setStyleSheet("font-size: 18px; color: white;")
        self.mapping_button = QPushButton("Mapping Mode")
        self.mapping_button.setFixedWidth(150)
        self.mapping_button.setStyleSheet("padding: 10px; font-size: 14px; background-color: #2c2c2c; color: white; border: 1px solid gray; border-radius: 5px;")
        self.mapping_button.setCheckable(True)
        self.mapping_button.toggled.connect(self.toggle_mapping_mode)
        self.FeelLabel = QLabel()
        center_layout.addWidget(midi_label)
        center_layout.addWidget(self.FeelLabel)
        center_layout.addWidget(self.mapping_button)

        # Right 30% - Empty
        right_placeholder = QWidget()
        right_placeholder.setFixedWidth(240)

        h_stack_layout.addWidget(left_container)
        h_stack_layout.addLayout(center_layout)
        h_stack_layout.addWidget(right_placeholder)

        # Add layouts to main layout
        main_layout.addLayout(top_container)
        main_layout.addLayout(h_stack_layout)

        # Set main layout
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def ImageUpdateSlot(self, Image):
        self.FeelLabel.setPixmap(QPixmap.fromImage(Image))

    def toggle_mapping_mode(self, enabled):
        button_color = "rgba(255, 0, 0, 0.3)" if enabled else "#2c2c2c"
        self.mapping_button.setStyleSheet(f"padding: 10px; font-size: 14px; background-color: {button_color}; color: white; border: 1px solid gray; border-radius: 5px;")

        self.controller.setMappingMode(enabled)
        if enabled:
            self.mapping_thread = MappingThread(self.controller, "")
            self.mapping_thread.start()
        else:
            self.mapping_thread.stop()
            for cont in self.mapping_labels:
                 cont.setStyleSheet("background-color: transparent; border-radius: 5px;")

    def mapping_clicked(self, container, finger):
        if self.controller.getMode():
            self.mapping_thread.updateFinger(finger)
            for label in self.mapping_labels:
                label.setStyleSheet("background-color: transparent; border-radius: 5px;")
            container.setStyleSheet("background-color: rgba(255, 0, 0, 0.3); border-radius: 5px;")
            


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet("QMainWindow { background-color: #1c1c1c; }")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
