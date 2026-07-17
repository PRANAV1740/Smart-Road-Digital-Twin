# ==================================================
# SMART ROAD DIGITAL TWIN - MAIN DASHBOARD
# PROFESSIONAL UI POLISH
# ==================================================

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from services.data_source_manager import DataSourceManager
from services.esp32_service import ESP32Service
from services.ml_service import MLService
from services.simulator import Simulator

from utils import data

from widgets.alert_panel import AlertPanel
from widgets.analytics_panel import AnalyticsPanel
from widgets.camera_panel import CameraPanel
from widgets.history_panel import HistoryPanel
from widgets.map_widget import MapWidget
from widgets.reports_panel import ReportsPanel
from widgets.sensor_panel import SensorPanel
from widgets.settings_panel import SettingsPanel
from widgets.statistics_panel import StatisticsPanel
from widgets.status_card import StatusBar
from widgets.ml_summary_card import MLSummaryCard
from widgets.ml_panel import MLPanel


class Dashboard(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Smart Road Digital Twin")
        self.resize(1500, 860)
        self.setMinimumSize(1180, 720)

        self.camera_stream_url = "http://192.168.4.1:81/stream"

        # ==================================================
        # MACHINE LEARNING
        # ==================================================
        # ONE MLService instance, shared by both data sources.
        #
        #   Simulator    -> feeds it fake waveforms
        #   ESP32Service -> feeds it real UDP packets
        #
        # The model does not know which is talking to it. That is
        # what lets you switch between simulation and real hardware
        # without touching the ML code at all.
        # ==================================================

        self.ml_service = MLService()

        self.simulator = Simulator(ml_service=self.ml_service)
        self.data_source_manager = DataSourceManager()

        self.esp32_service = ESP32Service(ml_service=self.ml_service)
        self.esp32_service.start()

        self.simulator_timer = QTimer(self)
        self.simulator_timer.timeout.connect(self.update_data_source)
        self.simulator_timer.start(300)

        self.setStyleSheet(
            """
            QWidget {
                background-color:#0f1318;
                color:#f4f7fb;
                font-family:"Segoe UI";
            }

            QLabel {
                background:transparent;
            }

            QFrame#headerFrame {
                background:#151a21;
                border:1px solid #242c36;
                border-radius:10px;
            }

            QLabel#productLabel {
                color:#f8fafc;
                font-size:24px;
                font-weight:700;
                letter-spacing:1px;
            }

            QLabel#productSubtitle {
                color:#8e99a8;
                font-size:11px;
                font-weight:500;
            }

            QLabel#versionBadge {
                color:#9fc5ff;
                background:#18283d;
                border:1px solid #274a73;
                border-radius:10px;
                padding:5px 10px;
                font-size:10px;
                font-weight:700;
            }

            QScrollArea {
                border:none;
                background:#0f1318;
            }

            QScrollArea > QWidget > QWidget {
                background:#0f1318;
            }

            QScrollBar:vertical {
                background:#10151b;
                width:11px;
                margin:2px;
                border-radius:5px;
            }

            QScrollBar::handle:vertical {
                background:#3c4653;
                min-height:36px;
                border-radius:5px;
            }

            QScrollBar::handle:vertical:hover {
                background:#566372;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height:0px;
            }

            QScrollBar:horizontal {
                background:#10151b;
                height:10px;
                margin:2px;
                border-radius:5px;
            }

            QScrollBar::handle:horizontal {
                background:#3c4653;
                min-width:36px;
                border-radius:5px;
            }

            QScrollBar::handle:horizontal:hover {
                background:#566372;
            }

            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {
                width:0px;
            }

            QTabWidget::pane {
                background:#10151b;
                border:1px solid #242c36;
                border-radius:9px;
                top:-1px;
            }

            QTabBar::tab {
                background:#151a21;
                color:#8793a2;
                border:1px solid #242c36;
                border-bottom:none;
                padding:10px 24px;
                min-width:128px;
                min-height:20px;
                font-size:11px;
                font-weight:700;
                letter-spacing:0.5px;
            }

            QTabBar::tab:first {
                border-top-left-radius:8px;
            }

            QTabBar::tab:last {
                border-top-right-radius:8px;
            }

            QTabBar::tab:selected {
                background:#1d2733;
                color:#f8fafc;
                border-color:#344253;
                border-top:2px solid #4f8cff;
            }

            QTabBar::tab:hover:!selected {
                background:#1a2028;
                color:#d5dbe3;
            }
            """
        )

        self.build_interface()

    def build_interface(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 12, 14, 12)
        main_layout.setSpacing(10)

        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")

        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(18, 10, 18, 10)
        header_layout.setSpacing(12)

        title_block = QVBoxLayout()
        title_block.setSpacing(1)

        title = QLabel("SMART ROAD DIGITAL TWIN")
        title.setObjectName("productLabel")

        subtitle = QLabel(
            "AI-assisted road-condition monitoring and digital mapping"
        )
        subtitle.setObjectName("productSubtitle")

        title_block.addWidget(title)
        title_block.addWidget(subtitle)

        version_badge = QLabel("SYSTEM v1.0")
        version_badge.setObjectName("versionBadge")
        version_badge.setAlignment(Qt.AlignCenter)

        header_layout.addLayout(title_block)
        header_layout.addStretch()
        header_layout.addWidget(version_badge)

        main_layout.addWidget(header_frame)

        self.status_bar = StatusBar()
        main_layout.addWidget(self.status_bar)

        self.main_tabs = QTabWidget()
        self.main_tabs.setDocumentMode(True)
        self.main_tabs.setMovable(False)
        self.main_tabs.setTabsClosable(False)

        self.monitoring_page = self.create_monitoring_page()
        self.analytics_page = self.create_analytics_page()
        self.reports_page = self.create_reports_page()
        self.settings_page = self.create_settings_page()
        self.ml_page = self.create_ml_page()

        self.main_tabs.addTab(self.monitoring_page, "MONITORING")
        self.main_tabs.addTab(self.analytics_page, "ANALYTICS")
        self.main_tabs.addTab(self.reports_page, "REPORTS")
        self.main_tabs.addTab(self.settings_page, "SETTINGS")
        self.main_tabs.addTab(self.ml_page, "ML ENGINE")

        self.main_tabs.currentChanged.connect(self.handle_tab_change)
        main_layout.addWidget(self.main_tabs, 1)

    def create_monitoring_page(self):
        monitoring_page = QWidget()
        body_layout = QHBoxLayout(monitoring_page)
        body_layout.setContentsMargins(10, 10, 10, 10)
        body_layout.setSpacing(12)

        self.map_widget = MapWidget()
        body_layout.addWidget(self.map_widget, 3)

        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 4, 0)
        right_layout.setSpacing(12)

        self.camera_panel = CameraPanel()
        self.camera_panel.setMinimumHeight(390)
        right_layout.addWidget(self.camera_panel)

        self.alert_panel = AlertPanel()
        self.alert_panel.setMinimumHeight(75)
        right_layout.addWidget(self.alert_panel)

        self.ml_summary_card = MLSummaryCard()
        self.ml_summary_card.setMinimumHeight(75)
        right_layout.addWidget(self.ml_summary_card)

        self.sensor_panel = SensorPanel()
        self.sensor_panel.setMinimumHeight(320)
        right_layout.addWidget(self.sensor_panel)

        self.statistics_panel = StatisticsPanel()
        self.statistics_panel.setMinimumHeight(300)
        right_layout.addWidget(self.statistics_panel)

        self.history_panel = HistoryPanel()
        self.history_panel.setMinimumHeight(360)
        right_layout.addWidget(self.history_panel)

        right_layout.addStretch()

        self.right_scroll_area = QScrollArea()
        self.right_scroll_area.setWidgetResizable(True)
        self.right_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.right_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.right_scroll_area.setWidget(right_container)

        body_layout.addWidget(self.right_scroll_area, 2)
        return monitoring_page

    def create_analytics_page(self):
        analytics_page = QWidget()
        page_layout = QVBoxLayout(analytics_page)
        page_layout.setContentsMargins(10, 10, 10, 10)
        page_layout.setSpacing(0)

        self.analytics_panel = AnalyticsPanel()
        self.analytics_panel.setMinimumHeight(900)
        self.analytics_panel.setMinimumWidth(1100)

        self.analytics_scroll_area = QScrollArea()
        self.analytics_scroll_area.setWidgetResizable(True)
        self.analytics_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.analytics_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.analytics_scroll_area.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.analytics_scroll_area.setWidget(self.analytics_panel)

        page_layout.addWidget(self.analytics_scroll_area)
        return analytics_page

    def create_reports_page(self):
        reports_page = QWidget()
        page_layout = QVBoxLayout(reports_page)
        page_layout.setContentsMargins(14, 14, 14, 14)
        page_layout.setSpacing(8)

        page_title = QLabel("REPORT CENTRE")
        page_title.setAlignment(Qt.AlignCenter)
        page_title.setStyleSheet(
            """
            font-size:24px;
            font-weight:700;
            color:#f8fafc;
            padding-top:6px;
            """
        )

        page_subtitle = QLabel(
            "Review stored detections and generate structured CSV or PDF reports"
        )
        page_subtitle.setAlignment(Qt.AlignCenter)
        page_subtitle.setStyleSheet(
            """
            font-size:11px;
            color:#8e99a8;
            padding-bottom:10px;
            """
        )

        page_layout.addWidget(page_title)
        page_layout.addWidget(page_subtitle)

        reports_container = QWidget()
        reports_container_layout = QVBoxLayout(reports_container)
        reports_container_layout.setContentsMargins(16, 6, 16, 18)
        reports_container_layout.setSpacing(12)

        self.reports_panel = ReportsPanel()
        self.reports_panel.setMinimumHeight(520)
        reports_container_layout.addWidget(self.reports_panel)
        reports_container_layout.addStretch()

        self.reports_scroll_area = QScrollArea()
        self.reports_scroll_area.setWidgetResizable(True)
        self.reports_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.reports_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.reports_scroll_area.setWidget(reports_container)

        page_layout.addWidget(self.reports_scroll_area, 1)
        return reports_page

    def create_settings_page(self):
        settings_page = QWidget()
        page_layout = QVBoxLayout(settings_page)
        page_layout.setContentsMargins(10, 10, 10, 10)
        page_layout.setSpacing(0)

        self.settings_panel = SettingsPanel()
        self.settings_panel.setMinimumHeight(900)
        self.settings_panel.setMinimumWidth(900)

        self.settings_scroll_area = QScrollArea()
        self.settings_scroll_area.setWidgetResizable(True)
        self.settings_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.settings_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.settings_scroll_area.setWidget(self.settings_panel)

        page_layout.addWidget(self.settings_scroll_area)

        self.settings_panel.mode_changed.connect(self.change_data_source_mode)
        self.settings_panel.clear_history_requested.connect(self.clear_event_history)
        self.settings_panel.database_cleared.connect(self.handle_database_reset)
        self.settings_panel.camera_url_saved.connect(self.save_camera_url)

        self.settings_panel.set_active_mode(
            self.data_source_manager.get_mode()
        )

        return settings_page

    def create_ml_page(self):
        ml_page = QWidget()
        page_layout = QVBoxLayout(ml_page)
        page_layout.setContentsMargins(10, 10, 10, 10)
        page_layout.setSpacing(0)

        self.ml_panel = MLPanel(self.ml_service)

        self.ml_scroll_area = QScrollArea()
        self.ml_scroll_area.setWidgetResizable(True)
        self.ml_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.ml_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.ml_scroll_area.setWidget(self.ml_panel)

        page_layout.addWidget(self.ml_scroll_area)
        return ml_page

    def handle_tab_change(self, index):
        selected_widget = self.main_tabs.widget(index)

        if selected_widget is self.analytics_page:
            self.analytics_panel.refresh_analytics()

        elif selected_widget is self.reports_page:
            self.reports_panel.refresh_report()

        elif selected_widget is self.settings_page:
            self.settings_panel.set_active_mode(
                self.data_source_manager.get_mode()
            )

    def change_data_source_mode(self, mode):
        try:
            self.data_source_manager.set_mode(mode)
            self.update_data_source()
            self.settings_panel.set_active_mode(
                self.data_source_manager.get_mode()
            )

        except ValueError as error:
            print(f"Data source mode error: {error}")

    def clear_event_history(self):
        """
        Reset the visible card list safely.

        The current HistoryPanel is database-driven, so stored
        records remain available and can appear again on refresh.
        """

        if hasattr(self.history_panel, "reset_history"):
            self.history_panel.reset_history()

            if hasattr(self.history_panel, "live_status_label"):
                self.history_panel.live_status_label.setText(
                    "Visible history reset. Database records remain stored."
                )

        else:
            if hasattr(self.history_panel, "history_box"):
                self.history_panel.history_box.clear()

            if hasattr(self.history_panel, "displayed_database_ids"):
                self.history_panel.displayed_database_ids.clear()

            self.history_panel.last_warning_level = ""
            self.history_panel.last_pothole_id = None

    def handle_database_reset(self):
        if hasattr(self.history_panel, "reset_history"):
            self.history_panel.reset_history()

        else:
            if hasattr(self.history_panel, "history_box"):
                self.history_panel.history_box.clear()

            if hasattr(self.history_panel, "displayed_database_ids"):
                self.history_panel.displayed_database_ids.clear()

            self.history_panel.last_warning_level = ""
            self.history_panel.last_pothole_id = None

        if hasattr(self.camera_panel, "reset_capture_tracking"):
            self.camera_panel.reset_capture_tracking()

        self.reports_panel.refresh_report()
        self.analytics_panel.refresh_analytics()

        if hasattr(self.statistics_panel, "update_statistics"):
            self.statistics_panel.update_statistics()

        elif hasattr(self.statistics_panel, "refresh_statistics"):
            self.statistics_panel.refresh_statistics()

        elif hasattr(self.statistics_panel, "update_data"):
            self.statistics_panel.update_data()

    def save_camera_url(self, camera_url):
        self.camera_stream_url = camera_url
        print("ESP32-CAM URL saved:", self.camera_stream_url)

    def update_data_source(self):
        self.data_source_manager.update()

        using_simulator = self.data_source_manager.using_simulator()

        # ==================================================
        # WHO OWNS road_status?
        # ==================================================
        # SIMULATION : the map widget owns it. The car drives a
        #              scripted track past known potholes, so the
        #              twin animation is the truth. ML still runs
        #              and displays its prediction alongside, which
        #              is a nice live check that the model agrees.
        #
        # LIVE       : the ML model owns it. Real sensor data has no
        #              scripted track, so the model's prediction IS
        #              the detection.
        # ==================================================

        data.ml_authoritative = (
            not using_simulator
            and self.ml_service.is_ready()
        )

        if using_simulator:
            self.simulator.enabled = True
            self.simulator.update()
        else:
            self.simulator.enabled = False

        if hasattr(self, "settings_panel"):
            self.settings_panel.set_active_mode(
                self.data_source_manager.get_mode()
            )

    def closeEvent(self, event):
        self.simulator_timer.stop()

        if hasattr(self.analytics_panel, "refresh_timer"):
            self.analytics_panel.refresh_timer.stop()

        if hasattr(self.reports_panel, "refresh_timer"):
            self.reports_panel.refresh_timer.stop()

        if hasattr(self.history_panel, "stop"):
            self.history_panel.stop()
        elif hasattr(self.history_panel, "timer"):
            self.history_panel.timer.stop()

        if hasattr(self.camera_panel, "stop"):
            self.camera_panel.stop()

        self.esp32_service.stop()
        event.accept()