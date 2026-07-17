from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar
from PySide6.QtCore import Qt, QTimer

from utils import data


class SensorPanel(QWidget):
    def __init__(self):
        super().__init__()

        self.setMinimumHeight(260)

        self.setStyleSheet("""
            QWidget {
                background:#1b1f24;
                border-radius:12px;
            }
            QLabel {
                color:white;
            }
            QProgressBar {
                background:#2b2b2b;
                border:none;
                border-radius:7px;
                height:12px;
                text-align:center;
                color:white;
                font-size:10px;
                font-weight:bold;
            }
            QProgressBar::chunk {
                background:#00d26a;
                border-radius:7px;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(5)

        title = QLabel("SENSOR PANEL")
        title.setAlignment(Qt.AlignCenter)
        title.setFixedHeight(36)
        title.setStyleSheet("""
            font-size:20px;
            font-weight:bold;
            padding:4px;
            background:#2b2b2b;
            border-radius:10px;
        """)

        self.warning_label = QLabel()
        self.road_status = QLabel()

        self.distance_label = QLabel()
        self.distance_bar = QProgressBar()

        self.speed_label = QLabel()
        self.speed_bar = QProgressBar()

        self.depth_label = QLabel()
        self.depth_bar = QProgressBar()

        self.jerk_label = QLabel()
        self.jerk_bar = QProgressBar()

        self.gps_label = QLabel()
        self.photos_label = QLabel()
        self.detected_label = QLabel()

        # ----- Machine Learning display -----
        # ml_label      : the model's verdict + how confident it is
        # ml_info_label : which fields it is reading and how many
        #                 windows it has classified so far
        self.ml_label = QLabel()
        self.ml_label.setAlignment(Qt.AlignCenter)

        self.ml_info_label = QLabel()
        self.ml_info_label.setStyleSheet(
            "color:#8e99a8; font-size:10px; padding:2px;"
        )

        layout.addWidget(title)
        layout.addWidget(self.ml_label)
        layout.addWidget(self.ml_info_label)
        layout.addWidget(self.warning_label)
        layout.addWidget(self.road_status)

        layout.addWidget(self.distance_label)
        layout.addWidget(self.distance_bar)

        layout.addWidget(self.speed_label)
        layout.addWidget(self.speed_bar)

        layout.addWidget(self.depth_label)
        layout.addWidget(self.depth_bar)

        layout.addWidget(self.jerk_label)
        layout.addWidget(self.jerk_bar)

        layout.addWidget(self.gps_label)
        layout.addWidget(self.photos_label)
        layout.addWidget(self.detected_label)

        self.setLayout(layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_values)
        self.timer.start(200)

        self.update_values()

    def update_values(self):
        self.warning_label.setText(f"WARNING LEVEL: {data.warning_level}")
        self.road_status.setText(f"ROAD STATUS: {data.road_status}")

        self.distance_label.setText(f"ULTRASONIC DISTANCE: {data.distance} cm")
        self.speed_label.setText(f"SPEED: {data.speed} km/h")
        self.depth_label.setText(f"DEPTH: {data.depth} cm")
        self.jerk_label.setText(f"JERK: {data.jerk} g")
        self.gps_label.setText(f"GPS: {data.gps}")
        self.photos_label.setText(f"PHOTOS CAPTURED: {data.photos}")
        self.detected_label.setText(
            f"POTHOLES DETECTED: {data.total_potholes_detected}"
        )

        self.distance_bar.setMaximum(130)
        self.distance_bar.setValue(min(data.distance, 130))

        self.speed_bar.setMaximum(100)
        self.speed_bar.setValue(data.speed)

        self.depth_bar.setMaximum(15)
        self.depth_bar.setValue(data.depth)

        self.jerk_bar.setMaximum(5)
        self.jerk_bar.setValue(int(data.jerk))

        if data.warning_level == "DANGER":
            self.warning_label.setStyleSheet("""
                color:#ff5555;
                font-size:15px;
                font-weight:bold;
                padding:5px;
                background:#331111;
                border-radius:8px;
            """)
        elif data.warning_level == "CAUTION":
            self.warning_label.setStyleSheet("""
                color:#ffd400;
                font-size:15px;
                font-weight:bold;
                padding:5px;
                background:#443700;
                border-radius:8px;
            """)
        else:
            self.warning_label.setStyleSheet("""
                color:#00d26a;
                font-size:15px;
                font-weight:bold;
                padding:5px;
                background:#112b1d;
                border-radius:8px;
            """)

        self.road_status.setStyleSheet("""
            color:#ffffff;
            font-size:14px;
            font-weight:bold;
            padding:4px;
            background:#2b2b2b;
            border-radius:8px;
        """)

        self.update_ml_display()

    # ==================================================
    # MACHINE LEARNING DISPLAY
    # ==================================================

    def update_ml_display(self):
        """
        Show what the ML model currently thinks the road is.

        This reads data.ml_prediction / data.ml_confidence, which are
        written by services/ml_service.py every time it classifies a
        window of ~50 sensor readings (about once per second).
        """

        # ----- Model not running -----
        if not data.ml_active:
            self.ml_label.setText("ML: WAITING FOR DATA")
            self.ml_label.setStyleSheet("""
                color:#8e99a8;
                font-size:14px;
                font-weight:bold;
                padding:6px;
                background:#20262e;
                border-radius:8px;
            """)
            self.ml_info_label.setText(
                "Model idle - no windows classified yet"
            )
            return

        # ----- Model running: show the verdict -----
        prediction = data.ml_prediction.upper()
        confidence = data.ml_confidence

        self.ml_label.setText(f"ML: {prediction}  ({confidence}%)")

        colours = {
            "pothole": ("#ff5555", "#331111"),
            "bump":    ("#ffd400", "#443700"),
            "braking": ("#4f8cff", "#182840"),
            "smooth":  ("#00d26a", "#112b1d"),
        }

        text_colour, background_colour = colours.get(
            data.ml_prediction,
            ("#ffffff", "#2b2b2b"),
        )

        self.ml_label.setStyleSheet(f"""
            color:{text_colour};
            font-size:15px;
            font-weight:bold;
            padding:6px;
            background:{background_colour};
            border-radius:8px;
        """)

        # ----- Supporting info -----
        field_mode = data.ml_field_mode

        if field_mode == "raw":
            source_text = "raw ax/ay/az"
        elif field_mode == "processed":
            source_text = "jerk/pitch/roll (reduced accuracy)"
        else:
            source_text = "unknown"

        self.ml_info_label.setText(
            f"Windows classified: {data.ml_total_classified}"
            f"   |   Input: {source_text}"
        )