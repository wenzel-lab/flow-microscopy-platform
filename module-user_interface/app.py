# from webapp.auth.views import bp as auth_bp
import os
from dotenv import load_dotenv
from webapp import create_app


load_dotenv(".env")
DEBUG = True if os.getenv("DEBUG", "false").lower() in ["true", "t", "1"] else False
APP_PORT = int(os.getenv("APP_PORT", "5000"))

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=APP_PORT, debug=True, use_reloader=True)
