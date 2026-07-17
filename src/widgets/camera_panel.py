# ==================================================
# SMART ROAD DIGITAL TWIN - CAMERA PANEL
# ==================================================

from pathlib import Path

from PySide6.QtCore import (
    QPoint,
    QRect,
    Qt,
    QDateTime,
    QTimer,
)
from PySide6.QtGui import (
    QColor,
    QFont,
    QPainter,
    QPen,
    QPixmap,
    QPolygon,
)
from PySide6.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QWidget,
)

from database.database import update_pothole_image
from utils import data


class CameraView(QWidget):
    """
    Simulated ESP32-CAM road view.

    This widget currently draws an animated road-monitoring
    screen. Later, real ESP32-CAM frames can be displayed
    inside this same widget.
    """

    def __init__(self):
        super().__init__()

        self.scan_y = 0
        self.frame_count = 0

        self.setMinimumHeight(280)

        self.timer = QTimer(self)
        self.timer.timeout.connect(
            self.update_frame
        )
        self.timer.start(80)

    def update_frame(self):
        """
        Advance the simulated camera animation.
        """

        self.frame_count += 1
        self.scan_y += 5

        if self.scan_y > self.height():
            self.scan_y = 0

        self.update()

    def paintEvent(self, event):
        """
        Draw the simulated camera frame.
        """

        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.Antialiasing
        )

        width = self.width()
        height = self.height()

        painter.fillRect(
            self.rect(),
            QColor("#090d12"),
        )

        self.draw_road(
            painter,
            width,
            height,
        )

        self.draw_recording_header(
            painter,
            width,
        )

        if data.road_status == "POTHOLE":
            self.draw_detection_box(
                painter,
                width,
                height,
            )
        else:
            self.draw_standby_text(
                painter,
                width,
                height,
            )

        self.draw_scan_line(
            painter,
            width,
        )

        self.draw_bottom_status(
            painter,
            height,
        )

    def draw_road(
        self,
        painter,
        width,
        height,
    ):
        """
        Draw a perspective road surface.
        """

        road_left = int(
            width * 0.18
        )

        road_right = int(
            width * 0.82
        )

        road_polygon = QPolygon(
            [
                QPoint(
                    road_left,
                    height,
                ),
                QPoint(
                    road_right,
                    height,
                ),
                QPoint(
                    int(width * 0.60),
                    42,
                ),
                QPoint(
                    int(width * 0.40),
                    42,
                ),
            ]
        )

        painter.setPen(
            Qt.NoPen
        )

        painter.setBrush(
            QColor("#242a30")
        )

        painter.drawPolygon(
            road_polygon
        )

        painter.setPen(
            QPen(
                QColor("#f7d477"),
                3,
                Qt.DashLine,
            )
        )

        center_x = width // 2

        painter.drawLine(
            center_x,
            height,
            center_x,
            58,
        )

        painter.setPen(
            QPen(
                QColor("#8a8f95"),
                3,
            )
        )

        painter.drawLine(
            road_left,
            height,
            int(width * 0.40),
            42,
        )

        painter.drawLine(
            road_right,
            height,
            int(width * 0.60),
            42,
        )

    def draw_recording_header(
        self,
        painter,
        width,
    ):
        """
        Draw recording and time information.
        """

        now = (
            QDateTime.currentDateTime()
            .toString("hh:mm:ss")
        )

        painter.setFont(
            QFont(
                "Arial",
                11,
                QFont.Bold,
            )
        )

        painter.setPen(
            QColor("#ff3333")
        )

        painter.drawText(
            18,
            28,
            "● REC",
        )

        painter.setPen(
            QColor("#dddddd")
        )

        painter.drawText(
            width - 190,
            28,
            f"FPS: 24  |  {now}",
        )

    def draw_standby_text(
        self,
        painter,
        width,
        height,
    ):
        """
        Draw standby text when the road is clear.
        """

        painter.setFont(
            QFont(
                "Arial",
                14,
                QFont.Bold,
            )
        )

        painter.setPen(
            QColor("#cccccc")
        )

        painter.drawText(
            QRect(
                0,
                55,
                width,
                height - 120,
            ),
            Qt.AlignCenter,
            "AI DETECTION: STANDBY",
        )

    def draw_detection_box(
        self,
        painter,
        width,
        height,
    ):
        """
        Draw the pothole detection overlay.
        """

        box_width = 150
        box_height = 80

        box_x = (
            width - box_width
        ) // 2

        box_y = int(
            height * 0.52
        )

        painter.setPen(
            QPen(
                QColor("#ff3333"),
                3,
            )
        )

        painter.setBrush(
            QColor(
                255,
                51,
                51,
                35,
            )
        )

        painter.drawRect(
            box_x,
            box_y,
            box_width,
            box_height,
        )

        painter.setFont(
            QFont(
                "Arial",
                11,
                QFont.Bold,
            )
        )

        painter.setPen(
            QColor("#ff3333")
        )

        painter.drawText(
            box_x,
            box_y - 10,
            "POTHOLE",
        )

        confidence = (
            92
            + self.frame_count % 7
        )

        painter.setPen(
            QColor("#ffffff")
        )

        painter.drawText(
            box_x,
            box_y + box_height + 22,
            f"Confidence: {confidence}%",
        )

    def draw_scan_line(
        self,
        painter,
        width,
    ):
        """
        Draw the animated scanning line.
        """

        painter.setPen(
            QPen(
                QColor(
                    0,
                    229,
                    255,
                    120,
                ),
                2,
            )
        )

        painter.drawLine(
            0,
            self.scan_y,
            width,
            self.scan_y,
        )

    def draw_bottom_status(
        self,
        painter,
        height,
    ):
        """
        Draw monitoring status text.
        """

        painter.setFont(
            QFont(
                "Arial",
                10,
            )
        )

        painter.setPen(
            QColor("#00d26a")
        )

        painter.drawText(
            18,
            height - 18,
            "Road surface monitoring active",
        )


class CameraPanel(QWidget):
    """
    Camera panel with simulated ESP32-CAM output.

    A snapshot is created for every new pothole. The image
    is saved locally and linked to the matching database
    record.

    If the database record is not available immediately,
    the same image is retained and database linking is
    retried without creating duplicate images.
    """

    def __init__(self):
        super().__init__()

        self.setMinimumHeight(390)

        self.last_captured_pothole_id = None

        self.pending_pothole_id = None
        self.pending_image_path = None
        self.pending_retry_count = 0

        self.maximum_database_retries = 20

        self.capture_folder = (
            Path(__file__).resolve().parent.parent
            / "assets"
            / "captures"
        )

        self.capture_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.setStyleSheet(
            """
            QWidget {
                background:#2b2b2b;
                border-radius:12px;
            }

            QLabel {
                color:white;
            }
            """
        )

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            10,
            8,
            10,
            10,
        )

        layout.setSpacing(8)

        title = QLabel(
            "CAMERA PANEL"
        )

        title.setAlignment(
            Qt.AlignCenter
        )

        title.setFixedHeight(48)

        title.setStyleSheet(
            """
            font-size:22px;
            font-weight:bold;
            padding:8px;
            background:#2b2b2b;
            border-radius:10px;
            """
        )

        self.camera_view = CameraView()

        self.status_label = QLabel(
            "Camera simulation ready"
        )

        self.status_label.setAlignment(
            Qt.AlignCenter
        )

        self.status_label.setFixedHeight(38)

        self.status_label.setStyleSheet(
            """
            background:#111820;
            color:#cccccc;
            border:1px solid #444444;
            border-radius:8px;
            padding:6px;
            font-size:13px;
            """
        )

        layout.addWidget(
            title
        )

        layout.addWidget(
            self.camera_view,
            1,
        )

        layout.addWidget(
            self.status_label
        )

        self.capture_timer = QTimer(self)

        self.capture_timer.timeout.connect(
            self.check_snapshot
        )

        self.capture_timer.start(250)

    def check_snapshot(self):
        """
        Detect newly created potholes and manage snapshots.
        """

        if self.pending_image_path is not None:
            self.retry_pending_database_update()
            return

        pothole_id = getattr(
            data,
            "current_pothole_id",
            None,
        )

        if (
            data.road_status != "POTHOLE"
            or pothole_id is None
        ):
            self.status_label.setText(
                "AI detection module: standby"
            )
            return

        self.status_label.setText(
            f"Pothole {pothole_id} detected"
        )

        if (
            pothole_id
            == self.last_captured_pothole_id
        ):
            return

        image_path = self.create_snapshot(
            pothole_id
        )

        if image_path is None:
            return

        self.pending_pothole_id = (
            pothole_id
        )

        self.pending_image_path = (
            image_path
        )

        self.pending_retry_count = 0

        self.retry_pending_database_update()

    def create_snapshot(
        self,
        pothole_id,
    ):
        """
        Create one PNG snapshot.

        Returns:
            Saved image Path when successful.
            None when saving fails.
        """

        timestamp = (
            QDateTime.currentDateTime()
            .toString(
                "yyyyMMdd_HHmmss_zzz"
            )
        )

        image_path = (
            self.capture_folder
            / (
                f"pothole_{pothole_id}_"
                f"{timestamp}.png"
            )
        )

        pixmap = QPixmap(
            self.camera_view.size()
        )

        pixmap.fill(
            QColor("#090d12")
        )

        self.camera_view.render(
            pixmap
        )

        image_saved = pixmap.save(
            str(image_path),
            "PNG",
        )

        if not image_saved:
            self.status_label.setText(
                "Snapshot could not be saved"
            )

            print(
                "Camera snapshot save failed:",
                image_path,
            )

            return None

        self.status_label.setText(
            "Snapshot saved, linking database..."
        )

        print(
            f"Pothole {pothole_id} snapshot created:",
            image_path,
        )

        return image_path

    def retry_pending_database_update(self):
        """
        Link a previously saved image to its database record.

        The same image is reused during retries, so duplicate
        image files are never created.
        """

        if (
            self.pending_pothole_id is None
            or self.pending_image_path is None
        ):
            return

        if not self.pending_image_path.exists():
            print(
                "Pending camera image no longer exists:",
                self.pending_image_path,
            )

            self.clear_pending_capture()

            self.status_label.setText(
                "Pending snapshot file was not found"
            )

            return

        database_updated = (
            update_pothole_image(
                pothole_id=(
                    self.pending_pothole_id
                ),
                image_path=str(
                    self.pending_image_path
                ),
            )
        )

        if database_updated:
            self.complete_capture()
            return

        self.pending_retry_count += 1

        self.status_label.setText(
            (
                "Snapshot ready, waiting for "
                "database record..."
            )
        )

        if (
            self.pending_retry_count
            >= self.maximum_database_retries
        ):
            print(
                "Camera database update failed after retries:",
                self.pending_pothole_id,
                self.pending_image_path,
            )

            self.status_label.setText(
                (
                    "Snapshot saved, but database "
                    "record was not found"
                )
            )

            self.clear_pending_capture()

    def complete_capture(self):
        """
        Complete the image and database workflow.
        """

        pothole_id = (
            self.pending_pothole_id
        )

        image_path = (
            self.pending_image_path
        )

        self.last_captured_pothole_id = (
            pothole_id
        )

        self.mark_map_pothole_captured(
            pothole_id,
            image_path,
        )

        data.photos = (
            getattr(
                data,
                "photos",
                0,
            )
            + 1
        )

        data.latest_image_path = str(
            image_path
        )

        data.latest_captured_pothole_id = (
            pothole_id
        )

        self.status_label.setText(
            f"Snapshot saved: {image_path.name}"
        )

        print(
            f"Pothole {pothole_id} snapshot linked:",
            image_path,
        )

        self.clear_pending_capture()

    def mark_map_pothole_captured(
        self,
        pothole_id,
        image_path,
    ):
        """
        Update the corresponding in-memory pothole.
        """

        potholes = getattr(
            data,
            "potholes",
            [],
        )

        for pothole in potholes:
            if pothole.get("id") == pothole_id:
                pothole[
                    "photo_captured"
                ] = True

                pothole[
                    "image_path"
                ] = str(
                    image_path
                )

                break

    def clear_pending_capture(self):
        """
        Clear the current pending database-link operation.
        """

        self.pending_pothole_id = None
        self.pending_image_path = None
        self.pending_retry_count = 0

    def reset_capture_tracking(self):
        """
        Reset the panel after database clearing or when a
        new monitoring session starts.
        """

        self.last_captured_pothole_id = None

        self.clear_pending_capture()

        self.status_label.setText(
            "Camera simulation ready"
        )

    def stop(self):
        """
        Stop Camera Panel timers safely.
        """

        self.capture_timer.stop()
        self.camera_view.timer.stop()