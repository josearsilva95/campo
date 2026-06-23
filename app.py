import os
import subprocess
import config
from flask import Flask
from routes.auth import auth_bp
from routes.adm import adm_bp
from routes.tecnico import tecnico_bp
from routes.relatorio import relatorio_bp
from routes.whatsapp import whatsapp_bp

app = Flask(__name__)
app.config.from_object(config)

def _git_hash():
    try:
        return subprocess.check_output(
            ['git', 'rev-parse', '--short', 'HEAD'],
            stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        return 'dev'

APP_VERSION = _git_hash()

@app.context_processor
def inject_version():
    return {'v': APP_VERSION}

app.register_blueprint(auth_bp)
app.register_blueprint(adm_bp)
app.register_blueprint(tecnico_bp)
app.register_blueprint(relatorio_bp)
app.register_blueprint(whatsapp_bp)

if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_ENV") == "development")
