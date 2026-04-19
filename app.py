"""
UrbanPulse — Predictive Urban Growth Analytics Engine
======================================================
Flask backend with full API, data processing, and visualization.

Author  : Kotagiri Kulbhushan
Stack   : Flask · Pandas · Plotly · Folium · Jinja2
"""

from flask import Flask
from routes.dashboard import dashboard_bp
from routes.api import api_bp
from routes.upload import upload_bp

app = Flask(__name__)
app.secret_key = "urbanpulse_secret_2026"
app.config["UPLOAD_FOLDER"] = "data"
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB

# ── Register blueprints
app.register_blueprint(dashboard_bp)
app.register_blueprint(api_bp,      url_prefix="/api")
app.register_blueprint(upload_bp,   url_prefix="/upload")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
