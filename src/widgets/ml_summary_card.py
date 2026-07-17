from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget
)
from utils import data

class MLSummaryCard(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("mlSummaryCard")
        self.setStyleSheet(
            """
            QFrame#mlSummaryCard {
                background-color: #1b1f24;
                border: 1px solid #242c36;
                border-radius: 12px;
            }
            QLabel {
                color: #f4f7fb;
                font-family: "Segoe UI";
            }
            """
        )
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Left side: Prediction + Color dot
        self.prediction_layout = QHBoxLayout()
        self.color_dot = QLabel()
        self.color_dot.setFixedSize(16, 16)
        self.color_dot.setStyleSheet("background-color: grey; border-radius: 8px;")
        
        self.prediction_label = QLabel("Waiting...")
        self.prediction_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        
        self.prediction_layout.addWidget(self.color_dot)
        self.prediction_layout.addWidget(self.prediction_label)
        self.prediction_layout.addStretch()
        
        # Middle: Confidence
        self.confidence_layout = QVBoxLayout()
        self.confidence_title = QLabel("CONFIDENCE")
        self.confidence_title.setStyleSheet("font-size: 10px; color: #8e99a8; font-weight: bold;")
        self.confidence_value = QLabel("0%")
        self.confidence_value.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.confidence_layout.addWidget(self.confidence_title)
        self.confidence_layout.addWidget(self.confidence_value)
        self.confidence_layout.setAlignment(Qt.AlignCenter)
        
        # Right: Total classified and field mode
        self.stats_layout = QVBoxLayout()
        self.windows_label = QLabel("CLASSIFIED: 0")
        self.windows_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        self.mode_label = QLabel("MODE: unknown")
        self.mode_label.setStyleSheet("font-size: 10px; color: #8e99a8;")
        self.stats_layout.addWidget(self.windows_label)
        self.stats_layout.addWidget(self.mode_label)
        self.stats_layout.setAlignment(Qt.AlignRight)
        
        main_layout.addLayout(self.prediction_layout, 1)
        main_layout.addLayout(self.confidence_layout, 1)
        main_layout.addLayout(self.stats_layout, 1)
        
        # Overlay for inactive state
        self.inactive_label = QLabel("ML: Waiting for data...")
        self.inactive_label.setStyleSheet("color: #8e99a8; font-size: 14px; background: transparent;")
        self.inactive_label.setAlignment(Qt.AlignCenter)
        self.inactive_label.hide()
        
        self.colors = {
            "smooth": "#00d26a",
            "pothole": "#ff5555",
            "bump": "#ffd400",
            "braking": "#4f8cff"
        }
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.start(300)
        self.update_data()
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.inactive_label.setGeometry(0, 0, self.width(), self.height())
        
    def update_data(self):
        if not data.ml_active:
            # Hide children and show waiting text
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
            
            color = self.colors.get(pred, "grey")
            
            self.color_dot.setStyleSheet(f"background-color: {color}; border-radius: 8px;")
            self.prediction_label.setText(pred.upper())
            self.confidence_value.setText(f"{conf}%")
            self.windows_label.setText(f"CLASSIFIED: {data.ml_total_classified}")
            self.mode_label.setText(f"MODE: {data.ml_field_mode.upper()}")
            
    def _set_layout_visible(self, layout, visible):
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item.widget():
                item.widget().setVisible(visible)
            elif item.layout():
                self._set_layout_visible(item.layout(), visible)
