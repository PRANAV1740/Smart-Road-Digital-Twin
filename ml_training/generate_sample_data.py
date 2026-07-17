"""
generate_sample_data.py
-----------------------
Creates fake-but-realistic sensor CSVs so you can test the whole pipeline
BEFORE you have real data. Once you record real runs, delete this file.

What it creates:
    smooth.csv   - flat road, just sensor noise
    pothole.csv  - frequent sharp Z-axis spikes (wheel dropping into holes)
    bump.csv     - smooth raised humps on Z (speed bumps)
    braking.csv  - sustained negative X (deceleration)
    ride.csv     - a mixed ride for prediction + mapping
"""

import numpy as np
import pandas as pd

np.random.seed(42)
FS = 50        # sampling rate in Hz (matches your MPU6050 setting)
DUR = 40       # seconds per run
N = FS * DUR   # total samples per run
DELHI = (28.6139, 77.2090)   # starting GPS point


def gps_track(lat0, lon0, n, heading_deg=45.0, speed_mps=4.0):
    lat, lon = lat0, lon0
    heading = np.deg2rad(heading_deg)
    lats, lons = [], []
    for _ in range(n):
        heading += np.random.normal(0, 0.01)
        dist = speed_mps / FS
        dlat = (dist * np.cos(heading)) / 111320.0
        dlon = (dist * np.sin(heading)) / (111320.0 * np.cos(np.deg2rad(lat)))
        lat += dlat
        lon += dlon
        lats.append(lat)
        lons.append(lon)
    return np.array(lats), np.array(lons)


def base_signal(n):
    x = np.random.normal(0, 0.02, n)
    y = np.random.normal(0, 0.02, n)
    z = 1.0 + np.random.normal(0, 0.02, n)
    return x, y, z


def add_potholes(x, y, z, every=35):
    for i in range(every, len(z) - 5, every + np.random.randint(-8, 8)):
        z[i]     += np.random.uniform(0.7, 1.1)
        z[i + 1] -= np.random.uniform(0.4, 0.7)
        z[i + 2] += np.random.uniform(0.1, 0.3)
        x[i]     += np.random.uniform(-0.3, 0.3)
    return x, y, z


def add_bumps(x, y, z, every=55):
    width = 18
    hump = np.sin(np.linspace(0, np.pi, width))
    for i in range(20, len(z) - width, every + np.random.randint(-6, 6)):
        amp = np.random.uniform(0.35, 0.55)
        z[i:i + width] += amp * hump
        x[i:i + width] -= 0.1 * hump
    return x, y, z


def add_braking(x, y, z, every=90):
    dur = 55
    ramp = np.concatenate([np.linspace(0, 1, 10),
                           np.ones(dur - 20),
                           np.linspace(1, 0, 10)])
    for i in range(20, len(z) - dur, every + np.random.randint(-10, 10)):
        x[i:i + dur] -= np.random.uniform(0.35, 0.5) * ramp
        z[i:i + dur] += 0.08 * ramp
    return x, y, z


def make_run(kind, heading):
    x, y, z = base_signal(N)
    if kind == "pothole":
        x, y, z = add_potholes(x, y, z)
    elif kind == "bump":
        x, y, z = add_bumps(x, y, z)
    elif kind == "braking":
        x, y, z = add_braking(x, y, z)
    lats, lons = gps_track(*DELHI, N, heading_deg=heading)
    t = np.arange(N) / FS
    return pd.DataFrame({"timestamp": t, "x": x, "y": y, "z": z,
                         "lat": lats, "lon": lons})


# ---- Generate 4 labeled training files ----
make_run("smooth",   10).to_csv("smooth.csv",   index=False)
make_run("pothole",  40).to_csv("pothole.csv",  index=False)
make_run("bump",     70).to_csv("bump.csv",     index=False)
make_run("braking", 100).to_csv("braking.csv",  index=False)

# ---- Generate 1 mixed ride for prediction + mapping ----
segments = []
lat, lon = DELHI
heading = 30.0
plan = ["smooth", "pothole", "smooth", "bump", "braking", "smooth", "pothole"]
t0 = 0.0
for kind in plan:
    seg = make_run(kind, heading).iloc[:300].copy()
    lats, lons = gps_track(lat, lon, len(seg), heading_deg=heading)
    seg["lat"], seg["lon"] = lats, lons
    seg["timestamp"] = t0 + np.arange(len(seg)) / FS
    lat, lon, t0 = lats[-1], lons[-1], seg["timestamp"].iloc[-1]
    heading += 15
    segments.append(seg)
pd.concat(segments, ignore_index=True).to_csv("ride.csv", index=False)

print("Created: smooth.csv, pothole.csv, bump.csv, braking.csv, ride.csv")
print("You're ready to run the pipeline!")
