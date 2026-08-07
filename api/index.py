import os
import sys
import time
import math
import json
import random
from pathlib import Path

# Add parent and src directories to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = BASE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Try importing MLService
ml_service = None
try:
    from services.ml_service import MLService
    api_model = Path(__file__).resolve().parent / "roadsense_model.joblib"
    src_model = SRC_DIR / "roadsense_model.joblib"
    model_path = api_model if api_model.exists() else src_model
    
    ml_service = MLService(model_path=str(model_path))
    print(f"[Vercel ML] Loaded ML Service. Status: {ml_service.status_message}")
except Exception as e:
    print(f"[Vercel ML] Warning loading MLService: {e}")

# Simulated Telemetry State
state = {
    "lat": 12.9716,
    "lng": 77.5946,
    "speed": 42.5,
    "ax": 0.02,
    "ay": -0.05,
    "az": 9.81,
    "prediction": "smooth",
    "confidence": 98.4,
    "status": "LIVE SIMULATION",
    "potholes_count": 3,
    "bumps_count": 2,
    "total_distance": 14.8
}

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Smart Road Digital Twin — RoadSense ML</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {
            --bg-dark: #080c14;
            --card-bg: rgba(15, 23, 42, 0.75);
            --card-border: rgba(255, 255, 255, 0.08);
            --accent-cyan: #00f2fe;
            --accent-blue: #4facfe;
            --smooth-color: #10b981;
            --pothole-color: #ef4444;
            --bump-color: #f59e0b;
            --braking-color: #3b82f6;
            --text-main: #f8fafc;
            --text-sub: #94a3b8;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }

        body {
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-dark);
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            overflow-x: hidden;
        }

        header {
            background: rgba(11, 17, 32, 0.9);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--card-border);
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: sticky;
            top: 0;
            z-index: 1000;
        }

        .brand { display: flex; align-items: center; gap: 12px; }

        .brand-icon {
            width: 38px;
            height: 38px;
            background: linear-gradient(135deg, var(--accent-cyan), var(--accent-blue));
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            color: #000;
            box-shadow: 0 0 15px rgba(0, 242, 254, 0.4);
        }

        .brand-title {
            font-size: 1.25rem;
            font-weight: 700;
            background: linear-gradient(90deg, #fff, #94a3b8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .badge-vercel {
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.15);
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.75rem;
            color: #e2e8f0;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .pulse-dot {
            width: 8px;
            height: 8px;
            background-color: var(--smooth-color);
            border-radius: 50%;
            box-shadow: 0 0 8px var(--smooth-color);
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.4; transform: scale(1.2); }
            100% { opacity: 1; transform: scale(1); }
        }

        .dashboard-container {
            display: grid;
            grid-template-columns: 1fr 380px;
            gap: 20px;
            padding: 20px;
            max-width: 1600px;
            margin: 0 auto;
            width: 100%;
            flex: 1;
        }

        @media (max-width: 1024px) {
            .dashboard-container { grid-template-columns: 1fr; }
        }

        .glass-card {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            backdrop-filter: blur(16px);
            padding: 20px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        }

        .card-header {
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--text-sub);
            margin-bottom: 12px;
            font-weight: 600;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .main-column { display: flex; flex-direction: column; gap: 20px; }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
        }

        .stat-card {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--card-border);
            border-radius: 12px;
            padding: 16px;
        }

        .stat-val {
            font-family: 'JetBrains Mono', monospace;
            font-size: 1.8rem;
            font-weight: 700;
            margin-top: 4px;
        }

        .verdict-banner {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: rgba(16, 185, 129, 0.1);
            border: 1px solid rgba(16, 185, 129, 0.3);
            border-radius: 16px;
            padding: 20px 24px;
            transition: all 0.3s ease;
        }

        .verdict-title {
            font-size: 0.85rem;
            color: var(--text-sub);
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .verdict-badge {
            font-size: 2rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--smooth-color);
        }

        .verdict-conf {
            font-family: 'JetBrains Mono', monospace;
            font-size: 1.2rem;
            color: #cbd5e1;
        }

        #map-container {
            height: 380px;
            width: 100%;
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid var(--card-border);
        }

        .chart-wrapper { height: 240px; position: relative; }

        .sidebar { display: flex; flex-direction: column; gap: 20px; }

        .btn {
            background: linear-gradient(135deg, var(--accent-cyan), var(--accent-blue));
            color: #000;
            border: none;
            padding: 12px 20px;
            border-radius: 10px;
            font-weight: 700;
            font-size: 0.9rem;
            cursor: pointer;
            width: 100%;
            transition: transform 0.2s, box-shadow 0.2s;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 20px rgba(0, 242, 254, 0.4);
        }

        .preset-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-top: 10px;
        }

        .preset-btn {
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid var(--card-border);
            border-radius: 8px;
            padding: 10px;
            color: var(--text-main);
            font-size: 0.8rem;
            cursor: pointer;
            text-align: center;
            transition: all 0.2s;
        }

        .preset-btn:hover {
            background: rgba(255, 255, 255, 0.1);
            border-color: var(--accent-cyan);
        }

        .slider-group { display: flex; flex-direction: column; gap: 12px; margin-top: 14px; }
        .slider-row { display: flex; justify-content: space-between; font-size: 0.85rem; color: var(--text-sub); }
        .slider-row span { font-family: 'JetBrains Mono', monospace; color: var(--text-main); }
        input[type="range"] { width: 100%; accent-color: var(--accent-cyan); }

        footer {
            text-align: center;
            padding: 16px;
            color: var(--text-sub);
            font-size: 0.8rem;
            border-top: 1px solid var(--card-border);
            margin-top: auto;
        }

        .code-snippet {
            font-family: 'JetBrains Mono', monospace;
            background: #020617;
            padding: 10px;
            border-radius: 8px;
            border: 1px solid var(--card-border);
            font-size: 0.75rem;
            color: #38bdf8;
            overflow-x: auto;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <header>
        <div class="brand">
            <div class="brand-icon">RS</div>
            <div>
                <div class="brand-title">RoadSense Digital Twin</div>
                <div style="font-size: 0.75rem; color: var(--text-sub);">AI-Powered Road Anomaly Detection</div>
            </div>
        </div>
        <div class="badge-vercel">
            <div class="pulse-dot"></div>
            Vercel Serverless Ready
        </div>
    </header>

    <div class="dashboard-container">
        <div class="main-column">
            <div class="verdict-banner" id="verdictBanner">
                <div>
                    <div class="verdict-title">Current Machine Learning Verdict</div>
                    <div class="verdict-badge" id="verdictLabel">SMOOTH ROAD</div>
                </div>
                <div style="text-align: right;">
                    <div class="verdict-title">Model Confidence</div>
                    <div class="verdict-conf" id="verdictConf">98.4%</div>
                </div>
            </div>

            <div class="stats-grid">
                <div class="stat-card">
                    <div class="card-header">Vehicle Speed</div>
                    <div class="stat-val" id="valSpeed">42.5 <span style="font-size:0.9rem; color:var(--text-sub)">km/h</span></div>
                </div>
                <div class="stat-card">
                    <div class="card-header">Potholes Detected</div>
                    <div class="stat-val" style="color: var(--pothole-color)" id="valPotholes">3</div>
                </div>
                <div class="stat-card">
                    <div class="card-header">Bumps Encountered</div>
                    <div class="stat-val" style="color: var(--bump-color)" id="valBumps">2</div>
                </div>
                <div class="stat-card">
                    <div class="card-header">Distance Tracked</div>
                    <div class="stat-val" id="valDistance">14.8 <span style="font-size:0.9rem; color:var(--text-sub)">km</span></div>
                </div>
            </div>

            <div class="glass-card">
                <div class="card-header">
                    <span>Live GPS Digital Twin Map</span>
                    <span style="font-size:0.75rem; color:var(--accent-cyan)">Leaflet + OpenStreetMap</span>
                </div>
                <div id="map-container"></div>
            </div>

            <div class="glass-card">
                <div class="card-header">
                    <span>Real-time Accelerometer Telemetry (50 Hz IMU)</span>
                    <span style="font-size:0.75rem; color:var(--text-sub)">AX / AY / AZ Waveform</span>
                </div>
                <div class="chart-wrapper">
                    <canvas id="sensorChart"></canvas>
                </div>
            </div>
        </div>

        <div class="sidebar">
            <div class="glass-card">
                <div class="card-header">
                    <span>IMU Sensor Simulator</span>
                    <span style="font-size:0.75rem; color:var(--accent-cyan)">Interactive</span>
                </div>
                <p style="font-size: 0.8rem; color: var(--text-sub); margin-bottom: 12px;">
                    Test the Random Forest ML model by selecting road presets or adjusting sensor sliders:
                </p>

                <div class="preset-grid">
                    <div class="preset-btn" onclick="applyPreset('smooth')">✨ Smooth</div>
                    <div class="preset-btn" onclick="applyPreset('pothole')">🕳️ Pothole</div>
                    <div class="preset-btn" onclick="applyPreset('bump')">🚧 Speed Bump</div>
                    <div class="preset-btn" onclick="applyPreset('braking')">🛑 Hard Brake</div>
                </div>

                <div class="slider-group">
                    <div>
                        <div class="slider-row"><span>Accel X (Lateral)</span><span id="txtAX">0.02 g</span></div>
                        <input type="range" id="sliderAX" min="-3" max="3" step="0.05" value="0.02" oninput="updateSliders()">
                    </div>
                    <div>
                        <div class="slider-row"><span>Accel Y (Longitudinal)</span><span id="txtAY">-0.05 g</span></div>
                        <input type="range" id="sliderAY" min="-3" max="3" step="0.05" value="-0.05" oninput="updateSliders()">
                    </div>
                    <div>
                        <div class="slider-row"><span>Accel Z (Vertical)</span><span id="txtAZ">9.81 m/s²</span></div>
                        <input type="range" id="sliderAZ" min="0" max="25" step="0.1" value="9.81" oninput="updateSliders()">
                    </div>
                </div>

                <div style="margin-top: 16px;">
                    <button class="btn" onclick="runPrediction()">Run ML Prediction</button>
                </div>
            </div>

            <div class="glass-card">
                <div class="card-header">Vercel REST API Endpoint</div>
                <p style="font-size: 0.8rem; color: var(--text-sub);">
                    Send HTTP POST requests directly to Vercel serverless API:
                </p>
                <div class="code-snippet">
POST /api/predict<br>
Content-Type: application/json<br><br>
{<br>
&nbsp;&nbsp;"ax": 0.05,<br>
&nbsp;&nbsp;"ay": -0.12,<br>
&nbsp;&nbsp;"az": 14.50<br>
}
                </div>
            </div>

            <div class="glass-card">
                <div class="card-header">Model Architecture</div>
                <div style="font-size: 0.8rem; color: var(--text-sub); display: flex; flex-direction: column; gap: 8px;">
                    <div style="display:flex; justify-content:space-between;"><span>Algorithm:</span><strong style="color:#fff">Random Forest</strong></div>
                    <div style="display:flex; justify-content:space-between;"><span>Window Size:</span><strong style="color:#fff">50 Samples (1.0s)</strong></div>
                    <div style="display:flex; justify-content:space-between;"><span>Features Extracted:</span><strong style="color:#fff">24 Stats (Mean, Std, RMS, P2P)</strong></div>
                    <div style="display:flex; justify-content:space-between;"><span>Status:</span><strong style="color:var(--smooth-color)">Active / Loaded</strong></div>
                </div>
            </div>
        </div>
    </div>

    <footer>
        Smart Road Digital Twin &copy; 2026 — RoadSense ML Vercel Deployment Ready
    </footer>

    <script>
        const map = L.map('map-container').setView([12.9716, 77.5946], 15);
        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            maxZoom: 19,
            attribution: '&copy; OpenStreetMap & CartoDB'
        }).addTo(map);

        const carIcon = L.divIcon({
            className: 'car-marker',
            html: '<div style="width:16px; height:16px; background:#00f2fe; border-radius:50%; box-shadow:0 0 12px #00f2fe; border:2px solid #fff;"></div>'
        });
        const carMarker = L.marker([12.9716, 77.5946], {icon: carIcon}).addTo(map).bindPopup("Digital Twin Vehicle");

        const potholeIcon = L.divIcon({
            html: '<div style="width:12px; height:12px; background:#ef4444; border-radius:50%; box-shadow:0 0 8px #ef4444;"></div>'
        });
        L.marker([12.9730, 77.5960], {icon: potholeIcon}).addTo(map).bindPopup("Pothole #1 (Severe)");
        L.marker([12.9705, 77.5925], {icon: potholeIcon}).addTo(map).bindPopup("Pothole #2 (Moderate)");

        const routeCoords = [
            [12.9690, 77.5900],
            [12.9705, 77.5925],
            [12.9716, 77.5946],
            [12.9730, 77.5960],
            [12.9745, 77.5980]
        ];
        L.polyline(routeCoords, {color: '#00f2fe', weight: 4, opacity: 0.7}).addTo(map);

        const ctx = document.getElementById('sensorChart').getContext('2d');
        const maxPoints = 30;
        const labels = Array.from({length: maxPoints}, (_, i) => `${i}s`);
        
        const sensorChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    { label: 'AX (Lateral)', data: Array(maxPoints).fill(0.02), borderColor: '#00f2fe', borderWidth: 2, tension: 0.3, pointRadius: 0 },
                    { label: 'AY (Longitudinal)', data: Array(maxPoints).fill(-0.05), borderColor: '#f59e0b', borderWidth: 2, tension: 0.3, pointRadius: 0 },
                    { label: 'AZ (Vertical)', data: Array(maxPoints).fill(9.81), borderColor: '#ef4444', borderWidth: 2, tension: 0.3, pointRadius: 0 }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { display: false },
                    y: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#94a3b8' } }
                },
                plugins: {
                    legend: { labels: { color: '#e2e8f0', font: { family: 'Inter' } } }
                }
            }
        });

        function updateSliders() {
            const ax = parseFloat(document.getElementById('sliderAX').value);
            const ay = parseFloat(document.getElementById('sliderAY').value);
            const az = parseFloat(document.getElementById('sliderAZ').value);

            document.getElementById('txtAX').innerText = `${ax.toFixed(2)} g`;
            document.getElementById('txtAY').innerText = `${ay.toFixed(2)} g`;
            document.getElementById('txtAZ').innerText = `${az.toFixed(2)} m/s²`;
        }

        function applyPreset(type) {
            if (type === 'smooth') {
                document.getElementById('sliderAX').value = 0.02;
                document.getElementById('sliderAY').value = -0.05;
                document.getElementById('sliderAZ').value = 9.81;
            } else if (type === 'pothole') {
                document.getElementById('sliderAX').value = 0.85;
                document.getElementById('sliderAY').value = -1.20;
                document.getElementById('sliderAZ').value = 19.50;
            } else if (type === 'bump') {
                document.getElementById('sliderAX').value = 0.30;
                document.getElementById('sliderAY').value = 0.80;
                document.getElementById('sliderAZ').value = 14.20;
            } else if (type === 'braking') {
                document.getElementById('sliderAX').value = 0.05;
                document.getElementById('sliderAY').value = -2.80;
                document.getElementById('sliderAZ').value = 9.75;
            }
            updateSliders();
            runPrediction();
        }

        async function runPrediction() {
            const ax = parseFloat(document.getElementById('sliderAX').value);
            const ay = parseFloat(document.getElementById('sliderAY').value);
            const az = parseFloat(document.getElementById('sliderAZ').value);

            try {
                const res = await fetch('/api/predict', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ ax, ay, az })
                });
                const data = await res.json();
                updateVerdictUI(data.prediction, data.confidence);
                pushChartData(ax, ay, az);
            } catch (err) {
                console.error("Prediction failed:", err);
            }
        }

        function updateVerdictUI(prediction, confidence) {
            const banner = document.getElementById('verdictBanner');
            const label = document.getElementById('verdictLabel');
            const conf = document.getElementById('verdictConf');

            const upper = prediction.toUpperCase();
            label.innerText = upper;
            conf.innerText = `${confidence.toFixed(1)}%`;

            if (upper.includes('SMOOTH')) {
                label.style.color = 'var(--smooth-color)';
                banner.style.background = 'rgba(16, 185, 129, 0.1)';
                banner.style.borderColor = 'rgba(16, 185, 129, 0.3)';
            } else if (upper.includes('POTHOLE')) {
                label.style.color = 'var(--pothole-color)';
                banner.style.background = 'rgba(239, 68, 68, 0.15)';
                banner.style.borderColor = 'rgba(239, 68, 68, 0.4)';
            } else if (upper.includes('BUMP')) {
                label.style.color = 'var(--bump-color)';
                banner.style.background = 'rgba(245, 158, 11, 0.15)';
                banner.style.borderColor = 'rgba(245, 158, 11, 0.4)';
            } else if (upper.includes('BRAKING')) {
                label.style.color = 'var(--braking-color)';
                banner.style.background = 'rgba(59, 130, 246, 0.15)';
                banner.style.borderColor = 'rgba(59, 130, 246, 0.4)';
            }
        }

        function pushChartData(ax, ay, az) {
            const datasets = sensorChart.data.datasets;
            datasets[0].data.shift();
            datasets[0].data.push(ax);
            datasets[1].data.shift();
            datasets[1].data.push(ay);
            datasets[2].data.shift();
            datasets[2].data.push(az);
            sensorChart.update();
        }

        let step = 0;
        setInterval(() => {
            step++;
            const lat = 12.9716 + Math.sin(step * 0.05) * 0.003;
            const lng = 77.5946 + Math.cos(step * 0.05) * 0.003;
            carMarker.setLatLng([lat, lng]);

            const jitterX = (Math.random() - 0.5) * 0.04;
            const jitterY = (Math.random() - 0.5) * 0.04;
            const currentAX = parseFloat(document.getElementById('sliderAX').value) + jitterX;
            const currentAY = parseFloat(document.getElementById('sliderAY').value) + jitterY;
            const currentAZ = parseFloat(document.getElementById('sliderAZ').value);

            pushChartData(currentAX, currentAY, currentAZ);
        }, 1000);
    </script>
</body>
</html>"""

def handle_prediction(data_json):
    if ml_service and ml_service.is_ready():
        samples = data_json.get("samples")
        if isinstance(samples, list) and len(samples) > 0:
            for sample in samples:
                ml_service.feed_reading(
                    sample.get("ax", sample.get("x", 0)),
                    sample.get("ay", sample.get("y", 0)),
                    sample.get("az", sample.get("z", 9.81))
                )
        else:
            ax = float(data_json.get("ax", data_json.get("x", 0.02)))
            ay = float(data_json.get("ay", data_json.get("y", -0.05)))
            az = float(data_json.get("az", data_json.get("z", 9.81)))
            
            for _ in range(ml_service.window_size):
                ml_service.feed_reading(
                    ax + random.uniform(-0.02, 0.02),
                    ay + random.uniform(-0.02, 0.02),
                    az + random.uniform(-0.1, 0.1)
                )
        
        return {
            "success": True,
            "prediction": ml_service.last_prediction,
            "confidence": round(ml_service.last_confidence, 2),
            "mode": "ML_MODEL",
            "timestamp": time.time()
        }
    
    ax = float(data_json.get("ax", 0.02))
    ay = float(data_json.get("ay", -0.05))
    az = float(data_json.get("az", 9.81))
    
    if az > 16.0 or abs(ax) > 1.2:
        prediction = "pothole"
        confidence = 94.2
    elif az > 13.0 or abs(ay) > 0.9:
        prediction = "bump"
        confidence = 91.5
    elif ay < -2.0:
        prediction = "braking"
        confidence = 96.0
    else:
        prediction = "smooth"
        confidence = 98.8
        
    return {
        "success": True,
        "prediction": prediction,
        "confidence": confidence,
        "mode": "HEURISTIC_FALLBACK",
        "timestamp": time.time()
    }

# Try importing Flask
try:
    from flask import Flask, jsonify, request, render_template_string
    from flask_cors import CORS

    app = Flask(__name__)
    CORS(app)

    @app.route("/")
    def index():
        return render_template_string(HTML_TEMPLATE)

    @app.route("/api/status", methods=["GET"])
    def get_status():
        ready = ml_service.is_ready() if ml_service else False
        msg = ml_service.status_message if ml_service else "ML service not initialized"
        classes = list(ml_service.model.classes_) if (ml_service and ml_service.model) else ["braking", "bump", "pothole", "smooth"]
        return jsonify({
            "status": "online",
            "service": "RoadSense ML Digital Twin",
            "ml_ready": ready,
            "message": msg,
            "classes": classes,
            "timestamp": time.time()
        })

    @app.route("/api/telemetry", methods=["GET"])
    def get_telemetry():
        return jsonify(state)

    @app.route("/api/predict", methods=["POST"])
    def predict():
        try:
            data_json = request.get_json(force=True) or {}
            res = handle_prediction(data_json)
            return jsonify(res)
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 400

    @app.route("/api/history", methods=["GET"])
    def get_history():
        return jsonify({
            "events": [
                {"id": 101, "type": "pothole", "confidence": 98.2, "lat": 12.9730, "lng": 77.5960, "time": "13:42:10"},
                {"id": 102, "type": "bump", "confidence": 92.5, "lat": 12.9705, "lng": 77.5925, "time": "13:45:22"},
                {"id": 103, "type": "pothole", "confidence": 95.7, "lat": 12.9745, "lng": 77.5980, "time": "13:49:05"}
            ]
        })

except ImportError:
    # Pure WSGI Fallback if Flask is not installed in local environment
    def app(environ, start_response):
        path = environ.get('PATH_INFO', '/')
        method = environ.get('REQUEST_METHOD', 'GET')
        
        if path == '/' or path == '/index.html':
            start_response('200 OK', [('Content-Type', 'text/html; charset=utf-8')])
            return [HTML_TEMPLATE.encode('utf-8')]
            
        elif path == '/api/status':
            start_response('200 OK', [('Content-Type', 'application/json')])
            body = json.dumps({
                "status": "online",
                "service": "RoadSense ML Digital Twin",
                "ml_ready": ml_service.is_ready() if ml_service else False,
                "timestamp": time.time()
            })
            return [body.encode('utf-8')]
            
        elif path == '/api/telemetry':
            start_response('200 OK', [('Content-Type', 'application/json')])
            return [json.dumps(state).encode('utf-8')]
            
        elif path == '/api/predict' and method == 'POST':
            try:
                request_body_size = int(environ.get('CONTENT_LENGTH', 0))
                request_body = environ['wsgi.input'].read(request_body_size)
                data_json = json.loads(request_body) if request_body else {}
                res = handle_prediction(data_json)
                start_response('200 OK', [('Content-Type', 'application/json')])
                return [json.dumps(res).encode('utf-8')]
            except Exception as e:
                start_response('400 Bad Request', [('Content-Type', 'application/json')])
                return [json.dumps({"success": False, "error": str(e)}).encode('utf-8')]
                
        else:
            start_response('404 Not Found', [('Content-Type', 'application/json')])
            return [json.dumps({"error": "Not Found"}).encode('utf-8')]

if __name__ == "__main__":
    if 'Flask' in sys.modules:
        app.run(host="0.0.0.0", port=3000, debug=True)
    else:
        from wsgiref.simple_server import make_server
        httpd = make_server('0.0.0.0', 3000, app)
        print("Serving on http://0.0.0.0:3000 ...")
        httpd.serve_forever()
