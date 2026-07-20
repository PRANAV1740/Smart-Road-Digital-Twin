# ==================================================
# SMART ROAD DIGITAL TWIN - MAP WIDGET
# ==================================================

from PySide6.QtCore import (
    QPointF,
    QRectF,
    Qt,
    QTimer,
)
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QPainter,
    QPainterPath,
    QPen,
    QLinearGradient,
    QRadialGradient,
    QPolygonF
)
from PySide6.QtWidgets import QWidget, QGraphicsDropShadowEffect

from database.database import (
    get_pothole_by_id,
    save_pothole,
)
from utils import data
from widgets.pothole_details_dialog import (
    PotholeDetailsDialog,
)
from utils.theme import ThemeManager
from utils.animator import GlobalAnimator


class MapWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.setMinimumSize(850, 520)

        # Show a pointing cursor over clickable potholes.
        self.setMouseTracking(True)
        self.theme_manager = ThemeManager()

        self.blink = False
        self.trail_points = []

        self.left = 90
        self.top = 90
        self.right = 800
        self.bottom = 440

        self.warning_distance = 130

        # Radius used for pothole click detection.
        self.pothole_click_radius_x = 48
        self.pothole_click_radius_y = 38

        self.timer = QTimer(self)
        self.timer.timeout.connect(
            self.move_car
        )
        self.timer.start(40)

        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(
            self.toggle_blink
        )
        self.blink_timer.start(500)
        
        self.animator = GlobalAnimator()
        self.current_time = 0.0
        self.animator.tick.connect(self.on_animator_tick)

        # Motion trail for car
        self.car_trail_positions = []
        
        self.theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme(self.theme_manager.get_current_theme(), self.theme_manager.is_dark)

    def on_animator_tick(self, timestamp):
        self.current_time = timestamp
        self.update()

    def apply_theme(self, theme, is_dark):
        self.theme = theme
        self.is_dark = is_dark
        if is_dark:
            self.setGraphicsEffect(None)
        else:
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(10)
            shadow.setColor(QColor(0, 0, 0, 20))
            shadow.setOffset(0, 1)
            self.setGraphicsEffect(shadow)
        self.update()

    def toggle_blink(self):
        self.blink = not self.blink
        self.update()

    def move_car(self):
        speed = 2

        if data.direction == "RIGHT":
            data.car_x += speed
            data.car_y = self.top - 14

            if data.car_x >= self.right - 10:
                data.direction = "DOWN"

        elif data.direction == "DOWN":
            data.car_y += speed
            data.car_x = self.right - 14

            if data.car_y >= self.bottom - 10:
                data.direction = "LEFT"

        elif data.direction == "LEFT":
            data.car_x -= speed
            data.car_y = self.bottom - 14

            if data.car_x <= self.left - 10:
                data.direction = "UP"

        elif data.direction == "UP":
            data.car_y -= speed
            data.car_x = self.left - 14

            if data.car_y <= self.top - 10:
                data.direction = "RIGHT"

        self.update_sensor_logic()

        self.trail_points.append(
            QPointF(
                data.car_x + 14,
                data.car_y + 14,
            )
        )

        if len(self.trail_points) > 140:
            self.trail_points.pop(0)

        data.gps = (
            f"({data.car_x}, {data.car_y})"
        )

        self.update()

    def update_sensor_logic(self):
        # ==================================================
        # ML AUTHORITY CHECK
        # ==================================================
        # This method decides road_status by checking whether the car
        # is near a HARDCODED pothole coordinate. That is proximity
        # checking, not detection - it only works because the twin
        # already knows where the potholes are.
        #
        # In LIVE mode there is no scripted track and no known pothole
        # list, so the ML model's prediction is the only real source of
        # truth. We return early and let ml_service.py own road_status.
        #
        # In SIMULATION mode we keep the old behaviour so the digital
        # twin animation still works, and the ML prediction is shown
        # alongside it for comparison.
        # ==================================================

        if data.ml_authoritative:
            return

        car_x = data.car_x + 14
        car_y = data.car_y + 14

        data.warning_level = "SAFE"
        data.road_status = "SAFE"
        data.obstacle_ahead = False
        data.distance = 100
        data.depth = 0
        data.jerk = 0.3
        data.speed = 35
        data.current_pothole_id = None
        data.current_pothole_depth = 0
        data.current_pothole_severity = "NONE"

        nearest_warning = None
        nearest_warning_distance = 9999
        active_danger = None

        for pothole in data.potholes:
            px = pothole["x"]
            py = pothole["y"]

            dx = abs(car_x - px)
            dy = abs(car_y - py)

            on_pothole = (
                dx < 45
                and dy < 35
            )

            approaching = False

            if data.direction == "RIGHT":
                approaching = (
                    car_x < px
                    and (
                        px - car_x
                    ) <= self.warning_distance
                    and dy < 35
                )

            elif data.direction == "LEFT":
                approaching = (
                    car_x > px
                    and (
                        car_x - px
                    ) <= self.warning_distance
                    and dy < 35
                )

            elif data.direction == "DOWN":
                approaching = (
                    car_y < py
                    and (
                        py - car_y
                    ) <= self.warning_distance
                    and dx < 35
                )

            elif data.direction == "UP":
                approaching = (
                    car_y > py
                    and (
                        car_y - py
                    ) <= self.warning_distance
                    and dx < 35
                )

            if on_pothole:
                active_danger = pothole
                break

            if approaching:
                real_distance = int(
                    max(dx, dy)
                )

                if (
                    real_distance
                    < nearest_warning_distance
                ):
                    nearest_warning_distance = (
                        real_distance
                    )
                    nearest_warning = pothole

        if active_danger is not None:
            data.warning_level = "DANGER"
            data.road_status = "POTHOLE"
            data.obstacle_ahead = False
            data.distance = 0
            data.depth = active_danger["depth"]
            data.jerk = 3.2
            data.speed = 12
            data.current_pothole_id = (
                active_danger["id"]
            )
            data.current_pothole_depth = (
                active_danger["depth"]
            )
            data.current_pothole_severity = (
                active_danger["severity"]
            )

            if not active_danger["detected"]:
                active_danger["detected"] = True
                data.total_potholes_detected += 1

                saved = save_pothole(
                    pothole_id=active_danger["id"],
                    x=active_danger["x"],
                    y=active_danger["y"],
                    depth=active_danger["depth"],
                    severity=active_danger[
                        "severity"
                    ],
                    latitude=data.latitude,
                    longitude=data.longitude,
                    photo_captured=False,
                )

                if saved:
                    print(
                        f"Pothole "
                        f"{active_danger['id']} "
                        f"saved to database."
                    )

            

        elif nearest_warning is not None:
            data.warning_level = "CAUTION"
            data.road_status = "WARNING"
            data.obstacle_ahead = True
            data.distance = (
                nearest_warning_distance
            )
            data.depth = 0
            data.jerk = 0.8
            data.speed = 22
            data.current_pothole_id = (
                nearest_warning["id"]
            )
            data.current_pothole_depth = (
                nearest_warning["depth"]
            )
            data.current_pothole_severity = (
                nearest_warning["severity"]
            )
            data.total_warnings += 1

    # ==================================================
    # CLICKABLE POTHOLES
    # ==================================================

    def mousePressEvent(self, event):
        """
        Open the details dialog when the user clicks
        on a pothole.
        """

        if event.button() != Qt.LeftButton:
            super().mousePressEvent(event)
            return

        clicked_pothole = self.find_pothole_at(
            event.position().x(),
            event.position().y(),
        )

        if clicked_pothole is None:
            super().mousePressEvent(event)
            return

        self.open_pothole_details(
            clicked_pothole
        )

    def mouseMoveEvent(self, event):
        """
        Change the cursor when it moves over a pothole.
        """

        hovered_pothole = self.find_pothole_at(
            event.position().x(),
            event.position().y(),
        )

        if hovered_pothole is not None:
            self.setCursor(
                Qt.PointingHandCursor
            )
        else:
            self.setCursor(
                Qt.ArrowCursor
            )

        super().mouseMoveEvent(event)

    def find_pothole_at(
        self,
        mouse_x,
        mouse_y,
    ):
        """
        Return the pothole located near the mouse position.
        """

        for pothole in data.potholes:
            pothole_x = pothole["x"]
            pothole_y = pothole["y"]

            inside_x = (
                abs(mouse_x - pothole_x)
                <= self.pothole_click_radius_x
            )

            inside_y = (
                abs(mouse_y - pothole_y)
                <= self.pothole_click_radius_y
            )

            if inside_x and inside_y:
                return pothole

        return None

    def open_pothole_details(
        self,
        pothole,
    ):
        """
        Read the matching SQLite record and open the
        professional pothole information dialog.
        """

        database_record = None

        try:
            database_record = get_pothole_by_id(
                pothole["id"]
            )

        except Exception as error:
            print(
                "Unable to read pothole details "
                f"from database: {error}"
            )

        dialog = PotholeDetailsDialog(
            pothole=pothole,
            database_record=database_record,
            parent=self,
        )

        dialog.exec()

    # ==================================================
    # PAINTING
    # ==================================================

    def paintEvent(self, event):
        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.Antialiasing
        )
        
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), 14, 14)
        painter.setClipPath(path)

        self.draw_background(painter)
        self.draw_road_shadow(painter)
        self.draw_road(painter)
        self.draw_lane_markings(painter)
        self.draw_gps_trail(painter)
        self.draw_all_potholes(painter)
        self.draw_labels(painter)
        self.draw_vehicle(painter)
        
        if getattr(self, "is_dark", True) and hasattr(self, "theme"):
            painter.setClipping(False)
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(QColor(self.theme['border']), 2))
            painter.drawRoundedRect(self.rect().adjusted(1,1,-1,-1), 14, 14)

    def draw_background(self, painter):
        is_dark = getattr(self, "is_dark", True)
        # 1. Map canvas background (card surface)
        bg_color = QColor("#1a1d27") if is_dark else QColor("#e8e8ed")
        painter.fillRect(self.rect(), bg_color)
        
        # 2. Grass / roadside area (subtle depth gradient)
        grass_start = QColor("#183020") if is_dark else QColor("#a8c8a8")
        grass_end = QColor("#1e3a1e") if is_dark else QColor("#b8d4b8")
        
        grass_grad = QLinearGradient(0, 0, self.width(), self.height())
        grass_grad.setColorAt(0, grass_start)
        grass_grad.setColorAt(1, grass_end)
        painter.fillRect(self.rect().adjusted(10, 10, -10, -10), grass_grad)

        # Optional: Grid overlay (hologram terrain feel)
        grid_color = QColor(255, 255, 255, 15) if is_dark else QColor(0, 0, 0, 15)
        painter.setPen(QPen(grid_color, 1, Qt.DotLine))

        grid_spacing = 40
        for x in range(0, self.width(), grid_spacing):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), grid_spacing):
            painter.drawLine(0, y, self.width(), y)

    def draw_road_shadow(self, painter):
        painter.setPen(
            QPen(
                QColor(
                    0,
                    0,
                    0,
                    120,
                ),
                58,
            )
        )

        painter.drawRoundedRect(
            QRectF(
                self.left,
                self.top,
                self.right - self.left,
                self.bottom - self.top,
            ),
            28,
            28,
        )

    def draw_road(self, painter):
        road_rect = QRectF(
            self.left,
            self.top,
            self.right - self.left,
            self.bottom - self.top,
        )

        is_dark = getattr(self, "is_dark", True)
        road_edge = QColor("#555555") if is_dark else QColor("#48484a")
        
        # Faint blue glow around road edges
        glow_color = QColor(59, 130, 246, 40) if is_dark else QColor(0, 122, 255, 30)
        painter.setPen(QPen(glow_color, 54))
        painter.drawRoundedRect(road_rect, 25, 25)

        painter.setPen(QPen(road_edge, 46))
        painter.drawRoundedRect(road_rect, 25, 25)

        # Linear gradient along the road width
        # Lighter center, darker edges
        road_grad = QLinearGradient(road_rect.left(), road_rect.top(), road_rect.right(), road_rect.bottom())
        center_c = QColor("#4a4a4c") if is_dark else QColor("#7e7e83")
        edge_c = QColor("#3a3a3c") if is_dark else QColor("#6e6e73")
        road_grad.setColorAt(0, edge_c)
        road_grad.setColorAt(0.5, center_c)
        road_grad.setColorAt(1, edge_c)

        painter.setPen(QPen(road_grad, 34))
        painter.drawRoundedRect(road_rect, 22, 22)

    def draw_lane_markings(self, painter):
        painter.setPen(
            QPen(
                QColor("#ffffff"),
                3,
                Qt.SolidLine,
            )
        )
        painter.drawRoundedRect(
            QRectF(
                self.left + 8,
                self.top + 8,
                self.right - self.left - 16,
                self.bottom - self.top - 16,
            ),
            18,
            18,
        )
        
        painter.setPen(
            QPen(
                QColor("#f5c542"),
                3,
                Qt.DashLine,
            )
        )

        painter.drawRoundedRect(
            QRectF(
                self.left + 30,
                self.top + 30,
                self.right - self.left - 60,
                self.bottom - self.top - 60,
            ),
            10,
            10,
        )

    def draw_gps_trail(self, painter):
        if len(self.trail_points) < 2:
            return

        painter.setPen(
            QPen(
                QColor("#00e5ff"),
                2,
            )
        )

        for index in range(
            1,
            len(self.trail_points),
        ):
            painter.drawLine(
                self.trail_points[index - 1],
                self.trail_points[index],
            )

    def draw_all_potholes(self, painter):
        for pothole in data.potholes:
            self.draw_single_pothole(
                painter,
                pothole,
            )

    def draw_single_pothole(
        self,
        painter,
        pothole,
    ):
        x = pothole["x"]
        y = pothole["y"]

        is_current = (
            data.current_pothole_id
            == pothole["id"]
        )

        painter.setPen(Qt.NoPen)

        if (
            is_current
            and data.warning_level == "CAUTION"
            and self.blink
        ):
            painter.setBrush(
                QColor(
                    255,
                    204,
                    0,
                    90,
                )
            )

            painter.drawEllipse(
                QRectF(
                    x - 50,
                    y - 38,
                    100,
                    76,
                )
            )

        if (
            is_current
            and data.warning_level == "DANGER"
            and self.blink
        ):
            painter.setBrush(
                QColor(
                    255,
                    51,
                    51,
                    100,
                )
            )

            painter.drawEllipse(
                QRectF(
                    x - 55,
                    y - 42,
                    110,
                    84,
                )
            )

        is_dark = getattr(self, "is_dark", True)
        pothole_fill = QColor("#ff3b30")
        pothole_border = QColor("#ff6b6b") if is_dark else QColor("#cc0000")

        pulse = self.animator.get_sine_value(self.current_time, 0.8, 0, 2)
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(255, 59, 48, 40))
        h_rad = 50 + pulse * 2
        painter.drawEllipse(QRectF(x - h_rad/2, y - h_rad/2 + 5, h_rad, h_rad * 0.6))

        painter.setBrush(pothole_fill)
        painter.setPen(QPen(pothole_border, 2))

        w = 34 + pulse
        h = 20 + pulse
        painter.drawEllipse(QRectF(x - w/2, y - h/2, w, h))

        painter.setFont(
            QFont(
                "Arial",
                8,
                QFont.Bold,
            )
        )

        if pothole["detected"]:
            painter.setPen(
                QPen(
                    QColor("#ff3333"),
                    1,
                )
            )

            painter.drawText(
                x - 22,
                y + 42,
                "DETECTED",
            )

        else:
            painter.setPen(
                QPen(
                    QColor("#aaaaaa"),
                    1,
                )
            )

            painter.drawText(
                x - 18,
                y + 42,
                f"P-{pothole['id']}",
            )

        if (
            is_current
            and data.warning_level == "CAUTION"
        ):
            painter.setPen(
                QPen(
                    QColor("#ffcc00"),
                    2,
                )
            )

            painter.setFont(
                QFont(
                    "Arial",
                    11,
                    QFont.Bold,
                )
            )

            painter.drawText(
                x - 58,
                y - 38,
                "POTHOLE AHEAD",
            )

        elif (
            is_current
            and data.warning_level == "DANGER"
        ):
            painter.setPen(
                QPen(
                    QColor("#ff3333"),
                    2,
                )
            )

            painter.setFont(
                QFont(
                    "Arial",
                    11,
                    QFont.Bold,
                )
            )

            painter.drawText(
                x - 52,
                y - 38,
                "POTHOLE",
            )

    def draw_labels(self, painter):
        painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
        is_dark = getattr(self, "is_dark", True)
        
        # Start and End Labels
        text_color = QColor("#e0e0e0") if is_dark else QColor("#1d1d1f")
        painter.setPen(QPen(text_color, 2))
        painter.drawText(self.left - 5, self.top - 28, "START")
        painter.drawText(self.right - 75, self.bottom + 38, "END")

        # Map Title (Top Left)
        painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
        muted_color = QColor(150, 150, 150)
        painter.setPen(QPen(muted_color))
        painter.drawText(35, 30, "DIGITAL TWIN — LIVE")
        
        # Blinking dot next to title
        pulse = self.animator.get_sine_value(self.current_time, 1.5, 50, 255)
        painter.setBrush(QColor(16, 185, 129, int(pulse))) # Emerald Green
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QRectF(18, 20, 10, 10))

    def draw_vehicle(self, painter):
        import math
        x = data.car_x
        y = data.car_y
        
        if not self.car_trail_positions or self.car_trail_positions[-1] != (x, y):
            self.car_trail_positions.append((x, y))
            if len(self.car_trail_positions) > 10:
                self.car_trail_positions.pop(0)

        # Calculate angle
        self.car_angle = getattr(self, "car_angle", 0)
        if len(self.car_trail_positions) > 1:
            px, py = self.car_trail_positions[-2]
            dx = x - px
            dy = y - py
            if dx != 0 or dy != 0:
                self.car_angle = math.degrees(math.atan2(dy, dx))

        painter.save()
        
        trail_color = QColor(59, 130, 246)
        painter.setPen(Qt.NoPen)
        for i, (tx, ty) in enumerate(self.car_trail_positions):
            opacity = int(255 * (i / 10.0))
            if opacity > 0:
                trail_color.setAlpha(opacity)
                painter.setBrush(trail_color)
                painter.drawEllipse(QRectF(tx + 9, ty + 9, 10, 10))

        painter.translate(x + 14, y + 14)
        painter.rotate(self.car_angle)

        is_dark = getattr(self, "is_dark", True)
        
        # Halo glow (behind car)
        pulse_alpha = int(self.animator.get_sine_value(self.current_time, 1.5, 40, 150)) if is_dark else int(self.animator.get_sine_value(self.current_time, 1.5, 20, 100))
        halo_color = QColor(59, 130, 246)
        halo_grad = QRadialGradient(0, 0, 36)
        halo_grad.setColorAt(0, QColor(halo_color.red(), halo_color.green(), halo_color.blue(), pulse_alpha))
        halo_grad.setColorAt(1, QColor(halo_color.red(), halo_color.green(), halo_color.blue(), 0))
        
        painter.setBrush(halo_grad)
        painter.drawEllipse(QRectF(-36, -36, 72, 72))
        
        # Colors
        windshield_color = QColor("#ffffff") if is_dark else QColor("#e5e7eb")
        wheel_color = QColor("#374151") if is_dark else QColor("#111827")
        body_outline = QColor("#1e3a8a")

        # Wheels
        painter.setBrush(wheel_color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(QRectF(-9, -10, 6, 3), 1, 1) # rear left
        painter.drawRoundedRect(QRectF(-9, 7, 6, 3), 1, 1)   # rear right
        painter.drawRoundedRect(QRectF(5, -10, 6, 3), 1, 1)  # front left
        painter.drawRoundedRect(QRectF(5, 7, 6, 3), 1, 1)    # front right

        # Car Body
        from PySide6.QtGui import QLinearGradient
        body_grad = QLinearGradient(-14, 0, 14, 0)
        body_grad.setColorAt(0, QColor("#2563eb")) # rear
        body_grad.setColorAt(1, QColor("#3b82f6")) # front
        
        painter.setBrush(body_grad)
        painter.setPen(QPen(body_outline, 1))
        painter.drawRoundedRect(QRectF(-14, -8, 28, 16), 4, 4)

        # Windshield
        painter.setBrush(windshield_color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(QRectF(3, -5, 6, 10), 2, 2)

        painter.restore()