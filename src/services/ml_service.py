# ==================================================
# SMART ROAD DIGITAL TWIN - ML SERVICE
# ==================================================
#
# THIS IS THE MACHINE LEARNING PART OF THE PROJECT.
#
# Everything else in this app is UI, sensors, or database.
# This file is the "brain" that decides what the road is.
#
# --------------------------------------------------
# HOW IT WORKS
# --------------------------------------------------
# 1. Sensor readings arrive one at a time (or in batches)
# 2. We store them in a buffer (a waiting queue)
# 3. When the buffer holds a full window (50 readings = 1 second),
#    we summarise that window into 24 statistics ("features")
# 4. The trained Random Forest model looks at those 24 numbers
#    and answers: smooth / pothole / bump / braking
# 5. We write the answer into utils/data.py, which every panel reads
#
# --------------------------------------------------
# WHERE THE DATA COMES FROM
# --------------------------------------------------
# SIMULATION MODE : services/simulator.py generates fake waveforms
# LIVE MODE       : services/esp32_service.py receives real UDP packets
#
# Both call feed_reading(). The ML service does not know or care
# which one is talking to it. That is what makes it swappable.
#
# --------------------------------------------------
# THE MODEL FILE
# --------------------------------------------------
# roadsense_model.joblib must sit in the src/ folder.
# It is produced by running roadsense_pipeline.py.
# If it is missing, the app still runs - ML just stays disabled
# and the dashboard falls back to the old threshold logic.
# ==================================================

from collections import deque
from pathlib import Path
import sys
import time

# Ensure src directory is in sys.path for robust internal package imports
_src_dir = str(Path(__file__).resolve().parent.parent)
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

try:
    from utils import data
except ImportError:
    from src.utils import data

try:
    from database.database import save_pothole
except ImportError:
    from src.database.database import save_pothole



# --------------------------------------------------
# Optional imports
# --------------------------------------------------
# We import numpy / pandas / joblib defensively so that the
# dashboard NEVER crashes just because ML libraries are missing.
# --------------------------------------------------

ML_LIBRARIES_AVAILABLE = True
IMPORT_ERROR_MESSAGE = ""

try:
    import numpy as np
    import pandas as pd
    import joblib
except ImportError as import_error:
    ML_LIBRARIES_AVAILABLE = False
    IMPORT_ERROR_MESSAGE = str(import_error)


# --------------------------------------------------
# Field name candidates
# --------------------------------------------------
# The ESP32 firmware may send raw accelerometer values under
# different names depending on who wrote it. We try each name
# in order and use the first one we find.
#
# RAW values (ax/ay/az) are what the model was trained on and
# give the best accuracy.
#
# PROCESSED values (jerk/pitch/roll) are what the current
# firmware sends. They work, but accuracy will be lower because
# the model never saw values of that shape during training.
# --------------------------------------------------

RAW_FIELD_NAMES = {
    "x": ("ax", "acc_x", "accel_x", "x"),
    "y": ("ay", "acc_y", "accel_y", "y"),
    "z": ("az", "acc_z", "accel_z", "z"),
}

PROCESSED_FIELD_NAMES = {
    "x": ("pitch",),
    "y": ("roll",),
    "z": ("jerk",),
}


class MLService:
    """
    Real-time road condition classifier.

    Public methods you will actually call:

        is_ready()              -> True if the model loaded successfully
        feed_reading(x, y, z)   -> push ONE accelerometer reading
        feed_packet(dict)       -> push a whole ESP32 JSON packet
        get_summary()           -> stats dict for analytics panels
        reset()                 -> clear buffer and counters
    """

    def __init__(self, model_path=None, window_size=None, overlap=True):

        # ----- Model state -----
        self.model = None
        self.feature_columns = None
        self.window_size = window_size or 50
        self.axes = ("z", "x", "y")
        self.loaded = False
        self.status_message = "Not loaded"

        # ----- Reading buffer -----
        # deque = a list with a maximum length. When it is full and
        # you append, the oldest item falls off the front automatically.
        self.buffer = deque(maxlen=400)

        # overlap=True  -> slide the window forward by half each time
        #                  (more frequent predictions, smoother UI)
        # overlap=False -> clear the buffer after each prediction
        #                  (matches training exactly, fewer predictions)
        self.overlap = overlap

        # ----- Prediction state -----
        self.last_prediction = "smooth"
        self.last_confidence = 0.0
        self.prediction_history = deque(maxlen=200)

        # ----- Counters -----
        self.total_classified = 0
        self.class_counts = {
            "smooth": 0,
            "pothole": 0,
            "bump": 0,
            "braking": 0,
        }
        
        # ----- DB Cooldown -----
        self.last_db_save_time = 0.0

        # ----- Field detection -----
        # Set to "raw" or "processed" the first time a packet arrives.
        self.field_mode = None

        self._load_model(model_path)

    # ==================================================
    # MODEL LOADING
    # ==================================================

    def _resolve_model_path(self, model_path):
        """Find roadsense_model.joblib, checking a few sensible places."""

        if model_path is not None:
            return Path(model_path)

        # This file lives in src/services/, so parent.parent is src/
        src_directory = Path(__file__).resolve().parent.parent

        candidates = [
            src_directory / "roadsense_model.joblib",
            src_directory / "models" / "roadsense_model.joblib",
            src_directory.parent / "roadsense_model.joblib",
        ]

        for candidate in candidates:
            if candidate.exists():
                return candidate

        return candidates[0]

    def _load_model(self, model_path):
        """Load the trained Random Forest from disk."""

        if not ML_LIBRARIES_AVAILABLE:
            self.status_message = (
                f"ML libraries missing ({IMPORT_ERROR_MESSAGE}). "
                f"Run: pip install numpy pandas scikit-learn joblib"
            )
            print(f"[ML] {self.status_message}")
            return

        resolved_path = self._resolve_model_path(model_path)

        if not resolved_path.exists():
            self.status_message = f"Model file not found: {resolved_path}"
            print(f"[ML] {self.status_message}")
            print("[ML] Run roadsense_pipeline.py, then copy "
                  "roadsense_model.joblib into the src/ folder.")
            return

        try:
            bundle = joblib.load(str(resolved_path))

            self.model = bundle["model"]
            self.feature_columns = bundle["features"]
            self.window_size = bundle.get("window", self.window_size)
            self.axes = tuple(bundle.get("axes", self.axes))
            self.loaded = True
            self.status_message = "Model loaded"

            print(f"[ML] Model loaded from {resolved_path}")
            print(f"[ML] Window size : {self.window_size} readings")
            print(f"[ML] Features    : {len(self.feature_columns)}")
            print(f"[ML] Classes     : {list(self.model.classes_)}")

        except Exception as error:
            self.status_message = f"Failed to load model: {error}"
            print(f"[ML] {self.status_message}")

    def is_ready(self):
        """True when the model is loaded and can make predictions."""
        return self.loaded and self.model is not None

    # ==================================================
    # DATA INPUT
    # ==================================================

    def feed_reading(self, x, y, z):
        """
        Push ONE accelerometer reading into the buffer.

        Call this once per sensor sample. When enough samples
        accumulate to fill a window, classification happens
        automatically.
        """

        if not self.is_ready():
            return

        try:
            self.buffer.append({
                "x": float(x),
                "y": float(y),
                "z": float(z),
            })
        except (TypeError, ValueError):
            return

        if len(self.buffer) >= self.window_size:
            self._classify_window()

    def feed_packet(self, packet):
        """
        Push a whole ESP32 JSON packet.

        This handles three shapes of packet:

        1. BATCH (best for real-time at 50 Hz):
           {"samples": [{"ax":.., "ay":.., "az":..}, ...]}

        2. SINGLE RAW:
           {"ax": 0.01, "ay": -0.02, "az": 1.01, ...}

        3. SINGLE PROCESSED (what current firmware sends):
           {"jerk": 3.4, "pitch": 1.2, "roll": 0.8, ...}
        """

        if not self.is_ready() or not isinstance(packet, dict):
            return

        # ----- Shape 1: a batch of samples -----
        samples = packet.get("samples")

        if isinstance(samples, list) and samples:
            for sample in samples:
                if isinstance(sample, dict):
                    self._feed_single_dict(sample)
            return

        # ----- Shape 2 / 3: one reading in the packet itself -----
        self._feed_single_dict(packet)

    def _feed_single_dict(self, sample):
        """Pull x/y/z out of a dict, whatever the field names are."""

        values = self._extract_axis_values(sample)

        if values is None:
            return

        self.feed_reading(values["x"], values["y"], values["z"])

    def _extract_axis_values(self, sample):
        """
        Find the x/y/z values in a dict.

        Tries raw field names first (ax/ay/az). Falls back to
        processed names (pitch/roll/jerk). Remembers which mode
        worked so we can show it in the UI.
        """

        # --- Try raw first ---
        raw_values = {}
        raw_found = True

        for axis, candidates in RAW_FIELD_NAMES.items():
            value = self._first_present(sample, candidates)
            if value is None:
                raw_found = False
                break
            raw_values[axis] = value

        if raw_found:
            if self.field_mode != "raw":
                self.field_mode = "raw"
                data.ml_field_mode = "raw"
                print("[ML] Using RAW accelerometer fields (ax/ay/az). "
                      "This is the accurate path.")
            return raw_values

        # --- Fall back to processed ---
        processed_values = {}

        for axis, candidates in PROCESSED_FIELD_NAMES.items():
            value = self._first_present(sample, candidates)
            if value is None:
                return None
            processed_values[axis] = value

        if self.field_mode != "processed":
            self.field_mode = "processed"
            data.ml_field_mode = "processed"
            print("[ML] Using PROCESSED fields (jerk/pitch/roll). "
                  "Accuracy will be reduced - see notes in ml_service.py.")

        return processed_values

    @staticmethod
    def _first_present(sample, candidate_names):
        """Return the first candidate key that exists in the dict."""

        for name in candidate_names:
            if name in sample:
                try:
                    return float(sample[name])
                except (TypeError, ValueError):
                    return None

        return None

    # ==================================================
    # FEATURE EXTRACTION
    # ==================================================

    def _extract_features(self, window):
        """
        Turn a window of readings into 24 summary numbers.

        This MUST match extract_features() in roadsense_pipeline.py
        exactly - same statistics, same names, same order.
        If you change one, you must change both and retrain.
        """

        features = {}

        for axis in self.axes:
            values = np.array(
                [reading[axis] for reading in window],
                dtype=float,
            )

            features[f"{axis}_mean"]   = np.mean(values)
            features[f"{axis}_std"]    = np.std(values)
            features[f"{axis}_min"]    = np.min(values)
            features[f"{axis}_max"]    = np.max(values)
            features[f"{axis}_range"]  = np.ptp(values)
            features[f"{axis}_rms"]    = np.sqrt(np.mean(values ** 2))
            features[f"{axis}_energy"] = np.sum(values ** 2)
            features[f"{axis}_mad"]    = np.mean(
                np.abs(values - np.mean(values))
            )

        return features

    # ==================================================
    # CLASSIFICATION
    # ==================================================

    def _classify_window(self):
        """Take the newest full window, classify it, publish the result."""

        window = list(self.buffer)[-self.window_size:]

        features = self._extract_features(window)

        # reindex() forces the columns into the exact order the model
        # was trained with. Without this, a shuffled column order would
        # silently produce wrong predictions with no error message.
        feature_row = pd.DataFrame([features]).reindex(
            columns=self.feature_columns,
            fill_value=0,
        )

        try:
            prediction = self.model.predict(feature_row)[0]
        except Exception as error:
            print(f"[ML] Prediction failed: {error}")
            return

        confidence = self._get_confidence(feature_row, prediction)

        # ----- Update state -----
        self.last_prediction = str(prediction)
        self.last_confidence = confidence
        self.total_classified += 1
        self.prediction_history.append(str(prediction))

        if prediction in self.class_counts:
            self.class_counts[prediction] += 1

        self._publish(str(prediction), confidence)

        # ----- Advance the buffer -----
        if self.overlap:
            # Drop the oldest half. The next prediction arrives after
            # another half-window of readings, so the UI updates twice
            # as often without the model seeing anything twice in a row.
            for _ in range(self.window_size // 2):
                if self.buffer:
                    self.buffer.popleft()
        else:
            self.buffer.clear()

    def _get_confidence(self, feature_row, prediction):
        """How sure is the forest? Fraction of trees that voted this way."""

        try:
            probabilities = self.model.predict_proba(feature_row)[0]
            class_list = list(self.model.classes_)
            return float(probabilities[class_list.index(prediction)])
        except Exception:
            return 1.0

    # ==================================================
    # PUBLISH TO THE SHARED DATA STORE
    # ==================================================

    def _publish(self, prediction, confidence):
        """
        Write results into utils/data.py.

        Every panel in the dashboard reads from data.py on its own
        timer, so writing here is all it takes to update the whole UI.
        """

        # ----- ML-specific fields -----
        data.ml_prediction = prediction
        data.ml_confidence = round(confidence * 100, 1)
        data.ml_total_classified = self.total_classified
        data.ml_class_counts = dict(self.class_counts)
        data.ml_active = True

        # ----- Drive the existing status system -----
        # Only take control when ML is authoritative. In simulation mode
        # the map widget owns road_status (it drives the car around a
        # scripted track), so we leave it alone and just display our
        # prediction alongside.
        if not data.ml_authoritative:
            return

        if prediction == "pothole":
            data.road_status = "POTHOLE"
            data.warning_level = "DANGER"
            
            # Cooldown logic for saving
            current_time = time.time()
            if current_time - self.last_db_save_time > 3.0:
                self.last_db_save_time = current_time
                
                # Severity by confidence
                if confidence >= 0.90:
                    severity = "HIGH"
                elif confidence >= 0.70:
                    severity = "MEDIUM"
                else:
                    severity = "LOW"
                    
                # Setup pothole data
                pothole_id = f"ML_{int(current_time * 1000)}"
                depth = getattr(data, "depth", 0.0)
                
                data.current_pothole_id = pothole_id
                data.current_pothole_depth = depth
                data.current_pothole_severity = severity
                
                # Execute database save
                save_pothole(
                    pothole_id=pothole_id,
                    x=0.0,
                    y=0.0,
                    depth=depth,
                    severity=severity,
                    latitude=getattr(data, "latitude", 0.0),
                    longitude=getattr(data, "longitude", 0.0),
                    photo_captured=False,
                )
                print(f"[ML] Pothole {pothole_id} saved to database.")
                
                # Signal map_widget to take screenshot asynchronously
                data.ml_capture_requested = True
                data.ml_capture_pothole_id = pothole_id

        elif prediction == "bump":
            data.road_status = "BUMP"
            data.warning_level = "CAUTION"

        elif prediction == "braking":
            data.road_status = "BRAKING"
            data.warning_level = "SAFE"

        else:
            data.road_status = "SAFE"
            data.warning_level = "SAFE"

    # ==================================================
    # REPORTING
    # ==================================================

    def get_summary(self):
        """Stats dict, handy for analytics panels."""

        total = max(self.total_classified, 1)

        return {
            "loaded": self.loaded,
            "status": self.status_message,
            "field_mode": self.field_mode or "unknown",
            "total_classified": self.total_classified,
            "last_prediction": self.last_prediction,
            "last_confidence": round(self.last_confidence * 100, 1),
            "buffer_fill": len(self.buffer),
            "window_size": self.window_size,
            "class_counts": dict(self.class_counts),
            "pothole_rate": round(
                self.class_counts["pothole"] / total * 100, 1
            ),
            "bump_rate": round(
                self.class_counts["bump"] / total * 100, 1
            ),
            "smooth_rate": round(
                self.class_counts["smooth"] / total * 100, 1
            ),
            "braking_rate": round(
                self.class_counts["braking"] / total * 100, 1
            ),
        }

    def reset(self):
        """Clear the buffer and all counters."""

        self.buffer.clear()
        self.prediction_history.clear()
        self.total_classified = 0
        self.class_counts = {
            "smooth": 0,
            "pothole": 0,
            "bump": 0,
            "braking": 0,
        }
        self.last_prediction = "smooth"
        self.last_confidence = 0.0

        data.ml_prediction = "smooth"
        data.ml_confidence = 0.0
        data.ml_total_classified = 0
        data.ml_class_counts = dict(self.class_counts)
