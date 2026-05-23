import base64
import http.server
import json
import os
import shutil
import socketserver
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE_DIR     = Path(__file__).parent
DATA_DIR     = BASE_DIR / "data"
MATERIAL_DIR = Path(r'C:\Users\estef\OneDrive\UBA\Material_UBA')


def _load_config():
    cfg = {}
    # 1. config/settings.json (clave preferida — gitignoreada)
    settings_path = BASE_DIR / 'config' / 'settings.json'
    if settings_path.exists():
        try:
            data = json.loads(settings_path.read_text(encoding='utf-8'))
            cfg['GITHUB_TOKEN']  = data.get('github_token',  '')
            cfg['GITHUB_USER']   = data.get('github_user',   '')
            cfg['GITHUB_REPO']   = data.get('github_repo',   '')
            cfg['GITHUB_BRANCH'] = data.get('github_branch', 'main')
        except Exception:
            pass
    # 2. .env (override opcional)
    env_path = BASE_DIR / '.env'
    if env_path.exists():
        try:
            for line in env_path.read_text(encoding='utf-8').splitlines():
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, _, v = line.partition('=')
                    cfg[k.strip()] = v.strip().strip('"').strip("'")
        except Exception:
            pass
    return cfg

_config = _load_config()


def _gh_creds():
    """Devuelve (token, user, repo, branch) desde env o config."""
    token  = os.environ.get('GITHUB_TOKEN')  or _config.get('GITHUB_TOKEN',  '')
    user   = os.environ.get('GITHUB_USER')   or _config.get('GITHUB_USER',   '')
    repo   = os.environ.get('GITHUB_REPO')   or _config.get('GITHUB_REPO',   '')
    branch = os.environ.get('GITHUB_BRANCH') or _config.get('GITHUB_BRANCH', 'main')
    return token, user, repo, branch


def _gh_headers(token):
    h = {'User-Agent': 'StudyES-local', 'Content-Type': 'application/json'}
    if token:
        h['Authorization'] = f'token {token}'
    return h

MIME_TYPES = {
    '.pdf':  'application/pdf',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.doc':  'application/msword',
    '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    '.ppt':  'application/vnd.ms-powerpoint',
    '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    '.txt':  'text/plain; charset=utf-8',
    '.html': 'text/html; charset=utf-8',
    '.png':  'image/png',
    '.jpg':  'image/jpeg',
    '.jpeg': 'image/jpeg',
}

SUBCARPETAS_ORDEN = [
    'Teoria', 'Ejercicios', 'Resumenes',
    'Examenes', 'Presentaciones', 'Mapas_Mentales',
]


class StudyESHandler(http.server.SimpleHTTPRequestHandler):

    # ── GET ────────────────────────────────────────────────────────
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path   = urllib.parse.unquote(parsed.path)

        if path == '/ping':
            self._respond(200, {'ok': True})

        elif path == '/github-latest-sha':
            qs       = urllib.parse.parse_qs(parsed.query)
            rel_path = qs.get('path', [''])[0]
            if not rel_path:
                self._respond(400, {'error': 'Falta parámetro path'})
                return
            try:
                token, user, repo, _ = _gh_creds()
                api_url = f'https://api.github.com/repos/{user}/{repo}/commits?path=data/{rel_path}&per_page=1'
                req = urllib.request.Request(api_url, headers=_gh_headers(token))
                with urllib.request.urlopen(req, timeout=3) as r:
                    commits = json.loads(r.read())
                sha = commits[0]['sha'] if commits else None
                self._respond(200, {'sha': sha})
            except Exception as e:
                self._respond(500, {'error': str(e)})

        elif path.startswith('/api/material/'):
            carpeta = path[len('/api/material/'):]
            self._list_material(carpeta)
        elif path.startswith('/material-file/'):
            rel = path[len('/material-file/'):]
            self._serve_material_file(rel)
        else:
            super().do_GET()

    def _list_material(self, carpeta):
        if not carpeta:
            self._respond(400, {'error': 'Falta el nombre de carpeta'})
            return

        target = (MATERIAL_DIR / carpeta).resolve()
        if not str(target).startswith(str(MATERIAL_DIR.resolve())):
            self._respond(403, {'error': 'Ruta no permitida'})
            return

        if not target.is_dir():
            self._respond(200, {'carpeta': carpeta, 'grupos': {}, 'sin_subcarpeta': []})
            return

        grupos = {}
        sin_subcarpeta = []

        for sub in SUBCARPETAS_ORDEN:
            sub_path = target / sub
            if sub_path.is_dir():
                archivos = [
                    {
                        'nombre': f.name,
                        'tipo':   f.suffix.lower().lstrip('.'),
                        'url':    f'/material-file/{carpeta}/{sub}/{urllib.parse.quote(f.name)}',
                    }
                    for f in sorted(sub_path.iterdir())
                    if f.is_file() and not f.name.startswith('.')
                ]
                if archivos:
                    grupos[sub] = archivos

        for f in sorted(target.iterdir()):
            if f.is_file() and not f.name.startswith('.'):
                sin_subcarpeta.append({
                    'nombre': f.name,
                    'tipo':   f.suffix.lower().lstrip('.'),
                    'url':    f'/material-file/{carpeta}/{urllib.parse.quote(f.name)}',
                })

        self._respond(200, {
            'carpeta':        carpeta,
            'grupos':         grupos,
            'sin_subcarpeta': sin_subcarpeta,
        })

    def _serve_material_file(self, rel_path):
        rel_decoded = urllib.parse.unquote(rel_path)
        target      = (MATERIAL_DIR / rel_decoded).resolve()

        if not str(target).startswith(str(MATERIAL_DIR.resolve())):
            self._respond(403, {'error': 'No permitido'})
            return
        if not target.is_file():
            self._respond(404, {'error': 'Archivo no encontrado'})
            return

        mime = MIME_TYPES.get(target.suffix.lower(), 'application/octet-stream')
        size = target.stat().st_size
        self.send_response(200)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(size))
        self.send_header('Content-Disposition', f'inline; filename="{target.name}"')
        self.end_headers()
        with open(target, 'rb') as f:
            shutil.copyfileobj(f, self.wfile)

    # ── POST ───────────────────────────────────────────────────────
    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path   = urllib.parse.unquote(parsed.path)

        if path == '/save':
            length = int(self.headers.get('Content-Length', 0))
            body   = self.rfile.read(length)
            try:
                payload  = json.loads(body)
                rel_path = payload.get('path', '')
                data     = payload.get('data')

                target = (DATA_DIR / rel_path).resolve()
                if not str(target).startswith(str(DATA_DIR.resolve())):
                    self._respond(403, {'error': 'Ruta no permitida'})
                    return

                target.parent.mkdir(parents=True, exist_ok=True)
                with open(target, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

                self._respond(200, {'ok': True})
            except Exception as e:
                self._respond(500, {'error': str(e)})

        elif path == '/github-sync':
            length = int(self.headers.get('Content-Length', 0))
            body   = self.rfile.read(length)
            try:
                payload  = json.loads(body)
                rel_path = payload.get('path', '')
                data     = payload.get('data')

                token, user, repo, branch = _gh_creds()
                if not all([token, user, repo]):
                    self._respond(503, {'error': 'GitHub no configurado: falta token/user/repo en config/settings.json'})
                    return

                api_url = f'https://api.github.com/repos/{user}/{repo}/contents/{rel_path}'
                hdrs    = _gh_headers(token)

                # SHA actual del archivo (necesario para el PUT de GitHub)
                blob_sha = None
                try:
                    req = urllib.request.Request(api_url, headers=hdrs)
                    with urllib.request.urlopen(req) as r:
                        blob_sha = json.loads(r.read()).get('sha')
                except urllib.error.HTTPError as e:
                    if e.code != 404:
                        raise

                content_b64 = base64.b64encode(
                    json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')
                ).decode('ascii')

                put_body = {
                    'message': f'StudyES: actualizar {rel_path}',
                    'content': content_b64,
                    'branch':  branch,
                }
                if blob_sha:
                    put_body['sha'] = blob_sha

                put_req = urllib.request.Request(
                    api_url,
                    data=json.dumps(put_body).encode('utf-8'),
                    headers=hdrs,
                    method='PUT',
                )
                with urllib.request.urlopen(put_req) as r:
                    result     = json.loads(r.read())
                    commit_sha = result.get('commit', {}).get('sha')
                self._respond(200, {'ok': True, 'sha': commit_sha})

            except urllib.error.HTTPError as e:
                err_text = e.read().decode('utf-8', errors='ignore')
                try:
                    msg = json.loads(err_text).get('message', str(e))
                except Exception:
                    msg = str(e)
                self._respond(e.code, {'error': msg})
            except Exception as e:
                self._respond(500, {'error': str(e)})

        elif path == '/github-pull':
            length = int(self.headers.get('Content-Length', 0))
            body   = self.rfile.read(length)
            try:
                payload  = json.loads(body)
                rel_path = payload.get('path', '')

                token, user, repo, branch = _gh_creds()
                hdrs = _gh_headers(token)

                # Descargar contenido raw desde GitHub
                raw_url = f'https://raw.githubusercontent.com/{user}/{repo}/{branch}/data/{rel_path}'
                raw_req = urllib.request.Request(raw_url, headers={'User-Agent': 'StudyES-local'})
                if token:
                    raw_req.add_header('Authorization', f'token {token}')
                with urllib.request.urlopen(raw_req, timeout=5) as r:
                    file_data = json.loads(r.read())

                # Sobreescribir en disco local
                target = (DATA_DIR / rel_path).resolve()
                if not str(target).startswith(str(DATA_DIR.resolve())):
                    self._respond(403, {'error': 'Ruta no permitida'})
                    return
                target.parent.mkdir(parents=True, exist_ok=True)
                with open(target, 'w', encoding='utf-8') as f:
                    json.dump(file_data, f, ensure_ascii=False, indent=2)

                # Obtener SHA del último commit que tocó este archivo
                sha = None
                try:
                    commits_url = f'https://api.github.com/repos/{user}/{repo}/commits?path=data/{rel_path}&per_page=1'
                    req = urllib.request.Request(commits_url, headers=hdrs)
                    with urllib.request.urlopen(req, timeout=3) as r:
                        commits = json.loads(r.read())
                        if commits:
                            sha = commits[0]['sha']
                except Exception:
                    pass

                self._respond(200, {'ok': True, 'sha': sha})

            except Exception as e:
                self._respond(500, {'error': str(e)})

        else:
            self._respond(404, {'error': 'Ruta no encontrada'})

    def do_OPTIONS(self):
        self.send_response(200)
        self._extra_cors()
        self.end_headers()

    # ── Helpers ────────────────────────────────────────────────────
    def _respond(self, code, payload):
        body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self._extra_cors()
        self.end_headers()
        self.wfile.write(body)

    def _extra_cors(self):
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

    def log_message(self, fmt, *args):
        print(f'  {self.address_string()} — {fmt % args}')


class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True


if __name__ == '__main__':
    os.chdir(BASE_DIR)
    server = ThreadedHTTPServer(('localhost', 8000), StudyESHandler)
    print('=' * 40)
    print('  StudyES corriendo en http://localhost:8000')
    print('  Presioná Ctrl+C para detener')
    print('=' * 40)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nServidor detenido.')
