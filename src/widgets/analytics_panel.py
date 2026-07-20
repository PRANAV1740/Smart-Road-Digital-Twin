from collections import Counter
from datetime import datetime, timedelta

from PySide6.QtCore import Qt, QRectF, QPointF, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QLinearGradient, QRadialGradient, QPolygonF
from PySide6.QtWidgets import (
    QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget, QFrame
)

from database.database import get_all_potholes, get_statistics
from utils.theme import ThemeManager

class BaseChart(QWidget):
    def __init__(self):
        super().__init__()
        self.theme_manager = ThemeManager()
        self.theme = self.theme_manager.get_current_theme()
        self.is_dark = self.theme_manager.is_dark
        self.theme_manager.theme_changed.connect(self.apply_theme)
        
    def apply_theme(self, theme, is_dark):
        self.theme = theme
        self.is_dark = is_dark
        self.update()

class SeverityBarChart(BaseChart):
    def __init__(self):
        super().__init__()
        self.values = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        self.setMinimumHeight(240)

    def set_values(self, high, medium, low):
        self.values = {"HIGH": high, "MEDIUM": medium, "LOW": low}
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Transparent background
        
        width = self.width()
        height = self.height()
        margin_left, margin_right, margin_top, margin_bottom = 55, 25, 45, 50
        chart_width = width - margin_left - margin_right
        chart_height = height - margin_top - margin_bottom

        painter.setPen(QColor(self.theme['text_primary']))
        painter.setFont(QFont("Arial", 12, QFont.Bold))
        painter.drawText(QRectF(0, 8, width, 25), Qt.AlignCenter, "SEVERITY DISTRIBUTION")

        axis_pen = QPen(QColor(self.theme['border']), 1)
        painter.setPen(axis_pen)
        painter.drawLine(margin_left, margin_top, margin_left, margin_top + chart_height)
        painter.drawLine(margin_left, margin_top + chart_height, margin_left + chart_width, margin_top + chart_height)

        maximum_value = max(1, max(self.values.values()))
        categories = [
            ("HIGH", QColor(self.theme['danger'])),
            ("MEDIUM", QColor(self.theme['warning'])),
            ("LOW", QColor(self.theme['success'])),
        ]

        avail_w = chart_width / len(categories)
        bar_w = min(75, avail_w * 0.48)

        for i, (lbl, color) in enumerate(categories):
            val = self.values[lbl]
            bar_h = val / maximum_value * (chart_height - 25)
            cx = margin_left + avail_w * i + avail_w / 2
            bx = cx - bar_w / 2
            by = margin_top + chart_height - bar_h

            painter.setPen(Qt.NoPen)
            grad = QLinearGradient(0, by, 0, by + bar_h)
            grad.setColorAt(0, color.lighter(130))
            grad.setColorAt(1, color)
            painter.setBrush(grad)
            painter.drawRoundedRect(QRectF(bx, by, bar_w, bar_h), 6, 6)

            painter.setPen(QColor(self.theme['text_primary']))
            painter.setFont(QFont("Segoe UI", 11, QFont.Bold))
            painter.drawText(QRectF(bx, max(margin_top, by - 25), bar_w, 22), Qt.AlignCenter, str(val))

            painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
            painter.drawText(QRectF(cx - avail_w / 2, margin_top + chart_height + 8, avail_w, 25), Qt.AlignCenter, lbl)

class SeverityPieChart(BaseChart):
    def __init__(self):
        super().__init__()
        self.values = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        self.setMinimumHeight(240)

    def set_values(self, high, medium, low):
        self.values = {"HIGH": high, "MEDIUM": medium, "LOW": low}
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()

        painter.setPen(QColor(self.theme['text_primary']))
        painter.setFont(QFont("Arial", 12, QFont.Bold))
        painter.drawText(QRectF(0, 8, width, 25), Qt.AlignCenter, "SEVERITY PERCENTAGE")

        total = sum(self.values.values())
        chart_size = min(width * 0.52, height - 80)
        chart_rect = QRectF(28, 48, chart_size, chart_size)

        colors = {
            "HIGH": QColor(self.theme['danger']),
            "MEDIUM": QColor(self.theme['warning']),
            "LOW": QColor(self.theme['success']),
        }

        if total <= 0:
            painter.setPen(QPen(QColor(self.theme['text_muted']), 2))
            painter.setBrush(QColor(self.theme['border']))
            painter.drawEllipse(chart_rect)
            painter.setPen(QColor(self.theme['text_secondary']))
            painter.setFont(QFont("Arial", 10))
            painter.drawText(chart_rect, Qt.AlignCenter, "NO DATA")
        else:
            start_angle = 90 * 16
            for lbl in ["HIGH", "MEDIUM", "LOW"]:
                val = self.values[lbl]
                if val <= 0: continue
                angle = int(val / total * 360 * 16)
                painter.setPen(QPen(QColor(self.theme['surface']), 2))
                grad = QRadialGradient(chart_rect.center(), chart_size/2.0)
                grad.setColorAt(0, colors[lbl].lighter(120))
                grad.setColorAt(1, colors[lbl])
                painter.setBrush(grad)
                painter.drawPie(chart_rect, start_angle, -angle)
                start_angle -= angle

            inner_size = chart_size * 0.48
            inner_rect = QRectF(chart_rect.center().x() - inner_size / 2, chart_rect.center().y() - inner_size / 2, inner_size, inner_size)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(self.theme['surface']))
            painter.drawEllipse(inner_rect)
            painter.setPen(QColor(self.theme['text_primary']))
            painter.setFont(QFont("Segoe UI", 17, QFont.Bold))
            painter.drawText(inner_rect, Qt.AlignCenter, str(total))

        legend_x = chart_rect.right() + 30
        legend_y = 70
        for lbl in ["HIGH", "MEDIUM", "LOW"]:
            val = self.values[lbl]
            percent = (val / total * 100) if total > 0 else 0
            painter.setPen(Qt.NoPen)
            painter.setBrush(colors[lbl])
            painter.drawRoundedRect(QRectF(legend_x, legend_y, 16, 16), 3, 3)
            painter.setPen(QColor(self.theme['text_primary']))
            painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
            painter.drawText(QRectF(legend_x + 25, legend_y - 4, max(100, width - legend_x - 30), 25), Qt.AlignLeft | Qt.AlignVCenter, f"{lbl}: {val} ({percent:.1f}%)")
            legend_y += 45

class DetectionTimelineChart(BaseChart):
    def __init__(self):
        super().__init__()
        self.labels = []
        self.values = []
        self.setMinimumHeight(280)

    def set_records(self, records):
        today = datetime.now().date()
        dates = [today - timedelta(days=offset) for offset in range(6, -1, -1)]
        daily_counts = Counter()
        for record in records:
            dat_str = str(record.get("detected_at", ""))
            try:
                d = datetime.strptime(dat_str, "%Y-%m-%d %H:%M:%S").date()
                daily_counts[d] += 1
            except ValueError:
                continue
        self.labels = [d.strftime("%d %b") for d in dates]
        self.values = [daily_counts[d] for d in dates]
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        margin_left, margin_right, margin_top, margin_bottom = 60, 30, 55, 55
        chart_width = width - margin_left - margin_right
        chart_height = height - margin_top - margin_bottom

        painter.setPen(QColor(self.theme['text_primary']))
        painter.setFont(QFont("Segoe UI", 12, QFont.Bold))
        painter.drawText(QRectF(0, 8, width, 25), Qt.AlignCenter, "LAST 7 DAYS DETECTION TREND")

        painter.setPen(QPen(QColor(self.theme['border']), 1))
        # Removed heavy grid lines, just drawing bottom axis
        painter.drawLine(margin_left, int(margin_top + chart_height), margin_left + chart_width, int(margin_top + chart_height))

        if not self.values: return
        maximum_value = max(1, max(self.values))
        pt_spacing = chart_width / max(1, len(self.values) - 1)
        points = []

        for i, val in enumerate(self.values):
            px = margin_left + i * pt_spacing
            py = margin_top + chart_height - (val / maximum_value * (chart_height - 15))
            points.append(QPointF(px, py))

        painter.setPen(QPen(QColor(self.theme['accent']), 3))
        for i in range(len(points) - 1):
            painter.drawLine(points[i], points[i + 1])
            
        # Draw area fill
        fill_poly = QPolygonF(points)
        fill_poly.append(QPointF(points[-1].x(), margin_top + chart_height))
        fill_poly.append(QPointF(points[0].x(), margin_top + chart_height))
        
        fill_grad = QLinearGradient(0, margin_top, 0, margin_top + chart_height)
        accent_col = QColor(self.theme['accent'])
        fill_grad.setColorAt(0, QColor(accent_col.red(), accent_col.green(), accent_col.blue(), 100))
        fill_grad.setColorAt(1, QColor(accent_col.red(), accent_col.green(), accent_col.blue(), 0))
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(fill_grad)
        painter.drawPolygon(fill_poly)

        for i, pt in enumerate(points):
            painter.setPen(QPen(QColor(self.theme['surface']), 2))
            painter.setBrush(QColor(self.theme['accent']))
            painter.drawEllipse(pt, 6, 6)

            painter.setPen(QColor(self.theme['text_primary']))
            painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
            painter.drawText(QRectF(pt.x() - 20, pt.y() - 28, 40, 20), Qt.AlignCenter, str(self.values[i]))

            painter.setFont(QFont("Segoe UI", 8))
            painter.drawText(QRectF(pt.x() - 38, margin_top + chart_height + 10, 76, 25), Qt.AlignCenter, self.labels[i])

class AnalyticsPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.theme_manager = ThemeManager()
        self.summary_labels = {}
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(12, 8, 12, 12)
        self.main_layout.setSpacing(10)

        self.title_label = QLabel("ROAD ANALYTICS")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.subtitle_label = QLabel("Database-driven pothole severity, depth and detection trends")
        self.subtitle_label.setAlignment(Qt.AlignCenter)

        self.main_layout.addWidget(self.title_label)
        self.main_layout.addWidget(self.subtitle_label)

        summary_layout = QHBoxLayout()
        summary_layout.setSpacing(12)
        items = [("total", "TOTAL POTHOLES"), ("average", "AVERAGE DEPTH"), ("maximum", "MAXIMUM DEPTH"), ("critical", "HIGH SEVERITY")]
        for key, title in items:
            summary_layout.addWidget(self.create_summary_card(key, title))
        self.main_layout.addLayout(summary_layout)

        charts_layout = QGridLayout()
        charts_layout.setSpacing(14)
        self.bar_chart = SeverityBarChart()
        self.pie_chart = SeverityPieChart()
        self.timeline_chart = DetectionTimelineChart()

        charts_layout.addWidget(self.bar_chart, 0, 0)
        charts_layout.addWidget(self.pie_chart, 0, 1)
        charts_layout.addWidget(self.timeline_chart, 1, 0, 1, 2)
        charts_layout.setColumnStretch(0, 1)
        charts_layout.setColumnStretch(1, 1)

        self.main_layout.addLayout(charts_layout)

        bottom_layout = QHBoxLayout()
        self.last_updated_label = QLabel("Last updated: --")
        self.refresh_button = QPushButton("REFRESH ANALYTICS")
        self.refresh_button.clicked.connect(self.refresh_analytics)
        self.refresh_button.setCursor(Qt.PointingHandCursor)

        bottom_layout.addWidget(self.last_updated_label)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.refresh_button)
        self.main_layout.addLayout(bottom_layout)

        self.theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme(self.theme_manager.get_current_theme(), self.theme_manager.is_dark)

        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_analytics)
        self.refresh_timer.start(2000)
        self.refresh_analytics()

    def create_summary_card(self, key, title):
        card = QFrame()
        card.setObjectName("summaryCard")
        card.setMinimumHeight(85)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(12, 10, 12, 10)
        tl = QLabel(title)
        tl.setObjectName("summaryTitle")
        tl.setAlignment(Qt.AlignCenter)
        vl = QLabel("0")
        vl.setObjectName("summaryValue")
        vl.setAlignment(Qt.AlignCenter)
        cl.addWidget(tl)
        cl.addWidget(vl)
        self.summary_labels[key] = {"widget": card, "title": tl, "val": vl}
        return card

    def apply_theme(self, theme, is_dark):
        self.theme = theme
        border = f"1px solid {theme['border']}" if is_dark else "none"
        shadow = "" if is_dark else "box-shadow: 0 1px 3px rgba(0,0,0,0.08);"
        
        self.title_label.setStyleSheet(f"color: {theme['text_primary']}; font-size: 28px; font-weight: bold; font-family: 'Segoe UI';")
        for key, ui in self.summary_labels.items():
            tint_col = theme['danger'] if key == "critical" else theme['text_primary']
            ui["val"].setStyleSheet(f"color: {tint_col}; font-size: 28px; font-weight: bold; background: transparent; border: none;")
            ui["title"].setStyleSheet(f"font-size: 11px; font-weight: bold; color: {theme['text_secondary']}; background: transparent; border: none;")
            ui["widget"].setStyleSheet(f"""
                QFrame#summaryCard {{
                    background-color: {theme['surface']};
                    border-radius: 12px;
                    border: {border};
                    {shadow}
                }}
            """)

        self.refresh_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme['accent']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 22px;
                font-size: 12px;
                font-weight: bold;
                font-family: 'Segoe UI';
            }}
            QPushButton:hover {{
                background-color: {theme['accent_hover']};
            }}
        """)

    def refresh_analytics(self):
        try:
            statistics = get_statistics()
            records = get_all_potholes()
            self.summary_labels["total"]["val"].setText(str(statistics["total"]))
            self.summary_labels["average"]["val"].setText(f"{statistics['average_depth']:.2f} cm")
            self.summary_labels["maximum"]["val"].setText(f"{statistics['maximum_depth']:.2f} cm")
            self.summary_labels["critical"]["val"].setText(str(statistics["high"]))
            
            self.bar_chart.set_values(statistics["high"], statistics["medium"], statistics["low"])
            self.pie_chart.set_values(statistics["high"], statistics["medium"], statistics["low"])
            self.timeline_chart.set_records(records)
            
            self.last_updated_label.setText(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
        except Exception as error:
            self.last_updated_label.setText(f"Analytics error: {error}")