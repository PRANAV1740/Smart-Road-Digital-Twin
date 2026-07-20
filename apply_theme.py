import sys
path = 'src/widgets/camera_panel.py'
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

code = code.replace('from utils import data', 'from utils import data\nfrom utils.theme import ThemeManager')

orig_cv_init = '''def __init__(self):
        super().__init__()

        self.scan_y = 0'''
new_cv_init = '''def __init__(self):
        super().__init__()
        self.theme_manager = ThemeManager()
        self.theme = self.theme_manager.get_current_theme()
        self.is_dark = self.theme_manager.is_dark
        self.theme_manager.theme_changed.connect(self.apply_theme)

        self.scan_y = 0'''
code = code.replace(orig_cv_init, new_cv_init)

apply_theme_cv = '''    def apply_theme(self, theme, is_dark):\n        self.theme = theme\n        self.is_dark = is_dark\n        self.update()\n\n    def update_frame'''
code = code.replace('    def update_frame', apply_theme_cv)

code = code.replace('QColor("#090d12")', 'QColor(self.theme["surface"])')
code = code.replace('QColor("#242a30")', 'QColor(self.theme["surface_elevated"])')
code = code.replace('QColor("#f7d477")', 'QColor(self.theme["warning"])')
code = code.replace('QColor("#8a8f95")', 'QColor(self.theme["border"])')
code = code.replace('QColor("#ff3333")', 'QColor(self.theme["danger"])')
code = code.replace('QColor("#dddddd")', 'QColor(self.theme["text_primary"])')
code = code.replace('QColor("#4a5568")', 'QColor(self.theme["text_muted"])')
code = code.replace('QColor("#34d399")', 'QColor(self.theme["success"])')

orig_cp_init = '''def __init__(self):
        super().__init__()

        self.last_captured_pothole_id = None'''
new_cp_init = '''def __init__(self):
        super().__init__()
        self.theme_manager = ThemeManager()
        self.theme = self.theme_manager.get_current_theme()

        self.last_captured_pothole_id = None'''
code = code.replace(orig_cp_init, new_cp_init)

apply_theme_hook_cp = '''
        self.theme_manager.theme_changed.connect(self.apply_theme)
        self.apply_theme(self.theme_manager.get_current_theme(), self.theme_manager.is_dark)

        self.capture_timer = QTimer(self)
'''
code = code.replace('\n        self.capture_timer = QTimer(self)\n', apply_theme_hook_cp)

apply_theme_func_cp = '''
    def apply_theme(self, theme, is_dark):
        self.theme = theme
        self.setStyleSheet(f"""
            QWidget {{
                background: {theme['surface']};
                border-radius: 8px;
            }}
        """)
        self.title_label.setStyleSheet(f"""
            color: {theme['text_primary']};
            font-size: 14px;
            font-weight: bold;
            padding: 8px;
        """)
        self.status_label.setStyleSheet(f"""
            color: {theme['text_primary']};
            background: {theme['surface_elevated']};
            border: 1px solid {theme['border']};
            border-radius: 6px;
            padding: 8px;
        """)
        self.details_label.setStyleSheet(f"""
            color: {theme['text_secondary']};
            font-size: 12px;
        """)

    def check_snapshot'''
code = code.replace('\n    def check_snapshot', apply_theme_func_cp)

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)
print('Done modifying camera_panel.py')
