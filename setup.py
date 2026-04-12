#!/usr/bin/env python3
"""
Lexiora — Setup Script
======================
Importa los workflows de la carpeta workflows/ en una instancia de n8n.

Uso:
    # Con variables de entorno:
    N8N_API_KEY=<key> python setup.py

    # O con el .env del proyecto (requiere python-dotenv):
    python setup.py

Requisitos previos:
    1. n8n corriendo (local: docker compose up -d / producción: ya activo)
    2. API Key de n8n: Settings → API → Create API Key
    3. Credenciales configuradas en n8n → Credentials:
       - "OpenAI Lexiora"   → tipo: OpenAI API
       - "WhatsApp Lexiora" → tipo: HTTP Header Auth (name: Authorization, value: Bearer <token>)
    4. sql/setup.sql ejecutado en Supabase SQL Editor
"""

import os
import json
import sys
import requests
from pathlib import Path

# ── Cargar .env si existe ────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv es opcional

# ── Configuración ────────────────────────────────────────────────────────────
N8N_API_URL = os.getenv("N8N_API_URL", "http://localhost:5678")
N8N_API_KEY = os.getenv("N8N_API_KEY")
WORKFLOWS_DIR = Path(__file__).parent / "workflows"

if not N8N_API_KEY:
    print("ERROR: N8N_API_KEY no está configurado.")
    print()
    print("  1. En n8n: Settings → API → Create API Key")
    print("  2. Exportar antes de correr este script:")
    print("       Windows:  set N8N_API_KEY=<tu-api-key>")
    print("       Linux/Mac: export N8N_API_KEY=<tu-api-key>")
    sys.exit(1)

HEADERS = {
    "X-N8N-API-KEY": N8N_API_KEY,
    "Content-Type": "application/json",
}


def list_existing_workflows() -> dict:
    """Retorna {nombre: id} de los workflows ya existentes en n8n."""
    try:
        r = requests.get(f"{N8N_API_URL}/api/v1/workflows", headers=HEADERS, timeout=10)
        r.raise_for_status()
        return {w["name"]: w["id"] for w in r.json().get("data", [])}
    except requests.exceptions.ConnectionError:
        print(f"\nERROR: No se pudo conectar a {N8N_API_URL}")
        print("  Verifica que n8n esté corriendo (docker compose up -d)")
        sys.exit(1)


def import_workflow(json_path: Path, existing: dict) -> str | None:
    """Crea o actualiza un workflow en n8n. Retorna el ID si fue exitoso."""
    with open(json_path, encoding="utf-8") as f:
        workflow = json.load(f)

    name = workflow.get("name", json_path.stem)

    if name in existing:
        wid = existing[name]
        print(f"  ↻ '{name}' ya existe (id: {wid}) — actualizando...")
        r = requests.put(
            f"{N8N_API_URL}/api/v1/workflows/{wid}",
            headers=HEADERS,
            json=workflow,
            timeout=30,
        )
    else:
        print(f"  + Creando '{name}'...")
        r = requests.post(
            f"{N8N_API_URL}/api/v1/workflows",
            headers=HEADERS,
            json=workflow,
            timeout=30,
        )

    if r.ok:
        wid = r.json().get("id", "?")
        print(f"    ✓ OK (id: {wid})")
        return wid
    else:
        print(f"    ✗ Error {r.status_code}: {r.text[:200]}")
        return None


def activate_workflow(wid: str, name: str):
    """Activa el workflow en n8n."""
    r = requests.post(
        f"{N8N_API_URL}/api/v1/workflows/{wid}/activate",
        headers=HEADERS,
        timeout=10,
    )
    if r.ok:
        print(f"    ✓ '{name}' activado")
    else:
        # Algunos workflows (ej: ingest con chat trigger) no se activan vía API
        print(f"    ⚠ No se pudo activar '{name}' via API — actívalo manualmente en n8n")


# ── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"\nLexiora — Importando workflows en {N8N_API_URL}\n")

    workflow_files = sorted(WORKFLOWS_DIR.glob("*.json"))
    if not workflow_files:
        print(f"No se encontraron archivos JSON en {WORKFLOWS_DIR}/")
        print("Exporta los workflows desde n8n y guárdalos en esa carpeta.")
        sys.exit(1)

    existing = list_existing_workflows()
    imported_ids = {}

    for wf_path in workflow_files:
        wid = import_workflow(wf_path, existing)
        if wid:
            imported_ids[wf_path.stem] = wid

    if imported_ids:
        print()
        for name, wid in imported_ids.items():
            activate_workflow(wid, name)

    print("\n✅ Listo.\n")
    print("Próximos pasos:")
    print("  1. Configura las credenciales en n8n → Credentials (si no lo hiciste):")
    print("       - 'OpenAI Lexiora'    → tipo: OpenAI API")
    print("       - 'WhatsApp Lexiora'  → tipo: HTTP Header Auth")
    print("         name: Authorization | value: Bearer <tu-whatsapp-token>")
    print()
    print("  2. Ejecuta sql/setup.sql en Supabase Dashboard → SQL Editor")
    print()
    print("  3. Configura el webhook de WhatsApp en Meta for Developers:")
    print(f"       URL:    {N8N_API_URL.rstrip('/')}/webhook/whatsapp")
    print("       Token:  (el Verify Token configurado en el nodo Webhook de n8n)")
    print()
    print("  4. Para ingestar documentos, abre el chat de lexiora-ingest:")
    print(f"       {N8N_API_URL.rstrip('/')}/webhook/lexiora-ingest-chat/chat")
