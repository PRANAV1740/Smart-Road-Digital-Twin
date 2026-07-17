# ==================================================
# SMART ROAD DIGITAL TWIN - CENTRAL DATA STORE
# ==================================================

# ------------------------------
# Vehicle State
# ------------------------------
car_x = 80
car_y = 80
direction = "RIGHT"
speed = 0

# ------------------------------
# Road / Warning State
# ------------------------------
road_status = "SAFE"        # SAFE / WARNING / POTHOLE
warning_level = "SAFE"      # SAFE / CAUTION / DANGER
obstacle_ahead = False

# ------------------------------
# Ultrasonic Sensor
# ------------------------------
distance = 100              # distance in cm

# ------------------------------
# MPU6050 / Vibration Sensor
# ------------------------------
depth = 0
jerk = 0.3
pitch = 0.0
roll = 0.0

# ------------------------------
# GPS
# ------------------------------
gps = "(80, 80)"
latitude = 0.0
longitude = 0.0

# ------------------------------
# Camera
# ------------------------------
photos = 0
camera_status = "IDLE"

# ------------------------------
# Connection Status
# ------------------------------
esp32_connected = False
camera_connected = False
gps_connected = False
ultrasonic_connected = False
imu_connected = False

# ------------------------------
# Multiple Potholes
# ------------------------------
potholes = [
    {
        "id": 1,
        "x": 420,
        "y": 90,
        "depth": 9,
        "severity": "HIGH",
        "detected": False,
        "photo_captured": False,
    },
    {
        "id": 2,
        "x": 680,
        "y": 440,
        "depth": 6,
        "severity": "MEDIUM",
        "detected": False,
        "photo_captured": False,
    },
    {
        "id": 3,
        "x": 90,
        "y": 280,
        "depth": 11,
        "severity": "HIGH",
        "detected": False,
        "photo_captured": False,
    },
]

# Current pothole being detected
current_pothole_id = None
current_pothole_depth = 0
current_pothole_severity = "NONE"

# ------------------------------
# Event Counters
# ------------------------------
total_potholes_detected = 0
total_warnings = 0
# ------------------------------
# ESP32 Communication
# ------------------------------
system_mode = "SIMULATION"
packets_received = 0
last_packet_time = 0.0

# ------------------------------
# Machine Learning
# ------------------------------
# Written by services/ml_service.py, read by the widgets.

ml_active = False            # True once the model has made a prediction
ml_prediction = "smooth"     # smooth / pothole / bump / braking
ml_confidence = 0.0          # 0-100, how sure the model is
ml_total_classified = 0      # how many windows classified so far
ml_field_mode = "unknown"    # "raw" (ax/ay/az) or "processed" (jerk/pitch/roll)

ml_class_counts = {
    "smooth": 0,
    "pothole": 0,
    "bump": 0,
    "braking": 0,
}

# ml_authoritative decides WHO owns road_status / warning_level.
#
#   False -> the map widget owns them (simulation: the car drives a
#            scripted track past hardcoded potholes). ML still runs
#            and displays, but does not override the simulation.
#
#   True  -> the ML model owns them (live ESP32 data: there is no
#            scripted track, so the model's prediction IS the truth).
#
# dashboard.py flips this automatically when you switch modes.
ml_authoritative = False