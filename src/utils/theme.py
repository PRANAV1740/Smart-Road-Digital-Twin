from PySide6.QtCore import QObject, Signal

class Singleton(type(QObject)):
    def __init__(cls, name, bases, dict):
        super().__init__(name, bases, dict)
        cls.instance = None

    def __call__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = super().__call__(*args, **kwargs)
        return cls.instance

class ThemeManager(QObject, metaclass=Singleton):
    """
    Singleton to manage theme state and broadcasts.
    """
    theme_changed = Signal(dict, bool)  # dict of colors, is_dark indicator

    def __init__(self):
        super().__init__()
        self.is_dark = True

    def toggle_theme(self):
        self.is_dark = not self.is_dark
        theme = get_theme(self.is_dark)
        self.theme_changed.emit(theme, self.is_dark)
        
    def get_current_theme(self):
        return get_theme(self.is_dark)
    
    def set_dark_mode(self, is_dark):
        if self.is_dark != is_dark:
            self.is_dark = is_dark
            theme = get_theme(self.is_dark)
            self.theme_changed.emit(theme, self.is_dark)


def get_theme(is_dark=True):
    """
    Returns a dictionary of colors for the requested theme.
    Colors match the Apple/Tesla inspired minimal schema.
    """
    if is_dark:
        return {
            "background": "#0f1117",
            "surface": "#1a1d27",
            "surface_elevated": "#242836",
            "text_primary": "#f0f2f5",
            "text_secondary": "#8b90a0",
            "text_muted": "#555b6e",
            "border": "#2a2e3a",
            "accent": "#3b82f6",  # blue
            "accent_hover": "#2563eb",
            "success": "#22c55e",
            "warning": "#f59e0b",
            "danger": "#ef4444",
            "info": "#3b82f6",
            "type": "dark"
        }
    else:
        return {
            "background": "#f5f5f7",
            "surface": "#ffffff",
            "surface_elevated": "#ffffff",
            "text_primary": "#1d1d1f",
            "text_secondary": "#6e6e73",
            "text_muted": "#aeaeb2",
            "border": "#e5e5ea",
            "accent": "#007aff",  # Apple blue
            "accent_hover": "#0056cc",
            "success": "#34c759",
            "warning": "#ff9f0a",
            "danger": "#ff3b30",
            "info": "#007aff",
            "type": "light"
        }
