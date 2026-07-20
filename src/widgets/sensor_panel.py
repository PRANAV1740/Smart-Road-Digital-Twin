import collections
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, Property, QPointF
from PySide6.QtGui import QFont, QColor, QPainter, QPen, QPolygonF

from utils import data
from utils.theme import ThemeManager


class SensorCard(QFrame):
    def __init__(self, title, initial_val="0"):
        super().__init__()
        self.setObjectName("miniCard")
        self.title_text = title
        
        self.history = collections.deque(maxlen=20)
        self.current_val_str = initial_val
        self.current_num = 0.0
        
        self.theme = None
        self.border_css = "none"
        self._bg_color = QColor("#000000")
        
        self.setMinimumHeight(44)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        
        # Connection dot
        self.dot = QLabel()
        self.dot.setFixedSize(6, 6)
        self.dot.setStyleSheet("background-color: #10b981; border-radius: 3px;")
        
        self.dot_shadow = QGraphicsDropShadowEffect(self.dot)
        self.dot_shadow.setBlurRadius(8)
        self.dot_shadow.setOffset(0, 0)
        self.dot_shadow.setColor(QColor("#10b981"))
        self.dot.setGraphicsEffect(self.dot_shadow)
        
        self.title_lbl = QLabel(title)
        
        self.val_lbl = QLabel(initial_val)
        self.val_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        self.val_shadow = QGraphicsDropShadowEffect(self.val_lbl)
        self.val_shadow.setBlurRadius(10)
        self.val_shadow.setOffset(0, 0)
        self.val_lbl.setGraphicsEffect(self.val_shadow)
        
        layout.addWidget(self.dot)
        layout.addWidget(self.title_lbl)
        
        # Spacer where the sparkline will be drawn (handled in paintEvent)
        self.spark_area = QWidget()
        self.spark_area.setMinimumWidth(60)
        layout.addWidget(self.spark_area, 1)
        
        layout.addWidget(self.val_lbl)
        
        self.anim = QPropertyAnimation(self, b"bg_color")
        self.anim.setDuration(150)
        self.anim.setEasingCurve(QEasingCurve.OutQuad)

    def get_bg_color(self):
        return self._bg_color

    def set_bg_color(self, color):
        self._bg_color = color
        is_dark = getattr(self, 'theme', {}).get('type', 'dark') == 'dark'
        bg_str = color.name() if is_dark else f"qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #ffffff, stop:1 #e0e7ff)"
        self.setStyleSheet(f"QFrame#miniCard {{ background: {bg_str}; border-radius: 12px; border: {getattr(self, 'border_css', 'none')}; }}")

    bg_color = Property(QColor, get_bg_color, set_bg_color)
    
    def update_theme(self, theme, is_dark):
        self.theme = theme
        self.border_css = f"1px solid {theme['border']}" if is_dark else "none"
        self._bg_color = QColor(theme['surface'])
        self.set_bg_color(self._bg_color)
        
        self.title_lbl.setStyleSheet(f"color: {theme['text_secondary']}; font-size: 11px; font-weight: bold; background: transparent; border: none; font-family: 'Segoe UI';")
        self.val_lbl.setStyleSheet(f"color: {theme['text_primary']}; font-size: 16px; font-weight: bold; background: transparent; border: none; font-family: 'Segoe UI';")

    def update_val(self, num_val, str_val, val_color_hex, glow_color_hex, trigger_flash=True):
        if str_val != self.current_val_str:
            self.history.append(num_val)
            self.current_num = num_val
            self.current_val_str = str_val
            self.val_lbl.setText(str_val)
            self.val_lbl.setStyleSheet(f"color: {val_color_hex}; font-size: 16px; font-weight: bold; background: transparent; border: none; font-family: 'Segoe UI';")
            self.val_shadow.setColor(QColor(glow_color_hex))
            
            if trigger_flash and self.theme:
                # Flash slightly brighter/accent color
                self.anim.stop()
                self.anim.setStartValue(QColor(self.theme['surface_elevated']))
                self.anim.setEndValue(QColor(self.theme['surface']))
                self.anim.start()
            
            self.update() # trigger sparkline repaint

    def paintEvent(self, event):
        super().paintEvent(event)
        if len(self.history) < 2 or not self.theme:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Position sparkline in the empty spark_area widget
        area_rect = self.spark_area.geometry()
        
        points = list(self.history)
        min_v = min(points)
        max_v = max(points)
        range_v = max_v - min_v if max_v != min_v else 1
        
        poly = QPolygonF()
        x_step = area_rect.width() / 19.0
        
        for i, val in enumerate(points):
            nx = area_rect.left() + (i * x_step)
            # map to height
            ny = area_rect.bottom() - 4 - ((val - min_v) / range_v) * (area_rect.height() - 8)
            poly.append(QPointF(nx, ny))
            
        painter.setPen(QPen(QColor(self.theme['accent']), 1.5))
        painter.drawPolyline(poly)


class SensorPanel(QWidget):
    def __init__(self):
        super().__init__()

        self.setMinimumHeight(420)
        self.theme_manager = ThemeManager()

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(10)
        
        self.val_labels = {}

        title = QLabel("SENSOR FEED")
        title.setFixedHeight(30)
        title.setStyleSheet("font-size: 14px; font-weight: bold; background: transparent; padding-left: 4px;")
        self.main_layout.addWidget(title)
        self.title_label = title

        # Scroll area for mini cards
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("border: none; background: transparent;")
        
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(6)

        # Mini cards
        self.ml_card = SensorCard("ML MODEL STATUS", "WAITING")
        self.scroll_layout.addWidget(self.ml_card)
        
        self.ml_info_label = QLabel("Idle")
        self.ml_info_label.setAlignment(Qt.AlignRight)
        self.scroll_layout.addWidget(self.ml_info_label)

        self.status_card = SensorCard("ROAD STATUS", "SAFE")
        self.scroll_layout.addWidget(self.status_card)

        self.dist_card = SensorCard("ULTRASONIC DISTANCE", "100 cm")
        self.scroll_layout.addWidget(self.dist_card)
        
        self.speed_card = SensorCard("VEHICLE SPEED", "0 km/h")
        self.scroll_layout.addWidget(self.speed_card)
        
        self.depth_card = SensorCard("POTHOLE DEPTH", "0 cm")
        self.scroll_layout.addWidget(self.depth_card)
        
        self.jerk_card = SensorCard("JERK SENSOR (g)", "0.0")
        self.scroll_layout.addWidget(self.jerk_card)
        
        self.gps_card = SensorCard("GPS COORDINATES", "(0, 0)")
        self.scroll_layout.addWidget(self.gps_card)

        # Mapping for update iterations
        self.cards = {
            "ml": self.ml_card,
            "status": self.status_card,
            "dist": self.dist_card,
            "speed": self.speed_card,
            "depth": self.depth_card,
            "jerk": self.jerk_card,
            "gps": self.gps_card
        }

        self.scroll_layout.addStretch()
        self.scroll_area.setWidget(self.scroll_content)
        
        self.main_layout.addWidget(self.scroll_area)

        self.theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme(self.theme_manager.get_current_theme(), self.theme_manager.is_dark)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_values)
        self.timer.start(200)
        self.update_values()

    def apply_theme(self, theme, is_dark):
        self.theme = theme
        
        self.title_label.setStyleSheet(f"color: {theme['text_primary']}; font-size: 14px; font-weight: bold; font-family: 'Segoe UI';")
        self.ml_info_label.setStyleSheet(f"color: {theme['text_secondary']}; font-size: 11px; font-family: 'Segoe UI'; padding-right: 4px;")
        
        for c in self.cards.values():
            c.update_theme(theme, is_dark)
            
        self.update_values()

    def update_values(self):
        if not hasattr(self, 'theme'): return
        
        t_prim = self.theme['text_primary']
        
        # Status mappings
        if data.warning_level == "DANGER":
            s_col = self.theme['danger']
        elif data.warning_level == "CAUTION":
            s_col = self.theme['warning']
        else:
            s_col = self.theme['success']
            
        self.cards["status"].update_val(0, data.road_status, s_col, s_col)
        self.cards["dist"].update_val(data.distance, f"{data.distance} cm", t_prim, "#00000000")
        self.cards["speed"].update_val(data.speed, f"{data.speed} km/h", t_prim, "#00000000")
        self.cards["depth"].update_val(data.depth, f"{data.depth} cm", t_prim, "#00000000")
        
        # Jerk dynamic threshold
        j = data.jerk
        if j > 2.0:
            j_col, j_glow = self.theme['danger'], self.theme['danger']
        else:
            j_col, j_glow = self.theme['success'], self.theme['success']
        self.cards["jerk"].update_val(j, f"{j}", j_col, j_glow)
        
        self.cards["gps"].update_val(data.distance, f"{data.gps}", t_prim, "#00000000")
        
        self.update_ml_display()

    def update_ml_display(self):
        if not data.ml_active:
            self.cards["ml"].update_val(0, "WAITING", self.theme['text_muted'], "#00000000", False)
            self.ml_info_label.setText("No windows classified")
            return

        prediction = data.ml_prediction.upper()
        conf = data.ml_confidence
        
        colors = {
            "pothole": self.theme['danger'],
            "bump": self.theme['warning'],
            "braking": self.theme['info'],
            "smooth": self.theme['success'],
        }
        c = colors.get(data.ml_prediction, self.theme['accent'])
        
        self.cards["ml"].update_val(conf, f"{prediction} ({conf}%)", c, c)

        fm = data.ml_field_mode
        src = "raw ax/ay/az" if fm == "raw" else "jerk/pitch/roll"
        self.ml_info_label.setText(f"Processed: {data.ml_total_classified} | {src}")