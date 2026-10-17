import os
from flask import Flask

app = Flask(__name__)

APP_VERSION = os.getenv("APP_VERSION", "2.0")
DEPLOYMENT_TIER = os.getenv("DEPLOYMENT_TIER", "Canary")


@app.route("/")
def home():
    return f"""
    <!DOCTYPE html>
    <html>
      <head>
        <title>Canary Demo - v{APP_VERSION}</title>
      </head>
      <body style="font-family: Arial; text-align: center; margin-top: 50px;">
        <div style="display: inline-block; padding: 25px;
                    border: 3px solid #e67e22; border-radius: 12px;
                    background-color: #fff3e0;">
          <h2>Welcome to DevOps Canary Application</h2>
          <p style="font-size: 20px;">
            Version: <strong>{APP_VERSION}</strong>
          </p>
          <p style="font-size: 20px; color: #e67e22;">
            Deployment: <strong>{DEPLOYMENT_TIER}</strong>
          </p>
          <p>New canary release with an updated interface!</p>
        </div>
      </body>
    </html>
    """, 200


@app.route("/healthz")
def healthz():
    return "OK", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
