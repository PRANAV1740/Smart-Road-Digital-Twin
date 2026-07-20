import datetime
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QScrollArea, QFrame, QHBoxLayout, QGraphicsOpacityEffect
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor

from utils import data
from utils.theme import ThemeManager
from utils.animator import GlobalAnimator

class ToastCard(QFrame):
    def __init__(self, msg, color_hex, theme, is_dark, is_danger=False):
        super().__init__()
        self.setObjectName("toast")
        self.setFixedHeight(28)
        self.setMaximumWidth(0) # start collapsed for slide in
        self.is_danger = is_danger
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        
        now = datetime.datetime.now().strftime("%H:%M:%S")
        self.time_lbl = QLabel(now)
        self.msg_lbl = QLabel(msg)
        
        layout.addWidget(self.msg_lbl)
        layout.addStretch()
        layout.addWidget(self.time_lbl)
        
        self.op_effect = QGraphicsOpacityEffect(self)
        self.op_effect.setOpacity(1.0)
        self.setGraphicsEffect(self.op_effect)
        
        dark_base = QColor(theme['surface']).darker(110)
        bg = f"{color_hex}20"
        
        bg_str = theme['surface'] if is_dark else f"qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #ffffff, stop:1 #e0e7ff)"
        
        self.setStyleSheet(f"""
            QFrame#toast {{
                background: {bg_str};
                border-radius: 6px;
                border: none;
                border-left: 4px solid qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {color_hex}99, stop:1 {color_hex});
            }}
        """)
        
        self.time_lbl.setStyleSheet(f"color: {theme['text_secondary']}; font-size: 10px; font-weight: bold; background: transparent; border: none;")
        self.msg_lbl.setStyleSheet(f"color: {theme['text_primary']}; font-size: 12px; font-weight: bold; background: transparent; border: none;")
        
        # entry slide-in
        self.anim = QPropertyAnimation(self, b"maximumWidth")
        self.anim.setDuration(300)
        self.anim.setStartValue(0)
        self.anim.setEndValue(3000) # expand huge to let layout take over
        self.anim.setEasingCurve(QEasingCurve.OutElastic)
        self.anim.start()
        
        if self.is_danger:
            self.animator = GlobalAnimator()
            self.animator.tick.connect(self.on_animator_tick)
            
    def on_animator_tick(self, timestamp):
        val = self.animator.get_sine_value(timestamp, 1.5, 0.6, 1.0)
        self.op_effect.setOpacity(val)


class AlertPanel(QFrame):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(130)  # taller to fit 4 toasts
        self.theme_manager = ThemeManager()
        self.last_alert_state = None
        self.toasts = []

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("border: none; background: transparent;")
        
        self.list_widget = QWidget()
        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setContentsMargins(4, 4, 4, 4)
        self.list_layout.setSpacing(6)
        self.list_layout.addStretch()
        
        self.scroll_area.setWidget(self.list_widget)
        self.main_layout.addWidget(self.scroll_area)
        
        self.theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme(self.theme_manager.get_current_theme(), self.theme_manager.is_dark)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_alert)
        self.timer.start(300)

        self.update_alert()

    def apply_theme(self, theme, is_dark):
        self.theme = theme
        
        border = f"1px solid {theme['border']}" if is_dark else "none"
        shadow = "" if is_dark else "box-shadow: 0 1px 3px rgba(0,0,0,0.08);"
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {theme['surface']};
                border-radius: 12px;
                border: {border};
                {shadow}
            }}
        """)

    def add_toast(self, msg, color_hex, is_danger=False):
        toast = ToastCard(msg, color_hex, self.theme, self.theme_manager.is_dark, is_danger)
        
        self.toasts.insert(0, {"toast": toast, "is_danger": is_danger})
        
        # Insert at top (index 0, before stretch)
        self.list_layout.insertWidget(0, toast)
        
        # Limit to 10 toasts
        if len(self.toasts) > 10:
            oldest = self.toasts.pop()
            self.list_layout.removeWidget(oldest["toast"])
            oldest["toast"].deleteLater()
            
        # Update opacities for older items
        for i, ui in enumerate(self.toasts):
            if not ui["is_danger"]:
                alpha = max(0.4, 1.0 - (i * 0.12))
                ui["toast"].op_effect.setOpacity(alpha)

    def update_alert(self):
        new_state = None
        
        if data.warning_level == "SAFE":
            new_state = ("ROAD CLEAR", self.theme['success'] if hasattr(self, 'theme') else "#22c55e", False)
        elif data.warning_level == "CAUTION":
            new_state = (f"POTHOLE AHEAD • {data.distance} cm", self.theme['warning'] if hasattr(self, 'theme') else "#f59e0b", False)
        elif data.warning_level == "DANGER":
            new_state = (f"POTHOLE DETECTED • Depth: {data.depth} cm", self.theme['danger'] if hasattr(self, 'theme') else "#ef4444", True)

        # Only add a toast if the state string changed
        if new_state and (not self.last_alert_state or self.last_alert_state[0] != new_state[0]):
            self.add_toast(new_state[0], new_state[1], new_state[2])
            self.last_alert_state = new_state