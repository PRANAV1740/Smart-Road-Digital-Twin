# ==================================================
# SMART ROAD DIGITAL TWIN - DATA SOURCE MANAGER
# ==================================================

import sys
import time
from pathlib import Path

_src_dir = str(Path(__file__).resolve().parent.parent)
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

try:
    from utils import data
except ImportError:
    from src.utils import data



# How long after the last real UDP packet we still consider the
# hardware "present". Matches ESP32Service.has_recent_data().
HARDWARE_TIMEOUT_SECONDS = 3.0


class DataSourceManager:
    """
    Controls whether dashboard data comes from
    the simulator or live ESP32 hardware.

    Available selected modes:

    AUTO
        Automatically uses live ESP32 data when connected.
        Falls back to simulation when ESP32 is unavailable.

    SIMULATION
        Always uses simulated data.

    LIVE
        Always expects live ESP32 data.
    """

    MODE_AUTO = "AUTO"
    MODE_SIMULATION = "SIMULATION"
    MODE_LIVE = "LIVE"

    def __init__(self):
        self.selected_mode = self.MODE_AUTO
        self.active_mode = self.MODE_SIMULATION

    def update(self):
        """
        Determine the currently active data source.
        """

        if self.selected_mode == self.MODE_SIMULATION:
            self.active_mode = self.MODE_SIMULATION

        elif self.selected_mode == self.MODE_LIVE:
            self.active_mode = self.MODE_LIVE

        else:
            # ==================================================
            # AUTO MODE DETECTION
            # ==================================================
            # This used to check data.esp32_connected. That flag is
            # unreliable here, because the SIMULATOR also sets it to
            # True (to make the status lights look alive). The result
            # was a feedback loop:
            #
            #   sim runs -> sets esp32_connected=True
            #            -> manager thinks hardware arrived
            #            -> switches to LIVE, disables sim
            #            -> socket times out, sets connected=False
            #            -> switches back to SIMULATION
            #            -> repeat forever
            #
            # data.last_packet_time is only ever written by
            # ESP32Service when a genuine UDP packet is decoded, so
            # the simulator cannot fake it. That makes it a safe
            # signal for "is real hardware actually talking to us".
            # ==================================================

            if self.has_live_hardware():
                self.active_mode = self.MODE_LIVE
            else:
                self.active_mode = self.MODE_SIMULATION

    @staticmethod
    def has_live_hardware(timeout=HARDWARE_TIMEOUT_SECONDS):
        """
        True only when a real ESP32 packet arrived recently.
        """

        if data.last_packet_time == 0:
            return False

        return (time.time() - data.last_packet_time) < timeout

    def set_mode(self, mode):
        """
        Change the selected source mode.

        Valid values:
        AUTO, SIMULATION, LIVE
        """

        normalized_mode = str(mode).strip().upper()

        valid_modes = {
            self.MODE_AUTO,
            self.MODE_SIMULATION,
            self.MODE_LIVE,
        }

        if normalized_mode not in valid_modes:
            raise ValueError(
                f"Invalid data source mode: {mode}"
            )

        self.selected_mode = normalized_mode
        self.update()

    def set_auto_mode(self):
        self.set_mode(self.MODE_AUTO)

    def set_simulation_mode(self):
        self.set_mode(self.MODE_SIMULATION)

    def set_live_mode(self):
        self.set_mode(self.MODE_LIVE)

    def using_simulator(self):
        return self.active_mode == self.MODE_SIMULATION

    def using_hardware(self):
        return self.active_mode == self.MODE_LIVE

    def get_mode(self):
        """
        Return the active mode currently supplying data.
        """

        return self.active_mode

    def get_selected_mode(self):
        """
        Return the mode selected in Settings.
        """

        return self.selected_mode

    def is_auto_mode(self):
        return self.selected_mode == self.MODE_AUTO