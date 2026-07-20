import sys
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
    QGraphicsDropShadowEffect
)
from PySide6.QtGui import QColor
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QRectF
from utils import data
from utils.theme import ThemeManager
from utils.animator import GlobalAnimator

class MLSummaryCard(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("mlSummaryCard")
        self.theme_manager = ThemeManager()
        self.setFixedHeight(50)
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(12, 4, 12, 4)
        main_layout.setSpacing(14)
        
        # Left side: Prediction Pill
        self.prediction_layout = QHBoxLayout()
        
        self.pill_container = QWidget()
        self.pill_container.setFixedSize(120, 36)
        contain_layout = QHBoxLayout(self.pill_container)
        contain_layout.setContentsMargins(0, 0, 0, 0)

        self.pill_frame = QFrame()
        self.pill_layout = QHBoxLayout(self.pill_frame)
        self.pill_layout.setContentsMargins(12, 4, 12, 4)
        self.prediction_label = QLabel("WAITING")
        self.prediction_label.setStyleSheet("font-size: 13px; font-weight: bold; background: transparent;")
        self.prediction_label.setAlignment(Qt.AlignCenter)
        self.pill_layout.addWidget(self.prediction_label)
        
        self.shadow_effect = QGraphicsDropShadowEffect(self)
        self.shadow_effect.setBlurRadius(8)
        self.shadow_effect.setOffset(0, 2)
        self.pill_frame.setGraphicsEffect(self.shadow_effect)

        contain_layout.addWidget(self.pill_frame)
        self.prediction_layout.addWidget(self.pill_container)
        self.prediction_layout.addStretch()
        
        # Middle: Confidence Progress
        self.confidence_layout = QVBoxLayout()
        self.confidence_layout.setSpacing(4)
        
        self.conf_header = QHBoxLayout()
        self.confidence_title = QLabel("CONFIDENCE")
        self.confidence_value = QLabel("0%")
        self.conf_header.addWidget(self.confidence_title)
        self.conf_header.addStretch()
        self.conf_header.addWidget(self.confidence_value)
        
        self.confidence_bar = QProgressBar()
        self.confidence_bar.setFixedHeight(6)
        self.confidence_bar.setTextVisible(False)
        self.confidence_bar.setRange(0, 100)
        self.confidence_bar.setValue(0)
        
        self.conf_anim = QPropertyAnimation(self.confidence_bar, b"value")
        self.conf_anim.setDuration(300)
        self.conf_anim.setEasingCurve(QEasingCurve.InOutQuad)
        
        self.confidence_layout.addLayout(self.conf_header)
        self.confidence_layout.addWidget(self.confidence_bar)
        
        # Right: Stats Overlay
        self.stats_layout = QVBoxLayout()
        self.stats_layout.setSpacing(2)
        self.windows_label = QLabel("CLASSIFIED: 0")
        self.mode_label = QLabel("MODE: UNKNOWN")
        self.stats_layout.addWidget(self.windows_label)
        self.stats_layout.addWidget(self.mode_label)
        self.stats_layout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        main_layout.addLayout(self.prediction_layout, 2)
        main_layout.addLayout(self.confidence_layout, 3)
        main_layout.addLayout(self.stats_layout, 2)
        
        # Overlay for inactive state
        self.inactive_label = QLabel("ML Model Waiting for data...")
        self.inactive_label.setAlignment(Qt.AlignCenter)
        self.inactive_label.hide()
        
        self.theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme(self.theme_manager.get_current_theme(), self.theme_manager.is_dark)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.start(300)
        self.update_data()
        
        self.animator = GlobalAnimator()
        self.animator.tick.connect(self.on_animator_tick)

    def on_animator_tick(self, timestamp):
        if data.ml_active and self.pill_container.isVisible():
            # pulse scale 100% to 102% using fixed sizes since pills are flat
            scale = self.animator.get_sine_value(timestamp, 2.0, 1.0, 1.05)
            s_w = int(100 * scale)
            s_h = int(28 * scale)
            self.pill_frame.setFixedSize(s_w, s_h)
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.inactive_label.setGeometry(0, 0, self.width(), self.height())

    def apply_theme(self, theme, is_dark):
        self.theme = theme
        border = f"1px solid {theme['border']}" if is_dark else "none"
        shadow = "" if is_dark else "box-shadow: 0 4px 12px rgba(0,0,0,0.06);"
        bg = f"qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #ffffff, stop:1 #e0e7ff)" if not is_dark else theme['surface']
        
        self.setStyleSheet(f"""
            QFrame#mlSummaryCard {{
                background: {bg};
                border-radius: 14px;
                border: {border};
                {shadow}
            }}
            QLabel {{
                font-family: "Segoe UI";
            }}
        """)
        
        self.confidence_title.setStyleSheet(f"font-size: 11px; color: {theme['text_secondary']};")
        self.confidence_value.setStyleSheet(f"font-size: 14px; color: {theme['text_primary']}; font-weight: bold;")
        self.windows_label.setStyleSheet(f"font-size: 12px; color: {theme['text_primary']}; font-weight: bold;")
        self.mode_label.setStyleSheet(f"font-size: 11px; color: {theme['text_secondary']};")
        self.inactive_label.setStyleSheet(f"color: {theme['text_muted']}; font-size: 14px; background: transparent; border: none;")
        
        self.confidence_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {theme['surface_elevated']};
                border-radius: 3px;
                border: none;
            }}
            QProgressBar::chunk {{
                background-color: {theme['accent']};
                border-radius: 3px;
            }}
        """)
        
        self.colors = {
            "smooth": theme['success'],
            "pothole": theme['danger'],
            "bump": theme['warning'],
            "braking": theme['info']
        }
        
        # re-apply colors if active
        self.update_data()
        
    def update_data(self):
        if not data.ml_active:
            for i in range(self.layout().count()):
                item = self.layout().itemAt(i)
                if item and item.layout():
                    self._set_layout_visible(item.layout(), False)
            self.inactive_label.show()
            self.inactive_label.raise_()
        else:
            self.inactive_label.hide()
            for i in range(self.layout().count()):
                item = self.layout().itemAt(i)
                if item and item.layout():
                    self._set_layout_visible(item.layout(), True)
            
            pred = data.ml_prediction
            conf = data.ml_confidence
            
            color_map = {
                "smooth": ("#22c55e", "#16a34a"),
                "pothole": ("#ef4444", "#dc2626"),
                "bump": ("#f59e0b", "#d97706"),
                "braking": ("#3b82f6", "#2563eb")
            }
            
            if pred in color_map:
                c1, c2 = color_map[pred]
                gradient = f"qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {c1}, stop:1 {c2})"
                self.shadow_effect.setColor(QColor(c1))
                text_color = "#ffffff"
            else:
                gradient = self.theme['surface_elevated']
                self.shadow_effect.setColor(QColor(0,0,0,0))
                text_color = self.theme['text_primary']
            
            # Pill Style
            self.pill_frame.setStyleSheet(f"""
                QFrame {{
                    background: {gradient};
                    border-radius: 14px;
                    border: none;
                }}
            """)
            self.prediction_label.setStyleSheet(f"color: {text_color}; font-size: 14px; font-weight: bold; background: transparent; border: none;")
            
            self.prediction_label.setText(pred.upper() if pred else "WAITING")
            self.confidence_value.setText(f"{conf}%")
            
            target_conf = min(max(conf, 0), 100)
            if self.confidence_bar.value() != target_conf:
                self.conf_anim.stop()
                self.conf_anim.setStartValue(self.confidence_bar.value())
                self.conf_anim.setEndValue(target_conf)
                self.conf_anim.start()

            self.windows_label.setText(f"CLASSIFIED: {data.ml_total_classified}")
            self.mode_label.setText(f"MODE: {data.ml_field_mode.upper()}")
            
    def _set_layout_visible(self, layout, visible):
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item.widget():
                item.widget().setVisible(visible)
            elif item.layout():
                self._set_layout_visible(item.layout(), visible)
