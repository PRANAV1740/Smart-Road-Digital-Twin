# ==================================================
# SMART ROAD DIGITAL TWIN - REPORTS PANEL
# ==================================================

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import (
    Qt,
    QRectF,
    QTimer,
)
from PySide6.QtGui import (
    QColor,
    QFont,
    QPageLayout,
    QPageSize,
    QPainter,
    QPdfWriter,
    QPen,
)
from PySide6.QtWidgets import (
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from database.database import (
    EXPORT_FOLDER,
    export_to_csv,
    get_all_potholes,
    get_statistics,
)


class ReportsPanel(QWidget):
    """
    Displays a summary of stored pothole data and provides
    CSV and PDF report export controls.
    """

    def __init__(self):
        super().__init__()

        self.setMinimumHeight(460)

        self.setStyleSheet(
            """
            QWidget {
                background-color:#252525;
                color:white;
            }

            QLabel#panelTitle {
                color:#ffffff;
                font-size:20px;
                font-weight:bold;
                padding:6px;
            }

            QLabel#lastUpdated {
                color:#aaaaaa;
                font-size:11px;
                padding:2px;
            }

            QLabel#cardTitle {
                color:#bdbdbd;
                font-size:11px;
                font-weight:bold;
            }

            QLabel#cardValue {
                color:#ffffff;
                font-size:22px;
                font-weight:bold;
            }

            QWidget#reportCard {
                background-color:#303030;
                border:1px solid #444444;
                border-radius:8px;
            }

            QPushButton {
                background-color:#3b82f6;
                color:white;
                border:none;
                border-radius:6px;
                padding:10px 14px;
                font-size:12px;
                font-weight:bold;
            }

            QPushButton:hover {
                background-color:#2563eb;
            }

            QPushButton:pressed {
                background-color:#1d4ed8;
            }

            QPushButton#pdfButton {
                background-color:#dc2626;
            }

            QPushButton#pdfButton:hover {
                background-color:#b91c1c;
            }

            QPushButton#refreshButton {
                background-color:#4b5563;
            }

            QPushButton#refreshButton:hover {
                background-color:#374151;
            }
            """
        )

        self.value_labels = {}

        self.build_interface()

        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(
            self.refresh_report
        )
        self.refresh_timer.start(2000)

        self.refresh_report()

    def build_interface(self):
        """Create the Reports Panel user interface."""

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 12, 14, 14)
        main_layout.setSpacing(12)

        title_label = QLabel("REPORTS")
        title_label.setObjectName("panelTitle")
        title_label.setAlignment(Qt.AlignCenter)

        main_layout.addWidget(title_label)

        self.last_updated_label = QLabel(
            "Last updated: --"
        )
        self.last_updated_label.setObjectName(
            "lastUpdated"
        )
        self.last_updated_label.setAlignment(
            Qt.AlignCenter
        )

        main_layout.addWidget(
            self.last_updated_label
        )

        statistics_layout = QGridLayout()
        statistics_layout.setHorizontalSpacing(10)
        statistics_layout.setVerticalSpacing(10)

        cards = [
            (
                "total",
                "TOTAL POTHOLES",
                0,
                0,
            ),
            (
                "high",
                "HIGH SEVERITY",
                0,
                1,
            ),
            (
                "medium",
                "MEDIUM SEVERITY",
                1,
                0,
            ),
            (
                "low",
                "LOW SEVERITY",
                1,
                1,
            ),
            (
                "average_depth",
                "AVERAGE DEPTH",
                2,
                0,
            ),
            (
                "maximum_depth",
                "MAXIMUM DEPTH",
                2,
                1,
            ),
            (
                "photos",
                "PHOTOS CAPTURED",
                3,
                0,
            ),
            (
                "latest_detection",
                "LATEST DETECTION",
                3,
                1,
            ),
        ]

        for (
            key,
            title,
            row,
            column,
        ) in cards:
            card = self.create_report_card(
                key,
                title,
            )

            statistics_layout.addWidget(
                card,
                row,
                column,
            )

        main_layout.addLayout(
            statistics_layout
        )

        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)

        self.csv_button = QPushButton(
            "EXPORT CSV"
        )
        self.csv_button.clicked.connect(
            self.export_csv_report
        )

        self.pdf_button = QPushButton(
            "EXPORT PDF"
        )
        self.pdf_button.setObjectName(
            "pdfButton"
        )
        self.pdf_button.clicked.connect(
            self.export_pdf_report
        )

        self.refresh_button = QPushButton(
            "REFRESH"
        )
        self.refresh_button.setObjectName(
            "refreshButton"
        )
        self.refresh_button.clicked.connect(
            self.refresh_report
        )

        button_layout.addWidget(
            self.csv_button
        )
        button_layout.addWidget(
            self.pdf_button
        )
        button_layout.addWidget(
            self.refresh_button
        )

        main_layout.addLayout(button_layout)

    def create_report_card(
        self,
        key,
        title,
    ):
        """Create one statistics card."""

        card = QWidget()
        card.setObjectName("reportCard")
        card.setMinimumHeight(72)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(
            10,
            8,
            10,
            8,
        )
        card_layout.setSpacing(3)

        title_label = QLabel(title)
        title_label.setObjectName(
            "cardTitle"
        )
        title_label.setAlignment(
            Qt.AlignCenter
        )

        value_label = QLabel("0")
        value_label.setObjectName(
            "cardValue"
        )
        value_label.setAlignment(
            Qt.AlignCenter
        )

        card_layout.addWidget(title_label)
        card_layout.addWidget(value_label)

        self.value_labels[key] = value_label

        return card

    def refresh_report(self):
        """
        Refresh all report values using the SQLite
        database.
        """

        try:
            statistics = get_statistics()
            records = get_all_potholes()

            self.value_labels["total"].setText(
                str(statistics["total"])
            )

            self.value_labels["high"].setText(
                str(statistics["high"])
            )

            self.value_labels["medium"].setText(
                str(statistics["medium"])
            )

            self.value_labels["low"].setText(
                str(statistics["low"])
            )

            self.value_labels[
                "average_depth"
            ].setText(
                f"{statistics['average_depth']:.2f} cm"
            )

            self.value_labels[
                "maximum_depth"
            ].setText(
                f"{statistics['maximum_depth']:.2f} cm"
            )

            self.value_labels["photos"].setText(
                str(statistics["photos"])
            )

            if records:
                latest_record = records[0]

                latest_text = str(
                    latest_record.get(
                        "detected_at",
                        "--",
                    )
                )

                if len(latest_text) >= 16:
                    latest_text = latest_text[5:16]

                self.value_labels[
                    "latest_detection"
                ].setText(latest_text)

            else:
                self.value_labels[
                    "latest_detection"
                ].setText("--")

            current_time = datetime.now().strftime(
                "%H:%M:%S"
            )

            self.last_updated_label.setText(
                f"Last updated: {current_time}"
            )

        except Exception as error:
            self.last_updated_label.setText(
                f"Database error: {error}"
            )

    def export_csv_report(self):
        """Export stored pothole data to CSV."""

        try:
            export_path = export_to_csv()

            if export_path is None:
                QMessageBox.information(
                    self,
                    "No Data",
                    (
                        "There are no stored potholes "
                        "to export."
                    ),
                )
                return

            QMessageBox.information(
                self,
                "CSV Export Successful",
                (
                    "The CSV report was created "
                    "successfully.\n\n"
                    f"{export_path}"
                ),
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "CSV Export Failed",
                str(error),
            )

    def export_pdf_report(self):
        """Ask for a location and create a PDF report."""

        records = get_all_potholes()

        if not records:
            QMessageBox.information(
                self,
                "No Data",
                (
                    "There are no stored potholes "
                    "to export."
                ),
            )
            return

        EXPORT_FOLDER.mkdir(
            parents=True,
            exist_ok=True,
        )

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        default_path = (
            EXPORT_FOLDER
            / f"smart_road_report_{timestamp}.pdf"
        )

        selected_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Smart Road PDF Report",
            str(default_path),
            "PDF Files (*.pdf)",
        )

        if not selected_path:
            return

        if not selected_path.lower().endswith(
            ".pdf"
        ):
            selected_path += ".pdf"

        try:
            self.create_pdf(
                Path(selected_path)
            )

            QMessageBox.information(
                self,
                "PDF Export Successful",
                (
                    "The PDF report was created "
                    "successfully.\n\n"
                    f"{selected_path}"
                ),
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "PDF Export Failed",
                str(error),
            )

    def create_pdf(self, export_path):
        """Generate a formatted PDF report."""

        statistics = get_statistics()
        records = get_all_potholes()

        pdf_writer = QPdfWriter(
            str(export_path)
        )

        pdf_writer.setPageSize(
            QPageSize(
                QPageSize.A4
            )
        )

        pdf_writer.setPageOrientation(
            QPageLayout.Portrait
        )

        pdf_writer.setResolution(96)
        pdf_writer.setTitle(
            "Smart Road Digital Twin Report"
        )
        pdf_writer.setCreator(
            "Smart Road Digital Twin"
        )

        painter = QPainter(pdf_writer)

        if not painter.isActive():
            raise RuntimeError(
                "Unable to start PDF writer."
            )

        try:
            page_width = pdf_writer.width()
            page_height = pdf_writer.height()

            margin = 55
            content_width = (
                page_width - (margin * 2)
            )

            y_position = margin

            title_font = QFont(
                "Arial",
                20,
                QFont.Bold,
            )

            heading_font = QFont(
                "Arial",
                13,
                QFont.Bold,
            )

            normal_font = QFont(
                "Arial",
                9,
            )

            small_font = QFont(
                "Arial",
                8,
            )

            painter.setPen(
                QColor("#111827")
            )
            painter.setFont(title_font)

            painter.drawText(
                QRectF(
                    margin,
                    y_position,
                    content_width,
                    35,
                ),
                Qt.AlignCenter,
                "SMART ROAD DIGITAL TWIN",
            )

            y_position += 42

            painter.setFont(heading_font)
            painter.drawText(
                QRectF(
                    margin,
                    y_position,
                    content_width,
                    25,
                ),
                Qt.AlignCenter,
                "Pothole Detection Report",
            )

            y_position += 35

            generated_time = (
                datetime.now().strftime(
                    "%d %B %Y, %I:%M:%S %p"
                )
            )

            painter.setFont(normal_font)
            painter.drawText(
                QRectF(
                    margin,
                    y_position,
                    content_width,
                    20,
                ),
                Qt.AlignCenter,
                (
                    "Generated on: "
                    f"{generated_time}"
                ),
            )

            y_position += 35

            painter.setFont(heading_font)
            painter.drawText(
                margin,
                y_position,
                "Summary",
            )

            y_position += 18

            summary_items = [
                (
                    "Total Potholes",
                    statistics["total"],
                ),
                (
                    "High Severity",
                    statistics["high"],
                ),
                (
                    "Medium Severity",
                    statistics["medium"],
                ),
                (
                    "Low Severity",
                    statistics["low"],
                ),
                (
                    "Average Depth",
                    (
                        f"{statistics['average_depth']:.2f} cm"
                    ),
                ),
                (
                    "Maximum Depth",
                    (
                        f"{statistics['maximum_depth']:.2f} cm"
                    ),
                ),
                (
                    "Photos Captured",
                    statistics["photos"],
                ),
            ]

            painter.setFont(normal_font)

            for label, value in summary_items:
                painter.drawText(
                    margin + 10,
                    y_position,
                    f"{label}: {value}",
                )
                y_position += 17

            y_position += 15

            painter.setFont(heading_font)
            painter.drawText(
                margin,
                y_position,
                "Detection Records",
            )

            y_position += 18

            column_widths = [
                45,
                58,
                50,
                65,
                70,
                120,
            ]

            headers = [
                "ID",
                "Depth",
                "X, Y",
                "Severity",
                "Photo",
                "Detected At",
            ]

            row_height = 24

            self.draw_pdf_table_row(
                painter=painter,
                x_position=margin,
                y_position=y_position,
                row_height=row_height,
                column_widths=column_widths,
                values=headers,
                font=small_font,
                bold=True,
            )

            y_position += row_height

            for record in records:
                if (
                    y_position + row_height
                    > page_height - margin
                ):
                    pdf_writer.newPage()
                    y_position = margin

                    self.draw_pdf_table_row(
                        painter=painter,
                        x_position=margin,
                        y_position=y_position,
                        row_height=row_height,
                        column_widths=column_widths,
                        values=headers,
                        font=small_font,
                        bold=True,
                    )

                    y_position += row_height

                photo_text = (
                    "Yes"
                    if record.get(
                        "photo_captured",
                        0,
                    )
                    else "No"
                )

                coordinates = (
                    f"{record.get('x', 0)}, "
                    f"{record.get('y', 0)}"
                )

                values = [
                    str(
                        record.get(
                            "pothole_id",
                            "",
                        )
                    ),
                    (
                        f"{float(record.get('depth', 0)):.1f}"
                    ),
                    coordinates,
                    str(
                        record.get(
                            "severity",
                            "",
                        )
                    ),
                    photo_text,
                    str(
                        record.get(
                            "detected_at",
                            "",
                        )
                    ),
                ]

                self.draw_pdf_table_row(
                    painter=painter,
                    x_position=margin,
                    y_position=y_position,
                    row_height=row_height,
                    column_widths=column_widths,
                    values=values,
                    font=small_font,
                    bold=False,
                )

                y_position += row_height

            y_position += 25

            if y_position > page_height - 80:
                pdf_writer.newPage()
                y_position = margin

            painter.setFont(normal_font)
            painter.setPen(
                QColor("#374151")
            )

            painter.drawText(
                QRectF(
                    margin,
                    y_position,
                    content_width,
                    40,
                ),
                Qt.AlignCenter,
                (
                    "Generated by Smart Road "
                    "Digital Twin Monitoring System"
                ),
            )

        finally:
            painter.end()

    def draw_pdf_table_row(
        self,
        painter,
        x_position,
        y_position,
        row_height,
        column_widths,
        values,
        font,
        bold=False,
    ):
        """Draw one table row inside the PDF."""

        if bold:
            table_font = QFont(font)
            table_font.setBold(True)
        else:
            table_font = font

        painter.setFont(table_font)

        current_x = x_position

        for index, width in enumerate(
            column_widths
        ):
            cell_rectangle = QRectF(
                current_x,
                y_position,
                width,
                row_height,
            )

            painter.setPen(
                QPen(
                    QColor("#6b7280"),
                    1,
                )
            )

            painter.drawRect(
                cell_rectangle
            )

            painter.setPen(
                QColor("#111827")
            )

            value = ""

            if index < len(values):
                value = str(values[index])

            painter.drawText(
                cell_rectangle.adjusted(
                    4,
                    2,
                    -4,
                    -2,
                ),
                (
                    Qt.AlignCenter
                    | Qt.TextWordWrap
                ),
                value,
            )

            current_x += width