import sys
import cv2
import time
import psutil
import torch
import numpy as np
import pynvml
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QFileDialog
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap
from ultralytics import YOLO

# --- CONFIGURATION ---
DEFAULT_MODEL = '../models/yolo11_small.pt' # Use .pt for best GPU support
DEFAULT_VIDEO = '../inference/Video/Inference -1.mp4'
OUTPUT_FILE = '../output/processed_video.mp4' # Fixed: Changed to .mp4 for stability

# YOUR EXACT 11 CLASSES
CLASS_NAMES = [
    "Auto Rickshaw",      # 0
    "Cycle Rickshaw",     # 1
    "CNG / Tempo",        # 2
    "Bus",                # 3
    "Jeep / SUV",         # 4
    "Microbus",           # 5
    "Minibus",            # 6
    "Motorcycle",         # 7
    "Truck",              # 8
    "Private Sedan Car",  # 9
    "Trailer"             # 10
]

class TrafficDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Regnum AI Assessment - Traffic Monitor")
        self.setGeometry(100, 100, 1400, 900)
        self.setStyleSheet("background-color: #1e1e1e; color: white;")

        self.current_video_path = DEFAULT_VIDEO
        self.gpu_handle = None 

        # --- SMART DEVICE LOADING ---
        if torch.cuda.is_available():
            self.device = 0
            device_name = "GTX 1050 Ti"
            print("✅ GPU DETECTED: Running on GTX 1050 Ti")
            try:
                pynvml.nvmlInit()
                self.gpu_handle = pynvml.nvmlDeviceGetHandleByIndex(0) 
                print("✅ NVIDIA SENSORS CONNECTED")
            except Exception as e:
                print(f"⚠️ GPU Sensors Error: {e}")
                self.gpu_handle = None
        else:
            self.device = 'cpu'
            device_name = "CPU"
            print("⚠️ GPU NOT FOUND")

        print(f"Loading Model: {DEFAULT_MODEL}...")
        self.model = YOLO(DEFAULT_MODEL)
        
        # Only move to GPU manually if it is a PyTorch model
        # (ONNX models handle devices differently)
        if DEFAULT_MODEL.endswith('.pt'):
            self.model.to(self.device)
            
        print("Model Loaded!")

        # --- GUI LAYOUT ---
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)

        # Left: Video
        self.video_label = QLabel("Click 'SELECT VIDEO' to choose a file...")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("border: 2px solid #444; background-color: black; font-size: 20px; color: #7f8c8d;")
        self.video_label.setMinimumSize(960, 540)
        self.main_layout.addWidget(self.video_label, stretch=3)

        # Right: Dashboard
        self.sidebar = QVBoxLayout()
        self.main_layout.addLayout(self.sidebar, stretch=1)

        # Stats
        self.add_stat_label("System Stats", header=True)
        self.fps_label = self.add_stat_label("FPS: 0")
        self.cpu_label = self.add_stat_label("CPU: 0%")
        self.gpu_label = self.add_stat_label(f"GPU: {device_name}")

        self.sidebar.addSpacing(20)
        self.add_stat_label("Vehicle Counts", header=True)
        
        self.count_labels = {}
        for name in CLASS_NAMES:
            self.count_labels[name] = self.add_stat_label(f"{name}: 0")

        self.sidebar.addStretch()

        # Controls
        self.select_btn = QPushButton("SELECT VIDEO")
        self.select_btn.setStyleSheet("background-color: #3498db; color: white; font-weight: bold; padding: 15px; margin-bottom: 10px;")
        self.select_btn.clicked.connect(self.select_video_file)
        self.sidebar.addWidget(self.select_btn)

        self.start_btn = QPushButton("START MONITORING")
        self.start_btn.setStyleSheet("background-color: #2ecc71; color: black; font-weight: bold; padding: 15px;")
        self.start_btn.clicked.connect(self.toggle_feed)
        self.sidebar.addWidget(self.start_btn)

        # Speed Optimization Variables
        self.frame_count = 0
        self.skip_interval = 2 # Process 1 frame, skip 2 (3x speedup)
        self.last_annotated_frame = None
        self.prev_frame_time = 0
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.cap = None
        self.out = None 
        self.running = False

    def add_stat_label(self, text, header=False):
        label = QLabel(text)
        font_size = "16px" if header else "13px"
        color = "#3498db" if header else "#ecf0f1"
        weight = "bold" if header else "normal"
        label.setStyleSheet(f"font-size: {font_size}; color: {color}; font-weight: {weight}; margin-bottom: 2px;")
        self.sidebar.addWidget(label)
        return label

    def select_video_file(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "Select Traffic Video", "", "Video Files (*.mp4 *.avi *.mov *.mkv);;All Files (*)", options=options)
        if fileName:
            self.current_video_path = fileName
            self.video_label.setText(f"Selected:\n{fileName.split('/')[-1]}")

    def toggle_feed(self):
        if not self.running:
            self.cap = cv2.VideoCapture(self.current_video_path)
            if not self.cap.isOpened():
                self.video_label.setText("Error: Could not open video file.")
                return

            w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # --- VIDEO WRITER FIX ---
            # Use 'mp4v' codec for .mp4 files (Better compatibility/stability than XVID)
            self.out = cv2.VideoWriter(OUTPUT_FILE, cv2.VideoWriter_fourcc(*'mp4v'), 25, (w, h))
            
            self.running = True
            self.select_btn.setEnabled(False)
            self.start_btn.setText("STOP & SAVE")
            self.start_btn.setStyleSheet("background-color: #e74c3c; color: white; padding: 15px;")
            self.timer.start(30)
        else:
            self.running = False
            self.timer.stop()
            self.cap.release()
            if self.out: self.out.release()
            self.select_btn.setEnabled(True)
            self.start_btn.setText("START MONITORING")
            self.start_btn.setStyleSheet("background-color: #2ecc71; color: black; padding: 15px;")
            self.video_label.setText(f"Processing Stopped.\nSaved to: {OUTPUT_FILE}")

    def update_frame(self):
        if not self.running: return
        
        ret, frame = self.cap.read()
        if not ret:
            self.toggle_feed()
            return

        self.frame_count += 1
        
        # --- LOGIC: SKIP FRAMES FOR SPEED ---
        # Only run heavy AI every (skip_interval + 1) frames
        if self.frame_count % (self.skip_interval + 1) == 0:
            
            # Run AI on this frame (Reduced size 320 for speed)
            results = self.model.track(
                frame, 
                persist=True, 
                verbose=False, 
                conf=0.25, 
                device=self.device, 
                imgsz=320 
            )
            
            self.last_annotated_frame = results[0].plot()

            counts = {name: 0 for name in CLASS_NAMES}
            if results[0].boxes.id is not None:
                classes = results[0].boxes.cls.cpu().numpy()
                for cls in classes:
                    if 0 <= int(cls) < len(CLASS_NAMES):
                        counts[CLASS_NAMES[int(cls)]] += 1
            
            for name, count in counts.items():
                self.count_labels[name].setText(f"{name}: {count}")

            final_display = self.last_annotated_frame
            
        else:
            # Skip AI, reuse the last known frame (keeps video smooth)
            if self.last_annotated_frame is not None:
                final_display = self.last_annotated_frame
            else:
                final_display = frame

        # --- WRITE EVERY FRAME ---
        # Important: Write to video every loop to avoid corruption
        if self.out:
            self.out.write(final_display)

        # --- STABLE FPS CALCULATION ---
        current_time = time.time()
        if self.prev_frame_time == 0:
            self.prev_frame_time = current_time
        
        time_diff = current_time - self.prev_frame_time
        
        if time_diff > 0:
            real_fps = 1.0 / time_diff
            
            # Smoothing (90% old, 10% new) to stop flickering
            current_fps_text = self.fps_label.text().split(": ")[-1]
            try:
                old_fps = float(current_fps_text)
            except ValueError:
                old_fps = 0.0
            
            smoothed_fps = (old_fps * 0.9) + (real_fps * 0.1)
            self.fps_label.setText(f"FPS: {smoothed_fps:.1f}")
        
        self.prev_frame_time = current_time

        self.cpu_label.setText(f"CPU: {psutil.cpu_percent()}%")
        
        if self.gpu_handle:
            try:
                util = pynvml.nvmlDeviceGetUtilizationRates(self.gpu_handle)
                mem = pynvml.nvmlDeviceGetMemoryInfo(self.gpu_handle)
                mem_used_mb = mem.used / 1024 / 1024
                self.gpu_label.setText(f"GPU: {util.gpu}% | Mem: {int(mem_used_mb)}MB")
                
                if util.gpu > 80:
                    self.gpu_label.setStyleSheet("font-size: 13px; color: #e74c3c; font-weight: bold;")
                else:
                    self.gpu_label.setStyleSheet("font-size: 13px; color: #ecf0f1; font-weight: bold;")
            except: pass

        # Display on GUI
        h, w, ch = final_display.shape
        bytes_per_line = ch * w
        qt_img = QImage(final_display.data, w, h, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
        self.video_label.setPixmap(QPixmap.fromImage(qt_img).scaled(
            self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TrafficDashboard()
    window.show()
    sys.exit(app.exec_())