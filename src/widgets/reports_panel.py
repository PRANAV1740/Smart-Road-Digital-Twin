from datetime import datetime
from pathlib import Path
from PySide6.QtCore import Qt, QRectF, QTimer, QPropertyAnimation
from PySide6.QtGui import QColor, QFont, QPageLayout, QPageSize, QPainter, QPdfWriter, QPen
from PySide6.QtWidgets import (
    QFileDialog, QGridLayout, QHBoxLayout, QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget, QFrame, QGraphicsDropShadowEffect
)
from database.database import (
    EXPORT_FOLDER, export_to_csv, get_all_potholes, get_statistics,
)
from utils.theme import ThemeManager

class HoverButton(QPushButton):
    def __init__(self, text):
        super().__init__(text)
        self.setCursor(Qt.PointingHandCursor)
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(0)
        self.shadow.setOffset(0, 0)
        self.setGraphicsEffect(self.shadow)
        
        self.anim = QPropertyAnimation(self.shadow, b"blurRadius")
        self.anim.setDuration(150)
        
    def enterEvent(self, event):
        self.anim.stop()
        self.anim.setEndValue(20)
        self.anim.start()
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        self.anim.stop()
        self.anim.setEndValue(0)
        self.anim.start()
        super().leaveEvent(event)

class ReportsPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(380)
        self.theme_manager = ThemeManager()
        self.value_labels = {}
        self.build_interface()
        
        self.theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme(self.theme_manager.get_current_theme(), self.theme_manager.is_dark)

        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_report)
        self.refresh_timer.start(2000)
        self.refresh_report()

    def build_interface(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        self.title_label = QLabel("REPORTS")
        self.title_label.setObjectName("panelTitle")
        self.title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.title_label)

        self.last_updated_label = QLabel("Last updated: --")
        self.last_updated_label.setObjectName("lastUpdated")
        self.last_updated_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.last_updated_label)

        statistics_layout = QGridLayout()
        statistics_layout.setHorizontalSpacing(10)
        statistics_layout.setVerticalSpacing(10)

        cards = [
            ("total", "TOTAL POTHOLES", 0, 0),
            ("high", "HIGH SEVERITY", 0, 1),
            ("medium", "MEDIUM SEVERITY", 1, 0),
            ("low", "LOW SEVERITY", 1, 1),
            ("average_depth", "AVERAGE DEPTH", 2, 0),
            ("maximum_depth", "MAXIMUM DEPTH", 2, 1),
            ("photos", "PHOTOS CAPTURED", 3, 0),
            ("latest_detection", "LATEST DETECTION", 3, 1),
        ]

        for key, title, row, col in cards:
            card = self.create_report_card(key, title)
            statistics_layout.addWidget(card, row, col)

        main_layout.addLayout(statistics_layout)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(16)

        self.csv_button = HoverButton("EXPORT CSV")
        self.csv_button.clicked.connect(self.export_csv_report)

        self.pdf_button = HoverButton("EXPORT PDF")
        self.pdf_button.clicked.connect(self.export_pdf_report)

        self.refresh_button = HoverButton("REFRESH")
        self.refresh_button.clicked.connect(self.refresh_report)

        button_layout.addWidget(self.csv_button)
        button_layout.addWidget(self.pdf_button)
        button_layout.addWidget(self.refresh_button)
        main_layout.addLayout(button_layout)
        main_layout.addStretch()

    def create_report_card(self, key, title):
        card = QFrame()
        card.setObjectName("reportCard")
        card.setMinimumHeight(55)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(10, 8, 10, 8)
        cl.setSpacing(4)
        
        tl = QLabel(title)
        tl.setAlignment(Qt.AlignCenter)
        vl = QLabel("0")
        vl.setAlignment(Qt.AlignCenter)
        
        cl.addWidget(tl)
        cl.addWidget(vl)
        self.value_labels[key] = {"widget": card, "title": tl, "val": vl}
        return card

    def apply_theme(self, theme, is_dark):
        self.theme = theme
        
        border = f"1px solid {theme['border']}" if is_dark else "none"
        shadow = "" if is_dark else "box-shadow: 0 1px 3px rgba(0,0,0,0.08);"
        
        self.title_label.setStyleSheet(f"color: {theme['text_primary']}; font-size: 16px; font-weight: bold; font-family: 'Segoe UI';")
        self.last_updated_label.setStyleSheet(f"color: {theme['text_secondary']}; font-size: 11px; padding: 2px;")
        
        for k, ui in self.value_labels.items():
            ui["widget"].setStyleSheet(f"""
                QFrame#reportCard {{
                    background-color: {theme['surface']};
                    border-radius: 12px;
                    border: {border};
                    {shadow}
                }}
            """)
            ui["title"].setStyleSheet(f"color: {theme['text_secondary']}; font-size: 11px; font-weight: bold; font-family: 'Segoe UI'; border: none;")
            ui["val"].setStyleSheet(f"color: {theme['text_primary']}; font-size: 18px; font-weight: bold; font-family: 'Segoe UI'; border: none;")

        btn_style = f"""
            QPushButton {{
                background-color: {theme['accent']};
                color: white;
                border: none;
                border-radius: 20px;
                padding: 12px 24px;
                font-size: 13px;
                font-weight: bold;
                font-family: 'Segoe UI';
            }}
            QPushButton:hover {{ background-color: {theme['accent']}cc; }}
        """
        self.csv_button.setStyleSheet(btn_style)
        self.csv_button.shadow.setColor(QColor(theme['accent']))
        
        self.refresh_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme['surface_elevated']};
                color: {theme['text_primary']};
                border: 1px solid {theme['border']};
                border-radius: 20px;
                padding: 12px 24px;
                font-size: 13px;
                font-weight: bold;
                font-family: 'Segoe UI';
            }}
            QPushButton:hover {{ background-color: {theme['surface']}; }}
        """)
        self.refresh_button.shadow.setColor(QColor(theme['border']))
        
        self.pdf_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme['danger']};
                color: white;
                border: none;
                border-radius: 20px;
                padding: 12px 24px;
                font-size: 13px;
                font-weight: bold;
                font-family: 'Segoe UI';
            }}
            QPushButton:hover {{ background-color: #dc2626; opacity: 0.9; }}
        """)
        self.pdf_button.shadow.setColor(QColor(theme['danger']))

    def refresh_report(self):
        try:
            statistics = get_statistics()
            records = get_all_potholes()

            self.value_labels["total"]["val"].setText(str(statistics["total"]))
            self.value_labels["high"]["val"].setText(str(statistics["high"]))
            self.value_labels["medium"]["val"].setText(str(statistics["medium"]))
            self.value_labels["low"]["val"].setText(str(statistics["low"]))
            self.value_labels["average_depth"]["val"].setText(f"{statistics['average_depth']:.2f} cm")
            self.value_labels["maximum_depth"]["val"].setText(f"{statistics['maximum_depth']:.2f} cm")
            self.value_labels["photos"]["val"].setText(str(statistics["photos"]))

            if records:
                latest_text = str(records[0].get("detected_at", "--"))
                if len(latest_text) >= 16: latest_text = latest_text[5:16]
                self.value_labels["latest_detection"]["val"].setText(latest_text)
            else:
                self.value_labels["latest_detection"]["val"].setText("--")

            self.last_updated_label.setText(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
        except Exception as error:
            self.last_updated_label.setText(f"Database error: {error}")

    def export_csv_report(self):
        try:
            export_path = export_to_csv()
            if export_path is None:
                QMessageBox.information(self, "No Data", "There are no stored potholes to export.")
                return
            QMessageBox.information(self, "CSV Export Successful", f"The CSV report was created.\n\n{export_path}")
        except Exception as error:
            QMessageBox.critical(self, "CSV Export Failed", str(error))

    def export_pdf_report(self):
        records = get_all_potholes()
        if not records:
            QMessageBox.information(self, "No Data", "There are no stored potholes to export.")
            return

        EXPORT_FOLDER.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_path = EXPORT_FOLDER / f"smart_road_report_{timestamp}.pdf"

        selected_path, _ = QFileDialog.getSaveFileName(self, "Save Smart Road PDF Report", str(default_path), "PDF Files (*.pdf)")
        if not selected_path: return
        if not selected_path.lower().endswith(".pdf"): selected_path += ".pdf"

        try:
            self.create_pdf(Path(selected_path))
            QMessageBox.information(self, "PDF Export Successful", f"The PDF report was created.\n\n{selected_path}")
        except Exception as error:
            QMessageBox.critical(self, "PDF Export Failed", str(error))

    def create_pdf(self, export_path):
        statistics = get_statistics()
        records = get_all_potholes()
        pdf_writer = QPdfWriter(str(export_path))
        pdf_writer.setPageSize(QPageSize(QPageSize.A4))
        pdf_writer.setPageOrientation(QPageLayout.Portrait)
        pdf_writer.setResolution(96)
        pdf_writer.setTitle("Smart Road Digital Twin Report")
        pdf_writer.setCreator("Smart Road Digital Twin")

        painter = QPainter(pdf_writer)
        if not painter.isActive(): raise RuntimeError("Unable to start PDF writer.")

        try:
            page_width, page_height = pdf_writer.width(), pdf_writer.height()
            margin = 55
            content_width = page_width - (margin * 2)
            y_position = margin

            title_font = QFont("Arial", 20, QFont.Bold)
            heading_font = QFont("Arial", 13, QFont.Bold)
            normal_font = QFont("Arial", 9)
            small_font = QFont("Arial", 8)

            painter.setPen(QColor("#111827"))
            # Depending on dark theme it might be better to output PDFs in light theme
            painter.setFont(title_font)
            painter.drawText(QRectF(margin, y_position, content_width, 35), Qt.AlignCenter, "SMART ROAD DIGITAL TWIN")
            y_position += 42

            painter.setFont(heading_font)
            painter.drawText(QRectF(margin, y_position, content_width, 25), Qt.AlignCenter, "Pothole Detection Report")
            y_position += 35

            generated_time = datetime.now().strftime("%d %B %Y, %I:%M:%S %p")
            painter.setFont(normal_font)
            painter.drawText(QRectF(margin, y_position, content_width, 20), Qt.AlignCenter, f"Generated on: {generated_time}")
            y_position += 35

            painter.setFont(heading_font)
            painter.drawText(margin, y_position, "Summary")
            y_position += 18

            items = [
                ("Total Potholes", statistics["total"]), ("High Severity", statistics["high"]),
                ("Medium Severity", statistics["medium"]), ("Low Severity", statistics["low"]),
                ("Average Depth", f"{statistics['average_depth']:.2f} cm"), ("Maximum Depth", f"{statistics['maximum_depth']:.2f} cm"),
                ("Photos Captured", statistics["photos"])
            ]

            painter.setFont(normal_font)
            for label, value in items:
                painter.drawText(margin + 10, y_position, f"{label}: {value}")
                y_position += 17
            y_position += 20

            painter.setFont(heading_font)
            painter.drawText(margin, y_position, "Detection Records")
            y_position += 18

            column_widths = [45, 58, 50, 65, 70, 120]
            headers = ["ID", "Depth", "X, Y", "Severity", "Photo", "Detected At"]
            row_height = 24

            self.draw_pdf_table_row(painter, margin, y_position, row_height, column_widths, headers, small_font, True, 0)
            y_position += row_height

            for i, record in enumerate(records):
                if y_position + row_height > page_height - margin:
                    pdf_writer.newPage()
                    y_position = margin
                    self.draw_pdf_table_row(painter, margin, y_position, row_height, column_widths, headers, small_font, True, 0)
                    y_position += row_height

                photo_text = "Yes" if record.get("photo_captured", 0) else "No"
                coords = f"{record.get('x', 0)}, {record.get('y', 0)}"
                values = [
                    str(record.get("pothole_id", "")), f"{float(record.get('depth', 0)):.1f}",
                    coords, str(record.get("severity", "")), photo_text, str(record.get("detected_at", ""))
                ]
                self.draw_pdf_table_row(painter, margin, y_position, row_height, column_widths, values, small_font, False, i+1)
                y_position += row_height

            y_position += 25
            if y_position > page_height - 80:
                pdf_writer.newPage()
                y_position = margin

            painter.setFont(normal_font)
            painter.setPen(QColor("#374151"))
            painter.drawText(QRectF(margin, y_position, content_width, 40), Qt.AlignCenter, "Generated by Smart Road Digital Twin")
        finally:
            painter.end()

    def draw_pdf_table_row(self, painter, x_position, y_position, row_height, column_widths, values, font, bold=False, row_idx=0):
        table_font = QFont(font)
        if bold: table_font.setBold(True)
        painter.setFont(table_font)

        current_x = x_position
        for index, width in enumerate(column_widths):
            cell_rectangle = QRectF(current_x, y_position, width, row_height)
            
            if row_idx % 2 == 1:
                painter.fillRect(cell_rectangle, QColor("#f3f4f6"))
                
            painter.setPen(QPen(QColor("#d1d5db"), 1))
            painter.drawRect(cell_rectangle)

            painter.setPen(QColor("#111827"))
            val = str(values[index]) if index < len(values) else ""
            painter.drawText(cell_rectangle.adjusted(4, 2, -4, -2), Qt.AlignCenter | Qt.TextWordWrap, val)
            current_x += width