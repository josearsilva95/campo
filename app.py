from flask import Flask, session
from config import Config
from routes.auth import auth_bp
from routes.adm import adm_bp
from routes.tecnico import tecnico_bp
from routes.relatorio import relatorio_bp
from routes.whatsapp import whatsapp_bp

app = Flask(__name__)
app.config.from_object(Config)

app.register_blueprint(auth_bp)
app.register_blueprint(adm_bp)
app.register_blueprint(tecnico_bp)
app.register_blueprint(relatorio_bp)
app.register_blueprint(whatsapp_bp)

if __name__ == "__main__":
    app.run(debug=app.config.get("FLASK_ENV") == "development")
