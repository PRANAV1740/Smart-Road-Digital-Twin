"""
predict_new.py
--------------
Use the trained model on a NEW ride without re-training.

HOW TO RUN:
    python predict_new.py my_new_ride.csv

It loads roadsense_model.joblib (saved by the pipeline), windows your
new CSV, predicts each window, and generates an updated map.
"""

import sys
import numpy as np
import pandas as pd
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

COLORS = {"smooth": "green", "bump": "orange", "pothole": "red", "braking": "blue"}


def load_run(path):
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    return df


def make_windows(df, window_size, step):
    for start in range(0, len(df) - window_size + 1, step):
        yield df.iloc[start:start + window_size]


def extract_features(window, axes):
    feats = {}
    for ax in axes:
        v = window[ax].to_numpy()
        feats[f"{ax}_mean"]   = np.mean(v)
        feats[f"{ax}_std"]    = np.std(v)
        feats[f"{ax}_min"]    = np.min(v)
        feats[f"{ax}_max"]    = np.max(v)
        feats[f"{ax}_range"]  = np.ptp(v)
        feats[f"{ax}_rms"]    = np.sqrt(np.mean(v**2))
        feats[f"{ax}_energy"] = np.sum(v**2)
        feats[f"{ax}_mad"]    = np.mean(np.abs(v - np.mean(v)))
    return feats


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python predict_new.py <ride_csv_file>")
        print("Example: python predict_new.py my_ride.csv")
        sys.exit(1)

    ride_path = sys.argv[1]
    print(f"Loading model from roadsense_model.joblib...")
    bundle = joblib.load("roadsense_model.joblib")
    model = bundle["model"]
    feature_cols = bundle["features"]
    window_size = bundle["window"]
    axes = bundle["axes"]

    print(f"Reading {ride_path}...")
    df = load_run(ride_path)
    has_gps = {"lat", "lon"}.issubset(df.columns)

    records = []
    for w in make_windows(df, window_size, window_size):
        feats = extract_features(w, axes)
        X_row = pd.DataFrame([feats]).reindex(columns=feature_cols, fill_value=0)
        rec = {"pred": model.predict(X_row)[0]}
        if has_gps:
            rec["lat"] = w["lat"].mean()
            rec["lon"] = w["lon"].mean()
        records.append(rec)

    preds = pd.DataFrame(records)
    print(f"\nPredicted {len(preds)} windows:")
    print(preds["pred"].value_counts().to_string())

    # Save predictions to CSV
    preds.to_csv("predictions.csv", index=False)
    print("\nSaved → predictions.csv")

    # Build map
    if has_gps:
        import folium
        d = preds.dropna(subset=["lat", "lon"])
        center = [d["lat"].mean(), d["lon"].mean()]
        m = folium.Map(location=center, zoom_start=17)
        folium.PolyLine(d[["lat", "lon"]].values.tolist(),
                        color="gray", weight=2, opacity=0.4).add_to(m)
        for _, r in d.iterrows():
            folium.CircleMarker(
                [r["lat"], r["lon"]], radius=5,
                color=COLORS.get(r["pred"], "gray"),
                fill=True, fill_opacity=0.9, popup=str(r["pred"])
            ).add_to(m)
        legend = "<b>Road Quality</b><br>" + "<br>".join(
            f'<span style="color:{c}">&#9679;</span> {k}' for k, c in COLORS.items())
        m.get_root().html.add_child(folium.Element(
            f'<div style="position:fixed;bottom:20px;left:20px;z-index:9999;'
            f'background:white;padding:8px 12px;border:1px solid #999;'
            f'border-radius:6px;font-family:sans-serif;font-size:13px">{legend}</div>'))
        m.save("road_quality_map.html")
        print("Saved → road_quality_map.html")

        # static version
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.plot(d["lon"], d["lat"], color="lightgray", zorder=1)
        for cls, c in COLORS.items():
            sub = d[d["pred"] == cls]
            ax.scatter(sub["lon"], sub["lat"], c=c, label=cls, s=45, zorder=2)
        ax.set_xlabel("Longitude"); ax.set_ylabel("Latitude")
        ax.set_title("Road Quality Map"); ax.legend(); plt.tight_layout()
        plt.savefig("road_quality_map.png", dpi=150); plt.close()
        print("Saved → road_quality_map.png")

    print("\nDone!")
