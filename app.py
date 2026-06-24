import os
import time
import subprocess
import config
from flask import Flask, send_from_directory, make_response
from routes.auth import auth_bp
from routes.adm import adm_bp
from routes.tecnico import tecnico_bp
from routes.relatorio import relatorio_bp
from routes.whatsapp import whatsapp_bp

app = Flask(__name__)
app.config.from_object(config)


def _app_version():
    # Render injeta RENDER_GIT_COMMIT automaticamente em cada deploy
    for env_var in ('RENDER_GIT_COMMIT', 'RAILWAY_GIT_COMMIT_SHA'):
        v = os.getenv(env_var, '')
        if v:
            return v[:7]
    # Arquivo escrito pelo build command: `git rev-parse --short HEAD > static/version.txt`
    try:
        vfile = os.path.join(os.path.dirname(__file__), 'static', 'version.txt')
        with open(vfile) as f:
            v = f.read().strip()
            if v:
                return v
    except Exception:
        pass
    # Dev local: usa o git diretamente
    try:
        return subprocess.check_output(
            ['git', 'rev-parse', '--short', 'HEAD'],
            stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        pass
    # Último recurso: timestamp — muda a cada restart, força download dos arquivos
    return str(int(time.time()))


APP_VERSION = _app_version()


@app.context_processor
def inject_version():
    return {'v': APP_VERSION}


@app.route('/sw.js')
def service_worker():
    """Serve o SW da raiz com escopo global e sem cache."""
    resp = make_response(send_from_directory(app.static_folder, 'sw.js'))
    resp.headers['Service-Worker-Allowed'] = '/'
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    return resp


app.register_blueprint(auth_bp)
app.register_blueprint(adm_bp)
app.register_blueprint(tecnico_bp)
app.register_blueprint(relatorio_bp)
app.register_blueprint(whatsapp_bp)

if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_ENV") == "development")
