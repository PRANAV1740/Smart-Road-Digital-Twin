# ==================================================
# SMART ROAD DIGITAL TWIN - SIMULATOR
# ==================================================
#
# Generates fake sensor data so the dashboard works without
# any hardware connected.
#
# --------------------------------------------------
# WHY THIS FILE CHANGED FOR ML
# --------------------------------------------------
# The old simulator produced single random numbers:
#     data.jerk = random.uniform(2.5, 4.5)
#
# That is fine for filling in a text label, but the ML model
# cannot learn anything from it, because a real pothole is not
# "a big number" - it is a SHAPE over time (a sharp spike, then
# a rebound). One random number has no shape.
#
# So this simulator now also generates a small BURST of realistic
# accelerometer samples on every tick, shaped like the real thing,
# and feeds them to the ML service. The model then has to genuinely
# recognise the pattern - exactly as it will with real hardware.
#
# The waveform shapes here mirror generate_sample_data.py, which
# is what the model was trained on.
# ==================================================

import math
import random
import sys
from pathlib import Path

_src_dir = str(Path(__file__).resolve().parent.parent)
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

try:
    from utils import data
except ImportError:
    from src.utils import data



# Dashboard calls update() every 300 ms.
# At 50 Hz that is 15 samples per tick.
SAMPLES_PER_TICK = 15


class Simulator:
    def __init__(self, ml_service=None):
        self.enabled = True
        self.ml_service = ml_service

        # Position within a bump's hump shape, so the hump is drawn
        # smoothly across several ticks instead of restarting.
        self.bump_phase = 0.0

        # Countdown so pothole spikes fire occasionally rather than
        # on literally every sample.
        self.samples_until_spike = 8

    # ==================================================
    # MAIN UPDATE
    # ==================================================

    def update(self):
        if not self.enabled:
            return

        # ----- Connection status -----
        data.esp32_connected = True
        data.camera_connected = False
        data.gps_connected = True

        # ----- Headline numbers for the sensor panel -----
        data.distance = random.randint(20, 120)

        if data.road_status == "POTHOLE":
            data.depth = random.randint(7, 12)
            data.jerk = round(random.uniform(2.5, 4.5), 2)
            data.speed = random.randint(8, 18)
        else:
            data.depth = 0
            data.jerk = round(random.uniform(0.2, 0.8), 2)
            data.speed = random.randint(28, 42)

        # ----- Waveform samples for the ML model -----
        self._feed_ml_samples()

    # ==================================================
    # WAVEFORM GENERATION
    # ==================================================

    def _feed_ml_samples(self):
        """
        Generate a burst of realistic accelerometer samples matching
        the current road status, and push them into the ML service.
        """

        if self.ml_service is None:
            return

        if not self.ml_service.is_ready():
            return

        status = data.road_status

        for _ in range(SAMPLES_PER_TICK):

            if status == "POTHOLE":
                sample = self._pothole_sample()

            elif status == "WARNING":
                # Approaching a pothole - the road is getting rough,
                # so this reads like a speed bump / rough patch.
                sample = self._bump_sample()

            else:
                sample = self._smooth_sample()

            self.ml_service.feed_reading(
                sample["x"],
                sample["y"],
                sample["z"],
            )

    def _smooth_sample(self):
        """Flat road: gravity on Z, near zero on X/Y, small noise."""

        return {
            "x": random.gauss(0.0, 0.02),
            "y": random.gauss(0.0, 0.02),
            "z": 1.0 + random.gauss(0.0, 0.02),
        }

    def _pothole_sample(self):
        """
        Pothole: mostly quiet, punctuated by sharp bipolar spikes.

        The wheel drops into the hole (Z jumps hard on impact), then
        rebounds (Z dips below rest), then settles. Brief and violent
        - that is what makes z_max and z_range large, which is what
        the model keys on.
        """

        self.samples_until_spike -= 1

        if self.samples_until_spike <= 0:
            # Reset the countdown for the next spike
            self.samples_until_spike = random.randint(6, 14)

            return {
                "x": random.gauss(0.0, 0.02) + random.uniform(-0.3, 0.3),
                "y": random.gauss(0.0, 0.02),
                "z": 1.0 + random.uniform(0.7, 1.1),
            }

        if self.samples_until_spike % 7 == 0:
            # The rebound, shortly after the impact
            return {
                "x": random.gauss(0.0, 0.02),
                "y": random.gauss(0.0, 0.02),
                "z": 1.0 - random.uniform(0.4, 0.7),
            }

        return self._smooth_sample()

    def _bump_sample(self):
        """
        Speed bump: a smooth, wide raised hump on Z.

        Modelled as a half sine wave spread over many samples.
        Compared with a pothole this has a LOWER peak but is much
        WIDER, which is exactly the difference the model learns.
        """

        self.bump_phase += 0.12

        if self.bump_phase > math.pi:
            self.bump_phase = 0.0

        hump = math.sin(self.bump_phase)
        amplitude = random.uniform(0.35, 0.55)

        return {
            "x": random.gauss(0.0, 0.02) - 0.1 * hump,
            "y": random.gauss(0.0, 0.02),
            "z": 1.0 + amplitude * hump + random.gauss(0.0, 0.02),
        }
