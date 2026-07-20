from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QProgressBar, QVBoxLayout, QWidget, QGraphicsDropShadowEffect
)
from PySide6.QtGui import QColor

from utils import data
from utils.theme import ThemeManager


class HistoryHoverBox(QLabel):
    def __init__(self, color, label_text):
        super().__init__()
        self.normal_color = color
        self.setFixedSize(24, 24)
        self.setStyleSheet(f"background-color: {color}; border-radius: 4px;")
        self.setToolTip(label_text)
        
        self.anim = QPropertyAnimation(self, b"maximumSize")
        self.anim.setDuration(150)
        self.anim.setEasingCurve(QEasingCurve.InOutQuad)
        
    def enterEvent(self, event):
        self.setFixedSize(26, 26)
        self.setStyleSheet(f"background-color: {self.normal_color}; border-radius: 4px; border: 1px solid white;")
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        self.setFixedSize(24, 24)
        self.setStyleSheet(f"background-color: {self.normal_color}; border-radius: 4px;")
        super().leaveEvent(event)


class MLPanel(QWidget):
    def __init__(self, ml_service):
        super().__init__()
        self.ml_service = ml_service
        self.theme_manager = ThemeManager()
        self.theme = self.theme_manager.get_current_theme()
        
        self.ui_elements = {}
        self.class_bars = {}

        self.build_interface()
        
        self.theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme(self.theme_manager.get_current_theme(), self.theme_manager.is_dark)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.start(500)
        self.update_data()
        
    def build_interface(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)
        
        # -- Section 1: Model Status --
        self.status_card = QFrame()
        status_layout = QVBoxLayout(self.status_card)
        status_layout.setContentsMargins(16, 14, 16, 14)
        
        self.ui_elements["status_title"] = QLabel("MODEL STATUS: NOT LOADED")
        self.ui_elements["status_title"].setAlignment(Qt.AlignCenter)
        status_layout.addWidget(self.ui_elements["status_title"])
        
        self.ui_elements["status_details"] = QLabel(
            "Model type: Random Forest (200 trees)\n"
            "Window size: 50 readings (1 second)\n"
            "Features: 24 statistical features\n"
            "Classes: smooth, pothole, bump, braking\n"
            "Field mode: unknown"
        )
        self.ui_elements["status_details"].setAlignment(Qt.AlignCenter)
        status_layout.addWidget(self.ui_elements["status_details"])
        main_layout.addWidget(self.status_card)
        
        # -- Section 2: Live Prediction --
        self.live_card = QFrame()
        live_layout = QVBoxLayout(self.live_card)
        live_layout.setContentsMargins(12, 12, 12, 16)
        live_layout.setAlignment(Qt.AlignCenter)
        live_layout.setSpacing(10)
        
        self.ui_elements["live_title"] = QLabel("LIVE CLASSIFICATION")
        self.ui_elements["live_title"].setAlignment(Qt.AlignCenter)
        
        self.live_dot = QLabel()
        self.live_dot.setFixedSize(70, 70)
        
        self.live_dot_glow = QGraphicsDropShadowEffect(self.live_dot)
        self.live_dot_glow.setBlurRadius(25)
        self.live_dot_glow.setOffset(0, 0)
        self.live_dot_glow.setColor(QColor(0,0,0,0))
        self.live_dot.setGraphicsEffect(self.live_dot_glow)
        
        self.live_prediction = QLabel("WAITING")
        self.live_prediction.setAlignment(Qt.AlignCenter)
        
        self.live_confidence = QProgressBar()
        self.live_confidence.setRange(0, 100)
        self.live_confidence.setValue(0)
        self.live_confidence.setTextVisible(True)
        self.live_confidence.setFormat("%v% CONFIDENCE")
        self.live_confidence.setMinimumWidth(320)
        
        dot_layout = QHBoxLayout()
        dot_layout.addStretch()
        dot_layout.addWidget(self.live_dot)
        dot_layout.addStretch()
        
        live_layout.addWidget(self.ui_elements["live_title"])
        live_layout.addLayout(dot_layout)
        live_layout.addWidget(self.live_prediction)
        live_layout.addSpacing(10)
        live_layout.addWidget(self.live_confidence, alignment=Qt.AlignCenter)
        main_layout.addWidget(self.live_card)
        
        # -- Section 3: Classification Breakdown --
        self.breakdown_card = QFrame()
        breakdown_layout = QVBoxLayout(self.breakdown_card)
        breakdown_layout.setContentsMargins(16, 14, 16, 14)
        breakdown_layout.setSpacing(8)
        
        self.ui_elements["bd_title"] = QLabel("CLASSIFICATION BREAKDOWN")
        breakdown_layout.addWidget(self.ui_elements["bd_title"])
        
        for cls in ["smooth", "pothole", "bump", "braking"]:
            row = QHBoxLayout()
            lbl = QLabel(cls.upper())
            lbl.setFixedWidth(80)
            
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(0)
            bar.setTextVisible(False)
            bar.setFixedHeight(12)
            
            count_lbl = QLabel("0 (0%)")
            count_lbl.setFixedWidth(80)
            count_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            
            row.addWidget(lbl)
            row.addWidget(bar)
            row.addWidget(count_lbl)
            breakdown_layout.addLayout(row)
            
            anim = QPropertyAnimation(bar, b"value")
            anim.setDuration(400)
            anim.setEasingCurve(QEasingCurve.InOutQuad)
            
            self.class_bars[cls] = {"bar": bar, "label": count_lbl, "class_name": lbl, "anim": anim}
            
        main_layout.addWidget(self.breakdown_card)
        
        # -- Section 4: Prediction History --
        self.history_card = QFrame()
        self.history_card.setMinimumHeight(100)
        history_layout = QVBoxLayout(self.history_card)
        history_layout.setContentsMargins(16, 14, 16, 14)
        
        self.ui_elements["hist_title"] = QLabel("PREDICTION HISTORY (LAST 20)")
        history_layout.addWidget(self.ui_elements["hist_title"])
        
        self.history_strip = QFrame()
        self.history_strip_layout = QHBoxLayout(self.history_strip)
        self.history_strip_layout.setContentsMargins(0, 5, 0, 5)
        self.history_strip_layout.setSpacing(1)
        self.history_strip_layout.setAlignment(Qt.AlignLeft)
        history_layout.addWidget(self.history_strip)
        main_layout.addWidget(self.history_card)
        
        # -- Section 5: How It Works --
        self.info_card = QFrame()
        info_layout = QVBoxLayout(self.info_card)
        info_layout.setContentsMargins(12, 10, 12, 10)
        
        self.ui_elements["info_title"] = QLabel("HOW IT WORKS")
        info_layout.addWidget(self.ui_elements["info_title"])
        
        self.ui_elements["info_text"] = QLabel(
            "The ML engine classifies road conditions in real time. Raw accelerometer\n"
            "readings (X, Y, Z) are buffered into 1-second windows of 50 samples.\n"
            "From each window, 24 statistical features are extracted (mean, std, min,\n"
            "max, range, RMS, energy, MAD for each axis). A trained Random Forest\n"
            "classifier then predicts the road condition: smooth, pothole, speed bump,\n"
            "or braking event."
        )
        self.ui_elements["info_text"].setWordWrap(True)
        info_layout.addWidget(self.ui_elements["info_text"])
        main_layout.addWidget(self.info_card)
        
        main_layout.addStretch()

    def apply_theme(self, theme, is_dark):
        self.theme = theme
        border = f"1px solid {theme['border']}" if is_dark else "none"
        shadow = "" if is_dark else "box-shadow: 0 1px 3px rgba(0,0,0,0.08);"
        
        # Cards
        card_style = f"""
            QFrame {{
                background-color: {theme['surface']};
                border-radius: 14px;
                border: {border};
                {shadow}
            }}
        """
        self.status_card.setStyleSheet(card_style)
        self.live_card.setStyleSheet(card_style)
        self.breakdown_card.setStyleSheet(card_style)
        self.history_card.setStyleSheet(card_style)
        self.info_card.setStyleSheet(card_style)
        
        # No style for layout frame
        self.history_strip.setStyleSheet("background: transparent; border: none; box-shadow: none;")

        # Typography
        self.ui_elements["status_title"].setStyleSheet(f"font-size: 15px; font-weight: bold; font-family: 'Segoe UI'; border: none; background: transparent;")
        self.ui_elements["status_details"].setStyleSheet(f"color: {theme['text_secondary']}; font-size: 13px; font-family: 'Segoe UI'; line-height: 1.4; border: none; background: transparent;")
        
        self.ui_elements["live_title"].setStyleSheet(f"color: {theme['text_muted']}; font-size: 12px; font-weight: bold; font-family: 'Segoe UI'; border: none; background: transparent;")
        
        for k in ["bd_title", "hist_title", "info_title"]:
            self.ui_elements[k].setStyleSheet(f"color: {theme['text_primary']}; font-size: 14px; font-weight: bold; font-family: 'Segoe UI'; margin-bottom: 4px; border: none; background: transparent;")
            
        self.ui_elements["info_text"].setStyleSheet(f"color: {theme['text_secondary']}; font-size: 13px; font-family: 'Segoe UI'; line-height: 1.5; border: none; background: transparent;")

        for cls_name, cls_data in self.class_bars.items():
            cls_data["class_name"].setStyleSheet(f"color: {theme['text_secondary']}; font-size: 13px; font-weight: bold; font-family: 'Segoe UI'; border: none; background: transparent;")
            cls_data["label"].setStyleSheet(f"color: {theme['text_primary']}; font-size: 13px; font-weight: bold; font-family: 'Segoe UI'; border: none; background: transparent;")

        self.update_data() # refresh colors
        
    def get_color_for_class(self, cls):
        if cls == "smooth": return self.theme.get("success", "#10b981")
        if cls == "pothole": return self.theme.get("danger", "#ef4444")
        if cls == "bump": return self.theme.get("warning", "#f59e0b")
        if cls == "braking": return self.theme.get("accent", "#3b82f6")
        return self.theme.get("border", "grey")

    def update_data(self):
        if not hasattr(self, 'theme'): return
        
        summary = self.ml_service.get_summary()
        
        # 1. Model Status
        is_loaded = summary.get("loaded", False)
        status_color = self.theme['success'] if is_loaded else self.theme['danger']
        status_text = "LOADED" if is_loaded else "NOT LOADED"
        self.ui_elements["status_title"].setText(f"MODEL STATUS: {status_text}")
        self.ui_elements["status_title"].setStyleSheet(f"font-size: 15px; font-weight: bold; color: {status_color}; font-family: 'Segoe UI'; border: none; background: transparent;")
        
        field_mode = summary.get("field_mode", "unknown")
        self.ui_elements["status_details"].setText(
            "Model type: Random Forest (200 trees)\n"
            f"Window size: {summary.get('window_size', 50)} readings (1 second)\n"
            "Features: 24 statistical features\n"
            "Classes: smooth, pothole, bump, braking\n"
            f"Field mode: {field_mode.upper()}"
        )
        
        # 2. Live Prediction
        if data.ml_active:
            pred = data.ml_prediction
            conf = data.ml_confidence
            color = self.get_color_for_class(pred)
            
            self.live_dot.setStyleSheet(f"background-color: qradialgradient(cx: 0.5, cy: 0.5, radius: 0.5, fx: 0.5, fy: 0.5, stop: 0 {color}, stop: 1 {self.theme['surface_elevated']}); border-radius: 35px;")
            self.live_dot_glow.setColor(QColor(color))
            self.live_prediction.setText(pred.upper())
            self.live_prediction.setStyleSheet(f"font-size: 32px; font-weight: bold; color: {color}; font-family: 'Segoe UI'; border: none; background: transparent;")
            self.live_confidence.setValue(int(conf))
            
            self.live_confidence.setStyleSheet(f"""
                QProgressBar {{
                    border: none;
                    border-radius: 10px;
                    text-align: center;
                    background-color: {self.theme['surface_elevated']};
                    color: {self.theme['text_primary']};
                    font-weight: bold;
                    height: 24px;
                }}
                QProgressBar::chunk {{ background-color: {color}; border-radius: 10px; }}
            """)
        else:
            self.live_dot.setStyleSheet(f"background-color: {self.theme['border']}; border-radius: 35px;")
            self.live_dot_glow.setColor(QColor(0,0,0,0))
            self.live_prediction.setText("WAITING FOR DATA")
            self.live_prediction.setStyleSheet(f"font-size: 32px; font-weight: bold; color: {self.theme['text_muted']}; font-family: 'Segoe UI'; border: none; background: transparent;")
            self.live_confidence.setValue(0)
            self.live_confidence.setStyleSheet(f"""
                QProgressBar {{ border: none; border-radius: 10px; background-color: {self.theme['surface_elevated']}; height: 24px; }}
                QProgressBar::chunk {{ background-color: {self.theme['border']}; border-radius: 10px; }}
            """)
            
        # 3. Breakdown
        total = summary.get("total_classified", 0)
        counts = summary.get("class_counts", {})
        for cls in ["smooth", "pothole", "bump", "braking"]:
            count = counts.get(cls, 0)
            pct = 0 if total == 0 else (count / total) * 100
            
            bar = self.class_bars[cls]["bar"]
            anim = self.class_bars[cls]["anim"]
            target = int(pct)
            
            if bar.value() != target:
                anim.stop()
                anim.setStartValue(bar.value())
                anim.setEndValue(target)
                anim.start()

            bar_color = self.get_color_for_class(cls)
            bar_glow = self.theme.get("accent", "#3b82f6") if cls == 'braking' else bar_color
            
            bar.setStyleSheet(f"""
                QProgressBar {{ border: none; background-color: {self.theme['surface_elevated']}; border-radius: 6px; }}
                QProgressBar::chunk {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {bar_color}, stop:1 {bar_glow}); border-radius: 6px; }}
            """)
            lbl = self.class_bars[cls]["label"]
            lbl.setText(f"{count} ({int(pct)}%)")
            
        # 4. History
        for i in reversed(range(self.history_strip_layout.count())):
            item = self.history_strip_layout.itemAt(i)
            if item.widget(): item.widget().deleteLater()
                
        history = list(self.ml_service.prediction_history)[-22:] # More items in view
        for pred in history:
            color = self.get_color_for_class(pred)
            box = HistoryHoverBox(color, pred.upper())
            self.history_strip_layout.addWidget(box)
        
        self.history_strip_layout.addStretch()
