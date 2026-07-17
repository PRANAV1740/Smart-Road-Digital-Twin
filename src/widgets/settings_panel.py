# ==================================================
# SMART ROAD DIGITAL TWIN - SETTINGS PANEL
# ==================================================

from PySide6.QtCore import (
    Qt,
    Signal,
)
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from database.database import clear_database


class SettingsPanel(QWidget):
    """
    Settings and system-control page.

    Signals are sent to dashboard.py so the dashboard can
    control simulation mode, live hardware mode and history.
    """

    mode_changed = Signal(str)
    clear_history_requested = Signal()
    database_cleared = Signal()
    camera_url_saved = Signal(str)

    def __init__(self):
        super().__init__()

        self.current_active_mode = "SIMULATION"

        self.setStyleSheet(
            """
            QWidget {
                background-color:#1e1e1e;
                color:white;
            }

            QLabel#pageTitle {
                font-size:28px;
                font-weight:bold;
                color:white;
                padding:8px;
            }

            QLabel#pageSubtitle {
                font-size:12px;
                color:#aaaaaa;
                padding-bottom:10px;
            }

            QFrame#settingsCard {
                background-color:#282828;
                border:1px solid #404040;
                border-radius:12px;
            }

            QLabel#sectionTitle {
                font-size:17px;
                font-weight:bold;
                color:white;
            }

            QLabel#sectionDescription {
                font-size:11px;
                color:#aaaaaa;
            }

            QLabel#fieldLabel {
                font-size:12px;
                font-weight:bold;
                color:#dddddd;
            }

            QLabel#modeBadge {
                background-color:#374151;
                color:white;
                border-radius:7px;
                padding:8px 14px;
                font-size:12px;
                font-weight:bold;
            }

            QRadioButton {
                color:white;
                font-size:13px;
                spacing:8px;
                padding:6px;
            }

            QRadioButton::indicator {
                width:17px;
                height:17px;
            }

            QLineEdit {
                background-color:#111827;
                color:white;
                border:1px solid #4b5563;
                border-radius:7px;
                padding:10px;
                font-size:12px;
            }

            QLineEdit:focus {
                border:1px solid #3b82f6;
            }

            QPushButton {
                background-color:#3b82f6;
                color:white;
                border:none;
                border-radius:7px;
                padding:10px 18px;
                font-size:12px;
                font-weight:bold;
            }

            QPushButton:hover {
                background-color:#2563eb;
            }

            QPushButton:pressed {
                background-color:#1d4ed8;
            }

            QPushButton#secondaryButton {
                background-color:#4b5563;
            }

            QPushButton#secondaryButton:hover {
                background-color:#374151;
            }

            QPushButton#dangerButton {
                background-color:#dc2626;
            }

            QPushButton#dangerButton:hover {
                background-color:#b91c1c;
            }

            QPushButton#warningButton {
                background-color:#d97706;
            }

            QPushButton#warningButton:hover {
                background-color:#b45309;
            }
            """
        )

        self.build_interface()

    def build_interface(self):
        """Create the complete Settings page."""

        main_layout = QVBoxLayout(self)

        main_layout.setContentsMargins(
            24,
            18,
            24,
            24,
        )

        main_layout.setSpacing(16)

        title_label = QLabel(
            "SYSTEM SETTINGS"
        )
        title_label.setObjectName(
            "pageTitle"
        )
        title_label.setAlignment(
            Qt.AlignCenter
        )

        subtitle_label = QLabel(
            (
                "Configure data sources, camera connection "
                "and application maintenance options"
            )
        )
        subtitle_label.setObjectName(
            "pageSubtitle"
        )
        subtitle_label.setAlignment(
            Qt.AlignCenter
        )

        main_layout.addWidget(
            title_label
        )

        main_layout.addWidget(
            subtitle_label
        )

        # -----------------------------------------
        # Data source settings
        # -----------------------------------------
        source_card = self.create_card()

        source_layout = QVBoxLayout(
            source_card
        )

        source_layout.setContentsMargins(
            18,
            16,
            18,
            18,
        )

        source_layout.setSpacing(12)

        source_title = QLabel(
            "DATA SOURCE"
        )
        source_title.setObjectName(
            "sectionTitle"
        )

        source_description = QLabel(
            (
                "Choose how dashboard sensor data should "
                "be supplied."
            )
        )
        source_description.setObjectName(
            "sectionDescription"
        )

        source_layout.addWidget(
            source_title
        )

        source_layout.addWidget(
            source_description
        )

        mode_layout = QHBoxLayout()
        mode_layout.setSpacing(20)

        self.auto_radio = QRadioButton(
            "AUTO"
        )

        self.simulation_radio = QRadioButton(
            "SIMULATION"
        )

        self.live_radio = QRadioButton(
            "LIVE HARDWARE"
        )

        self.mode_group = QButtonGroup(
            self
        )

        self.mode_group.addButton(
            self.auto_radio
        )

        self.mode_group.addButton(
            self.simulation_radio
        )

        self.mode_group.addButton(
            self.live_radio
        )

        self.auto_radio.setChecked(True)

        self.auto_radio.toggled.connect(
            self.handle_mode_selection
        )

        self.simulation_radio.toggled.connect(
            self.handle_mode_selection
        )

        self.live_radio.toggled.connect(
            self.handle_mode_selection
        )

        mode_layout.addWidget(
            self.auto_radio
        )

        mode_layout.addWidget(
            self.simulation_radio
        )

        mode_layout.addWidget(
            self.live_radio
        )

        mode_layout.addStretch()

        source_layout.addLayout(
            mode_layout
        )

        status_layout = QHBoxLayout()

        selected_label = QLabel(
            "Selected mode:"
        )
        selected_label.setObjectName(
            "fieldLabel"
        )

        self.selected_mode_label = QLabel(
            "AUTO"
        )
        self.selected_mode_label.setObjectName(
            "modeBadge"
        )

        active_label = QLabel(
            "Active source:"
        )
        active_label.setObjectName(
            "fieldLabel"
        )

        self.active_mode_label = QLabel(
            "SIMULATION"
        )
        self.active_mode_label.setObjectName(
            "modeBadge"
        )

        status_layout.addWidget(
            selected_label
        )

        status_layout.addWidget(
            self.selected_mode_label
        )

        status_layout.addSpacing(30)

        status_layout.addWidget(
            active_label
        )

        status_layout.addWidget(
            self.active_mode_label
        )

        status_layout.addStretch()

        source_layout.addLayout(
            status_layout
        )

        main_layout.addWidget(
            source_card
        )

        # -----------------------------------------
        # Camera configuration
        # -----------------------------------------
        camera_card = self.create_card()

        camera_layout = QVBoxLayout(
            camera_card
        )

        camera_layout.setContentsMargins(
            18,
            16,
            18,
            18,
        )

        camera_layout.setSpacing(12)

        camera_title = QLabel(
            "ESP32-CAM CONFIGURATION"
        )
        camera_title.setObjectName(
            "sectionTitle"
        )

        camera_description = QLabel(
            (
                "Enter the ESP32-CAM stream URL. "
                "Real video integration will use this address."
            )
        )
        camera_description.setObjectName(
            "sectionDescription"
        )

        camera_layout.addWidget(
            camera_title
        )

        camera_layout.addWidget(
            camera_description
        )

        camera_input_layout = QHBoxLayout()
        camera_input_layout.setSpacing(10)

        camera_url_label = QLabel(
            "Camera URL"
        )
        camera_url_label.setObjectName(
            "fieldLabel"
        )

        self.camera_url_input = QLineEdit()

        self.camera_url_input.setPlaceholderText(
            "Example: http://192.168.4.1:81/stream"
        )

        self.camera_url_input.setText(
            "http://192.168.4.1:81/stream"
        )

        self.save_camera_button = QPushButton(
            "SAVE CAMERA URL"
        )

        self.save_camera_button.clicked.connect(
            self.save_camera_url
        )

        camera_input_layout.addWidget(
            camera_url_label
        )

        camera_input_layout.addWidget(
            self.camera_url_input,
            1,
        )

        camera_input_layout.addWidget(
            self.save_camera_button
        )

        camera_layout.addLayout(
            camera_input_layout
        )

        main_layout.addWidget(
            camera_card
        )

        # -----------------------------------------
        # Communication information
        # -----------------------------------------
        communication_card = self.create_card()

        communication_layout = QGridLayout(
            communication_card
        )

        communication_layout.setContentsMargins(
            18,
            16,
            18,
            18,
        )

        communication_layout.setHorizontalSpacing(
            18
        )

        communication_layout.setVerticalSpacing(
            12
        )

        communication_title = QLabel(
            "COMMUNICATION"
        )
        communication_title.setObjectName(
            "sectionTitle"
        )

        communication_layout.addWidget(
            communication_title,
            0,
            0,
            1,
            2,
        )

        udp_label = QLabel(
            "ESP32 UDP Port"
        )
        udp_label.setObjectName(
            "fieldLabel"
        )

        udp_value = QLabel(
            "5005"
        )
        udp_value.setObjectName(
            "modeBadge"
        )

        protocol_label = QLabel(
            "Protocol"
        )
        protocol_label.setObjectName(
            "fieldLabel"
        )

        protocol_value = QLabel(
            "Wi-Fi UDP / JSON"
        )
        protocol_value.setObjectName(
            "modeBadge"
        )

        gps_label = QLabel(
            "Position Source"
        )
        gps_label.setObjectName(
            "fieldLabel"
        )

        gps_value = QLabel(
            "Simulated / Wheel Movement"
        )
        gps_value.setObjectName(
            "modeBadge"
        )

        communication_layout.addWidget(
            udp_label,
            1,
            0,
        )

        communication_layout.addWidget(
            udp_value,
            1,
            1,
        )

        communication_layout.addWidget(
            protocol_label,
            2,
            0,
        )

        communication_layout.addWidget(
            protocol_value,
            2,
            1,
        )

        communication_layout.addWidget(
            gps_label,
            3,
            0,
        )

        communication_layout.addWidget(
            gps_value,
            3,
            1,
        )

        main_layout.addWidget(
            communication_card
        )

        # -----------------------------------------
        # Maintenance controls
        # -----------------------------------------
        maintenance_card = self.create_card()

        maintenance_layout = QVBoxLayout(
            maintenance_card
        )

        maintenance_layout.setContentsMargins(
            18,
            16,
            18,
            18,
        )

        maintenance_layout.setSpacing(12)

        maintenance_title = QLabel(
            "MAINTENANCE"
        )
        maintenance_title.setObjectName(
            "sectionTitle"
        )

        maintenance_description = QLabel(
            (
                "Clear the visible history or permanently "
                "remove all pothole records from SQLite."
            )
        )
        maintenance_description.setObjectName(
            "sectionDescription"
        )

        maintenance_layout.addWidget(
            maintenance_title
        )

        maintenance_layout.addWidget(
            maintenance_description
        )

        maintenance_buttons = QHBoxLayout()
        maintenance_buttons.setSpacing(12)

        self.clear_history_button = QPushButton(
            "CLEAR EVENT HISTORY"
        )
        self.clear_history_button.setObjectName(
            "warningButton"
        )

        self.clear_history_button.clicked.connect(
            self.request_clear_history
        )

        self.clear_database_button = QPushButton(
            "RESET DATABASE"
        )
        self.clear_database_button.setObjectName(
            "dangerButton"
        )

        self.clear_database_button.clicked.connect(
            self.reset_database
        )

        maintenance_buttons.addWidget(
            self.clear_history_button
        )

        maintenance_buttons.addWidget(
            self.clear_database_button
        )

        maintenance_buttons.addStretch()

        maintenance_layout.addLayout(
            maintenance_buttons
        )

        main_layout.addWidget(
            maintenance_card
        )

        # -----------------------------------------
        # About project
        # -----------------------------------------
        about_card = self.create_card()

        about_layout = QVBoxLayout(
            about_card
        )

        about_layout.setContentsMargins(
            18,
            16,
            18,
            18,
        )

        about_layout.setSpacing(8)

        about_title = QLabel(
            "ABOUT"
        )
        about_title.setObjectName(
            "sectionTitle"
        )

        about_text = QLabel(
            (
                "Smart Road Digital Twin\n"
                "Desktop road-condition monitoring system\n\n"
                "Technology: Python, PySide6, SQLite, "
                "ESP32, ESP32-CAM, MPU6050 and Ultrasonic Sensor\n"
                "Current stage: Software development and "
                "hardware-integration preparation"
            )
        )

        about_text.setWordWrap(True)

        about_text.setStyleSheet(
            """
            color:#cfcfcf;
            font-size:12px;
            line-height:1.5;
            """
        )

        about_layout.addWidget(
            about_title
        )

        about_layout.addWidget(
            about_text
        )

        main_layout.addWidget(
            about_card
        )

        main_layout.addStretch()

    def create_card(self):
        """Create a reusable settings card."""

        card = QFrame()
        card.setObjectName(
            "settingsCard"
        )

        return card

    def handle_mode_selection(self):
        """Emit the mode selected by the user."""

        if self.auto_radio.isChecked():
            selected_mode = "AUTO"

        elif self.simulation_radio.isChecked():
            selected_mode = "SIMULATION"

        elif self.live_radio.isChecked():
            selected_mode = "LIVE"

        else:
            return

        self.selected_mode_label.setText(
            selected_mode
        )

        self.mode_changed.emit(
            selected_mode
        )

    def set_active_mode(self, active_mode):
        """
        Update the active data-source badge from dashboard.py.
        """

        normalized_mode = str(
            active_mode
        ).strip().upper()

        self.current_active_mode = normalized_mode

        self.active_mode_label.setText(
            normalized_mode
        )

        if normalized_mode == "LIVE":
            self.active_mode_label.setStyleSheet(
                """
                background-color:#166534;
                color:white;
                border-radius:7px;
                padding:8px 14px;
                font-size:12px;
                font-weight:bold;
                """
            )

        else:
            self.active_mode_label.setStyleSheet(
                """
                background-color:#1d4ed8;
                color:white;
                border-radius:7px;
                padding:8px 14px;
                font-size:12px;
                font-weight:bold;
                """
            )

    def save_camera_url(self):
        """Validate and emit the camera URL."""

        camera_url = (
            self.camera_url_input.text().strip()
        )

        if not camera_url:
            QMessageBox.warning(
                self,
                "Invalid Camera URL",
                "Please enter an ESP32-CAM stream URL.",
            )
            return

        if not (
            camera_url.startswith("http://")
            or camera_url.startswith("https://")
        ):
            QMessageBox.warning(
                self,
                "Invalid Camera URL",
                (
                    "The camera URL must begin with "
                    "http:// or https://"
                ),
            )
            return

        self.camera_url_saved.emit(
            camera_url
        )

        QMessageBox.information(
            self,
            "Camera URL Saved",
            (
                "The camera stream URL has been saved "
                "for later camera integration.\n\n"
                f"{camera_url}"
            ),
        )

    def request_clear_history(self):
        """Confirm before clearing visible event history."""

        response = QMessageBox.question(
            self,
            "Clear Event History",
            (
                "Clear all events currently displayed "
                "inside the Event History panel?\n\n"
                "This will not delete SQLite database records."
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if response != QMessageBox.Yes:
            return

        self.clear_history_requested.emit()

        QMessageBox.information(
            self,
            "History Cleared",
            (
                "The visible Event History panel "
                "has been cleared."
            ),
        )

    def reset_database(self):
        """
        Permanently delete all pothole records after
        user confirmation.
        """

        first_confirmation = QMessageBox.warning(
            self,
            "Reset SQLite Database",
            (
                "This will permanently delete every stored "
                "pothole record.\n\n"
                "CSV and PDF files already exported will "
                "not be deleted.\n\n"
                "Do you want to continue?"
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if first_confirmation != QMessageBox.Yes:
            return

        try:
            clear_database()

            self.database_cleared.emit()

            QMessageBox.information(
                self,
                "Database Reset Complete",
                (
                    "All stored pothole records were "
                    "deleted successfully."
                ),
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Database Reset Failed",
                str(error),
            )