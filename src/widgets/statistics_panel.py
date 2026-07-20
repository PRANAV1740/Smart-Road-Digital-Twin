from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QMessageBox,
    QFrame
)
from PySide6.QtCore import QTimer, Qt

from database.database import (
    get_statistics,
    export_to_csv,
    clear_database,
)
from utils.theme import ThemeManager


class StatisticsPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(320)
        self.theme_manager = ThemeManager()
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(12)
        
        self.header_layout = QHBoxLayout()
        self.title_label = QLabel("ROAD STATISTICS")
        self.title_label.setStyleSheet("font-size: 14px; font-weight: bold; font-family: 'Segoe UI';")
        self.header_layout.addWidget(self.title_label)
        self.header_layout.addStretch()
        
        main_layout.addLayout(self.header_layout)
        
        # Grid for stat cards
        self.grid = QGridLayout()
        self.grid.setSpacing(10)
        
        self.stat_cards = {}
        
        # Row 0
        self.create_stat_card("TOTAL POTHOLES", "0", 0, 0, True)
        self.create_stat_card("HIGH SEVERITY", "0", 0, 1)
        self.create_stat_card("MEDIUM SEVERITY", "0", 0, 2)
        
        # Row 1
        self.create_stat_card("LOW SEVERITY", "0", 1, 0)
        self.create_stat_card("AVERAGE DEPTH", "0 cm", 1, 1)
        self.create_stat_card("MAXIMUM DEPTH", "0 cm", 1, 2)
        
        main_layout.addLayout(self.grid)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.export_button = QPushButton("EXPORT CSV")
        self.export_button.setCursor(Qt.PointingHandCursor)
        self.clear_button = QPushButton("CLEAR DATABASE")
        self.clear_button.setCursor(Qt.PointingHandCursor)
        
        self.export_button.clicked.connect(self.export_records)
        self.clear_button.clicked.connect(self.clear_records)
        
        button_layout.addWidget(self.export_button)
        button_layout.addWidget(self.clear_button)
        main_layout.addLayout(button_layout)
        main_layout.addStretch()
        
        self.theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme(self.theme_manager.get_current_theme(), self.theme_manager.is_dark)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_statistics)
        self.timer.start(1000)
        self.update_statistics()

    def create_stat_card(self, title, initial_val, row, col, is_accent=False):
        card = QFrame()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(10, 10, 10, 10)
        card_layout.setSpacing(4)
        
        val_lbl = QLabel(initial_val)
        val_lbl.setAlignment(Qt.AlignCenter)
        title_lbl = QLabel(title)
        title_lbl.setAlignment(Qt.AlignCenter)
        
        card_layout.addWidget(val_lbl)
        card_layout.addWidget(title_lbl)
        
        self.stat_cards[title] = {
            "widget": card,
            "title": title_lbl,
            "val": val_lbl,
            "is_accent": is_accent
        }
        self.grid.addWidget(card, row, col)

    def apply_theme(self, theme, is_dark):
        self.theme = theme
        
        border = f"1px solid {theme['border']}" if is_dark else "none"
        shadow = "" if is_dark else "box-shadow: 0 1px 3px rgba(0,0,0,0.08);"
        
        self.title_label.setStyleSheet(f"color: {theme['text_primary']}; font-size: 14px; font-weight: bold; background: transparent; border: none;")
        
        for k, ui in self.stat_cards.items():
            ui["widget"].setStyleSheet(f"""
                QFrame {{
                    background-color: {theme['surface']};
                    border-radius: 12px;
                    border: {border};
                    {shadow}
                }}
            """)
            val_color = theme['accent'] if ui["is_accent"] else theme['text_primary']
            if k == "HIGH SEVERITY":
                val_color = theme['danger']
            elif k == "MEDIUM SEVERITY":
                val_color = theme['warning']
                
            ui["val"].setStyleSheet(f"color: {val_color}; font-size: 28px; font-weight: bold; background: transparent; border: none; font-family: 'Segoe UI';")
            ui["title"].setStyleSheet(f"color: {theme['text_secondary']}; font-size: 11px; font-weight: bold; background: transparent; border: none; font-family: 'Segoe UI';")
            
        btn_style = f"""
            QPushButton {{
                background-color: {theme['surface_elevated']};
                color: {theme['text_primary']};
                border: 1px solid {theme['border']};
                border-radius: 8px;
                padding: 10px 16px;
                font-size: 12px;
                font-weight: 600;
                font-family: 'Segoe UI';
            }}
            QPushButton:hover {{
                background-color: {theme['surface']};
                color: {theme['accent_hover']};
            }}
        """
        self.export_button.setStyleSheet(btn_style)
        self.clear_button.setStyleSheet(btn_style)

    def update_statistics(self):
        statistics = get_statistics()
        self.stat_cards["TOTAL POTHOLES"]["val"].setText(f"{statistics['total']}")
        self.stat_cards["HIGH SEVERITY"]["val"].setText(f"{statistics['high']}")
        self.stat_cards["MEDIUM SEVERITY"]["val"].setText(f"{statistics['medium']}")
        self.stat_cards["LOW SEVERITY"]["val"].setText(f"{statistics['low']}")
        self.stat_cards["AVERAGE DEPTH"]["val"].setText(f"{statistics['average_depth']} cm")
        self.stat_cards["MAXIMUM DEPTH"]["val"].setText(f"{statistics['maximum_depth']} cm")

    def export_records(self):
        try:
            export_path = export_to_csv()
            if export_path is None:
                QMessageBox.information(self, "Export CSV", "Database is empty. Nothing to export.")
                return
            QMessageBox.information(self, "Export Successful", f"CSV file saved at:\n\n{export_path}")
        except Exception as error:
            QMessageBox.critical(self, "Export Error", str(error))

    def clear_records(self):
        answer = QMessageBox.question(
            self, "Clear Database", "Are you sure you want to delete all pothole records?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if answer != QMessageBox.Yes: return
        try:
            clear_database()
            self.update_statistics()
            QMessageBox.information(self, "Database Cleared", "All pothole records were deleted.")
        except Exception as error:
            QMessageBox.critical(self, "Database Error", str(error))