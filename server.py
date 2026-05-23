import http.server
import json
import os
import shutil
import urllib.parse
from pathlib import Path

BASE_DIR     = Path(__file__).parent
DATA_DIR     = BASE_DIR / "data"
MATERIAL_DIR = Path(r'C:\Users\estef\OneDrive\UBA\Material_UBA')

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


if __name__ == '__main__':
    os.chdir(BASE_DIR)
    server = http.server.HTTPServer(('localhost', 8000), StudyESHandler)
    print('=' * 40)
    print('  StudyES corriendo en http://localhost:8000')
    print('  Presioná Ctrl+C para detener')
    print('=' * 40)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nServidor detenido.')
