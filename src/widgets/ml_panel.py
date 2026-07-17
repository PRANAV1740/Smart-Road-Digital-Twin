from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QScrollArea,
    QWidget
)
from utils import data

class MLPanel(QWidget):
    def __init__(self, ml_service):
        super().__init__()
        self.ml_service = ml_service
        self.colors = {
            "smooth": "#00d26a",
            "pothole": "#ff5555",
            "bump": "#ffd400",
            "braking": "#4f8cff"
        }
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)
        
        # -- Section 1: Model Status --
        self.status_card = QFrame()
        self.status_card.setStyleSheet("background-color: #1b1f24; border: 1px solid #242c36; border-radius: 12px;")
        status_layout = QVBoxLayout(self.status_card)
        
        self.status_title = QLabel("MODEL STATUS: NOT LOADED")
        self.status_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #ff5555;")
        status_layout.addWidget(self.status_title)
        
        self.status_details = QLabel(
            "Model type: Random Forest (200 trees)\n"
            "Window size: 50 readings (1 second)\n"
            "Features: 24 statistical features\n"
            "Classes: smooth, pothole, bump, braking\n"
            "Field mode: unknown"
        )
        self.status_details.setStyleSheet("color: #8e99a8; font-size: 12px;")
        status_layout.addWidget(self.status_details)
        main_layout.addWidget(self.status_card)
        
        # -- Section 2: Live Prediction --
        self.live_card = QFrame()
        self.live_card.setStyleSheet("background-color: #1b1f24; border: 1px solid #242c36; border-radius: 12px;")
        live_layout = QVBoxLayout(self.live_card)
        live_layout.setAlignment(Qt.AlignCenter)
        
        self.live_dot = QLabel()
        self.live_dot.setFixedSize(60, 60)
        self.live_dot.setStyleSheet("background-color: grey; border-radius: 30px;")
        
        self.live_prediction = QLabel("WAITING")
        self.live_prediction.setStyleSheet("font-size: 32px; font-weight: bold; color: #f4f7fb;")
        self.live_prediction.setAlignment(Qt.AlignCenter)
        
        self.live_confidence = QProgressBar()
        self.live_confidence.setRange(0, 100)
        self.live_confidence.setValue(0)
        self.live_confidence.setTextVisible(True)
        self.live_confidence.setFormat("%v% CONFIDENCE")
        self.live_confidence.setStyleSheet(
            """
            QProgressBar {
                border: 1px solid #242c36;
                border-radius: 5px;
                text-align: center;
                background-color: #0f1318;
                color: #f4f7fb;
                font-weight: bold;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #4f8cff;
                border-radius: 5px;
            }
            """
        )
        self.live_confidence.setMinimumWidth(300)
        
        dot_layout = QHBoxLayout()
        dot_layout.addStretch()
        dot_layout.addWidget(self.live_dot)
        dot_layout.addStretch()
        
        live_layout.addLayout(dot_layout)
        live_layout.addWidget(self.live_prediction)
        live_layout.addWidget(self.live_confidence, alignment=Qt.AlignCenter)
        main_layout.addWidget(self.live_card)
        
        # -- Section 3: Classification Breakdown --
        self.breakdown_card = QFrame()
        self.breakdown_card.setStyleSheet("background-color: #1b1f24; border: 1px solid #242c36; border-radius: 12px;")
        breakdown_layout = QVBoxLayout(self.breakdown_card)
        
        bd_title = QLabel("CLASSIFICATION BREAKDOWN")
        bd_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #f4f7fb; margin-bottom: 10px;")
        breakdown_layout.addWidget(bd_title)
        
        self.class_bars = {}
        for cls in ["smooth", "pothole", "bump", "braking"]:
            row = QHBoxLayout()
            lbl = QLabel(cls.upper())
            lbl.setFixedWidth(80)
            lbl.setStyleSheet("font-size: 12px; font-weight: bold; color: #8e99a8;")
            
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(0)
            bar.setTextVisible(False)
            bar.setFixedHeight(12)
            bar.setStyleSheet(f"""
                QProgressBar {{
                    border: none;
                    background-color: #0f1318;
                    border-radius: 6px;
                }}
                QProgressBar::chunk {{
                    background-color: {self.colors[cls]};
                    border-radius: 6px;
                }}
            """)
            
            count_lbl = QLabel("0 (0%)")
            count_lbl.setFixedWidth(80)
            count_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            count_lbl.setStyleSheet("font-size: 12px; font-weight: bold; color: #f4f7fb;")
            
            row.addWidget(lbl)
            row.addWidget(bar)
            row.addWidget(count_lbl)
            breakdown_layout.addLayout(row)
            self.class_bars[cls] = {"bar": bar, "label": count_lbl}
            
        main_layout.addWidget(self.breakdown_card)
        
        # -- Section 4: Prediction History --
        self.history_card = QFrame()
        self.history_card.setStyleSheet("background-color: #1b1f24; border: 1px solid #242c36; border-radius: 12px;")
        self.history_card.setMinimumHeight(100)
        history_layout = QVBoxLayout(self.history_card)
        
        hist_title = QLabel("PREDICTION HISTORY (LAST 20)")
        hist_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #f4f7fb;")
        history_layout.addWidget(hist_title)
        
        self.history_strip = QFrame()
        self.history_strip_layout = QHBoxLayout(self.history_strip)
        self.history_strip_layout.setContentsMargins(0, 5, 0, 5)
        self.history_strip_layout.setSpacing(4)
        self.history_strip_layout.setAlignment(Qt.AlignLeft)
        history_layout.addWidget(self.history_strip)
        main_layout.addWidget(self.history_card)
        
        # -- Section 5: How It Works --
        self.info_card = QFrame()
        self.info_card.setStyleSheet("background-color: #1b1f24; border: 1px solid #242c36; border-radius: 12px;")
        info_layout = QVBoxLayout(self.info_card)
        
        info_title = QLabel("HOW IT WORKS")
        info_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #f4f7fb; margin-bottom: 5px;")
        info_layout.addWidget(info_title)
        
        info_text = QLabel(
            "The ML engine classifies road conditions in real time. Raw accelerometer\n"
            "readings (X, Y, Z) are buffered into 1-second windows of 50 samples.\n"
            "From each window, 24 statistical features are extracted (mean, std, min,\n"
            "max, range, RMS, energy, MAD for each axis). A trained Random Forest\n"
            "classifier then predicts the road condition: smooth, pothole, speed bump,\n"
            "or braking event."
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet("color: #8e99a8; font-size: 12px; line-height: 1.5;")
        info_layout.addWidget(info_text)
        main_layout.addWidget(self.info_card)
        
        main_layout.addStretch()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.start(500)
        self.update_data()
        
    def update_data(self):
        summary = self.ml_service.get_summary()
        
        # 1. Model Status
        is_loaded = summary.get("loaded", False)
        status_color = "#00d26a" if is_loaded else "#ff5555"
        status_text = "LOADED" if is_loaded else "NOT LOADED"
        self.status_title.setText(f"MODEL STATUS: {status_text}")
        self.status_title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {status_color};")
        
        field_mode = summary.get("field_mode", "unknown")
        
        self.status_details.setText(
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
            color = self.colors.get(pred, "grey")
            
            self.live_dot.setStyleSheet(f"background-color: {color}; border-radius: 30px;")
            self.live_prediction.setText(pred.upper())
            self.live_prediction.setStyleSheet(f"font-size: 32px; font-weight: bold; color: {color};")
            self.live_confidence.setValue(int(conf))
            
            self.live_confidence.setStyleSheet(
                f"""
                QProgressBar {{
                    border: 1px solid #242c36;
                    border-radius: 5px;
                    text-align: center;
                    background-color: #0f1318;
                    color: #f4f7fb;
                    font-weight: bold;
                    height: 20px;
                }}
                QProgressBar::chunk {{
                    background-color: {color};
                    border-radius: 5px;
                }}
                """
            )
        else:
            self.live_dot.setStyleSheet("background-color: grey; border-radius: 30px;")
            self.live_prediction.setText("WAITING FOR DATA")
            self.live_prediction.setStyleSheet("font-size: 32px; font-weight: bold; color: #8e99a8;")
            self.live_confidence.setValue(0)
            
        # 3. Breakdown
        total = summary.get("total_classified", 0)
        counts = summary.get("class_counts", {})
        for cls in ["smooth", "pothole", "bump", "braking"]:
            count = counts.get(cls, 0)
            pct = 0 if total == 0 else (count / total) * 100
            bar = self.class_bars[cls]["bar"]
            bar.setValue(int(pct))
            lbl = self.class_bars[cls]["label"]
            lbl.setText(f"{count} ({int(pct)}%)")
            
        # 4. History
        # Clear old history
        for i in reversed(range(self.history_strip_layout.count())):
            item = self.history_strip_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()
                
        history = list(self.ml_service.prediction_history)[-20:]
        for pred in history:
            color = self.colors.get(pred, "grey")
            box = QLabel()
            box.setFixedSize(20, 20)
            box.setStyleSheet(f"background-color: {color}; border-radius: 4px; border: 1px solid #0f1318;")
            # Tooltip can be added if needed
            self.history_strip_layout.addWidget(box)
        
        self.history_strip_layout.addStretch()
