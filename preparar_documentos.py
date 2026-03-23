#!/usr/bin/env python3
"""
preparar_documentos.py — Pre-procesador de documentos jurídicos para Lexiora RAG
==================================================================================

Convierte leyes, dictámenes y cualquier documento jurídico en el formato JSON
que espera el workflow lexiora-ingest para vectorizarlo en Supabase.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INSTALACIÓN (solo la primera vez):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    pip install requests beautifulsoup4 pdfplumber python-docx

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MODO 1 — LEY DESDE BCN (Biblioteca del Congreso Nacional)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Cómo obtener la URL de BCN:
    1. Ir a https://www.bcn.cl/leychile
    2. Buscar la ley (ej: "Código del Trabajo" o "Ley 18.620")
    3. Copiar la URL de la barra del navegador
    4. La URL tendrá este formato: https://www.bcn.cl/leychile/navegar?idNorma=XXXXX

  Ejemplos de URLs útiles:
    Código del Trabajo:   https://www.bcn.cl/leychile/navegar?idNorma=207436
    Código Civil:         https://www.bcn.cl/leychile/navegar?idNorma=172986
    Código Penal:         https://www.bcn.cl/leychile/navegar?idNorma=1984
    Ley Datos Personales: https://www.bcn.cl/leychile/navegar?idNorma=141599

  Comando:
    python preparar_documentos.py \
      --url "https://www.bcn.cl/leychile/navegar?idNorma=207436" \
      --fuente "Código del Trabajo" \
      --numero "Ley 18.620" \
      --materia "laboral" \
      --salida codigo_trabajo.json

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MODO 2 — ARCHIVO PDF (dictámenes de Contraloría, leyes en PDF, etc.)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Cómo descargar dictámenes de Contraloría:
    1. Ir a https://www.contraloria.cl/web/cgr/buscador-de-dictamenes
    2. Buscar por número o materia
    3. Descargar el PDF del dictamen
    4. Guardar en la misma carpeta que este script o indicar la ruta completa

  Comando:
    python preparar_documentos.py \
      --pdf "dictamen_3576_054.pdf" \
      --fuente "Contraloría General de la República" \
      --numero "Dictamen 3576/054" \
      --materia "administrativo" \
      --salida dictamen_3576.json

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MODO 3 — CARPETA CON MÚLTIPLES PDFs (procesa todos a la vez)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Útil cuando se tienen 50+ dictámenes descargados en una carpeta.
  El nombre del archivo PDF se usa como número de referencia si no se especifica.

  Estructura esperada de la carpeta:
    dictamenes/
    ├── dictamen_3576_054.pdf
    ├── dictamen_4120_023.pdf
    └── dictamen_5001_089.pdf

  Comando:
    python preparar_documentos.py \
      --carpeta "./dictamenes/" \
      --fuente "Contraloría General de la República" \
      --materia "administrativo" \
      --salida todos_dictamenes.json

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MODO 4 — ARCHIVO DE TEXTO PLANO (.txt)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Comando:
    python preparar_documentos.py \
      --txt "ley_19628.txt" \
      --fuente "Ley de Protección de Datos Personales" \
      --numero "Ley 19.628" \
      --materia "datos_personales" \
      --salida ley_19628.json

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MODO 5 — ARCHIVO WORD (.docx)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Comando:
    python preparar_documentos.py \
      --docx "reglamento_interno.docx" \
      --fuente "Reglamento Interno Empresa" \
      --materia "reglamento" \
      --salida reglamento.json

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OPCIONES ADICIONALES (se pueden combinar con cualquier modo):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  --chunk N        Tamaño máximo de cada fragmento en caracteres (default: 3000)
                   Reducir si las respuestas del modelo son muy largas.
                   Aumentar si los artículos son muy breves y quieres más contexto.

  --overlap N      Cuántos caracteres repetir entre fragmentos consecutivos (default: 300)
                   Útil para documentos sin artículos (dictámenes en prosa).

  --sin-articulos  Forzar chunking por tamaño aunque el documento tenga artículos.
                   Útil para dictámenes con estructura narrativa, no articulada.

  --fecha FECHA    Fecha del documento en formato YYYY-MM-DD (default: hoy)
                   Ejemplo: --fecha 2024-03-15

  --url-fuente URL URL del documento original para incluir en metadata
                   Ejemplo: --url-fuente "https://contraloria.cl/dictamen/3576"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FLUJO COMPLETO PARA INGESTAR EN LEXIORA:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  1. python preparar_documentos.py --url "..." --fuente "..." → genera output.json
  2. Copiar output.json a documentos_ejemplo/
  3. En n8n: abrir workflow "lexiora-ingest"
  4. En el nodo "Preparar Documentos": cambiar la ruta al nuevo JSON
  5. Ejecutar el workflow manualmente
  6. Verificar en Supabase → Table Editor → tabla "documents" que aparecieron los chunks
"""

import argparse
import json
import os
import re
import sys
from datetime import date
from pathlib import Path


# ──────────────────────────────────────────────────────────────────────────────
# CONSTANTES
# ──────────────────────────────────────────────────────────────────────────────

CHUNK_DEFAULT  = 3000   # ~750 tokens con text-embedding-3-small
OVERLAP_DEFAULT = 300   # overlap para preservar contexto en los cortes

# Regex para detectar inicio de artículos en leyes chilenas.
# Detecta: "Artículo 1", "Artículo 1°", "ARTÍCULO 1", "Art. 1", "Artículo 1.-"
ARTICLE_RE = re.compile(
    r'(?:^|(?<=\n))\s*(?:Art[íi]culo|ARTÍCULO|Art\.)\s+(\d+\w*)[°º]?\s*[.\-–]?',
    re.IGNORECASE
)


# ──────────────────────────────────────────────────────────────────────────────
# EXTRACCIÓN DE TEXTO SEGÚN TIPO DE FUENTE
# ──────────────────────────────────────────────────────────────────────────────

def extraer_texto_url(url: str) -> tuple[str, str]:
    """
    Descarga y extrae el texto de una ley publicada en BCN (bcn.cl/leychile).
    Retorna (texto_limpio, titulo_detectado).
    """
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        print("ERROR: Instala las dependencias: pip install requests beautifulsoup4")
        sys.exit(1)

    print(f"  Descargando: {url}")
    headers = {"User-Agent": "Mozilla/5.0 (compatible; Lexiora-Ingest/1.0)"}

    try:
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        resp.encoding = "utf-8"
    except Exception as e:
        print(f"  ERROR al descargar: {e}")
        sys.exit(1)

    soup = BeautifulSoup(resp.text, "html.parser")

    # Intentar detectar el título de la ley desde el HTML
    titulo = ""
    for selector in ["h1", "h2", ".titulo-norma", ".norma-titulo", "title"]:
        tag = soup.select_one(selector)
        if tag and tag.get_text(strip=True):
            titulo = tag.get_text(strip=True)
            break

    # Eliminar elementos que no son contenido de la ley
    for tag in soup(["script", "style", "nav", "header", "footer",
                     "aside", "form", ".breadcrumb", ".menu", ".navegacion"]):
        tag.decompose()

    # Extraer texto del body principal
    # BCN tiene el contenido en distintos contenedores según la versión
    contenido = None
    for selector in [".norma-cuerpo", ".texto-norma", "#texto-norma",
                     ".articulos", "article", "main", ".contenido"]:
        contenido = soup.select_one(selector)
        if contenido:
            break

    texto = contenido.get_text(separator="\n") if contenido else soup.get_text(separator="\n")
    return limpiar_texto(texto), titulo


def extraer_texto_pdf(ruta: str) -> str:
    """
    Extrae texto de un archivo PDF usando pdfplumber.
    Maneja PDFs de múltiples páginas y limpia encabezados/pies repetidos.
    """
    try:
        import pdfplumber
    except ImportError:
        print("ERROR: Instala pdfplumber: pip install pdfplumber")
        sys.exit(1)

    print(f"  Leyendo PDF: {ruta}")
    paginas = []

    try:
        with pdfplumber.open(ruta) as pdf:
            total = len(pdf.pages)
            print(f"  Total de páginas: {total}")

            for i, pagina in enumerate(pdf.pages, 1):
                if i % 20 == 0:
                    print(f"  Procesando página {i}/{total}...")
                texto = pagina.extract_text()
                if texto:
                    paginas.append(texto)
    except Exception as e:
        print(f"  ERROR al leer PDF: {e}")
        sys.exit(1)

    texto_completo = "\n".join(paginas)

    # Eliminar líneas que parecen encabezados/pies de página repetidos
    # (líneas cortas que aparecen en casi todas las páginas)
    texto_completo = eliminar_encabezados_repetidos(texto_completo, paginas)

    return limpiar_texto(texto_completo)


def extraer_texto_txt(ruta: str) -> str:
    """Lee un archivo de texto plano."""
    print(f"  Leyendo TXT: {ruta}")
    try:
        with open(ruta, "r", encoding="utf-8", errors="replace") as f:
            return limpiar_texto(f.read())
    except Exception as e:
        print(f"  ERROR al leer archivo: {e}")
        sys.exit(1)


def extraer_texto_docx(ruta: str) -> str:
    """Extrae texto de un archivo Word (.docx)."""
    try:
        from docx import Document
    except ImportError:
        print("ERROR: Instala python-docx: pip install python-docx")
        sys.exit(1)

    print(f"  Leyendo DOCX: {ruta}")
    try:
        doc = Document(ruta)
        parrafos = [p.text for p in doc.paragraphs if p.text.strip()]
        return limpiar_texto("\n".join(parrafos))
    except Exception as e:
        print(f"  ERROR al leer DOCX: {e}")
        sys.exit(1)


# ──────────────────────────────────────────────────────────────────────────────
# LIMPIEZA DE TEXTO
# ──────────────────────────────────────────────────────────────────────────────

def limpiar_texto(texto: str) -> str:
    """Limpia el texto extraído: normaliza espacios, elimina basura visual."""
    # Normalizar saltos de línea
    texto = texto.replace("\r\n", "\n").replace("\r", "\n")
    # Eliminar líneas con solo números (páginas)
    texto = re.sub(r'^\s*\d+\s*$', '', texto, flags=re.MULTILINE)
    # Eliminar guiones de corte de palabras al final de línea
    texto = re.sub(r'-\n(\w)', r'\1', texto)
    # Colapsar más de 2 saltos de línea consecutivos
    texto = re.sub(r'\n{3,}', '\n\n', texto)
    # Eliminar espacios múltiples dentro de línea
    texto = re.sub(r'[ \t]{2,}', ' ', texto)
    # Eliminar líneas vacías al inicio y fin
    return texto.strip()


def eliminar_encabezados_repetidos(texto_completo: str, paginas: list[str]) -> str:
    """
    Detecta líneas que aparecen en más del 60% de las páginas
    (encabezados/pies de página del PDF) y las elimina.
    """
    if len(paginas) < 5:
        return texto_completo  # Con pocos páginas no aplica

    # Contar frecuencia de cada línea
    from collections import Counter
    lineas_por_pagina = [set(p.split('\n')) for p in paginas]
    conteo = Counter()
    for lineas in lineas_por_pagina:
        for linea in lineas:
            linea = linea.strip()
            if 3 < len(linea) < 100:  # Líneas cortas típicas de encabezados
                conteo[linea] += 1

    umbral = len(paginas) * 0.6
    encabezados = {linea for linea, cnt in conteo.items() if cnt >= umbral}

    if encabezados:
        print(f"  Eliminando {len(encabezados)} líneas repetidas (encabezados/pies de página)")

    lineas = texto_completo.split('\n')
    return '\n'.join(l for l in lineas if l.strip() not in encabezados)


# ──────────────────────────────────────────────────────────────────────────────
# CHUNKING (DIVISIÓN EN FRAGMENTOS)
# ──────────────────────────────────────────────────────────────────────────────

def dividir_por_articulos(texto: str, max_chars: int, fuente: str,
                           numero: str, materia: str, fecha: str,
                           url_fuente: str) -> list[dict]:
    """
    Divide el texto en chunks usando los artículos como límites naturales.
    Si un artículo es más largo que max_chars, lo sub-divide con overlap.
    Esta es la estrategia óptima para leyes con estructura articulada.
    """
    # Encontrar todas las posiciones donde comienza un artículo
    matches = list(ARTICLE_RE.finditer(texto))

    if not matches:
        return []  # No se encontraron artículos

    print(f"  Artículos detectados: {len(matches)}")
    chunks = []

    for i, match in enumerate(matches):
        num_articulo = match.group(1)
        inicio = match.start()
        fin = matches[i + 1].start() if i + 1 < len(matches) else len(texto)
        contenido = texto[inicio:fin].strip()

        if not contenido:
            continue

        # Si el artículo cabe en un chunk, guardarlo directamente
        if len(contenido) <= max_chars:
            chunks.append({
                "content": contenido,
                "metadata": {
                    "fuente":    fuente,
                    "numero":    numero or fuente,
                    "titulo":    f"Artículo {num_articulo}",
                    "materia":   materia,
                    "fecha":     fecha,
                    "url_fuente": url_fuente,
                    "tipo_chunk": "articulo_completo"
                }
            })
        else:
            # Artículo largo: dividir en sub-chunks con overlap
            sub_chunks = dividir_con_overlap(contenido, max_chars, overlap=300)
            for j, sub in enumerate(sub_chunks):
                chunks.append({
                    "content": sub,
                    "metadata": {
                        "fuente":    fuente,
                        "numero":    numero or fuente,
                        "titulo":    f"Artículo {num_articulo} (parte {j+1}/{len(sub_chunks)})",
                        "materia":   materia,
                        "fecha":     fecha,
                        "url_fuente": url_fuente,
                        "tipo_chunk": "articulo_dividido"
                    }
                })

    return chunks


def dividir_con_overlap(texto: str, max_chars: int, overlap: int) -> list[str]:
    """
    Divide texto en chunks de tamaño max_chars con superposición de `overlap` chars.
    Intenta cortar en límites de oración o párrafo para no romper frases a la mitad.
    """
    if len(texto) <= max_chars:
        return [texto]

    chunks = []
    inicio = 0

    while inicio < len(texto):
        fin = inicio + max_chars

        if fin >= len(texto):
            # Último chunk: tomar todo lo que queda
            chunks.append(texto[inicio:].strip())
            break

        # Intentar cortar en un punto o salto de línea cercano al límite
        # Buscar hacia atrás desde el límite
        corte = fin
        for separador in ['\n\n', '\n', '. ', '.\n']:
            pos = texto.rfind(separador, inicio + max_chars // 2, fin)
            if pos != -1:
                corte = pos + len(separador)
                break

        chunk = texto[inicio:corte].strip()
        if chunk:
            chunks.append(chunk)

        # El siguiente chunk empieza `overlap` caracteres antes del corte
        inicio = max(inicio + 1, corte - overlap)

    return chunks


def dividir_texto_completo(texto: str, max_chars: int, overlap: int,
                            fuente: str, numero: str, materia: str,
                            fecha: str, url_fuente: str,
                            forzar_size: bool = False) -> list[dict]:
    """
    Estrategia de chunking principal:
    1. Si el texto tiene artículos Y no se fuerza size → dividir por artículos
    2. Si no hay artículos o se fuerza size → dividir por tamaño con overlap
    """
    tiene_articulos = bool(ARTICLE_RE.search(texto))

    if tiene_articulos and not forzar_size:
        print("  Estrategia: división por artículos")
        chunks_dicts = dividir_por_articulos(
            texto, max_chars, fuente, numero, materia, fecha, url_fuente
        )
        if chunks_dicts:
            return chunks_dicts
        # Si el regex no resultó, caer en chunking por tamaño
        print("  No se extrajeron artículos válidos, usando chunking por tamaño")

    print("  Estrategia: división por tamaño con overlap")
    partes = dividir_con_overlap(texto, max_chars, overlap)
    total = len(partes)

    return [
        {
            "content": parte,
            "metadata": {
                "fuente":    fuente,
                "numero":    numero or fuente,
                "titulo":    f"Fragmento {i+1} de {total}",
                "materia":   materia,
                "fecha":     fecha,
                "url_fuente": url_fuente,
                "tipo_chunk": "fragmento"
            }
        }
        for i, parte in enumerate(partes)
        if parte.strip()
    ]


# ──────────────────────────────────────────────────────────────────────────────
# PROCESAMIENTO PRINCIPAL
# ──────────────────────────────────────────────────────────────────────────────

def procesar_documento(texto: str, titulo_detectado: str, args) -> list[dict]:
    """Aplica limpieza y chunking a un texto ya extraído."""
    fuente  = args.fuente
    numero  = args.numero or titulo_detectado or args.fuente
    materia = args.materia or "general"
    fecha   = args.fecha or str(date.today())
    url_f   = args.url_fuente or ""

    print(f"  Longitud del texto: {len(texto):,} caracteres")

    chunks = dividir_texto_completo(
        texto       = texto,
        max_chars   = args.chunk,
        overlap     = args.overlap,
        fuente      = fuente,
        numero      = numero,
        materia     = materia,
        fecha       = fecha,
        url_fuente  = url_f,
        forzar_size = args.sin_articulos
    )

    # Filtrar chunks demasiado cortos (menos de 100 chars no aportan valor al RAG)
    antes = len(chunks)
    chunks = [c for c in chunks if len(c["content"]) >= 100]
    if antes != len(chunks):
        print(f"  Filtrados {antes - len(chunks)} chunks demasiado cortos (<100 chars)")

    return chunks


# ──────────────────────────────────────────────────────────────────────────────
# PUNTO DE ENTRADA
# ──────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Pre-procesador de documentos jurídicos para Lexiora RAG",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Ver el encabezado del script para ejemplos completos de uso."
    )

    # Fuentes de entrada (mutuamente excluyentes)
    grupo = parser.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--url",     metavar="URL",   help="URL de la ley en bcn.cl/leychile")
    grupo.add_argument("--pdf",     metavar="RUTA",  help="Ruta a un archivo PDF")
    grupo.add_argument("--txt",     metavar="RUTA",  help="Ruta a un archivo de texto plano (.txt)")
    grupo.add_argument("--docx",    metavar="RUTA",  help="Ruta a un archivo Word (.docx)")
    grupo.add_argument("--carpeta", metavar="RUTA",  help="Carpeta con múltiples PDFs")

    # Metadata del documento
    parser.add_argument("--fuente",    required=True, help='Nombre del cuerpo legal (ej: "Código del Trabajo")')
    parser.add_argument("--numero",    default="",    help='Número de ley/dictamen (ej: "Ley 18.620")')
    parser.add_argument("--materia",   default="",    help='Categoría temática (ej: "laboral", "administrativo")')
    parser.add_argument("--fecha",     default="",    help="Fecha del documento YYYY-MM-DD (default: hoy)")
    parser.add_argument("--url-fuente",default="",    help="URL del documento original (para citas)")

    # Opciones de chunking
    parser.add_argument("--chunk",   type=int, default=CHUNK_DEFAULT,   help=f"Tamaño máximo de chunk en chars (default: {CHUNK_DEFAULT})")
    parser.add_argument("--overlap", type=int, default=OVERLAP_DEFAULT, help=f"Overlap entre chunks en chars (default: {OVERLAP_DEFAULT})")
    parser.add_argument("--sin-articulos", action="store_true",         help="Forzar chunking por tamaño aunque haya artículos")

    # Salida
    parser.add_argument("--salida", default="documentos_salida.json", help="Nombre del archivo JSON de salida (default: documentos_salida.json)")

    args = parser.parse_args()
    todos_los_chunks = []

    # ── Modo carpeta: procesar múltiples PDFs ─────────────────────────────────
    if args.carpeta:
        carpeta = Path(args.carpeta)
        if not carpeta.is_dir():
            print(f"ERROR: La carpeta '{args.carpeta}' no existe.")
            sys.exit(1)

        pdfs = sorted(carpeta.glob("*.pdf"))
        if not pdfs:
            print(f"ERROR: No se encontraron archivos PDF en '{args.carpeta}'")
            sys.exit(1)

        print(f"\nProcesando {len(pdfs)} PDF(s) en '{args.carpeta}'")

        for i, pdf_path in enumerate(pdfs, 1):
            print(f"\n[{i}/{len(pdfs)}] {pdf_path.name}")
            # Usar el nombre del archivo como número de referencia si no se especificó
            args_doc = argparse.Namespace(**vars(args))
            if not args_doc.numero:
                args_doc.numero = pdf_path.stem.replace("_", " ").replace("-", " ")

            texto = extraer_texto_pdf(str(pdf_path))
            if not texto:
                print(f"  ADVERTENCIA: No se pudo extraer texto de {pdf_path.name}, omitiendo.")
                continue

            chunks = procesar_documento(texto, "", args_doc)
            todos_los_chunks.extend(chunks)
            print(f"  → {len(chunks)} chunks generados")

    # ── Modo archivo único o URL ───────────────────────────────────────────────
    else:
        print(f"\nProcesando documento...")
        titulo_detectado = ""

        if args.url:
            texto, titulo_detectado = extraer_texto_url(args.url)
            if titulo_detectado and not args.numero:
                args.numero = titulo_detectado
                print(f"  Título detectado: {titulo_detectado}")
        elif args.pdf:
            if not Path(args.pdf).exists():
                print(f"ERROR: El archivo '{args.pdf}' no existe.")
                sys.exit(1)
            texto = extraer_texto_pdf(args.pdf)
        elif args.txt:
            if not Path(args.txt).exists():
                print(f"ERROR: El archivo '{args.txt}' no existe.")
                sys.exit(1)
            texto = extraer_texto_txt(args.txt)
        elif args.docx:
            if not Path(args.docx).exists():
                print(f"ERROR: El archivo '{args.docx}' no existe.")
                sys.exit(1)
            texto = extraer_texto_docx(args.docx)

        if not texto:
            print("ERROR: No se pudo extraer texto del documento.")
            sys.exit(1)

        todos_los_chunks = procesar_documento(texto, titulo_detectado, args)

    # ── Guardar resultado ─────────────────────────────────────────────────────
    if not todos_los_chunks:
        print("\nERROR: No se generaron chunks. Verifique el documento y los parámetros.")
        sys.exit(1)

    salida = Path(args.salida)
    salida.parent.mkdir(parents=True, exist_ok=True)

    with open(salida, "w", encoding="utf-8") as f:
        json.dump(todos_los_chunks, f, ensure_ascii=False, indent=2)

    # ── Resumen final ─────────────────────────────────────────────────────────
    longitudes = [len(c["content"]) for c in todos_los_chunks]
    print(f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓  PROCESAMIENTO COMPLETADO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Chunks generados:  {len(todos_los_chunks)}
  Tamaño promedio:   {sum(longitudes)//len(longitudes):,} chars/chunk
  Tamaño mínimo:     {min(longitudes):,} chars
  Tamaño máximo:     {max(longitudes):,} chars
  Archivo de salida: {salida}

PRÓXIMO PASO:
  Abrir n8n → workflow "lexiora-ingest"
  En el nodo "Preparar Documentos", cambiar la
  ruta al archivo: {salida}
  Luego ejecutar el workflow manualmente.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")


if __name__ == "__main__":
    main()
