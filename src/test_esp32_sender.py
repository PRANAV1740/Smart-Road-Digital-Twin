import json
import socket
import time


LAPTOP_IP = "127.0.0.1"
PORT = 5005

sensor_data = {
    "distance": 25,
    "depth": 8,
    "jerk": 3.4,
    "pitch": 1.2,
    "roll": 0.8,
    "speed": 16,
    "latitude": 28.6123,
    "longitude": 77.2295,
    "gps": "(28.6123, 77.2295)",
    "camera_connected": False,
    "gps_connected": True,
    "ultrasonic_connected": True,
    "imu_connected": True,
}

sock = socket.socket(
    socket.AF_INET,
    socket.SOCK_DGRAM,
)

while True:
    message = json.dumps(sensor_data).encode("utf-8")

    sock.sendto(
        message,
        (LAPTOP_IP, PORT),
    )

    print("Test ESP32 data sent")

    time.sleep(1)