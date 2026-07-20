# ==================================================
# SMART ROAD DIGITAL TWIN - MAIN DASHBOARD
# PROFESSIONAL UI POLISH
# ==================================================

from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QPushButton,
    QSpacerItem,
    QSizePolicy,
    QGraphicsOpacityEffect
)
from utils.theme import ThemeManager
from utils.animator import GlobalAnimator

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

class RotatingThemeButton(QPushButton):
    def __init__(self):
        super().__init__()
        self.setFixedSize(32, 32)
        self.setCursor(Qt.PointingHandCursor)
        self._rotation = 0.0
        self.anim = QPropertyAnimation(self, b"rotation_angle")
        self.anim.setDuration(300)
        self.anim.setEasingCurve(QEasingCurve.InOutQuad)
        
    def get_rotation(self):
        return self._rotation
        
    def set_rotation(self, value):
        self._rotation = value
        self.update()
        
    rotation_angle = Property(float, get_rotation, set_rotation)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(self._rotation)
        painter.translate(-self.width() / 2, -self.height() / 2)
        super().paintEvent(event)
        
    def spin(self):
        self.anim.stop()
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(180.0)
        self.anim.start()


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

        self.theme_manager = ThemeManager()
        self.theme = self.theme_manager.get_current_theme()
        self.theme_manager.theme_changed.connect(self.apply_theme)

        self.build_interface()
        
        self.animator = GlobalAnimator()
        self.animator.tick.connect(self.on_animator_tick)

        self.apply_theme(self.theme_manager.get_current_theme(), self.theme_manager.is_dark)
        
        # Fade to black overlay for theme transition
        self.theme_overlay = QFrame(self)
        self.theme_overlay.setStyleSheet("background-color: #000000;")
        self.theme_overlay_effect = QGraphicsOpacityEffect(self.theme_overlay)
        self.theme_overlay_effect.setOpacity(0.0)
        self.theme_overlay.setGraphicsEffect(self.theme_overlay_effect)
        self.theme_overlay.hide()
        
        self.overlay_anim = QPropertyAnimation(self.theme_overlay_effect, b"opacity")
        self.overlay_anim.setDuration(150)
        self.overlay_anim.finished.connect(self.on_theme_fade_step)

    def on_animator_tick(self, timestamp):
        # Pulse LIVE badge only if in hardware mode
        if self.data_source_manager.get_mode() == "hardware":
            val = self.animator.get_sine_value(timestamp, 1.5, 0.5, 1.0)
            if hasattr(self, 'live_badge_effect'):
                self.live_badge_effect.setOpacity(val)
        else:
            if hasattr(self, 'live_badge_effect'):
                self.live_badge_effect.setOpacity(1.0)

    def on_theme_toggle_clicked(self):
        self.theme_toggle_btn.spin()
        self.theme_overlay.setGeometry(self.rect())
        self.theme_overlay.show()
        self.theme_overlay.raise_()
        
        self.overlay_anim.stop()
        self.overlay_anim.setStartValue(0.0)
        self.overlay_anim.setEndValue(1.0)
        self.overlay_anim.start()
        
    def on_theme_fade_step(self):
        if self.overlay_anim.direction() == QPropertyAnimation.Forward:
            # We are faded to black, switch theme!
            self.theme_manager.toggle_theme()
            # Fade out
            self.overlay_anim.setDirection(QPropertyAnimation.Backward)
            self.overlay_anim.start()
        else:
            self.theme_overlay.hide()
            self.overlay_anim.setDirection(QPropertyAnimation.Forward)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.theme_overlay.setGeometry(self.rect())

    def build_interface(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # HEADER BAR
        self.header_frame = QFrame()
        self.header_frame.setObjectName("headerFrame")
        self.header_frame.setFixedHeight(56)

        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(20, 0, 20, 0)
        header_layout.setSpacing(20)

        # Left: App name + Dot
        left_box = QHBoxLayout()
        left_box.setSpacing(6)
        self.app_title = QLabel("RoadSense")
        self.app_title.setStyleSheet("font-size: 20px; font-weight: 600; font-family: 'Segoe UI';")
        self.status_dot = QLabel()
        self.status_dot.setFixedSize(8, 8)
        self.status_dot.setStyleSheet("border-radius: 4px; background-color: #22c55e;")
        left_box.addWidget(self.app_title)
        left_box.addWidget(self.status_dot, 0, Qt.AlignVCenter)

        header_layout.addLayout(left_box)
        header_layout.addStretch()

        # Center: Pill Tabs
        self.tabs_layout = QHBoxLayout()
        self.tabs_layout.setSpacing(4)
        
        self.tab_buttons = []
        tabs = [("MONITORING", 0), ("ANALYTICS", 1), ("REPORTS", 2), ("SETTINGS", 3), ("ML ENGINE", 4)]
        
        for name, idx in tabs:
            btn = QPushButton(name)
            btn.setFixedHeight(32)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, i=idx: self.set_active_tab(i))
            self.tabs_layout.addWidget(btn)
            self.tab_buttons.append(btn)
            
        header_layout.addLayout(self.tabs_layout)
        header_layout.addStretch()

        # Right: Theme toggle & Live Badge
        right_box = QHBoxLayout()
        right_box.setSpacing(12)
        
        self.theme_toggle_btn = RotatingThemeButton()
        self.theme_toggle_btn.setText("🌙")
        self.theme_toggle_btn.clicked.connect(self.on_theme_toggle_clicked)
        
        self.live_badge = QLabel("LIVE")
        self.live_badge.setAlignment(Qt.AlignCenter)
        self.live_badge.setFixedSize(50, 24)
        
        self.live_badge_effect = QGraphicsOpacityEffect(self.live_badge)
        self.live_badge.setGraphicsEffect(self.live_badge_effect)
        
        right_box.addWidget(self.theme_toggle_btn)
        right_box.addWidget(self.live_badge, 0, Qt.AlignVCenter)
        
        header_layout.addLayout(right_box)
        
        main_layout.addWidget(self.header_frame)

        # Remove the legacy status bar for the minimal design
        # if self.status_bar exists, we don't need it.

        # Tab Widget content area
        content_frame = QFrame()
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(14, 14, 14, 14)
        
        self.main_tabs = QTabWidget()
        self.main_tabs.setDocumentMode(True)
        self.main_tabs.tabBar().hide() # Hide default
        
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
        content_layout.addWidget(self.main_tabs)
        main_layout.addWidget(content_frame, 1)

        self.set_active_tab(0) # Default
        
        # Sequentially fade in all layout elements to boot
        self.run_boot_sequence()
        
    def run_boot_sequence(self):
        targets = [
            self.map_widget, self.camera_panel, self.alert_panel, 
            self.ml_summary_card, self.sensor_panel, self.statistics_panel, self.history_panel
        ]
        
        def start_fade(w):
            eff = w.graphicsEffect()
            anim = QPropertyAnimation(eff, b"opacity")
            anim.setDuration(400)
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
            anim.setEasingCurve(QEasingCurve.OutCubic)
            
            # Prevent python from garbage collecting the animation instantly
            if not hasattr(w, "_boot_anim"):
                w._boot_anim = anim
            anim.start()

        for i, w in enumerate(targets):
            eff = QGraphicsOpacityEffect(w)
            eff.setOpacity(0.0)
            w.setGraphicsEffect(eff)
            QTimer.singleShot(150 + i * 50, lambda widget=w: (start_fade(widget)))

    def create_monitoring_page(self):
        monitoring_page = QWidget()
        body_layout = QHBoxLayout(monitoring_page)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(8)

        self.map_widget = MapWidget()
        body_layout.addWidget(self.map_widget, 3)

        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 4, 0)
        right_layout.setSpacing(6)

        self.camera_panel = CameraPanel()
        self.camera_panel.setMinimumHeight(280)
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
        
        # We also need to refresh the button state specifically if switched externally
        theme = self.theme_manager.get_current_theme()
        
        for i, btn in enumerate(self.tab_buttons):
            if i == index:
                btn.setStyleSheet(f"""
                    QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {self.theme['accent']}, stop:1 {self.theme['accent']}99);
                    border-radius: 14px;
                    color: #ffffff;
                    font-weight: bold;
                    padding: 0 16px;
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: transparent;
                        border-radius: 14px;
                        color: {self.theme['text_secondary']};
                        font-weight: bold;
                        padding: 0 16px;
                    }}
                    QPushButton:hover {{
                        color: {self.theme['text_primary']};
                        background-color: {self.theme['surface_elevated']};
                    }}
                """)

        if selected_widget is self.analytics_page:
            self.analytics_panel.refresh_analytics()

        elif selected_widget is self.reports_page:
            self.reports_panel.refresh_report()

        elif selected_widget is self.settings_page:
            self.settings_panel.set_active_mode(
                self.data_source_manager.get_mode()
            )
            
    def set_active_tab(self, index):
        self.main_tabs.setCurrentIndex(index)
        self.handle_tab_change(index)

    def apply_theme(self, theme, is_dark):
        self.theme = theme
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {theme['background']};
                color: {theme['text_primary']};
                font-family: "Segoe UI";
            }}
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
            QScrollArea > QWidget > QWidget {{
                background-color: transparent;
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 8px;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: {theme['border']};
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QTabWidget::pane {{
                border: none;
                background: transparent;
            }}
        """)
        
        border_color = theme['border']
        # Very subtle bottom border gradient via qlineargradient
        self.header_frame.setStyleSheet(f"""
            QFrame#headerFrame {{
                background-color: {theme['surface']};
                border-bottom: 2px solid qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {theme['surface']}, stop:0.5 {theme['accent']}, stop:1 {theme['surface']});
            }}
        """)
        
        self.app_title.setStyleSheet(f"color: {theme['text_primary']}; font-size: 20px; font-weight: 600; font-family: 'Segoe UI'; background: transparent; border: none;")
        self.status_dot.setStyleSheet(f"border-radius: 4px; background-color: {theme['success']}; border: none;")
        
        mode = self.data_source_manager.get_mode()
        if mode == "simulation":
            badge_bg = f"{theme['surface_elevated']}"
            badge_c = f"{theme['text_muted']}"
            badge_b = f"{theme['border']}"
            self.live_badge.setText("SIM")
        else:
            badge_bg = f"{theme['success']}20"
            badge_c = f"{theme['success']}"
            badge_b = f"{theme['success']}80"
            self.live_badge.setText("LIVE")
            
        self.live_badge.setStyleSheet(f"""
            color: {badge_c};
            background-color: {badge_bg};
            border-radius: 12px;
            font-size: 11px;
            font-weight: 700;
            border: 1px solid {badge_b};
        """)
        
        self.theme_toggle_btn.setText("☀️" if is_dark else "🌙")
        self.theme_toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border-radius: 16px;
                font-size: 16px;
                border: none;
                color: {theme['text_primary']};
            }}
            QPushButton:hover {{
                background-color: {theme['surface_elevated']};
            }}
        """)
        
        # update tabs active colors
        self.set_active_tab(self.main_tabs.currentIndex())

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