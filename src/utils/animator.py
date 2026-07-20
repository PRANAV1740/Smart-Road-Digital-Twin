import time
import math
from PySide6.QtCore import QObject, Signal, QTimer

class GlobalAnimatorMetaclass(type(QObject)):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(GlobalAnimatorMetaclass, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class GlobalAnimator(QObject, metaclass=GlobalAnimatorMetaclass):
    """
    Centralized animation ticker.
    Instead of each widget spawning a QTimer for breathing/pulsing effects,
    this single timer emits the current time at 30 FPS.
    Widgets connect real-time ticks to their geometry/paint logic using math.sin().
    """
    tick = Signal(float) # Emits the current time in seconds

    def __init__(self):
        super().__init__()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_timeout)
        self.timer.start(33) # roughly 30 fps
        
    def _on_timeout(self):
        self.tick.emit(time.time())

    @staticmethod
    def get_sine_value(current_time, cycle_duration_seconds, min_val, max_val):
        """
        Helper for breathing effects. 
        Calculates a smooth oscillation between min_val and max_val based on current_time.
        """
        # math.sin returns -1 to 1. Normalize it to 0 to 1
        normalized_sin = (math.sin(current_time * (2 * math.pi / cycle_duration_seconds)) + 1) / 2
        return min_val + (max_val - min_val) * normalized_sin
