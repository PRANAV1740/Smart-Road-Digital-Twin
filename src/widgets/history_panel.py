# ==================================================
# SMART ROAD DIGITAL TWIN - PHOTO HISTORY PANEL
# ==================================================

from pathlib import Path

from PySide6.QtCore import (
    Qt,
    QDateTime,
    QTimer,
    Signal,
)
from PySide6.QtGui import (
    QColor,
    QFont,
    QPixmap,
)
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from database.database import get_all_potholes
from utils import data


class ClickableImageLabel(QLabel):
    """
    QLabel that emits a signal when clicked.
    """

    clicked = Signal()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()

        super().mousePressEvent(event)


class ImageViewerDialog(QDialog):
    """
    Popup window used to display a captured pothole image.
    """

    def __init__(
        self,
        image_path,
        pothole_id,
        parent=None,
    ):
        super().__init__(parent)

        self.image_path = Path(image_path)

        self.setWindowTitle(
            f"Pothole {pothole_id} - Captured Image"
        )

        self.resize(
            900,
            650,
        )

        self.setMinimumSize(
            600,
            450,
        )

        self.setStyleSheet(
            """
            QDialog {
                background:#10151b;
            }

            QLabel {
                color:white;
            }

            QPushButton {
                background:#2f81f7;
                color:white;
                border:none;
                border-radius:7px;
                padding:8px 24px;
                font-size:14px;
                font-weight:bold;
            }

            QPushButton:hover {
                background:#4393ff;
            }

            QPushButton:pressed {
                background:#1f6feb;
            }
            """
        )

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            15,
            15,
            15,
            15,
        )

        layout.setSpacing(12)

        title = QLabel(
            f"POTHOLE {pothole_id} CAPTURE"
        )

        title.setAlignment(
            Qt.AlignCenter
        )

        title.setStyleSheet(
            """
            font-size:20px;
            font-weight:bold;
            background:#1b222b;
            border-radius:8px;
            padding:10px;
            """
        )

        self.image_label = QLabel()

        self.image_label.setAlignment(
            Qt.AlignCenter
        )

        self.image_label.setMinimumSize(
            500,
            330,
        )

        self.image_label.setStyleSheet(
            """
            background:#080c10;
            border:1px solid #3b434d;
            border-radius:10px;
            """
        )

        path_label = QLabel(
            str(self.image_path)
        )

        path_label.setAlignment(
            Qt.AlignCenter
        )

        path_label.setWordWrap(True)

        path_label.setStyleSheet(
            """
            color:#9ba7b4;
            background:#151b22;
            border-radius:7px;
            padding:7px;
            font-size:12px;
            """
        )

        close_button = QPushButton(
            "Close"
        )

        close_button.setFixedWidth(
            130
        )

        close_button.clicked.connect(
            self.accept
        )

        button_layout = QHBoxLayout()

        button_layout.addStretch()

        button_layout.addWidget(
            close_button
        )

        button_layout.addStretch()

        layout.addWidget(
            title
        )

        layout.addWidget(
            self.image_label,
            1,
        )

        layout.addWidget(
            path_label
        )

        layout.addLayout(
            button_layout
        )

        self.load_image()

    def load_image(self):
        """
        Load and display the selected image.
        """

        if not self.image_path.exists():
            self.image_label.setText(
                "Captured image file was not found."
            )
            return

        pixmap = QPixmap(
            str(self.image_path)
        )

        if pixmap.isNull():
            self.image_label.setText(
                "The image could not be loaded."
            )
            return

        scaled_pixmap = pixmap.scaled(
            self.image_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )

        self.image_label.setPixmap(
            scaled_pixmap
        )

        self.original_pixmap = pixmap

    def resizeEvent(self, event):
        """
        Keep the image properly scaled when the popup resizes.
        """

        super().resizeEvent(event)

        if not hasattr(
            self,
            "original_pixmap",
        ):
            return

        scaled_pixmap = (
            self.original_pixmap.scaled(
                self.image_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        )

        self.image_label.setPixmap(
            scaled_pixmap
        )


class PotholeHistoryCard(QFrame):
    """
    Visual card for one stored pothole record.
    """

    def __init__(
        self,
        record,
        parent=None,
    ):
        super().__init__(parent)

        self.record = {}
        self.image_path = ""

        self.setObjectName(
            "historyCard"
        )

        self.setMinimumHeight(
            155
        )

        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed,
        )

        self.setStyleSheet(
            """
            QFrame#historyCard {
                background:#131920;
                border:1px solid #343d47;
                border-radius:10px;
            }

            QFrame#historyCard:hover {
                border:1px solid #4b8ed8;
                background:#171f28;
            }

            QLabel {
                background:transparent;
                border:none;
            }
            """
        )

        main_layout = QHBoxLayout(self)

        main_layout.setContentsMargins(
            10,
            10,
            10,
            10,
        )

        main_layout.setSpacing(
            12
        )

        self.image_label = (
            ClickableImageLabel()
        )

        self.image_label.setFixedSize(
            145,
            115,
        )

        self.image_label.setAlignment(
            Qt.AlignCenter
        )

        self.image_label.setCursor(
            Qt.PointingHandCursor
        )

        self.image_label.setStyleSheet(
            """
            background:#080c10;
            color:#83909e;
            border:1px solid #3b434d;
            border-radius:8px;
            font-size:12px;
            """
        )

        self.image_label.clicked.connect(
            self.open_image
        )

        information_layout = QVBoxLayout()

        information_layout.setSpacing(
            5
        )

        self.heading_label = QLabel()

        self.heading_label.setStyleSheet(
            """
            color:#ffffff;
            font-size:16px;
            font-weight:bold;
            """
        )

        self.details_label = QLabel()

        self.details_label.setWordWrap(
            True
        )

        self.details_label.setStyleSheet(
            """
            color:#c6cdd5;
            font-size:12px;
            """
        )

        self.location_label = QLabel()

        self.location_label.setWordWrap(
            True
        )

        self.location_label.setStyleSheet(
            """
            color:#8f9aa6;
            font-size:11px;
            """
        )

        self.photo_label = QLabel()

        self.photo_label.setStyleSheet(
            """
            font-size:11px;
            font-weight:bold;
            """
        )

        information_layout.addWidget(
            self.heading_label
        )

        information_layout.addWidget(
            self.details_label
        )

        information_layout.addWidget(
            self.location_label
        )

        information_layout.addWidget(
            self.photo_label
        )

        information_layout.addStretch()

        main_layout.addWidget(
            self.image_label
        )

        main_layout.addLayout(
            information_layout,
            1,
        )

        self.update_record(
            record
        )

    def update_record(
        self,
        record,
    ):
        """
        Update card details when the database row changes.

        This is especially useful when the image is added
        after the pothole record was originally created.
        """

        self.record = dict(
            record
        )

        pothole_id = self.record.get(
            "pothole_id",
            "-",
        )

        severity = str(
            self.record.get(
                "severity",
                "UNKNOWN",
            )
        ).upper()

        depth = self.record.get(
            "depth",
            0,
        )

        detected_at = self.record.get(
            "detected_at",
            "-",
        )

        x_position = self.record.get(
            "x",
            0,
        )

        y_position = self.record.get(
            "y",
            0,
        )

        latitude = self.record.get(
            "latitude",
            0.0,
        )

        longitude = self.record.get(
            "longitude",
            0.0,
        )

        photo_captured = bool(
            self.record.get(
                "photo_captured",
                0,
            )
        )

        self.image_path = str(
            self.record.get(
                "image_path",
                "",
            )
            or ""
        )

        self.heading_label.setText(
            (
                f"Pothole #{pothole_id}  •  "
                f"{severity}"
            )
        )

        self.heading_label.setStyleSheet(
            self.get_heading_style(
                severity
            )
        )

        self.details_label.setText(
            (
                f"Depth: {depth} cm\n"
                f"Detected: {detected_at}"
            )
        )

        self.location_label.setText(
            (
                f"Map position: "
                f"({x_position}, {y_position})\n"
                f"GPS: ({latitude}, {longitude})"
            )
        )

        if (
            photo_captured
            and self.image_path
        ):
            self.photo_label.setText(
                "● PHOTO CAPTURED — click image to open"
            )

            self.photo_label.setStyleSheet(
                """
                color:#33d17a;
                font-size:11px;
                font-weight:bold;
                """
            )

            self.load_thumbnail()
        else:
            self.photo_label.setText(
                "○ PHOTO NOT AVAILABLE"
            )

            self.photo_label.setStyleSheet(
                """
                color:#f0ad4e;
                font-size:11px;
                font-weight:bold;
                """
            )

            self.show_placeholder()

    def get_heading_style(
        self,
        severity,
    ):
        """
        Return a severity-specific title style.
        """

        if severity == "HIGH":
            color = "#ff5c5c"

        elif severity == "MEDIUM":
            color = "#ffbf47"

        elif severity == "LOW":
            color = "#33d17a"

        else:
            color = "#ffffff"

        return f"""
            color:{color};
            font-size:16px;
            font-weight:bold;
        """

    def load_thumbnail(self):
        """
        Load the captured image into the card.
        """

        path = Path(
            self.image_path
        )

        if not path.exists():
            self.image_label.setPixmap(
                QPixmap()
            )

            self.image_label.setText(
                "IMAGE FILE\nNOT FOUND"
            )

            self.image_label.setCursor(
                Qt.ArrowCursor
            )

            return

        pixmap = QPixmap(
            str(path)
        )

        if pixmap.isNull():
            self.image_label.setPixmap(
                QPixmap()
            )

            self.image_label.setText(
                "INVALID\nIMAGE"
            )

            self.image_label.setCursor(
                Qt.ArrowCursor
            )

            return

        scaled_pixmap = pixmap.scaled(
            self.image_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )

        self.image_label.setText(
            ""
        )

        self.image_label.setPixmap(
            scaled_pixmap
        )

        self.image_label.setCursor(
            Qt.PointingHandCursor
        )

    def show_placeholder(self):
        """
        Show a placeholder when no image exists.
        """

        self.image_label.setPixmap(
            QPixmap()
        )

        self.image_label.setText(
            "NO PHOTO\nCAPTURED"
        )

        self.image_label.setCursor(
            Qt.ArrowCursor
        )

    def open_image(self):
        """
        Open the captured image in a larger popup.
        """

        if not self.image_path:
            return

        path = Path(
            self.image_path
        )

        if not path.exists():
            return

        pothole_id = self.record.get(
            "pothole_id",
            "-",
        )

        viewer = ImageViewerDialog(
            image_path=path,
            pothole_id=pothole_id,
            parent=self,
        )

        viewer.exec()


class HistoryPanel(QWidget):
    """
    Photo-based pothole history panel.

    Database records are displayed as cards and refreshed
    automatically whenever the record or image status changes.
    """

    def __init__(self):
        super().__init__()

        self.last_warning_level = ""
        self.last_pothole_id = None

        self.history_cards = {}

        self.setMinimumHeight(
            340
        )

        self.setStyleSheet(
            """
            QWidget {
                background:#1b1f24;
                border-radius:12px;
            }

            QLabel {
                color:white;
            }

            QScrollArea {
                background:#0b0f14;
                border:1px solid #444444;
                border-radius:8px;
            }

            QScrollBar:vertical {
                background:#111820;
                width:12px;
                margin:2px;
                border-radius:6px;
            }

            QScrollBar::handle:vertical {
                background:#4b5561;
                min-height:30px;
                border-radius:5px;
            }

            QScrollBar::handle:vertical:hover {
                background:#66717d;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height:0px;
            }
            """
        )

        main_layout = QVBoxLayout(
            self
        )

        main_layout.setContentsMargins(
            12,
            8,
            12,
            10,
        )

        main_layout.setSpacing(
            8
        )

        title = QLabel(
            "EVENT & PHOTO HISTORY"
        )

        title.setAlignment(
            Qt.AlignCenter
        )

        title.setFixedHeight(
            46
        )

        title.setStyleSheet(
            """
            font-size:20px;
            font-weight:bold;
            padding:8px;
            background:#2b2b2b;
            border-radius:10px;
            """
        )

        self.live_status_label = QLabel(
            "Monitoring road conditions..."
        )

        self.live_status_label.setAlignment(
            Qt.AlignCenter
        )

        self.live_status_label.setFixedHeight(
            38
        )

        self.live_status_label.setStyleSheet(
            """
            background:#111820;
            color:#aeb7c2;
            border:1px solid #343d47;
            border-radius:7px;
            padding:6px;
            font-size:12px;
            """
        )

        self.scroll_area = QScrollArea()

        self.scroll_area.setWidgetResizable(
            True
        )

        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        self.cards_container = QWidget()

        self.cards_container.setStyleSheet(
            """
            background:#0b0f14;
            """
        )

        self.cards_layout = QVBoxLayout(
            self.cards_container
        )

        self.cards_layout.setContentsMargins(
            8,
            8,
            8,
            8,
        )

        self.cards_layout.setSpacing(
            9
        )

        self.empty_label = QLabel(
            (
                "No potholes stored in the database.\n"
                "Detected potholes and captured photos "
                "will appear here."
            )
        )

        self.empty_label.setAlignment(
            Qt.AlignCenter
        )

        self.empty_label.setWordWrap(
            True
        )

        self.empty_label.setMinimumHeight(
            100
        )

        self.empty_label.setStyleSheet(
            """
            color:#7f8a96;
            background:#111820;
            border:1px dashed #39424c;
            border-radius:8px;
            padding:18px;
            font-size:12px;
            """
        )

        self.cards_layout.addWidget(
            self.empty_label
        )

        self.cards_layout.addStretch()

        self.scroll_area.setWidget(
            self.cards_container
        )

        main_layout.addWidget(
            title
        )

        main_layout.addWidget(
            self.live_status_label
        )

        main_layout.addWidget(
            self.scroll_area,
            1,
        )

        self.load_database_history()

        self.timer = QTimer(self)

        self.timer.timeout.connect(
            self.update_history
        )

        self.timer.start(
            500
        )

    def load_database_history(self):
        """
        Load all existing SQLite pothole records.
        """

        self.sync_database_history()

    def sync_database_history(self):
        """
        Add new cards and refresh existing cards.

        get_all_potholes() returns newest records first.
        The newest card is therefore placed at the top.
        """

        try:
            records = get_all_potholes()

        except Exception as error:
            self.live_status_label.setText(
                f"Database error: {error}"
            )

            self.live_status_label.setStyleSheet(
                """
                background:#35171a;
                color:#ff7b7b;
                border:1px solid #82363d;
                border-radius:7px;
                padding:6px;
                font-size:12px;
                """
            )

            print(
                f"History database sync error: {error}"
            )

            return

        if not records:
            self.empty_label.show()
            return

        self.empty_label.hide()

        active_database_ids = set()

        for record in records:
            database_id = record.get(
                "id"
            )

            if database_id is None:
                continue

            active_database_ids.add(
                database_id
            )

            if (
                database_id
                in self.history_cards
            ):
                self.history_cards[
                    database_id
                ].update_record(
                    record
                )

                continue

            card = PotholeHistoryCard(
                record=record,
                parent=self.cards_container,
            )

            self.history_cards[
                database_id
            ] = card

            self.cards_layout.insertWidget(
                0,
                card,
            )

        removed_ids = (
            set(self.history_cards.keys())
            - active_database_ids
        )

        for database_id in removed_ids:
            card = self.history_cards.pop(
                database_id
            )

            self.cards_layout.removeWidget(
                card
            )

            card.deleteLater()

        if not self.history_cards:
            self.empty_label.show()

    def update_live_status(self):
        """
        Update the compact real-time status shown above history.
        """

        current_level = getattr(
            data,
            "warning_level",
            "SAFE",
        )

        current_id = getattr(
            data,
            "current_pothole_id",
            None,
        )

        if (
            current_level
            == self.last_warning_level
            and current_id
            == self.last_pothole_id
        ):
            return

        self.last_warning_level = (
            current_level
        )

        self.last_pothole_id = (
            current_id
        )

        now = (
            QDateTime.currentDateTime()
            .toString("hh:mm:ss")
        )

        if current_level == "SAFE":
            self.live_status_label.setText(
                (
                    f"{now}  ● ROAD CLEAR  |  "
                    f"Speed: "
                    f"{getattr(data, 'speed', 0)} km/h  |  "
                    f"GPS: "
                    f"{getattr(data, 'gps', '(0, 0)')}"
                )
            )

            self.live_status_label.setStyleSheet(
                """
                background:#11291c;
                color:#4ade80;
                border:1px solid #24633b;
                border-radius:7px;
                padding:6px;
                font-size:12px;
                font-weight:bold;
                """
            )

        elif current_level == "CAUTION":
            severity = getattr(
                data,
                "current_pothole_severity",
                "UNKNOWN",
            )

            distance = getattr(
                data,
                "distance",
                0,
            )

            self.live_status_label.setText(
                (
                    f"{now}  ● POTHOLE AHEAD  |  "
                    f"ID: {current_id}  |  "
                    f"Distance: {distance} cm  |  "
                    f"Severity: {severity}"
                )
            )

            self.live_status_label.setStyleSheet(
                """
                background:#302711;
                color:#ffd166;
                border:1px solid #75601f;
                border-radius:7px;
                padding:6px;
                font-size:12px;
                font-weight:bold;
                """
            )

        elif current_level == "DANGER":
            self.live_status_label.setText(
                (
                    f"{now}  ● POTHOLE DETECTED  |  "
                    f"ID: {current_id}  |  "
                    "Saving event and camera snapshot..."
                )
            )

            self.live_status_label.setStyleSheet(
                """
                background:#35171a;
                color:#ff6262;
                border:1px solid #82363d;
                border-radius:7px;
                padding:6px;
                font-size:12px;
                font-weight:bold;
                """
            )

    def update_history(self):
        """
        Periodically synchronize history and live status.
        """

        self.sync_database_history()
        self.update_live_status()

    def refresh_history(self):
        """
        Public method for manually refreshing the panel.
        """

        self.sync_database_history()

    def reset_history(self):
        """
        Clear the visual card list after database reset.
        """

        for card in self.history_cards.values():
            self.cards_layout.removeWidget(
                card
            )

            card.deleteLater()

        self.history_cards.clear()

        self.empty_label.show()

        self.live_status_label.setText(
            "Monitoring road conditions..."
        )

        self.last_warning_level = ""
        self.last_pothole_id = None

    def stop(self):
        """
        Stop the history synchronization timer.
        """

        self.timer.stop()