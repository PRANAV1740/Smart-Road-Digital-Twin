import time
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import QTimer

from utils import data
from utils.theme import ThemeManager

class StatusBar(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(58)
        self.theme_manager = ThemeManager()
        self.theme = self.theme_manager.get_current_theme()

        layout = QHBoxLayout()
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(8)

        self.system_label = QLabel()
        self.mode_label = QLabel()
        self.esp32_label = QLabel()
        self.camera_label = QLabel()
        self.gps_label = QLabel()
        self.ultrasonic_label = QLabel()
        self.imu_label = QLabel()
        self.packet_label = QLabel()

        layout.addWidget(self.system_label)
        layout.addWidget(self.mode_label)
        layout.addStretch()
        layout.addWidget(self.esp32_label)
        layout.addWidget(self.camera_label)
        layout.addWidget(self.gps_label)
        layout.addWidget(self.ultrasonic_label)
        layout.addWidget(self.imu_label)
        layout.addWidget(self.packet_label)

        self.setLayout(layout)

        self.theme_manager.theme_changed.connect(self.apply_theme)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_status)
        self.timer.start(500)

        self.update_status()

    def apply_theme(self, theme, is_dark):
        self.theme = theme
        self.update_status()

    def set_indicator(self, label, name, connected):
        color = self.theme['success'] if connected else self.theme['danger']
        status = "ONLINE" if connected else "OFFLINE"
        label.setText(f"● {name}: {status}")
        label.setStyleSheet(f"""
            QLabel {{
                background: {self.theme['surface_elevated']};
                color: {color};
                font-size: 11px;
                font-weight: bold;
                font-family: 'Segoe UI';
                padding: 7px 10px;
                border-radius: 8px;
            }}
        """)

    def update_system_indicator(self):
        self.system_label.setText("● SYSTEM: RUNNING")
        self.system_label.setStyleSheet(f"""
            QLabel {{
                background: {self.theme['surface_elevated']};
                color: {self.theme['success']};
                font-size: 11px;
                font-weight: bold;
                font-family: 'Segoe UI';
                padding: 7px 10px;
                border-radius: 8px;
            }}
        """)

    def update_mode_indicator(self):
        if data.esp32_connected:
            data.system_mode = "LIVE HARDWARE"
            mode_text = "● MODE: LIVE HARDWARE"
            mode_color = self.theme['accent']
        else:
            data.system_mode = "SIMULATION"
            mode_text = "● MODE: SIMULATION"
            mode_color = self.theme['warning']

        self.mode_label.setText(mode_text)
        self.mode_label.setStyleSheet(f"""
            QLabel {{
                background: {self.theme['surface_elevated']};
                color: {mode_color};
                font-size: 11px;
                font-weight: bold;
                font-family: 'Segoe UI';
                padding: 7px 10px;
                border-radius: 8px;
            }}
        """)

    def update_packet_indicator(self):
        packet_count = data.packets_received
        if data.last_packet_time > 0:
            seconds_ago = time.time() - data.last_packet_time
            if seconds_ago < 1:
                packet_text = f"PACKETS: {packet_count} | LIVE"
                color = self.theme['success']
            else:
                packet_text = f"PACKETS: {packet_count} | {seconds_ago:.1f}s"
                color = self.theme['warning']
        else:
            packet_text = "PACKETS: 0"
            color = self.theme['text_muted']

        self.packet_label.setText(packet_text)
        self.packet_label.setStyleSheet(f"""
            QLabel {{
                background: {self.theme['surface_elevated']};
                color: {color};
                font-size: 11px;
                font-weight: bold;
                font-family: 'Segoe UI';
                padding: 7px 10px;
                border-radius: 8px;
            }}
        """)

    def update_status(self):
        self.update_system_indicator()
        self.update_mode_indicator()
        self.update_packet_indicator()

        self.set_indicator(self.esp32_label, "ESP32", data.esp32_connected)
        self.set_indicator(self.camera_label, "CAM", data.camera_connected)
        self.set_indicator(self.gps_label, "GPS", data.gps_connected)
        self.set_indicator(self.ultrasonic_label, "US", data.ultrasonic_connected)
        self.set_indicator(self.imu_label, "IMU", data.imu_connected)