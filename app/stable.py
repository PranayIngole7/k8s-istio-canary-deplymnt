import os
from flask  import Flask

app = Flask(__name__)

# Read version and deployment tier from environment variables (defaults to v1.0 / Stable)
APP_VERSION = os.getenv("APP_VERSION", "1.0")
DEPLOYMENT_TIER = os.getenv("DEPLOYMENT_TIER", "Stable")

@app.route("/")
def home():
    return f"""
    <html>
        <head><title>Canary Demo - v{APP_VERSION}</title></head>
        <body style="font-family: Arial, sans-serif; text-align: center; margin-top: 50px;">
            <div style="padding: 20px; display: inline-block; border: 2px solid #333; border-radius: 10px; background-color: #f4f4f4;">
                <h2>Welcome to DevOps Canary Application</h2>
                <p style="font-size: 18px;">Version: <strong>{APP_VERSION}</strong></p>
                <p style="font-size: 18px;">Deployment: <span style="color: {'green' if DEPLOYMENT_TIER == 'Stable' else 'orange'};">{DEPLOYMENT_TIER}</span></p>
            </div>
        </body>
    </html>
    """, 200

@app.route("/healthz")
def healthz():
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)