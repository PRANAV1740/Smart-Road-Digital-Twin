from pathlib import Path
from PySide6.QtCore import Qt, QDateTime, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QPixmap
from PySide6.QtWidgets import (
    QDialog, QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QSizePolicy, QVBoxLayout, QWidget
)

from database.database import get_all_potholes
from utils import data
from utils.theme import ThemeManager

class ClickableImageLabel(QLabel):
    clicked = Signal()
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton: self.clicked.emit()
        super().mousePressEvent(event)

class ImageViewerDialog(QDialog):
    def __init__(self, image_path, pothole_id, theme_manager, parent=None):
        super().__init__(parent)
        self.image_path = Path(image_path)
        self.theme = theme_manager.get_current_theme()
        self.setWindowTitle(f"Pothole {pothole_id} - Captured Image")
        self.resize(900, 650)
        self.setMinimumSize(600, 450)
        
        self.setStyleSheet(f"""
            QDialog {{ background: {self.theme['background']}; }}
            QLabel {{ color: {self.theme['text_primary']}; font-family: 'Segoe UI'; }}
            QPushButton {{ background: {self.theme['accent']}; color: white; border: none; border-radius: 7px; padding: 8px 24px; font-size: 14px; font-weight: bold; font-family: 'Segoe UI'; }}
            QPushButton:hover {{ background: {self.theme['accent_hover']}; }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        title = QLabel(f"POTHOLE {pothole_id} CAPTURE")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; background: {self.theme['surface']}; border-radius: 8px; padding: 10px;")

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(500, 330)
        self.image_label.setStyleSheet(f"background: {self.theme['surface_elevated']}; border: 1px solid {self.theme['border']}; border-radius: 10px;")

        path_label = QLabel(str(self.image_path))
        path_label.setAlignment(Qt.AlignCenter)
        path_label.setWordWrap(True)
        path_label.setStyleSheet(f"color: {self.theme['text_secondary']}; background: {self.theme['surface']}; border-radius: 7px; padding: 7px; font-size: 12px;")

        close_button = QPushButton("Close")
        close_button.setFixedWidth(130)
        close_button.setCursor(Qt.PointingHandCursor)
        close_button.clicked.connect(self.accept)

        bl = QHBoxLayout()
        bl.addStretch()
        bl.addWidget(close_button)
        bl.addStretch()

        layout.addWidget(title)
        layout.addWidget(self.image_label, 1)
        layout.addWidget(path_label)
        layout.addLayout(bl)
        self.load_image()

    def load_image(self):
        if not self.image_path.exists():
            self.image_label.setText("Captured image file was not found.")
            return
        pixmap = QPixmap(str(self.image_path))
        if pixmap.isNull():
            self.image_label.setText("The image could not be loaded.")
            return
            
        self.image_label.setPixmap(pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.original_pixmap = pixmap

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "original_pixmap"):
            self.image_label.setPixmap(self.original_pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

class PotholeHistoryCard(QFrame):
    def __init__(self, record, theme_manager, parent=None):
        super().__init__(parent)
        self.record = {}
        self.image_path = ""
        self.theme_manager = theme_manager
        self.theme = self.theme_manager.get_current_theme()
        self.setObjectName("historyCard")
        self.setMinimumHeight(155)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(12)

        self.image_label = ClickableImageLabel()
        self.image_label.setFixedSize(145, 115)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setCursor(Qt.PointingHandCursor)
        self.image_label.clicked.connect(self.open_image)

        il = QVBoxLayout()
        il.setSpacing(6)

        self.heading_label = QLabel()
        self.details_label = QLabel()
        self.details_label.setWordWrap(True)
        self.location_label = QLabel()
        self.location_label.setWordWrap(True)
        self.photo_label = QLabel()
        
        il.addWidget(self.heading_label)
        il.addWidget(self.details_label)
        il.addWidget(self.location_label)
        il.addWidget(self.photo_label)
        il.addStretch()

        main_layout.addWidget(self.image_label)
        main_layout.addLayout(il, 1)

        self.update_styles()
        self.update_record(record)
        
    def update_styles(self):
        self.theme = self.theme_manager.get_current_theme()
        is_dark = self.theme_manager.is_dark
        border = f"1px solid {self.theme['border']}" if is_dark else "none"
        shadow = "" if is_dark else "box-shadow: 0 1px 3px rgba(0,0,0,0.08);"
        hover_shadow = "" if is_dark else "box-shadow: 0 4px 6px rgba(0,0,0,0.1);"

        self.setStyleSheet(f"""
            QFrame#historyCard {{
                background: {self.theme['surface_elevated']};
                border: {border};
                border-radius: 10px;
                {shadow}
            }}
            QFrame#historyCard:hover {{
                border: 1px solid {self.theme['accent']};
                {hover_shadow}
            }}
            QLabel {{ background: transparent; border: none; font-family: 'Segoe UI'; }}
        """)
        
        self.image_label.setStyleSheet(f"""
            background: {self.theme['surface']};
            color: {self.theme['text_muted']};
            border: 1px solid {self.theme['border']};
            border-radius: 8px;
            font-size: 12px;
            font-weight: bold;
        """)
        
        self.details_label.setStyleSheet(f"color: {self.theme['text_secondary']}; font-size: 12px;")
        self.location_label.setStyleSheet(f"color: {self.theme['text_muted']}; font-size: 11px;")
        
        self.update_record(self.record)

    def update_record(self, record):
        if not record: return
        self.record = dict(record)
        
        pid = self.record.get("pothole_id", "-")
        severity = str(self.record.get("severity", "UNKNOWN")).upper()
        depth = self.record.get("depth", 0)
        dt = self.record.get("detected_at", "-")
        x, y = self.record.get("x", 0), self.record.get("y", 0)
        lat, lon = self.record.get("latitude", 0.0), self.record.get("longitude", 0.0)
        photo_cap = bool(self.record.get("photo_captured", 0))
        self.image_path = str(self.record.get("image_path", "") or "")

        self.heading_label.setText(f"Pothole #{pid}  •  {severity}")
        
        if severity == "HIGH": c = self.theme['danger']
        elif severity == "MEDIUM": c = self.theme['warning']
        elif severity == "LOW": c = self.theme['success']
        else: c = self.theme['text_primary']
        
        self.heading_label.setStyleSheet(f"color: {c}; font-size: 16px; font-weight: bold;")

        self.details_label.setText(f"Depth: {depth} cm\nDetected: {dt}")
        self.location_label.setText(f"Map position: ({x}, {y})\nGPS: ({lat}, {lon})")

        if photo_cap and self.image_path:
            self.photo_label.setText("● PHOTO CAPTURED — click image to open")
            self.photo_label.setStyleSheet(f"color: {self.theme['success']}; font-size: 11px; font-weight: bold;")
            self.load_thumbnail()
        else:
            self.photo_label.setText("○ PHOTO NOT AVAILABLE")
            self.photo_label.setStyleSheet(f"color: {self.theme['warning']}; font-size: 11px; font-weight: bold;")
            self.show_placeholder()

    def load_thumbnail(self):
        path = Path(self.image_path)
        if not path.exists():
            self.image_label.setPixmap(QPixmap())
            self.image_label.setText("IMAGE FILE\nNOT FOUND")
            self.image_label.setCursor(Qt.ArrowCursor)
            return

        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            self.image_label.setPixmap(QPixmap())
            self.image_label.setText("INVALID\nIMAGE")
            self.image_label.setCursor(Qt.ArrowCursor)
            return

        self.image_label.setText("")
        self.image_label.setPixmap(pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.image_label.setCursor(Qt.PointingHandCursor)

    def show_placeholder(self):
        self.image_label.setPixmap(QPixmap())
        self.image_label.setText("NO PHOTO\nCAPTURED")
        self.image_label.setCursor(Qt.ArrowCursor)

    def open_image(self):
        if not self.image_path: return
        path = Path(self.image_path)
        if not path.exists(): return
        pid = self.record.get("pothole_id", "-")
        viewer = ImageViewerDialog(path, pid, self.theme_manager, self)
        viewer.exec()


class HistoryPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.last_warning_level = ""
        self.last_pothole_id = None
        self.history_cards = {}
        self.setMinimumHeight(340)

        self.theme_manager = ThemeManager()
        self.theme = self.theme_manager.get_current_theme()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        self.title = QLabel("EVENT & PHOTO HISTORY")
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setFixedHeight(46)

        self.live_status_label = QLabel("Monitoring road conditions...")
        self.live_status_label.setAlignment(Qt.AlignCenter)
        self.live_status_label.setFixedHeight(38)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(6, 6, 6, 6)
        self.cards_layout.setSpacing(8)

        self.empty_label = QLabel("No potholes stored in the database.\nDetected potholes and captured photos will appear here.")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setWordWrap(True)
        self.empty_label.setMinimumHeight(100)
        self.cards_layout.addWidget(self.empty_label)
        self.cards_layout.addStretch()

        self.scroll_area.setWidget(self.cards_container)

        main_layout.addWidget(self.title)
        main_layout.addWidget(self.live_status_label)
        main_layout.addWidget(self.scroll_area, 1)

        self.theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme(self.theme_manager.get_current_theme(), self.theme_manager.is_dark)

        self.load_database_history()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_history)
        self.timer.start(500)

    def apply_theme(self, theme, is_dark):
        self.theme = theme
        border = f"1px solid {theme['border']}" if is_dark else "none"
        shadow = "" if is_dark else "box-shadow: 0 1px 3px rgba(0,0,0,0.08);"
        
        self.setStyleSheet(f"""
            QWidget {{ background: {theme['surface']}; border-radius: 12px; }}
            QLabel {{ color: {theme['text_primary']}; font-family: 'Segoe UI'; }}
            QScrollArea {{ background: transparent; border: none; }}
            QScrollBar:vertical {{ background: {theme['background']}; width: 10px; border-radius: 5px; }}
            QScrollBar::handle:vertical {{ background: {theme['border']}; border-radius: 5px; min-height: 20px; }}
            QScrollBar::handle:vertical:hover {{ background: {theme['accent']}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
        """)
        
        self.cards_container.setStyleSheet("background: transparent;")
        
        self.title.setStyleSheet(f"""
            font-size: 20px;
            font-weight: bold;
            padding: 8px;
            background: transparent;
            border: none;
            box-shadow: none;
        """)

        self.empty_label.setStyleSheet(f"""
            color: {theme['text_secondary']};
            background: {theme['surface_elevated']};
            border: 1px dashed {theme['border']};
            border-radius: 8px;
            padding: 18px;
            font-size: 13px;
        """)
        
        for card in self.history_cards.values():
            card.update_styles()
            
        self.update_live_status(force_update=True)

    def load_database_history(self):
        self.sync_database_history()

    def sync_database_history(self):
        try:
            records = get_all_potholes()
        except Exception as error:
            self.live_status_label.setText(f"Database error: {error}")
            self.live_status_label.setStyleSheet(f"background: {self.theme['danger']}; color: white; border-radius: 7px; padding: 6px; font-size: 12px;")
            return

        if not records:
            self.empty_label.show()
            return

        self.empty_label.hide()
        active_ids = set()

        for record in records:
            pid = record.get("id")
            if pid is None: continue
            active_ids.add(pid)
            
            if pid in self.history_cards:
                self.history_cards[pid].update_record(record)
                continue

            card = PotholeHistoryCard(record, self.theme_manager, self.cards_container)
            self.history_cards[pid] = card
            self.cards_layout.insertWidget(0, card)

        for rm_id in list(set(self.history_cards.keys()) - active_ids):
            c = self.history_cards.pop(rm_id)
            self.cards_layout.removeWidget(c)
            c.deleteLater()

        if not self.history_cards: self.empty_label.show()

    def update_live_status(self, force_update=False):
        current_level = getattr(data, "warning_level", "SAFE")
        current_id = getattr(data, "current_pothole_id", None)

        if not force_update and current_level == self.last_warning_level and current_id == self.last_pothole_id:
            return

        self.last_warning_level = current_level
        self.last_pothole_id = current_id
        now = QDateTime.currentDateTime().toString("hh:mm:ss")

        if current_level == "SAFE":
            msg = f"{now}  ● ROAD CLEAR  |  Speed: {getattr(data, 'speed', 0)} km/h  |  GPS: {getattr(data, 'gps', '(0, 0)')}"
            b = self.theme['surface_elevated']
            c = self.theme['success']
        elif current_level == "CAUTION":
            sev = getattr(data, "current_pothole_severity", "UNKNOWN")
            dist = getattr(data, "distance", 0)
            msg = f"{now}  ● POTHOLE AHEAD  |  ID: {current_id}  |  Distance: {dist} cm  |  Severity: {sev}"
            b = self.theme['warning']
            c = "#ffffff" if self.theme_manager.is_dark else "#000000"
        elif current_level == "DANGER":
            msg = f"{now}  ● POTHOLE DETECTED  |  ID: {current_id}  |  Saving event and camera snapshot..."
            b = self.theme['danger']
            c = "#ffffff"
        else:
            msg = f"{now}  ● MONITORING"
            b, c = self.theme['surface_elevated'], self.theme['text_primary']

        self.live_status_label.setText(msg)
        self.live_status_label.setStyleSheet(f"background: {b}; color: {c}; border-radius: 7px; padding: 6px; font-size: 13px; font-weight: bold; border: 1px solid {self.theme['border']};")

    def update_history(self):
        self.sync_database_history()
        self.update_live_status()

    def refresh_history(self):
        self.sync_database_history()

    def reset_history(self):
        for card in self.history_cards.values():
            self.cards_layout.removeWidget(card)
            card.deleteLater()
        self.history_cards.clear()
        self.empty_label.show()
        self.live_status_label.setText("Monitoring road conditions...")
        self.last_warning_level = ""
        self.last_pothole_id = None

    def stop(self):
        self.timer.stop()