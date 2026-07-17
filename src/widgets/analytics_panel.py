# ==================================================
# SMART ROAD DIGITAL TWIN - ANALYTICS PANEL
# ==================================================

from collections import Counter
from datetime import datetime, timedelta
import math

from PySide6.QtCore import (
    Qt,
    QRectF,
    QPointF,
    QTimer,
)
from PySide6.QtGui import (
    QColor,
    QFont,
    QPainter,
    QPen,
)
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from database.database import (
    get_all_potholes,
    get_statistics,
)


# ==================================================
# SEVERITY BAR CHART
# ==================================================

class SeverityBarChart(QWidget):
    """Display High, Medium and Low pothole counts."""

    def __init__(self):
        super().__init__()

        self.values = {
            "HIGH": 0,
            "MEDIUM": 0,
            "LOW": 0,
        }

        self.setMinimumHeight(280)

    def set_values(
        self,
        high,
        medium,
        low,
    ):
        self.values = {
            "HIGH": high,
            "MEDIUM": medium,
            "LOW": low,
        }

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(
            QPainter.Antialiasing
        )

        painter.fillRect(
            self.rect(),
            QColor("#252525"),
        )

        width = self.width()
        height = self.height()

        margin_left = 55
        margin_right = 25
        margin_top = 45
        margin_bottom = 50

        chart_width = (
            width
            - margin_left
            - margin_right
        )

        chart_height = (
            height
            - margin_top
            - margin_bottom
        )

        painter.setPen(
            QColor("#ffffff")
        )

        painter.setFont(
            QFont(
                "Arial",
                12,
                QFont.Bold,
            )
        )

        painter.drawText(
            QRectF(
                0,
                8,
                width,
                25,
            ),
            Qt.AlignCenter,
            "SEVERITY DISTRIBUTION",
        )

        axis_pen = QPen(
            QColor("#777777"),
            1,
        )

        painter.setPen(axis_pen)

        painter.drawLine(
            margin_left,
            margin_top,
            margin_left,
            margin_top + chart_height,
        )

        painter.drawLine(
            margin_left,
            margin_top + chart_height,
            margin_left + chart_width,
            margin_top + chart_height,
        )

        maximum_value = max(
            self.values.values()
        )

        if maximum_value <= 0:
            maximum_value = 1

        categories = [
            (
                "HIGH",
                QColor("#ef4444"),
            ),
            (
                "MEDIUM",
                QColor("#f59e0b"),
            ),
            (
                "LOW",
                QColor("#22c55e"),
            ),
        ]

        available_width = (
            chart_width / len(categories)
        )

        bar_width = min(
            75,
            available_width * 0.48,
        )

        for index, (
            label,
            color,
        ) in enumerate(categories):

            value = self.values[label]

            bar_height = (
                value
                / maximum_value
                * (chart_height - 25)
            )

            center_x = (
                margin_left
                + available_width
                * index
                + available_width / 2
            )

            bar_x = (
                center_x
                - bar_width / 2
            )

            bar_y = (
                margin_top
                + chart_height
                - bar_height
            )

            bar_rectangle = QRectF(
                bar_x,
                bar_y,
                bar_width,
                bar_height,
            )

            painter.setPen(
                Qt.NoPen
            )
            painter.setBrush(color)

            painter.drawRoundedRect(
                bar_rectangle,
                6,
                6,
            )

            painter.setPen(
                QColor("#ffffff")
            )

            painter.setFont(
                QFont(
                    "Arial",
                    11,
                    QFont.Bold,
                )
            )

            painter.drawText(
                QRectF(
                    bar_x,
                    max(
                        margin_top,
                        bar_y - 25,
                    ),
                    bar_width,
                    22,
                ),
                Qt.AlignCenter,
                str(value),
            )

            painter.setFont(
                QFont(
                    "Arial",
                    9,
                    QFont.Bold,
                )
            )

            painter.drawText(
                QRectF(
                    center_x
                    - available_width / 2,
                    margin_top
                    + chart_height
                    + 8,
                    available_width,
                    25,
                ),
                Qt.AlignCenter,
                label,
            )


# ==================================================
# SEVERITY PIE CHART
# ==================================================

class SeverityPieChart(QWidget):
    """Display severity percentages in a pie chart."""

    def __init__(self):
        super().__init__()

        self.values = {
            "HIGH": 0,
            "MEDIUM": 0,
            "LOW": 0,
        }

        self.setMinimumHeight(280)

    def set_values(
        self,
        high,
        medium,
        low,
    ):
        self.values = {
            "HIGH": high,
            "MEDIUM": medium,
            "LOW": low,
        }

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(
            QPainter.Antialiasing
        )

        painter.fillRect(
            self.rect(),
            QColor("#252525"),
        )

        width = self.width()
        height = self.height()

        painter.setPen(
            QColor("#ffffff")
        )

        painter.setFont(
            QFont(
                "Arial",
                12,
                QFont.Bold,
            )
        )

        painter.drawText(
            QRectF(
                0,
                8,
                width,
                25,
            ),
            Qt.AlignCenter,
            "SEVERITY PERCENTAGE",
        )

        total = sum(
            self.values.values()
        )

        chart_size = min(
            width * 0.52,
            height - 80,
        )

        chart_rectangle = QRectF(
            28,
            48,
            chart_size,
            chart_size,
        )

        colors = {
            "HIGH": QColor("#ef4444"),
            "MEDIUM": QColor("#f59e0b"),
            "LOW": QColor("#22c55e"),
        }

        if total <= 0:
            painter.setPen(
                QPen(
                    QColor("#555555"),
                    2,
                )
            )

            painter.setBrush(
                QColor("#303030")
            )

            painter.drawEllipse(
                chart_rectangle
            )

            painter.setPen(
                QColor("#aaaaaa")
            )

            painter.setFont(
                QFont(
                    "Arial",
                    10,
                )
            )

            painter.drawText(
                chart_rectangle,
                Qt.AlignCenter,
                "NO DATA",
            )

        else:
            start_angle = 90 * 16

            for label in [
                "HIGH",
                "MEDIUM",
                "LOW",
            ]:
                value = self.values[label]

                if value <= 0:
                    continue

                angle = int(
                    value
                    / total
                    * 360
                    * 16
                )

                painter.setPen(
                    QPen(
                        QColor("#252525"),
                        2,
                    )
                )

                painter.setBrush(
                    colors[label]
                )

                painter.drawPie(
                    chart_rectangle,
                    start_angle,
                    -angle,
                )

                start_angle -= angle

            inner_size = chart_size * 0.48

            inner_rectangle = QRectF(
                chart_rectangle.center().x()
                - inner_size / 2,
                chart_rectangle.center().y()
                - inner_size / 2,
                inner_size,
                inner_size,
            )

            painter.setPen(
                Qt.NoPen
            )

            painter.setBrush(
                QColor("#252525")
            )

            painter.drawEllipse(
                inner_rectangle
            )

            painter.setPen(
                QColor("#ffffff")
            )

            painter.setFont(
                QFont(
                    "Arial",
                    17,
                    QFont.Bold,
                )
            )

            painter.drawText(
                inner_rectangle,
                Qt.AlignCenter,
                str(total),
            )

        legend_x = (
            chart_rectangle.right()
            + 30
        )

        legend_y = 70

        for label in [
            "HIGH",
            "MEDIUM",
            "LOW",
        ]:
            value = self.values[label]

            percentage = (
                value / total * 100
                if total > 0
                else 0
            )

            painter.setPen(
                Qt.NoPen
            )

            painter.setBrush(
                colors[label]
            )

            painter.drawRoundedRect(
                QRectF(
                    legend_x,
                    legend_y,
                    16,
                    16,
                ),
                3,
                3,
            )

            painter.setPen(
                QColor("#ffffff")
            )

            painter.setFont(
                QFont(
                    "Arial",
                    9,
                    QFont.Bold,
                )
            )

            painter.drawText(
                QRectF(
                    legend_x + 25,
                    legend_y - 4,
                    max(
                        100,
                        width - legend_x - 30,
                    ),
                    25,
                ),
                Qt.AlignLeft
                | Qt.AlignVCenter,
                (
                    f"{label}: "
                    f"{value} "
                    f"({percentage:.1f}%)"
                ),
            )

            legend_y += 45


# ==================================================
# DETECTION TIMELINE CHART
# ==================================================

class DetectionTimelineChart(QWidget):
    """Display daily pothole detections for the last seven days."""

    def __init__(self):
        super().__init__()

        self.labels = []
        self.values = []

        self.setMinimumHeight(320)

    def set_records(self, records):
        today = datetime.now().date()

        dates = [
            today - timedelta(days=offset)
            for offset in range(6, -1, -1)
        ]

        daily_counts = Counter()

        for record in records:
            detected_at = str(
                record.get(
                    "detected_at",
                    "",
                )
            )

            try:
                detected_date = (
                    datetime.strptime(
                        detected_at,
                        "%Y-%m-%d %H:%M:%S",
                    ).date()
                )

                daily_counts[
                    detected_date
                ] += 1

            except ValueError:
                continue

        self.labels = [
            date.strftime("%d %b")
            for date in dates
        ]

        self.values = [
            daily_counts[date]
            for date in dates
        ]

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(
            QPainter.Antialiasing
        )

        painter.fillRect(
            self.rect(),
            QColor("#252525"),
        )

        width = self.width()
        height = self.height()

        margin_left = 60
        margin_right = 30
        margin_top = 55
        margin_bottom = 55

        chart_width = (
            width
            - margin_left
            - margin_right
        )

        chart_height = (
            height
            - margin_top
            - margin_bottom
        )

        painter.setPen(
            QColor("#ffffff")
        )

        painter.setFont(
            QFont(
                "Arial",
                12,
                QFont.Bold,
            )
        )

        painter.drawText(
            QRectF(
                0,
                8,
                width,
                25,
            ),
            Qt.AlignCenter,
            "LAST 7 DAYS DETECTION TREND",
        )

        painter.setPen(
            QPen(
                QColor("#444444"),
                1,
            )
        )

        horizontal_lines = 4

        for line_index in range(
            horizontal_lines + 1
        ):
            line_y = (
                margin_top
                + chart_height
                * line_index
                / horizontal_lines
            )

            painter.drawLine(
                margin_left,
                int(line_y),
                margin_left + chart_width,
                int(line_y),
            )

        if not self.values:
            return

        maximum_value = max(
            self.values
        )

        if maximum_value <= 0:
            maximum_value = 1

        point_spacing = (
            chart_width
            / max(
                1,
                len(self.values) - 1,
            )
        )

        points = []

        for index, value in enumerate(
            self.values
        ):
            point_x = (
                margin_left
                + index * point_spacing
            )

            point_y = (
                margin_top
                + chart_height
                - (
                    value
                    / maximum_value
                    * (chart_height - 15)
                )
            )

            points.append(
                QPointF(
                    point_x,
                    point_y,
                )
            )

        line_pen = QPen(
            QColor("#38bdf8"),
            3,
        )

        painter.setPen(line_pen)

        for index in range(
            len(points) - 1
        ):
            painter.drawLine(
                points[index],
                points[index + 1],
            )

        for index, point in enumerate(
            points
        ):
            painter.setPen(
                QPen(
                    QColor("#ffffff"),
                    2,
                )
            )

            painter.setBrush(
                QColor("#0ea5e9")
            )

            painter.drawEllipse(
                point,
                6,
                6,
            )

            painter.setPen(
                QColor("#ffffff")
            )

            painter.setFont(
                QFont(
                    "Arial",
                    9,
                    QFont.Bold,
                )
            )

            painter.drawText(
                QRectF(
                    point.x() - 20,
                    point.y() - 28,
                    40,
                    20,
                ),
                Qt.AlignCenter,
                str(self.values[index]),
            )

            painter.setFont(
                QFont(
                    "Arial",
                    8,
                )
            )

            painter.drawText(
                QRectF(
                    point.x() - 38,
                    margin_top
                    + chart_height
                    + 10,
                    76,
                    25,
                ),
                Qt.AlignCenter,
                self.labels[index],
            )


# ==================================================
# MAIN ANALYTICS PANEL
# ==================================================

class AnalyticsPanel(QWidget):
    """
    Dedicated analytics page showing database-driven
    pothole charts and summary information.
    """

    def __init__(self):
        super().__init__()

        self.setStyleSheet(
            """
            QWidget {
                background-color:#1e1e1e;
                color:white;
            }

            QLabel#analyticsTitle {
                font-size:28px;
                font-weight:bold;
                color:#ffffff;
                padding:8px;
            }

            QLabel#analyticsSubtitle {
                font-size:12px;
                color:#a3a3a3;
                padding-bottom:8px;
            }

            QWidget#summaryCard {
                background-color:#292929;
                border:1px solid #414141;
                border-radius:10px;
            }

            QLabel#summaryTitle {
                color:#bdbdbd;
                font-size:11px;
                font-weight:bold;
            }

            QLabel#summaryValue {
                color:#ffffff;
                font-size:22px;
                font-weight:bold;
            }

            QPushButton {
                background-color:#3b82f6;
                color:white;
                border:none;
                border-radius:6px;
                padding:10px 22px;
                font-size:12px;
                font-weight:bold;
            }

            QPushButton:hover {
                background-color:#2563eb;
            }

            QPushButton:pressed {
                background-color:#1d4ed8;
            }
            """
        )

        self.summary_labels = {}

        self.build_interface()

        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(
            self.refresh_analytics
        )
        self.refresh_timer.start(2000)

        self.refresh_analytics()

    def build_interface(self):
        main_layout = QVBoxLayout(self)

        main_layout.setContentsMargins(
            18,
            12,
            18,
            18,
        )

        main_layout.setSpacing(14)

        title_label = QLabel(
            "ROAD ANALYTICS"
        )
        title_label.setObjectName(
            "analyticsTitle"
        )
        title_label.setAlignment(
            Qt.AlignCenter
        )

        subtitle_label = QLabel(
            (
                "Database-driven pothole severity, "
                "depth and detection trends"
            )
        )
        subtitle_label.setObjectName(
            "analyticsSubtitle"
        )
        subtitle_label.setAlignment(
            Qt.AlignCenter
        )

        main_layout.addWidget(
            title_label
        )
        main_layout.addWidget(
            subtitle_label
        )

        summary_layout = QHBoxLayout()
        summary_layout.setSpacing(12)

        summary_items = [
            (
                "total",
                "TOTAL POTHOLES",
            ),
            (
                "average",
                "AVERAGE DEPTH",
            ),
            (
                "maximum",
                "MAXIMUM DEPTH",
            ),
            (
                "critical",
                "HIGH SEVERITY",
            ),
        ]

        for key, title in summary_items:
            card = self.create_summary_card(
                key,
                title,
            )

            summary_layout.addWidget(
                card
            )

        main_layout.addLayout(
            summary_layout
        )

        charts_layout = QGridLayout()
        charts_layout.setSpacing(14)

        self.bar_chart = SeverityBarChart()
        self.pie_chart = SeverityPieChart()
        self.timeline_chart = (
            DetectionTimelineChart()
        )

        charts_layout.addWidget(
            self.bar_chart,
            0,
            0,
        )

        charts_layout.addWidget(
            self.pie_chart,
            0,
            1,
        )

        charts_layout.addWidget(
            self.timeline_chart,
            1,
            0,
            1,
            2,
        )

        charts_layout.setColumnStretch(
            0,
            1,
        )

        charts_layout.setColumnStretch(
            1,
            1,
        )

        main_layout.addLayout(
            charts_layout
        )

        bottom_layout = QHBoxLayout()

        self.last_updated_label = QLabel(
            "Last updated: --"
        )

        self.last_updated_label.setStyleSheet(
            """
            color:#a3a3a3;
            font-size:11px;
            """
        )

        self.refresh_button = QPushButton(
            "REFRESH ANALYTICS"
        )

        self.refresh_button.clicked.connect(
            self.refresh_analytics
        )

        bottom_layout.addWidget(
            self.last_updated_label
        )

        bottom_layout.addStretch()

        bottom_layout.addWidget(
            self.refresh_button
        )

        main_layout.addLayout(
            bottom_layout
        )

    def create_summary_card(
        self,
        key,
        title,
    ):
        card = QWidget()
        card.setObjectName(
            "summaryCard"
        )

        card.setMinimumHeight(85)

        card_layout = QVBoxLayout(card)

        card_layout.setContentsMargins(
            12,
            10,
            12,
            10,
        )

        title_label = QLabel(title)
        title_label.setObjectName(
            "summaryTitle"
        )
        title_label.setAlignment(
            Qt.AlignCenter
        )

        value_label = QLabel("0")
        value_label.setObjectName(
            "summaryValue"
        )
        value_label.setAlignment(
            Qt.AlignCenter
        )

        card_layout.addWidget(
            title_label
        )

        card_layout.addWidget(
            value_label
        )

        self.summary_labels[
            key
        ] = value_label

        return card

    def refresh_analytics(self):
        """Reload all analytics from the database."""

        try:
            statistics = get_statistics()
            records = get_all_potholes()

            self.summary_labels[
                "total"
            ].setText(
                str(statistics["total"])
            )

            self.summary_labels[
                "average"
            ].setText(
                (
                    f"{statistics['average_depth']:.2f} cm"
                )
            )

            self.summary_labels[
                "maximum"
            ].setText(
                (
                    f"{statistics['maximum_depth']:.2f} cm"
                )
            )

            self.summary_labels[
                "critical"
            ].setText(
                str(statistics["high"])
            )

            self.bar_chart.set_values(
                statistics["high"],
                statistics["medium"],
                statistics["low"],
            )

            self.pie_chart.set_values(
                statistics["high"],
                statistics["medium"],
                statistics["low"],
            )

            self.timeline_chart.set_records(
                records
            )

            current_time = datetime.now().strftime(
                "%H:%M:%S"
            )

            self.last_updated_label.setText(
                f"Last updated: {current_time}"
            )

        except Exception as error:
            self.last_updated_label.setText(
                f"Analytics error: {error}"
            )