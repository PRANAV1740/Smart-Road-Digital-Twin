from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QMessageBox,
)
from PySide6.QtCore import QTimer, Qt

from database.database import (
    get_statistics,
    export_to_csv,
    clear_database,
)


class StatisticsPanel(QWidget):
    def __init__(self):
        super().__init__()

        self.setMinimumHeight(250)

        self.setStyleSheet(
            """
            QWidget {
                background:#1b1f24;
                border-radius:12px;
            }

            QLabel {
                color:white;
            }

            QPushButton {
                background:#2b2b2b;
                color:white;
                border:1px solid #555555;
                border-radius:8px;
                padding:8px;
                font-size:13px;
                font-weight:bold;
            }

            QPushButton:hover {
                background:#3a3f45;
            }
            """
        )

        layout = QVBoxLayout()
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        title = QLabel("ROAD STATISTICS")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            """
            font-size:20px;
            font-weight:bold;
            padding:8px;
            background:#2b2b2b;
            border-radius:10px;
            """
        )

        layout.addWidget(title)

        self.total_label = QLabel()
        self.high_label = QLabel()
        self.medium_label = QLabel()
        self.low_label = QLabel()
        self.average_depth_label = QLabel()
        self.maximum_depth_label = QLabel()

        labels = [
            self.total_label,
            self.high_label,
            self.medium_label,
            self.low_label,
            self.average_depth_label,
            self.maximum_depth_label,
        ]

        for label in labels:
            label.setStyleSheet(
                """
                background:#0b0f14;
                border:1px solid #3a3f45;
                border-radius:7px;
                padding:7px;
                font-size:14px;
                """
            )
            layout.addWidget(label)

        button_layout = QHBoxLayout()

        self.export_button = QPushButton("EXPORT CSV")
        self.clear_button = QPushButton("CLEAR DATABASE")

        self.export_button.clicked.connect(self.export_records)
        self.clear_button.clicked.connect(self.clear_records)

        button_layout.addWidget(self.export_button)
        button_layout.addWidget(self.clear_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_statistics)
        self.timer.start(1000)

        self.update_statistics()

    def update_statistics(self):
        statistics = get_statistics()

        self.total_label.setText(
            f"Total Potholes: {statistics['total']}"
        )

        self.high_label.setText(
            f"High Severity: {statistics['high']}"
        )

        self.medium_label.setText(
            f"Medium Severity: {statistics['medium']}"
        )

        self.low_label.setText(
            f"Low Severity: {statistics['low']}"
        )

        self.average_depth_label.setText(
            f"Average Depth: "
            f"{statistics['average_depth']} cm"
        )

        self.maximum_depth_label.setText(
            f"Maximum Depth: "
            f"{statistics['maximum_depth']} cm"
        )

    def export_records(self):
        try:
            export_path = export_to_csv()

            if export_path is None:
                QMessageBox.information(
                    self,
                    "Export CSV",
                    "Database is empty. Nothing to export.",
                )
                return

            QMessageBox.information(
                self,
                "Export Successful",
                f"CSV file saved at:\n\n{export_path}",
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Export Error",
                str(error),
            )

    def clear_records(self):
        answer = QMessageBox.question(
            self,
            "Clear Database",
            "Are you sure you want to delete all pothole records?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:
            return

        try:
            clear_database()
            self.update_statistics()

            QMessageBox.information(
                self,
                "Database Cleared",
                "All pothole records were deleted.",
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Database Error",
                str(error),
            )