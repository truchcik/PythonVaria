import sys
import os
import cv2
import json
import subprocess
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QComboBox,
    QApplication, QWidget, QPushButton, QLabel, QFileDialog, QVBoxLayout, QHBoxLayout,
    QSlider, QLineEdit
)
from PySide6.QtGui import QPixmap, QImage, QKeyEvent

CONFIG_FILE = "last_path.json"
MAX_RECENT = 100


def convert_frame_to_pixmap(frame):
    rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    height, width, channel = rgb_image.shape
    bytes_per_line = 3 * width
    q_image = QImage(rgb_image.data, width, height, bytes_per_line, QImage.Format_RGB888)
    return QPixmap.fromImage(q_image)


def load_last_path():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            data = json.load(f)
            recent = data.get("recent", [])
            if recent:
                return os.path.dirname(recent[0]["path"])
    return ""


def save_recent_clip(path, frame):
    data = {"recent": []}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                pass
    recent = data.get("recent", [])
    new_entry = {"path": path, "frame": frame}
    recent = [entry for entry in recent if entry["path"] != path]
    recent.insert(0, new_entry)
    recent = recent[:MAX_RECENT]
    data["recent"] = recent
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f, indent=2)


class VideoPlayer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Player with Screenshot Tool")

        self.video_path = None
        self.capture = None
        self.current_frame = None
        self.frame_pos = 0
        self.total_frames = 0
        self.fps = 30
        self.playback_speed = 1.0
        self.user_sliding = False

        self.timer = QTimer()
        self.timer.timeout.connect(self.next_frame)

        self.init_ui()

    def init_ui(self):
        self.recent_combo = QComboBox()
        self.recent_combo.addItem("Recent clips")
        self.recent_combo.activated.connect(self.load_recent_video)
        self.populate_recent_combo()
        self.video_label = QLabel("Load a video to start")
        self.video_label.setAlignment(Qt.AlignCenter)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setEnabled(False)
        self.slider.sliderPressed.connect(self.pause_for_slider)
        self.slider.sliderReleased.connect(self.slider_released)
        self.slider.valueChanged.connect(self.slider_preview_frame)

        self.load_button = QPushButton("Open Video")
        self.load_button.clicked.connect(self.load_video)

        self.play_button = QPushButton("Play/Pause")
        self.play_button.clicked.connect(self.toggle_playback)

        self.speed_quarter = QPushButton("0.25x [1]")
        self.speed_quarter.clicked.connect(lambda: self.set_speed(0.25))

        self.speed_half = QPushButton("0.5x [2]")
        self.speed_half.clicked.connect(lambda: self.set_speed(0.5))

        self.speed_full = QPushButton("1x [3]")
        self.speed_full.clicked.connect(lambda: self.set_speed(1))

        self.speed_double = QPushButton("2x [4]")
        self.speed_double.clicked.connect(lambda: self.set_speed(2.0))

        self.speed_quadruple = QPushButton("4x [5]")
        self.speed_quadruple.clicked.connect(lambda: self.set_speed(4.0))

        self.screenshot_button = QPushButton("Screenshot [Enter]")
        self.screenshot_button.clicked.connect(self.take_screenshot)

        self.screenshot_n_button = QPushButton("Screenshot Every N-th Frame")
        self.screenshot_n_button.clicked.connect(self.screenshot_every_n)

        self.open_folder_button = QPushButton("Screen Fld")
        self.open_folder_button.clicked.connect(self.open_screenshot_folder)

        self.n_input = QLineEdit("10")
        self.n_input.textChanged.connect(self.update_screenshot_button)
        self.n_input.setFixedWidth(50)

        controls = QHBoxLayout()
        controls.addWidget(self.load_button)
        controls.addWidget(self.play_button)
        controls.addWidget(self.speed_quarter)
        controls.addWidget(self.speed_half)
        controls.addWidget(self.speed_full)
        controls.addWidget(self.speed_double)
        controls.addWidget(self.speed_quadruple)
        controls.addWidget(self.screenshot_button)
        controls.addWidget(QLabel("Every N:"))
        controls.addWidget(self.n_input)
        controls.addWidget(self.screenshot_n_button)
        controls.addWidget(self.open_folder_button)

        layout = QVBoxLayout()
        layout.addWidget(self.recent_combo)
        layout.addWidget(self.video_label)
        layout.addWidget(self.slider)
        layout.addLayout(controls)
        self.setLayout(layout)

    def populate_recent_combo(self):
        self.recent_combo.clear()
        self.recent_combo.addItem("Recent clips")
        current_path = self.video_path
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                try:
                    data = json.load(f)
                    for entry in data.get("recent", []):
                        path = entry.get("path", "")
                        frame = entry.get("frame", 0)
                        display_name = os.path.basename(path)
                        self.recent_combo.addItem(display_name, path)
                        idx = self.recent_combo.count() - 1
                        self.recent_combo.setItemData(idx, f"{path}Last position: frame {frame}", Qt.ToolTipRole)
                        if current_path and path == current_path:
                            self.recent_combo.setCurrentIndex(idx)
                except json.JSONDecodeError:
                    pass

    def load_recent_video(self, index):
        if index == 0:
            return
        path = self.recent_combo.itemData(index)
        if path and os.path.exists(path):
            self.load_selected_video(path)

    def load_video(self):
        start_path = load_last_path()
        path, _ = QFileDialog.getOpenFileName(self, "Open Video", start_path, "MP4 files (*.mp4)")
        if path:
            self.load_selected_video(path)

    def load_selected_video(self, path):
        self.video_path = path
        self.capture = cv2.VideoCapture(path)
        self.total_frames = int(self.capture.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.capture.get(cv2.CAP_PROP_FPS)

        # Load last frame position from history if available
        frame_pos = 0
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                try:
                    data = json.load(f)
                    for entry in data.get("recent", []):
                        if entry.get("path") == path:
                            frame_pos = entry.get("frame", 0)
                            break
                except json.JSONDecodeError:
                    pass

        self.frame_pos = frame_pos
        self.slider.setRange(0, self.total_frames - 1)
        self.slider.setEnabled(True)
        self.capture.set(cv2.CAP_PROP_POS_FRAMES, self.frame_pos)
        self.next_frame()
        self.update_screenshot_button()
        self.populate_recent_combo()

    def next_frame(self):
        if self.capture and not self.user_sliding:
            ret, frame = self.capture.read()
            if ret:
                self.current_frame = frame
                self.frame_pos = int(self.capture.get(cv2.CAP_PROP_POS_FRAMES))
                pixmap = convert_frame_to_pixmap(frame)
                self.video_label.setPixmap(pixmap.scaled(self.video_label.size(), Qt.KeepAspectRatio))
                self.slider.setValue(self.frame_pos)
            else:
                self.timer.stop()

    def toggle_playback(self):
        if self.timer.isActive():
            self.timer.stop()
        else:
            interval = int(1000 / (self.fps * self.playback_speed))
            self.timer.start(interval)

    def set_speed(self, speed):
        self.playback_speed = speed
        if self.timer.isActive():
            self.toggle_playback()
            self.toggle_playback()

    def take_screenshot(self):
        if self.current_frame is not None and self.video_path:
            base_path = os.path.dirname(self.video_path)
            name = os.path.basename(self.video_path).split('.')[0]
            screen_folder = os.path.join(base_path, "screens")
            os.makedirs(screen_folder, exist_ok=True)
            frame_path = os.path.join(screen_folder, f"{name}_frame{self.frame_pos}.png")
            cv2.imwrite(frame_path, self.current_frame)
            print(f"Screenshot saved to {frame_path}")

    def open_screenshot_folder(self):
        if self.video_path:
            screen_folder = os.path.join(os.path.dirname(self.video_path), "screens")
            os.makedirs(screen_folder, exist_ok=True)
            if sys.platform == 'win32':
                os.startfile(screen_folder)
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', screen_folder])
            else:
                subprocess.Popen(['xdg-open', screen_folder])

    def update_screenshot_button(self):
        try:
            n = int(self.n_input.text())
            if n > 0 and self.total_frames > 0:
                count = self.total_frames // n
                self.screenshot_n_button.setText(f"Screenshot Every N-th Frame ({count})")
            else:
                self.screenshot_n_button.setText("Screenshot Every N-th Frame")
        except ValueError:
            self.screenshot_n_button.setText("Screenshot Every N-th Frame")

    def screenshot_every_n(self):
        self.screenshot_n_button.setEnabled(False)
        if self.capture and self.video_path:
            try:
                n = int(self.n_input.text())
                base_path = os.path.dirname(self.video_path)
                name = os.path.basename(self.video_path).split('.')[0]
                screen_folder = os.path.join(base_path, "screens")
                os.makedirs(screen_folder, exist_ok=True)

                self.capture.set(cv2.CAP_PROP_POS_FRAMES, 0)

                count = self.total_frames // n
                for idx, i in enumerate(range(0, self.total_frames, n), start=1):
                    self.screenshot_n_button.setText(f"Saving {idx}/{count}...")
                    QApplication.processEvents()
                    self.capture.set(cv2.CAP_PROP_POS_FRAMES, i)
                    ret, frame = self.capture.read()
                    if ret:
                        frame_path = os.path.join(screen_folder, f"{name}_frame{i}.png")
                        cv2.imwrite(frame_path, frame)
                self.screenshot_n_button.setText(f"Screen every Nth frame ({count})")
                self.screenshot_n_button.setEnabled(True)
                print(f"Saved screenshots every {n} frames to {screen_folder}")
            except ValueError:
                print("Please enter a valid number for N")

    def pause_for_slider(self):
        self.user_sliding = True
        self.timer.stop()

    def slider_preview_frame(self, value):
        if self.capture and self.user_sliding:
            self.capture.set(cv2.CAP_PROP_POS_FRAMES, value)
            ret, frame = self.capture.read()
            if ret:
                self.current_frame = frame
                self.frame_pos = value
                pixmap = convert_frame_to_pixmap(frame)
                self.video_label.setPixmap(pixmap.scaled(self.video_label.size(), Qt.KeepAspectRatio))

    def slider_released(self):
        self.user_sliding = False

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Space:
            self.toggle_playback()
        elif event.key() == Qt.Key_1:
            self.set_speed(0.25)
        elif event.key() == Qt.Key_2:
            self.set_speed(0.5)
        elif event.key() == Qt.Key_3:
            self.set_speed(1)
        elif event.key() == Qt.Key_4:
            self.set_speed(2.0)
        elif event.key() == Qt.Key_5:
            self.set_speed(4.0)
        elif event.key() == Qt.Key_Return:
            self.take_screenshot()

    def closeEvent(self, event):
        if self.video_path:
            save_recent_clip(self.video_path, self.frame_pos)
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = VideoPlayer()
    player.resize(800, 600)
    player.show()
    app.aboutToQuit.connect(lambda: save_recent_clip(player.video_path, player.frame_pos) if player.video_path else None)
    sys.exit(app.exec())
