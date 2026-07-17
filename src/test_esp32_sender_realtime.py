# ==================================================
# SMART ROAD DIGITAL TWIN - REALISTIC ESP32 SENDER
# ==================================================
#
# This simulates what your ESP32 firmware SHOULD send once it is
# streaming real accelerometer data. Use it to test the ML path
# end-to-end before the hardware is ready.
#
# --------------------------------------------------
# HOW TO USE
# --------------------------------------------------
#   Terminal 1:   python main.py
#   Terminal 2:   python test_esp32_sender_realtime.py
#
# Then open the dashboard and watch the ML label in the sensor
# panel change between SMOOTH / POTHOLE / BUMP as this script
# cycles through road conditions.
#
# --------------------------------------------------
# WHY THIS IS DIFFERENT FROM test_esp32_sender.py
# --------------------------------------------------
# The old sender posted ONE packet per second with a single
# pre-decided "jerk" number. Two problems for ML:
#
#   1. The model needs 50 readings to make one decision.
#      At 1 packet/sec that is 50 seconds per prediction.
#
#   2. A single number has no SHAPE. The model classifies by
#      recognising the shape of an event over time.
#
# This sender fixes both. It sends a BATCH of raw samples in
# each packet:
#
#     {
#       "samples": [
#           {"ax": .., "ay": .., "az": ..},
#           ... 15 of them ...
#       ],
#       "distance": 40,
#       "latitude": 28.6139,
#       ...
#     }
#
# 15 samples every 300 ms = 50 samples/sec = 50 Hz.
# That gives the model a fresh prediction roughly every second.
#
# --------------------------------------------------
# WHAT TO TELL YOUR FIRMWARE PERSON
# --------------------------------------------------
# Match this packet shape:
#   - add a "samples" array of raw MPU6050 readings
#   - each entry has ax, ay, az
#   - send ~15 samples every 300 ms (or 50 every second)
#   - keep all the existing fields (distance, gps, etc.) as they are
#
# ml_service.py already understands this format. Nothing on the
# Python side needs to change when the firmware switches over.
# ==================================================

import json
import math
import random
import socket
import time


LAPTOP_IP = "127.0.0.1"
PORT = 5005

SAMPLE_RATE = 50          # Hz - matches the MPU6050 config
SEND_INTERVAL = 0.3       # seconds between packets
SAMPLES_PER_PACKET = int(SAMPLE_RATE * SEND_INTERVAL)   # 15

# How long to stay on each road condition, in seconds
SECONDS_PER_CONDITION = 8

CONDITION_CYCLE = ["smooth", "pothole", "smooth", "bump", "braking"]


class WaveformGenerator:
    """
    Produces accelerometer samples shaped like real road events.

    These shapes mirror generate_sample_data.py - the same shapes
    the model was trained on.
    """

    def __init__(self):
        self.bump_phase = 0.0
        self.samples_until_spike = 8
        self.brake_progress = 0.0

    def smooth(self):
        return {
            "ax": round(random.gauss(0.0, 0.02), 4),
            "ay": round(random.gauss(0.0, 0.02), 4),
            "az": round(1.0 + random.gauss(0.0, 0.02), 4),
        }

    def pothole(self):
        self.samples_until_spike -= 1

        if self.samples_until_spike <= 0:
            self.samples_until_spike = random.randint(6, 14)
            return {
                "ax": round(random.uniform(-0.3, 0.3), 4),
                "ay": round(random.gauss(0.0, 0.02), 4),
                "az": round(1.0 + random.uniform(0.7, 1.1), 4),
            }

        if self.samples_until_spike % 7 == 0:
            return {
                "ax": round(random.gauss(0.0, 0.02), 4),
                "ay": round(random.gauss(0.0, 0.02), 4),
                "az": round(1.0 - random.uniform(0.4, 0.7), 4),
            }

        return self.smooth()

    def bump(self):
        self.bump_phase += 0.12

        if self.bump_phase > math.pi:
            self.bump_phase = 0.0

        hump = math.sin(self.bump_phase)
        amplitude = random.uniform(0.35, 0.55)

        return {
            "ax": round(random.gauss(0.0, 0.02) - 0.1 * hump, 4),
            "ay": round(random.gauss(0.0, 0.02), 4),
            "az": round(1.0 + amplitude * hump + random.gauss(0.0, 0.02), 4),
        }

    def braking(self):
        # Sustained negative X. Barely touches Z - which is exactly
        # why the model needs X features to tell braking from smooth.
        self.brake_progress += 0.04

        if self.brake_progress > 1.0:
            self.brake_progress = 0.0

        ramp = math.sin(self.brake_progress * math.pi)

        return {
            "ax": round(-random.uniform(0.35, 0.5) * ramp, 4),
            "ay": round(random.gauss(0.0, 0.02), 4),
            "az": round(1.0 + 0.08 * ramp + random.gauss(0.0, 0.02), 4),
        }

    def get(self, condition):
        if condition == "pothole":
            return self.pothole()
        if condition == "bump":
            return self.bump()
        if condition == "braking":
            return self.braking()
        return self.smooth()


def main():
    generator = WaveformGenerator()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    condition_index = 0
    condition_started = time.time()
    packets_sent = 0

    # A slowly drifting GPS position, so the map has something to move
    latitude = 28.6139
    longitude = 77.2090

    print("=" * 55)
    print("  REALISTIC ESP32 SENDER")
    print("=" * 55)
    print(f"  Target        : {LAPTOP_IP}:{PORT}")
    print(f"  Sample rate   : {SAMPLE_RATE} Hz")
    print(f"  Packet every  : {SEND_INTERVAL}s "
          f"({SAMPLES_PER_PACKET} samples per packet)")
    print(f"  Cycling       : {' -> '.join(CONDITION_CYCLE)}")
    print(f"  Switching every {SECONDS_PER_CONDITION}s")
    print("=" * 55)
    print("  Press Ctrl+C to stop\n")

    try:
        while True:
            # ----- Rotate through road conditions -----
            if time.time() - condition_started > SECONDS_PER_CONDITION:
                condition_index = (condition_index + 1) % len(CONDITION_CYCLE)
                condition_started = time.time()
                print(f"\n>>> Now simulating: "
                      f"{CONDITION_CYCLE[condition_index].upper()}\n")

            condition = CONDITION_CYCLE[condition_index]

            # ----- Build the batch of raw samples -----
            samples = [
                generator.get(condition)
                for _ in range(SAMPLES_PER_PACKET)
            ]

            # ----- Drift the GPS a little -----
            latitude += random.gauss(0, 0.00002)
            longitude += random.gauss(0, 0.00002)

            # ----- Assemble the packet -----
            packet = {
                "samples": samples,

                # Everything below is unchanged from your existing
                # firmware format - the ML additions do not replace
                # any of it.
                "distance": random.randint(20, 120),
                "depth": 8 if condition == "pothole" else 0,
                "speed": 12 if condition == "pothole" else 35,
                "latitude": round(latitude, 6),
                "longitude": round(longitude, 6),
                "gps": f"({latitude:.5f}, {longitude:.5f})",
                "camera_connected": False,
                "gps_connected": True,
                "ultrasonic_connected": True,
                "imu_connected": True,
            }

            sock.sendto(
                json.dumps(packet).encode("utf-8"),
                (LAPTOP_IP, PORT),
            )

            packets_sent += 1

            if packets_sent % 10 == 0:
                print(f"  Sent {packets_sent} packets "
                      f"({packets_sent * SAMPLES_PER_PACKET} samples) "
                      f"| current: {condition}")

            time.sleep(SEND_INTERVAL)

    except KeyboardInterrupt:
        print("\n\nStopped. "
              f"Sent {packets_sent} packets total.")

    finally:
        sock.close()


if __name__ == "__main__":
    main()
