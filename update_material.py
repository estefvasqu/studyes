import json
import shutil
from pathlib import Path

SOURCE_BASE = Path(r'C:\Users\estef\OneDrive\UBA\Material_UBA')
DEST_BASE   = Path(__file__).parent / 'material'
INDEX_PATH  = DEST_BASE / 'index.json'

MATERIAS = {
    'Microeconomia_II':    ['Teoria', 'Ejercicios', 'Resumenes', 'Examenes', 'Presentaciones', 'Mapas_Mentales'],
    'Desarrollo_Economico': ['Teoria', 'Resumenes', 'Examenes', 'Presentaciones', 'Mapas_Mentales'],
}

EXTENSIONES = {'.pdf', '.docx', '.pptx', '.html', '.xlsx', '.png', '.jpg'}


def sincronizar():
    print('--- Copiando archivos nuevos o modificados ---')
    for materia, subcarpetas in MATERIAS.items():
        for sub in subcarpetas:
            origen  = SOURCE_BASE / materia / sub
            destino = DEST_BASE   / materia / sub
            destino.mkdir(parents=True, exist_ok=True)

            if not origen.is_dir():
                continue

            for archivo in sorted(origen.iterdir()):
                if not archivo.is_file():
                    continue
                if archivo.name.startswith('.'):
                    continue
                if archivo.suffix.lower() not in EXTENSIONES:
                    continue

                dest_file = destino / archivo.name
                if not dest_file.exists() or archivo.stat().st_mtime > dest_file.stat().st_mtime:
                    shutil.copy2(archivo, dest_file)
                    print(f'✓ Copiado: {materia}/{sub}/{archivo.name}')
                else:
                    print(f'= Sin cambios: {materia}/{sub}/{archivo.name}')


def actualizar_index():
    print('\n--- Actualizando material/index.json ---')
    index = {}
    total = 0
    for materia, subcarpetas in MATERIAS.items():
        index[materia] = {}
        for sub in subcarpetas:
            carpeta  = DEST_BASE / materia / sub
            archivos = []
            if carpeta.is_dir():
                for f in sorted(carpeta.iterdir()):
                    if f.is_file() and not f.name.startswith('.') and f.suffix.lower() in EXTENSIONES:
                        archivos.append(f.name)
            index[materia][sub] = archivos
            total += len(archivos)

    with open(INDEX_PATH, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    print(f'Index actualizado: {total} archivo(s) en total.')


if __name__ == '__main__':
    sincronizar()
    actualizar_index()
    print('\nListo.')
