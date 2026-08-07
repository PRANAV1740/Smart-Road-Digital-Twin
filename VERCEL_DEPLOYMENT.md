# 🚀 Vercel Deployment Guide — Smart Road Digital Twin

Your project is now fully configured and ready for **Vercel Serverless Deployment**!

---

## 📁 Files Created for Vercel

| File | Purpose |
|---|---|
| [`vercel.json`](file:///p:/Roadsense_test/vercel.json) | Vercel configuration specifying `@vercel/python` builder and route rewrites to `api/index.py`. |
| [`requirements.txt`](file:///p:/Roadsense_test/requirements.txt) | Python dependencies needed for serverless execution (`Flask`, `Flask-Cors`, `numpy`, `pandas`, `scikit-learn`, `joblib`). |
| [`.vercelignore`](file:///p:/Roadsense_test/.vercelignore) | Ignores heavy runtime/git files to ensure fast build times and lightweight bundles. |
| [`api/index.py`](file:///p:/Roadsense_test/api/index.py) | **Serverless Web Application & REST API Entrypoint** with interactive web dashboard & real-time ML inference engine. |
| [`api/roadsense_model.joblib`](file:///p:/Roadsense_test/api/roadsense_model.joblib) | Trained Random Forest model bundled for serverless inference. |

---

## 🌐 Features of the Vercel Web App

When deployed, your Vercel URL will serve:

1. **Interactive Glassmorphism Digital Twin Dashboard**:
   - **Live GPS Map**: Dynamic Leaflet.js map with telemetry tracking, route overlays, and pothole markers.
   - **Real-Time Telemetry Chart**: 50Hz IMU accelerometer waveform visualization ($A_x$, $A_y$, $A_z$).
   - **ML Verdict Badge**: Real-time road status (`SMOOTH`, `POTHOLE`, `BUMP`, `BRAKING`) with model confidence percentage.
   - **IMU Sensor Simulator**: Interactive sliders and presets to test real-time predictions against the Random Forest ML model.

2. **Serverless REST API Endpoints**:
   - `GET /` — Serves the Digital Twin Web Interface.
   - `POST /api/predict` — Accepts JSON sensor readings (`ax`, `ay`, `az`) and outputs ML predictions & confidence scores.
   - `GET /api/status` — Returns ML model load state, window size, features, and classes.
   - `GET /api/telemetry` — Returns vehicle location, speed, distance, and current anomaly stats.
   - `GET /api/history` — Returns recent road anomaly detections.

---

## 🛠️ Step-by-Step Deployment Instructions

### Option 1: Deploy via Vercel CLI (Recommended)

1. **Install Vercel CLI** (if not already installed):
   ```bash
   npm install -g vercel
   ```

2. **Deploy to Preview / Staging**:
   Run from the project root directory:
   ```bash
   vercel
   ```
   Follow the prompts:
   - *Set up and deploy?* **Y**
   - *Which scope?* Select your team/account
   - *Link to existing project?* **N**
   - *Project name?* `roadsense-digital-twin`
   - *In which directory is your code located?* `./`

3. **Deploy to Production**:
   ```bash
   vercel --prod
   ```

---

### Option 2: Deploy via GitHub / Vercel Dashboard

1. Push your repository code to **GitHub**, **GitLab**, or **Bitbucket**.
2. Go to [vercel.com/new](https://vercel.com/new).
3. Import your `Roadsense_test` repository.
4. Keep all default settings (Vercel auto-detects `vercel.json` and `requirements.txt`).
5. Click **Deploy**!

---

## ⚡ Testing the API Endpoint

Once deployed, test your Vercel URL using `curl` or Postman:

```bash
curl -X POST https://your-project.vercel.app/api/predict \
  -H "Content-Type: application/json" \
  -d '{"ax": 0.85, "ay": -1.20, "az": 19.50}'
```

**Response**:
```json
{
  "confidence": 94.2,
  "mode": "ML_MODEL",
  "prediction": "pothole",
  "success": true,
  "timestamp": 1770452790
}
```
