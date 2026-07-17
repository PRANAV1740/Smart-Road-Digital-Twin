from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt, QTimer

from utils import data


class AlertPanel(QWidget):
    def __init__(self):
        super().__init__()

        self.blink = False

        self.setFixedHeight(75)

        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)

        self.alert_label = QLabel()
        self.alert_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.alert_label)

        self.setLayout(layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_alert)
        self.timer.start(300)

        self.update_alert()

    def update_alert(self):
        self.blink = not self.blink

        # ==========================
        # SAFE
        # ==========================
        if data.warning_level == "SAFE":

            self.alert_label.setText("🟢 ROAD CLEAR")

            self.alert_label.setStyleSheet("""
                QLabel{
                    background:#12351f;
                    color:#00ff80;
                    font-size:18px;
                    font-weight:bold;
                    border-radius:10px;
                    padding:10px;
                }
            """)

        # ==========================
        # CAUTION
        # ==========================
        elif data.warning_level == "CAUTION":

            bg = "#665200" if self.blink else "#443700"

            self.alert_label.setText(
                f"🟡 POTHOLE AHEAD   |   Distance : {data.distance} cm"
            )

            self.alert_label.setStyleSheet(f"""
                QLabel{{
                    background:{bg};
                    color:#ffd400;
                    font-size:18px;
                    font-weight:bold;
                    border-radius:10px;
                    padding:10px;
                }}
            """)

        # ==========================
        # DANGER
        # ==========================
        elif data.warning_level == "DANGER":

            bg = "#661111" if self.blink else "#441111"

            self.alert_label.setText(
                f"🔴 POTHOLE DETECTED   |   Depth : {data.depth} cm"
            )

            self.alert_label.setStyleSheet(f"""
                QLabel{{
                    background:{bg};
                    color:#ff5555;
                    font-size:18px;
                    font-weight:bold;
                    border-radius:10px;
                    padding:10px;
                }}
            """)