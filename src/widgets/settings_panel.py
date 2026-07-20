from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QButtonGroup, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QPushButton, QRadioButton, QVBoxLayout, QWidget, QGraphicsDropShadowEffect
)

from database.database import clear_database
from utils.theme import ThemeManager

class SettingsPanel(QWidget):
    mode_changed = Signal(str)
    clear_history_requested = Signal()
    database_cleared = Signal()
    camera_url_saved = Signal(str)

    def __init__(self):
        super().__init__()
        self.current_active_mode = "SIMULATION"
        self.theme_manager = ThemeManager()
        self.ui_elements = {}
        self.build_interface()
        
        self.theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme(self.theme_manager.get_current_theme(), self.theme_manager.is_dark)

    def build_interface(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 12, 16, 16)
        main_layout.setSpacing(12)

        self.title_label = QLabel("SYSTEM SETTINGS")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.subtitle_label = QLabel("Configure data sources, camera connection and application maintenance options")
        self.subtitle_label.setAlignment(Qt.AlignCenter)

        main_layout.addWidget(self.title_label)
        main_layout.addWidget(self.subtitle_label)

        # -----------------------------------------
        # Data source settings
        # -----------------------------------------
        self.source_card = self.create_card()
        source_layout = QVBoxLayout(self.source_card)
        source_layout.setContentsMargins(12, 10, 12, 12)
        source_layout.setSpacing(8)

        self.ui_elements['source_title'] = QLabel("DATA SOURCE")
        self.ui_elements['source_desc'] = QLabel("Choose how dashboard sensor data should be supplied.")
        
        source_layout.addWidget(self.ui_elements['source_title'])
        source_layout.addWidget(self.ui_elements['source_desc'])

        mode_layout = QHBoxLayout()
        mode_layout.setSpacing(0)

        self.auto_radio = QRadioButton("AUTO")
        self.simulation_radio = QRadioButton("SIMULATION")
        self.live_radio = QRadioButton("LIVE HARDWARE")
        
        self.mode_group = QButtonGroup(self)
        self.mode_group.addButton(self.auto_radio)
        self.mode_group.addButton(self.simulation_radio)
        self.mode_group.addButton(self.live_radio)

        self.auto_radio.setChecked(True)
        self.auto_radio.toggled.connect(self.handle_mode_selection)
        self.simulation_radio.toggled.connect(self.handle_mode_selection)
        self.live_radio.toggled.connect(self.handle_mode_selection)

        # Wrap in a frame to simulate segmented control
        self.segmented_frame = QFrame()
        self.segmented_frame.setObjectName("segmentedFrame")
        seg_layout = QHBoxLayout(self.segmented_frame)
        seg_layout.setContentsMargins(2, 2, 2, 2)
        seg_layout.setSpacing(2)
        
        # We use QRadioButton style in apply_theme to make them look like segmented buttons
        self.auto_radio.setCursor(Qt.PointingHandCursor)
        self.simulation_radio.setCursor(Qt.PointingHandCursor)
        self.live_radio.setCursor(Qt.PointingHandCursor)

        seg_layout.addWidget(self.auto_radio)
        seg_layout.addWidget(self.simulation_radio)
        seg_layout.addWidget(self.live_radio)

        mode_layout.addWidget(self.segmented_frame)
        mode_layout.addStretch()
        source_layout.addLayout(mode_layout)

        status_layout = QHBoxLayout()
        self.ui_elements['selected_label'] = QLabel("Selected mode:")
        self.selected_mode_label = QLabel("AUTO")
        
        self.ui_elements['active_label'] = QLabel("Active source:")
        self.active_mode_label = QLabel("SIMULATION")

        status_layout.addWidget(self.ui_elements['selected_label'])
        status_layout.addWidget(self.selected_mode_label)
        status_layout.addSpacing(30)
        status_layout.addWidget(self.ui_elements['active_label'])
        status_layout.addWidget(self.active_mode_label)
        status_layout.addStretch()

        source_layout.addLayout(status_layout)
        main_layout.addWidget(self.source_card)

        # -----------------------------------------
        # Camera configuration
        # -----------------------------------------
        self.camera_card = self.create_card()
        camera_layout = QVBoxLayout(self.camera_card)
        camera_layout.setContentsMargins(12, 10, 12, 12)
        camera_layout.setSpacing(8)

        self.ui_elements['cam_title'] = QLabel("ESP32-CAM CONFIGURATION")
        self.ui_elements['cam_desc'] = QLabel("Enter the ESP32-CAM stream URL. Real video integration will use this address.")

        camera_layout.addWidget(self.ui_elements['cam_title'])
        camera_layout.addWidget(self.ui_elements['cam_desc'])

        camera_input_layout = QHBoxLayout()
        camera_input_layout.setSpacing(10)

        self.ui_elements['cam_url_label'] = QLabel("Camera URL")
        self.camera_url_input = QLineEdit()
        self.camera_url_input.setPlaceholderText("Example: http://192.168.4.1:81/stream")
        self.camera_url_input.setText("http://192.168.4.1:81/stream")

        self.url_shadow = QGraphicsDropShadowEffect(self.camera_url_input)
        self.url_shadow.setBlurRadius(0)
        self.url_shadow.setOffset(0, 0)
        self.camera_url_input.setGraphicsEffect(self.url_shadow)
        
        self.input_anim = QPropertyAnimation(self.url_shadow, b"blurRadius")
        self.input_anim.setDuration(800)
        self.input_anim.setEasingCurve(QEasingCurve.OutExpo)

        self.save_camera_button = QPushButton("SAVE CAMERA URL")
        self.save_camera_button.clicked.connect(self.save_camera_url)
        self.save_camera_button.setCursor(Qt.PointingHandCursor)

        camera_input_layout.addWidget(self.ui_elements['cam_url_label'])
        camera_input_layout.addWidget(self.camera_url_input, 1)
        camera_input_layout.addWidget(self.save_camera_button)

        camera_layout.addLayout(camera_input_layout)
        main_layout.addWidget(self.camera_card)

        # -----------------------------------------
        # Communication information
        # -----------------------------------------
        self.comm_card = self.create_card()
        comm_layout = QGridLayout(self.comm_card)
        comm_layout.setContentsMargins(12, 10, 12, 12)
        comm_layout.setHorizontalSpacing(14)
        comm_layout.setVerticalSpacing(8)

        self.ui_elements['comm_title'] = QLabel("COMMUNICATION")
        comm_layout.addWidget(self.ui_elements['comm_title'], 0, 0, 1, 2)

        self.ui_elements['udp_label'] = QLabel("ESP32 UDP Port")
        self.udp_value = QLabel("5005")
        
        self.ui_elements['proto_label'] = QLabel("Protocol")
        self.proto_value = QLabel("Wi-Fi UDP / JSON")
        
        self.ui_elements['gps_label'] = QLabel("Position Source")
        self.gps_value = QLabel("Simulated / Wheel Movement")
        
        comm_layout.addWidget(self.ui_elements['udp_label'], 1, 0)
        comm_layout.addWidget(self.udp_value, 1, 1)
        comm_layout.addWidget(self.ui_elements['proto_label'], 2, 0)
        comm_layout.addWidget(self.proto_value, 2, 1)
        comm_layout.addWidget(self.ui_elements['gps_label'], 3, 0)
        comm_layout.addWidget(self.gps_value, 3, 1)

        main_layout.addWidget(self.comm_card)

        # -----------------------------------------
        # Maintenance controls
        # -----------------------------------------
        self.maint_card = self.create_card()
        maint_layout = QVBoxLayout(self.maint_card)
        maint_layout.setContentsMargins(12, 10, 12, 12)
        maint_layout.setSpacing(8)

        self.ui_elements['maint_title'] = QLabel("MAINTENANCE")
        self.ui_elements['maint_desc'] = QLabel("Clear the visible history or permanently remove all pothole records from SQLite.")

        maint_layout.addWidget(self.ui_elements['maint_title'])
        maint_layout.addWidget(self.ui_elements['maint_desc'])

        maint_buttons = QHBoxLayout()
        maint_buttons.setSpacing(12)

        self.clear_history_button = QPushButton("CLEAR EVENT HISTORY")
        self.clear_history_button.setObjectName("warningButton")
        self.clear_history_button.setCursor(Qt.PointingHandCursor)
        self.clear_history_button.clicked.connect(self.request_clear_history)

        self.clear_database_button = QPushButton("RESET DATABASE")
        self.clear_database_button.setObjectName("dangerButton")
        self.clear_database_button.setCursor(Qt.PointingHandCursor)
        self.clear_database_button.clicked.connect(self.reset_database)

        maint_buttons.addWidget(self.clear_history_button)
        maint_buttons.addWidget(self.clear_database_button)
        maint_buttons.addStretch()

        maint_layout.addLayout(maint_buttons)
        main_layout.addWidget(self.maint_card)

        # -----------------------------------------
        # About project
        # -----------------------------------------
        self.about_card = self.create_card()
        about_layout = QVBoxLayout(self.about_card)
        about_layout.setContentsMargins(12, 10, 12, 12)
        about_layout.setSpacing(6)

        self.ui_elements['about_title'] = QLabel("ABOUT")
        self.ui_elements['about_text'] = QLabel(
            "Smart Road Digital Twin\n"
            "Desktop road-condition monitoring system\n\n"
            "Technology: Python, PySide6, SQLite, ESP32, ESP32-CAM, MPU6050 and Ultrasonic Sensor\n"
            "Current stage: Software development and hardware-integration preparation"
        )
        self.ui_elements['about_text'].setWordWrap(True)

        about_layout.addWidget(self.ui_elements['about_title'])
        about_layout.addWidget(self.ui_elements['about_text'])
        main_layout.addWidget(self.about_card)
        main_layout.addStretch()

    def create_card(self):
        card = QFrame()
        card.setObjectName("settingsCard")
        return card

    def apply_theme(self, theme, is_dark):
        self.theme = theme
        border = f"1px solid {theme['border']}" if is_dark else "none"
        shadow = "" if is_dark else "box-shadow: 0 1px 3px rgba(0,0,0,0.08);"
        
        self.title_label.setStyleSheet(f"color: {theme['text_primary']}; font-size: 20px; font-weight: bold; font-family: 'Segoe UI';")
        self.subtitle_label.setStyleSheet(f"color: {theme['text_secondary']}; font-size: 12px; font-family: 'Segoe UI';")
        
        card_style = f"""
            QFrame#settingsCard {{
                background-color: {theme['surface']};
                border-radius: 12px;
                border: {border};
                {shadow}
            }}
        """
        for card in [self.source_card, self.camera_card, self.comm_card, self.maint_card, self.about_card]:
            card.setStyleSheet(card_style)

        # Text styles
        for key, ui in self.ui_elements.items():
            if "title" in key:
                ui.setStyleSheet(f"color: {theme['text_primary']}; font-size: 14px; font-weight: bold; font-family: 'Segoe UI'; border: none;")
            elif "desc" in key or "text" in key:
                ui.setStyleSheet(f"color: {theme['text_secondary']}; font-size: 12px; font-family: 'Segoe UI'; border: none; line-height: 1.5;")
            elif "label" in key:
                ui.setStyleSheet(f"color: {theme['text_muted']}; font-size: 12px; font-weight: bold; font-family: 'Segoe UI'; border: none;")

        # Badges
        badge_style = f"""
            background-color: {theme['surface_elevated']};
            color: {theme['text_primary']};
            border-radius: 6px;
            padding: 6px 12px;
            font-size: 11px;
            font-weight: bold;
            font-family: 'Segoe UI';
        """
        self.selected_mode_label.setStyleSheet(badge_style)
        self.udp_value.setStyleSheet(badge_style)
        self.proto_value.setStyleSheet(badge_style)
        self.gps_value.setStyleSheet(badge_style)

        self.set_active_mode(self.current_active_mode) # reapplies active badge style with theme

        # Inputs
        self.camera_url_input.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {theme['border']};
                border-radius: 6px;
                padding: 10px;
                background-color: {theme['surface']};
                color: {theme['text_primary']};
                font-size: 13px;
                font-family: 'Segoe UI';
            }}
            QLineEdit:focus {{
                border: 1px solid {theme['accent']};
            }}
        """)
        self.url_shadow.setColor(QColor(theme['success']))
        
        primary_btn = f"""
            QPushButton {{
                background-color: {theme['accent']};
                color: white;
                border: none;
                border-radius: 20px;
                padding: 10px 18px;
                font-size: 12px;
                font-weight: bold;
                font-family: 'Segoe UI';
            }}
            QPushButton:hover {{ background-color: {theme['accent_hover']}; }}
        """
        self.save_camera_button.setStyleSheet(primary_btn)
        
        self.clear_history_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme['warning']};
                color: #ffffff;
                border: none;
                border-radius: 20px;
                padding: 10px 18px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{ opacity: 0.9; }}
        """)
        
        self.clear_database_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme['danger']};
                color: white;
                border: none;
                border-radius: 20px;
                padding: 10px 18px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{ opacity: 0.9; }}
        """)

        # Segmented Control styling for 3 radio buttons
        self.segmented_frame.setStyleSheet(f"""
            QFrame#segmentedFrame {{
                background-color: {theme['surface_elevated']};
                border-radius: 8px;
                padding: 2px;
            }}
        """)
        
        # We style QRadioButton so it looks like a pill button.
        radio_style = f"""
            QRadioButton {{
                background-color: transparent;
                color: {theme['text_secondary']};
                font-size: 11px;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 6px;
            }}
            QRadioButton::indicator {{
                width: 0px;
                height: 0px;
                border: none;
            }}
            QRadioButton:checked {{
                background-color: {theme['surface']};
                color: {theme['text_primary']};
                {"box-shadow: 0 1px 3px rgba(0,0,0,0.1);" if not is_dark else f"border: 1px solid {theme['border']};"}
            }}
            QRadioButton:hover:!checked {{
                color: {theme['text_primary']};
            }}
        """
        self.auto_radio.setStyleSheet(radio_style)
        self.simulation_radio.setStyleSheet(radio_style)
        self.live_radio.setStyleSheet(radio_style)

    def handle_mode_selection(self):
        if self.auto_radio.isChecked(): selected_mode = "AUTO"
        elif self.simulation_radio.isChecked(): selected_mode = "SIMULATION"
        elif self.live_radio.isChecked(): selected_mode = "LIVE"
        else: return
        self.selected_mode_label.setText(selected_mode)
        self.mode_changed.emit(selected_mode)

    def set_active_mode(self, active_mode):
        normalized_mode = str(active_mode).strip().upper()
        self.current_active_mode = normalized_mode
        self.active_mode_label.setText(normalized_mode)

        if not hasattr(self, 'theme'): return
        
        if normalized_mode == "LIVE":
            bg = self.theme['success']
        else:
            bg = self.theme['accent']
            
        self.active_mode_label.setStyleSheet(f"""
            background-color: {bg};
            color: white;
            border-radius: 6px;
            padding: 6px 12px;
            font-size: 11px;
            font-weight: bold;
            font-family: 'Segoe UI';
        """)

    def save_camera_url(self):
        url = self.camera_url_input.text().strip()
        if not url: return
        self.camera_url_saved.emit(url)
        
        # Flash visual feedback on save
        self.input_anim.stop()
        self.input_anim.setStartValue(20)
        self.input_anim.setEndValue(0)
        self.input_anim.start()
        QMessageBox.information(self, "Camera URL Saved", f"Saved: {url}\n\nNote: In the final app, this connects to the real ESP32-CAM stream.")

    def request_clear_history(self):
        answer = QMessageBox.question(
            self, "Clear Event History",
            "Are you sure you want to clear the visible event history list?\n(Records remain in the database)",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if answer == QMessageBox.Yes:
            self.clear_history_requested.emit()
            QMessageBox.information(self, "History Cleared", "Visible history list was cleared.")

    def reset_database(self):
        answer = QMessageBox.question(
            self, "Reset Database",
            "This will DELETE ALL pothole records permanently. Are you sure?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if answer == QMessageBox.Yes:
            try:
                clear_database()
                self.database_cleared.emit()
                QMessageBox.information(self, "Database Reset", "All records were deleted permanently.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to reset: {e}")