# ==================================================
# SMART ROAD DIGITAL TWIN - POTHOLE DETAILS DIALOG
# ==================================================

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)


class PotholeDetailsDialog(QDialog):
    """
    Professional popup showing details for one pothole.

    The dialog can display information from both:
    - the map's simulated pothole dictionary
    - the stored SQLite database record
    """

    def __init__(
        self,
        pothole,
        database_record=None,
        parent=None,
    ):
        super().__init__(parent)

        self.pothole = pothole
        self.database_record = database_record or {}

        pothole_id = pothole.get(
            "id",
            self.database_record.get(
                "pothole_id",
                "--",
            ),
        )

        self.setWindowTitle(
            f"Pothole P-{pothole_id} Details"
        )

        self.setMinimumSize(
            560,
            560,
        )

        self.setModal(True)

        self.setStyleSheet(
            """
            QDialog {
                background-color:#111827;
                color:white;
            }

            QLabel {
                color:white;
                background:transparent;
            }

            QLabel#dialogTitle {
                font-size:24px;
                font-weight:bold;
                color:#ffffff;
                padding:8px;
            }

            QLabel#dialogSubtitle {
                font-size:12px;
                color:#9ca3af;
                padding-bottom:8px;
            }

            QFrame#informationCard {
                background-color:#1f2937;
                border:1px solid #374151;
                border-radius:12px;
            }

            QLabel#fieldTitle {
                color:#9ca3af;
                font-size:11px;
                font-weight:bold;
            }

            QLabel#fieldValue {
                color:#ffffff;
                font-size:14px;
                font-weight:bold;
            }

            QLabel#severityHigh {
                background-color:#991b1b;
                color:white;
                border-radius:7px;
                padding:7px 14px;
                font-size:13px;
                font-weight:bold;
            }

            QLabel#severityMedium {
                background-color:#b45309;
                color:white;
                border-radius:7px;
                padding:7px 14px;
                font-size:13px;
                font-weight:bold;
            }

            QLabel#severityLow {
                background-color:#166534;
                color:white;
                border-radius:7px;
                padding:7px 14px;
                font-size:13px;
                font-weight:bold;
            }

            QLabel#imagePreview {
                background-color:#0b0f14;
                border:1px solid #374151;
                border-radius:10px;
                color:#9ca3af;
                font-size:13px;
            }

            QPushButton {
                background-color:#3b82f6;
                color:white;
                border:none;
                border-radius:7px;
                padding:10px 24px;
                font-size:12px;
                font-weight:bold;
            }

            QPushButton:hover {
                background-color:#2563eb;
            }

            QPushButton:pressed {
                background-color:#1d4ed8;
            }
            """
        )

        self.build_interface()

    def build_interface(self):
        """Create the complete pothole details popup."""

        main_layout = QVBoxLayout(self)

        main_layout.setContentsMargins(
            20,
            18,
            20,
            20,
        )

        main_layout.setSpacing(14)

        pothole_id = self.get_value(
            map_key="id",
            database_key="pothole_id",
            default="--",
        )

        title_label = QLabel(
            f"POTHOLE P-{pothole_id}"
        )

        title_label.setObjectName(
            "dialogTitle"
        )

        title_label.setAlignment(
            Qt.AlignCenter
        )

        subtitle_label = QLabel(
            "Digital Twin Road Defect Information"
        )

        subtitle_label.setObjectName(
            "dialogSubtitle"
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
        # Main information card
        # -----------------------------------------
        information_card = QFrame()
        information_card.setObjectName(
            "informationCard"
        )

        information_layout = QGridLayout(
            information_card
        )

        information_layout.setContentsMargins(
            18,
            18,
            18,
            18,
        )

        information_layout.setHorizontalSpacing(
            30
        )

        information_layout.setVerticalSpacing(
            15
        )

        depth = self.get_value(
            map_key="depth",
            database_key="depth",
            default=0,
        )

        severity = str(
            self.get_value(
                map_key="severity",
                database_key="severity",
                default="UNKNOWN",
            )
        ).upper()

        x_position = self.get_value(
            map_key="x",
            database_key="x",
            default=0,
        )

        y_position = self.get_value(
            map_key="y",
            database_key="y",
            default=0,
        )

        detected = bool(
            self.pothole.get(
                "detected",
                bool(self.database_record),
            )
        )

        photo_captured = bool(
            self.get_value(
                map_key="photo_captured",
                database_key="photo_captured",
                default=False,
            )
        )

        detected_at = self.database_record.get(
            "detected_at",
            "Not detected yet",
        )

        latitude = self.database_record.get(
            "latitude",
            0.0,
        )

        longitude = self.database_record.get(
            "longitude",
            0.0,
        )

        self.add_information_row(
            information_layout,
            row=0,
            title="POTHOLE ID",
            value=f"P-{pothole_id}",
        )

        self.add_information_row(
            information_layout,
            row=1,
            title="DEPTH",
            value=f"{depth} cm",
        )

        self.add_information_row(
            information_layout,
            row=2,
            title="MAP POSITION",
            value=f"({x_position}, {y_position})",
        )

        self.add_information_row(
            information_layout,
            row=3,
            title="DETECTION STATUS",
            value=(
                "DETECTED"
                if detected
                else "NOT DETECTED"
            ),
        )

        self.add_information_row(
            information_layout,
            row=4,
            title="DETECTED AT",
            value=str(detected_at),
        )

        self.add_information_row(
            information_layout,
            row=5,
            title="PHOTO CAPTURED",
            value=(
                "YES"
                if photo_captured
                else "NO"
            ),
        )

        self.add_information_row(
            information_layout,
            row=6,
            title="POSITION SOURCE",
            value=(
                f"Digital Twin X/Y | "
                f"{latitude}, {longitude}"
            ),
        )

        severity_title = QLabel(
            "SEVERITY"
        )
        severity_title.setObjectName(
            "fieldTitle"
        )

        severity_value = QLabel(
            severity
        )

        if severity == "HIGH":
            severity_value.setObjectName(
                "severityHigh"
            )

        elif severity == "MEDIUM":
            severity_value.setObjectName(
                "severityMedium"
            )

        else:
            severity_value.setObjectName(
                "severityLow"
            )

        information_layout.addWidget(
            severity_title,
            7,
            0,
        )

        information_layout.addWidget(
            severity_value,
            7,
            1,
            alignment=Qt.AlignLeft,
        )

        main_layout.addWidget(
            information_card
        )

        # -----------------------------------------
        # Image preview
        # -----------------------------------------
        image_title = QLabel(
            "CAPTURED ROAD IMAGE"
        )

        image_title.setStyleSheet(
            """
            color:#d1d5db;
            font-size:13px;
            font-weight:bold;
            padding-top:4px;
            """
        )

        main_layout.addWidget(
            image_title
        )

        self.image_preview = QLabel()
        self.image_preview.setObjectName(
            "imagePreview"
        )

        self.image_preview.setMinimumHeight(
            170
        )

        self.image_preview.setAlignment(
            Qt.AlignCenter
        )

        self.load_image_preview()

        main_layout.addWidget(
            self.image_preview
        )

        # -----------------------------------------
        # Close button
        # -----------------------------------------
        button_layout = QHBoxLayout()

        button_layout.addStretch()

        close_button = QPushButton(
            "CLOSE"
        )

        close_button.clicked.connect(
            self.accept
        )

        button_layout.addWidget(
            close_button
        )

        main_layout.addLayout(
            button_layout
        )

    def get_value(
        self,
        map_key,
        database_key,
        default=None,
    ):
        """
        Prefer the database value when available,
        otherwise use the map's pothole dictionary.
        """

        if database_key in self.database_record:
            value = self.database_record.get(
                database_key
            )

            if value is not None:
                return value

        return self.pothole.get(
            map_key,
            default,
        )

    def add_information_row(
        self,
        layout,
        row,
        title,
        value,
    ):
        """Add one title-value row to the details card."""

        title_label = QLabel(
            title
        )

        title_label.setObjectName(
            "fieldTitle"
        )

        value_label = QLabel(
            str(value)
        )

        value_label.setObjectName(
            "fieldValue"
        )

        value_label.setWordWrap(
            True
        )

        layout.addWidget(
            title_label,
            row,
            0,
        )

        layout.addWidget(
            value_label,
            row,
            1,
        )

    def load_image_preview(self):
        """
        Load the captured pothole image when its stored path
        exists. Otherwise show a clear placeholder.
        """

        image_path_text = str(
            self.database_record.get(
                "image_path",
                "",
            )
        ).strip()

        if not image_path_text:
            self.image_preview.setText(
                "No captured image available.\n"
                "An image will appear here after "
                "ESP32-CAM snapshot integration."
            )
            return

        image_path = Path(
            image_path_text
        )

        if not image_path.exists():
            self.image_preview.setText(
                "Image path is stored, but the file "
                "could not be found.\n\n"
                f"{image_path}"
            )
            return

        pixmap = QPixmap(
            str(image_path)
        )

        if pixmap.isNull():
            self.image_preview.setText(
                "The saved image could not be loaded."
            )
            return

        scaled_pixmap = pixmap.scaled(
            480,
            170,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )

        self.image_preview.setPixmap(
            scaled_pixmap
        )