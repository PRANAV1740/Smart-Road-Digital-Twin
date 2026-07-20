import json
import socket
import threading
import time

from services.ml_service import MLService
from utils import data


class ESP32Service:
    def __init__(self, host="127.0.0.1", port=5005, ml_service=None):
        self.host = host
        self.port = port

        self.running = False
        self.thread = None
        self.socket = None
        self.last_received_time = 0.0

        # The ML classifier. Every packet that arrives gets fed into it.
        # Passed in from dashboard.py so the simulator can share the
        # same instance - one brain, two possible data sources.
        self.ml_service = ml_service or MLService()

    def start(self):
        if self.running:
            return

        self.running = True

        self.thread = threading.Thread(
            target=self._listen,
            daemon=True,
        )
        self.thread.start()

    def stop(self):
        self.running = False

        if self.socket is not None:
            try:
                self.socket.close()
            except OSError:
                pass

        self.socket = None

    def has_recent_data(self, timeout=3):
        if self.last_received_time == 0:
            return False

        return time.time() - self.last_received_time < timeout

    def _listen(self):
        try:
            self.socket = socket.socket(
                socket.AF_INET,
                socket.SOCK_DGRAM,
            )

            self.socket.setsockopt(
                socket.SOL_SOCKET,
                socket.SO_REUSEADDR,
                1,
            )

            self.socket.bind(
                ("0.0.0.0", self.port)
            )

            self.socket.settimeout(1.0)

            print(
                f"ESP32 receiver successfully bound to "
                f"{self.host}:{self.port}"
            )

            while self.running:
                try:
                    packet, address = self.socket.recvfrom(4096)

                    message = packet.decode("utf-8")
                    sensor_data = json.loads(message)

                    self.update_data(sensor_data)

                    current_time = time.time()

                    self.last_received_time = current_time
                    data.last_packet_time = current_time
                    data.packets_received += 1
                    data.esp32_connected = True
                    data.system_mode = "LIVE HARDWARE"

                    print(
                        f"Packet #{data.packets_received} received "
                        f"from {address[0]}:{address[1]}"
                    )

                except socket.timeout:
                    if not self.has_recent_data():
                        data.esp32_connected = False
                        data.system_mode = "SIMULATION"

                except json.JSONDecodeError as error:
                    print(f"Invalid JSON received: {error}")

                except OSError as error:
                    if self.running:
                        print(f"ESP32 socket error: {error}")
                    break

                except Exception as error:
                    print(f"ESP32 receiver error: {error}")

        except OSError as error:
            print(
                f"Could not bind UDP port {self.port}: {error}"
            )

        except Exception as error:
            print(f"Could not start ESP32 receiver: {error}")

        finally:
            data.esp32_connected = False
            data.system_mode = "SIMULATION"

            if self.socket is not None:
                try:
                    self.socket.close()
                except OSError:
                    pass

            self.socket = None

    def update_data(self, sensor_data):
        if "distance" in sensor_data:
            data.distance = float(sensor_data["distance"])

        if "depth" in sensor_data:
            data.depth = float(sensor_data["depth"])

        if "jerk" in sensor_data:
            data.jerk = float(sensor_data["jerk"])

        if "pitch" in sensor_data:
            data.pitch = float(sensor_data["pitch"])

        if "roll" in sensor_data:
            data.roll = float(sensor_data["roll"])

        if "speed" in sensor_data:
            data.speed = float(sensor_data["speed"])

        if "latitude" in sensor_data:
            data.latitude = float(sensor_data["latitude"])

        if "longitude" in sensor_data:
            data.longitude = float(sensor_data["longitude"])

        if "gps" in sensor_data:
            data.gps = str(sensor_data["gps"])

        if "camera_connected" in sensor_data:
            data.camera_connected = bool(
                sensor_data["camera_connected"]
            )

        if "gps_connected" in sensor_data:
            data.gps_connected = bool(
                sensor_data["gps_connected"]
            )

        if "ultrasonic_connected" in sensor_data:
            data.ultrasonic_connected = bool(
                sensor_data["ultrasonic_connected"]
            )

        if "imu_connected" in sensor_data:
            data.imu_connected = bool(
                sensor_data["imu_connected"]
            )

        # ==================================================
        # MACHINE LEARNING HOOK
        # ==================================================
        # Hand the whole packet to the ML service. It works out
        # for itself which fields to read:
        #
        #   {"samples": [...]}          -> a batch (best, real 50 Hz)
        #   {"ax":.., "ay":.., "az":..} -> one raw reading (good)
        #   {"jerk":.., "pitch":..}     -> one processed reading (works)
        #
        # See ml_service.py for the details.
        # ==================================================

        if self.ml_service is not None:
            self.ml_service.feed_packet(sensor_data)