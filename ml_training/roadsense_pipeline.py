"""
==========================================================================
  RoadSense — Complete ML Pipeline
  Pothole Detection & Road Quality Mapping from IoT Sensor Data
==========================================================================

  HOW TO RUN (in your terminal):
      python generate_sample_data.py      # first time only — makes demo CSVs
      python roadsense_pipeline.py        # trains, evaluates, predicts, maps

  WHEN YOU HAVE REAL DATA:
      Replace smooth.csv / pothole.csv / bump.csv / braking.csv with your
      real recordings. Put a new ride in ride.csv. Run this script again.
      That's it — nothing else changes.
==========================================================================
"""

# ========================================================================
# IMPORTS
# ========================================================================
import numpy as np
import pandas as pd
import joblib
import matplotlib
matplotlib.use("Agg")          # saves plots as image files (no GUI popup)
import matplotlib.pyplot as plt

from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.metrics import (accuracy_score, classification_report,
                             confusion_matrix, ConfusionMatrixDisplay)


# ========================================================================
# CONFIG — the ONLY part you normally edit
# ========================================================================

# Each CSV is a separate labeled run (one road condition per file)
FILE_LABELS = {
    "smooth.csv":   "smooth",
    "pothole.csv":  "pothole",
    "bump.csv":     "bump",
    "braking.csv":  "braking",
}

RIDE_FILE    = "ride.csv"          # new unlabeled ride to predict + map
WINDOW_SIZE  = 50                  # 50 readings @ 50 Hz = 1 second
STEP         = 50                  # non-overlapping; use 25 for 50% overlap
AXES         = ("z", "x", "y")    # Z is the pothole axis (vertical)
MODEL_PATH   = "roadsense_model.joblib"

# Colors for the map
COLORS = {
    "smooth":  "green",
    "bump":    "orange",
    "pothole": "red",
    "braking": "blue",
}


# ========================================================================
# STEP 1 — LOAD labeled CSV files
# ========================================================================
#
#   WHAT'S HAPPENING:
#   Each CSV has columns like: timestamp, x, y, z, lat, lon
#   x = sideways acceleration
#   y = forward/backward acceleration
#   z = vertical acceleration (THIS is the pothole axis)
#   We just read them and clean up column names.
#
def load_run(path):
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    for ax in ("x", "y", "z"):
        if ax not in df.columns:
            raise ValueError(f"{path} is missing column '{ax}'. Found: {list(df.columns)}")
    return df


# ========================================================================
# STEP 2 — WINDOW the data into chunks
# ========================================================================
#
#   WHY WE WINDOW:
#   A single accelerometer reading is just one number — meaningless alone.
#   A pothole is a SHAPE over time: a sudden spike + rebound.
#   A speed bump is a different shape: a smooth wide hump.
#
#   So we slice the continuous signal into "windows" of 50 readings each.
#   At 50 Hz, that's exactly 1 second of driving per window.
#   Each window becomes ONE training example for the model.
#
#   Think of it like this:
#       raw data:    [-------- 40 seconds of driving --------]
#       windowed:    [1s][1s][1s][1s][1s]...[1s]  → 40 windows
#       each window: one training example
#
def make_windows(df, window_size=WINDOW_SIZE, step=STEP):
    n = len(df)
    for start in range(0, n - window_size + 1, step):
        yield df.iloc[start:start + window_size]


# ========================================================================
# STEP 3 — EXTRACT FEATURES from each window
# ========================================================================
#
#   WHY WE EXTRACT FEATURES:
#   A Random Forest can't eat 50 raw rows. It needs a FIXED list of
#   numbers per window. So we summarize each 1-second window into
#   statistics. Each statistic answers a physical question:
#
#       mean    → average offset (braking pulls X's mean negative)
#       std     → how shaky the ride was (roughness)
#       min     → deepest downward jolt
#       max     → biggest upward jolt (pothole impact peak)
#       range   → max - min = peak-to-peak swing (severity)
#       rms     → root mean square = vibration magnitude
#       energy  → sum of squares = total "oomph" in the window
#       mad     → mean absolute deviation = robust roughness
#
#   We compute these for Z (vertical), X, and Y.
#   That gives 8 features × 3 axes = 24 features per window.
#
def extract_features(window, axes=AXES):
    feats = {}
    for ax in axes:
        v = window[ax].to_numpy()
        feats[f"{ax}_mean"]   = np.mean(v)
        feats[f"{ax}_std"]    = np.std(v)
        feats[f"{ax}_min"]    = np.min(v)
        feats[f"{ax}_max"]    = np.max(v)
        feats[f"{ax}_range"]  = np.ptp(v)               # ptp = peak to peak
        feats[f"{ax}_rms"]    = np.sqrt(np.mean(v**2))
        feats[f"{ax}_energy"] = np.sum(v**2)
        feats[f"{ax}_mad"]    = np.mean(np.abs(v - np.mean(v)))
    return feats


def build_dataset(file_labels):
    """
    Loops over every labeled file → windows it → extracts features → stacks rows.
    Returns X (feature matrix) and y (labels).
    """
    rows = []
    labels = []
    for path, label in file_labels.items():
        df = load_run(path)
        for w in make_windows(df):
            rows.append(extract_features(w))
            labels.append(label)
    X = pd.DataFrame(rows)
    y = pd.Series(labels, name="label")
    return X, y


# ========================================================================
# STEP 4 + 5 — TRAIN, COMPARE MODELS, and EVALUATE
# ========================================================================
#
#   WHAT'S HAPPENING:
#   1. Split data into 75% train / 25% test (stratified = balanced classes)
#   2. Train a Random Forest (200 decision trees voting together)
#   3. Also test Decision Tree, k-NN, Logistic Regression for comparison
#   4. Pick the best, tune it, and evaluate with:
#       - Accuracy score (% correct)
#       - Per-class precision/recall/F1
#       - Confusion matrix (which classes get mixed up)
#       - 5-fold cross-validation (more trustworthy than one split)
#
def train_and_evaluate(X, y):

    # --- Split ---
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    # --- Compare multiple models ---
    print("=" * 60)
    print("MODEL COMPARISON (5-fold cross-validation)")
    print("=" * 60)
    models = {
        "Random Forest":       RandomForestClassifier(n_estimators=200, random_state=42),
        "Decision Tree":       DecisionTreeClassifier(random_state=42),
        "k-Nearest Neighbors": KNeighborsClassifier(n_neighbors=5),
        "Logistic Regression": LogisticRegression(max_iter=1000),
    }
    for name, model in models.items():
        scores = cross_val_score(model, X, y, cv=5)
        print(f"  {name:25s}  accuracy: {scores.mean():.3f} (+/- {scores.std():.3f})")
    print()

    # --- Tune the Random Forest ---
    print("Tuning Random Forest...")
    grid = GridSearchCV(
        RandomForestClassifier(random_state=42),
        {"n_estimators": [100, 200], "max_depth": [None, 6, 10]},
        cv=5
    )
    grid.fit(X, y)
    print(f"  Best params: {grid.best_params_}")
    print(f"  Best CV accuracy: {grid.best_score_:.3f}\n")

    clf = grid.best_estimator_

    # --- Final evaluation on held-out test set ---
    clf.fit(X_train, y_train)     # refit on the train split
    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)

    print("=" * 60)
    print("FINAL EVALUATION (on 25% held-out test set)")
    print("=" * 60)
    print(f"  Test accuracy: {acc:.3f}\n")
    print(classification_report(y_test, y_pred))

    cv = cross_val_score(clf, X, y, cv=5)
    print(f"  5-fold CV accuracy: {cv.mean():.3f} (+/- {cv.std():.3f})\n")

    # --- Plot: Confusion Matrix ---
    labels_sorted = sorted(y.unique())
    cm = confusion_matrix(y_test, y_pred, labels=labels_sorted)
    fig, ax = plt.subplots(figsize=(6, 5))
    ConfusionMatrixDisplay(cm, display_labels=labels_sorted).plot(cmap="Blues", ax=ax, values_format="d")
    plt.title("Confusion Matrix")
    plt.tight_layout()
    plt.savefig("confusion_matrix.png", dpi=150)
    plt.close()
    print("  Saved → confusion_matrix.png")

    # --- Plot: Feature Importance ---
    imp = pd.Series(clf.feature_importances_, index=X.columns).sort_values()
    fig, ax = plt.subplots(figsize=(7, 5))
    imp.tail(12).plot(kind="barh", ax=ax, color="#4A90D9")
    plt.title("Top 12 Feature Importances")
    plt.xlabel("Importance")
    plt.tight_layout()
    plt.savefig("feature_importance.png", dpi=150)
    plt.close()
    print("  Saved → feature_importance.png")

    return clf, list(X.columns)


# ========================================================================
# STEP 6 — PREDICT on a new ride
# ========================================================================
#
#   WHAT'S HAPPENING:
#   We take a new ride (ride.csv), window it EXACTLY like training,
#   extract the SAME features, and ask the model to classify each window.
#   We also grab the average GPS coordinates for each window so we can
#   place the prediction on a map.
#
def predict_ride(clf, feature_cols, ride_path):
    df = load_run(ride_path)
    has_gps = {"lat", "lon"}.issubset(df.columns)

    records = []
    for w in make_windows(df):
        feats = extract_features(w)
        X_row = pd.DataFrame([feats]).reindex(columns=feature_cols, fill_value=0)
        pred = clf.predict(X_row)[0]
        rec = {"pred": pred}
        if has_gps:
            rec["lat"] = w["lat"].mean()
            rec["lon"] = w["lon"].mean()
        records.append(rec)

    out = pd.DataFrame(records)
    print("=" * 60)
    print(f"PREDICTIONS on {ride_path} ({len(out)} windows)")
    print("=" * 60)
    print(out["pred"].value_counts().to_string())
    print()
    return out


# ========================================================================
# STEP 7 — BUILD THE MAP
# ========================================================================
#
#   WHAT'S HAPPENING:
#   Each window gets a colored dot on the map at its GPS location.
#       Green  = smooth road
#       Orange = speed bump
#       Red    = pothole
#       Blue   = braking
#
#   We make TWO versions:
#       1. road_quality_map.html  → interactive (open in browser, zoom/pan)
#       2. road_quality_map.png   → static image (for your report/presentation)
#
def build_map_interactive(pred_df, out_html="road_quality_map.html"):
    if not {"lat", "lon"}.issubset(pred_df.columns):
        print("  No GPS data → skipping interactive map.")
        return
    import folium
    d = pred_df.dropna(subset=["lat", "lon"])
    center = [d["lat"].mean(), d["lon"].mean()]
    m = folium.Map(location=center, zoom_start=17)

    # faint gray route line
    folium.PolyLine(d[["lat", "lon"]].values.tolist(),
                    color="gray", weight=2, opacity=0.4).add_to(m)

    # colored dots per window
    for _, r in d.iterrows():
        folium.CircleMarker(
            location=[r["lat"], r["lon"]],
            radius=5,
            color=COLORS.get(r["pred"], "gray"),
            fill=True, fill_opacity=0.9,
            popup=str(r["pred"]),
        ).add_to(m)

    # legend
    legend = "<b>Road Quality</b><br>" + "<br>".join(
        f'<span style="color:{c}">&#9679;</span> {k}' for k, c in COLORS.items())
    m.get_root().html.add_child(folium.Element(
        f'<div style="position:fixed;bottom:20px;left:20px;z-index:9999;'
        f'background:white;padding:8px 12px;border:1px solid #999;'
        f'border-radius:6px;font-family:sans-serif;font-size:13px">{legend}</div>'))

    m.save(out_html)
    print(f"  Saved → {out_html}  (open in browser to explore)")


def build_map_static(pred_df, out_png="road_quality_map.png"):
    if not {"lat", "lon"}.issubset(pred_df.columns):
        return
    d = pred_df.dropna(subset=["lat", "lon"])
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(d["lon"], d["lat"], color="lightgray", zorder=1)
    for cls, color in COLORS.items():
        sub = d[d["pred"] == cls]
        ax.scatter(sub["lon"], sub["lat"], c=color, label=cls, s=45, zorder=2)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("Road Quality Map — RoadSense")
    ax.legend()
    plt.tight_layout()
    plt.savefig(out_png, dpi=150)
    plt.close()
    print(f"  Saved → {out_png}")


# ========================================================================
# STEP 8 — SAVE THE MODEL (for deployment later)
# ========================================================================
#
#   We save the model TOGETHER with its feature list and settings.
#   This way, when you load it later (or deploy it), nothing can get
#   out of sync — the model and its expected inputs travel as one file.
#


# ========================================================================
# RUN EVERYTHING
# ========================================================================
if __name__ == "__main__":

    print("\n" + "=" * 60)
    print("  ROADSENSE — ML Pipeline")
    print("=" * 60 + "\n")

    # Steps 1–3: Load → Window → Extract features
    X, y = build_dataset(FILE_LABELS)
    print(f"Dataset ready: {X.shape[0]} windows × {X.shape[1]} features")
    print(f"Classes: {dict(y.value_counts())}\n")

    # Steps 4–5: Train, compare, evaluate
    clf, feature_cols = train_and_evaluate(X, y)

    # Step 8: Save model
    joblib.dump({
        "model": clf,
        "features": feature_cols,
        "window": WINDOW_SIZE,
        "axes": AXES,
    }, MODEL_PATH)
    print(f"  Saved → {MODEL_PATH}\n")

    # Step 6: Predict on new ride
    preds = predict_ride(clf, feature_cols, RIDE_FILE)

    # Step 7: Map it
    build_map_interactive(preds)
    build_map_static(preds)

    print("\nDone! Check your folder for the output files.")
    print("Open road_quality_map.html in a browser for the interactive map.")
