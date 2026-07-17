# RoadSense ML — Integrated into Smart Road Digital Twin

The machine learning is now wired into the dashboard. This file explains
what changed, where the ML lives, and how to run it.

---

## Which part is the ML?

**One file: `src/services/ml_service.py`.**

Everything else in the project is UI, sensors, or database. That file is
the brain. It is the only place a prediction is ever made.

Supporting it:

| File | Role in ML |
|---|---|
| `src/services/ml_service.py` | **The ML.** Buffers readings, extracts features, runs the model. |
| `src/roadsense_model.joblib` | The trained Random Forest, saved to disk. |
| `ml_training/roadsense_pipeline.py` | Trains the model. Run offline, not part of the app. |

---

## How to run it

### Simulation (no hardware needed)

```
cd src
python main.py
```

Look at the **sensor panel** on the right. The top line now reads
`ML: SMOOTH (99%)` and changes colour as the car drives past potholes.

### Live data path (test before hardware is ready)

Two terminals:

```
Terminal 1:   cd src && python main.py
Terminal 2:   cd src && python test_esp32_sender_realtime.py
```

The sender streams realistic 50 Hz accelerometer data and cycles through
smooth → pothole → smooth → bump → braking every 8 seconds. Watch the ML
label track it. The dashboard auto-detects the live data and switches
from SIMULATION to LIVE by itself.

---

## What changed

### New files

- `src/services/ml_service.py` — the ML service
- `src/roadsense_model.joblib` — the trained model
- `src/test_esp32_sender_realtime.py` — 50 Hz test sender
- `ml_training/` — the training scripts, moved out of the app

### Edited files

| File | Change |
|---|---|
| `utils/data.py` | Added ML fields at the bottom (`ml_prediction`, `ml_confidence`, `ml_authoritative`, etc.) |
| `services/esp32_service.py` | Takes an `ml_service`; feeds every packet to it |
| `services/simulator.py` | Now generates realistic **waveforms**, not single random numbers |
| `services/data_source_manager.py` | **Bug fix** — see below |
| `widgets/sensor_panel.py` | Shows the ML verdict + confidence |
| `widgets/map_widget.py` | Yields control of `road_status` to ML in live mode |
| `dashboard.py` | Creates one shared `MLService`, flips ML authority on mode change |

### Removed

- `analystics_panel.py` (root-level duplicate of `widgets/analytics_panel.py`, with a typo in the name)

---

## Two design decisions worth knowing

### 1. One ML service, two data sources

```
Simulator ------\
                 >---> MLService ---> data.py ---> all panels
ESP32Service ---/
```

The model does not know which source is talking to it. That is the whole
point — you can develop against the simulator and switch to real hardware
without touching any ML code.

### 2. `data.ml_authoritative` — who owns `road_status`?

This flag exists because there was a conflict. `map_widget.update_sensor_logic()`
was writing `road_status` every 40 ms based on the car's pixel distance to
hardcoded potholes. If ML also wrote it, they would fight.

- **Simulation** → `ml_authoritative = False`. The map owns `road_status`
  (the car drives a scripted track past known potholes). ML still runs and
  displays alongside — a live check that the model agrees with the twin.
- **Live** → `ml_authoritative = True`. There is no scripted track and no
  known pothole list, so the model's prediction *is* the detection.

`dashboard.py` flips this automatically. You do not set it by hand.

---

## Bug found and fixed during integration

`DataSourceManager` in AUTO mode decided sim-vs-live by checking
`data.esp32_connected`. But the **simulator also sets that flag to `True`**
to make the status lights look alive. That created a feedback loop:

```
sim runs -> sets esp32_connected=True
         -> manager thinks hardware arrived -> switches to LIVE
         -> simulator disabled
         -> socket times out -> esp32_connected=False
         -> switches back to SIMULATION -> repeat forever
```

The simulator was being switched off and on every second or so.

**Fix:** AUTO mode now checks `data.last_packet_time`, which is only ever
written when a genuine UDP packet is decoded. The simulator cannot fake it.

This was a pre-existing bug, unrelated to ML — but it had to be fixed
because `ml_authoritative` depends on knowing the mode correctly.

---

## IMPORTANT: the firmware needs one change

This is the single biggest thing standing between you and good accuracy.

**Current firmware sends:**
```json
{"jerk": 3.4, "pitch": 1.2, "roll": 0.8, "distance": 25, ...}
```

**It should also send raw MPU6050 values, in batches:**
```json
{
  "samples": [
    {"ax": 0.01, "ay": -0.02, "az": 1.03},
    {"ax": 0.02, "ay": -0.01, "az": 1.87},
    ... 15 of them ...
  ],
  "distance": 25, "gps": "...", ...
}
```

### Why it matters

1. **The model was trained on raw ax/ay/az.** Feeding it `jerk`/`pitch`/`roll`
   means feeding it numbers of a shape it never saw in training. It still
   works — `ml_service.py` falls back automatically — but accuracy drops.

2. **One packet per second is too slow.** The model needs 50 readings to make
   one decision. At 1 packet/sec that is 50 seconds per prediction. Batching
   15 samples per packet at 300 ms intervals gives 50 Hz and a prediction
   about every second.

The Python side already handles both formats. Nothing here needs to change
when the firmware switches over — `ml_service.py` detects which fields are
present and prints which mode it is using. The sensor panel shows it too.

Use `src/test_esp32_sender_realtime.py` as the reference for the packet
shape — it is exactly what the firmware should produce.

---

## Still placeholders (not ML-related)

These files are empty except for a header comment:

- `Sensors/mpu6050.py`, `Sensors/camera.py`, `Sensors/gps.py`,
  `Sensors/ultrasonic.py`
- `utils/constants.py`, `utils/helper.py`

Not a problem, but worth knowing if a reviewer opens them.

---

## Verified working

All of this was run and confirmed before hand-off:

- Model loads: 24 features, window 50, classes `[braking, bump, pothole, smooth]`
- Classification: 4/4 waveforms correct (smooth, pothole, bump, braking)
- Publishing to `data.py`: confirmed
- `ml_authoritative` gating: confirmed both directions
- Packet formats: batch, single-raw, and processed-fallback all work
- Garbage packets: handled without crashing
- Live path: dashboard + 50 Hz sender, ML tracked the condition cycle correctly
- Missing model: app still launches, ML stays off, no crash
