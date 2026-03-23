# Lexiora — Guía de Configuración para el Desarrollador

Guía paso a paso para dejar el sistema corriendo, tanto en desarrollo local como en el servidor de producción del cliente.

---

## Requisitos previos (instalar una sola vez)

| Herramienta | Versión mínima | Instalación |
|---|---|---|
| Docker Desktop | Cualquiera reciente | docker.com/get-started |
| Python | 3.10+ | python.org |
| Node.js | 18+ | nodejs.org |
| pnpm | 8+ | `npm install -g pnpm` |
| Git | Cualquiera | git-scm.com |
| Cliente SSH | — | OpenSSH (incluido en Windows 10+), Termius, o similar |

---

## PARTE 1 — Setup en desarrollo local

### Paso 1 — Clonar el repositorio

```bash
git clone <URL_DEL_REPO>
cd workflow_Lexiora
```

### Paso 2 — Configurar credenciales en `.env`

```bash
cp .env.example .env
```

Abrir `.env` y rellenar con las credenciales del cliente (ver `GUIA_CREDENCIALES.md` para saber cómo obtener cada una):

```
OPENAI_API_KEY=sk-...
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...
WHATSAPP_API_TOKEN=EAAxx...
WHATSAPP_PHONE_NUMBER_ID=12345...
N8N_WEBHOOK_URL=https://xxxx.ngrok-free.app   # temporal, ver paso 5
N8N_USER=admin
N8N_PASSWORD=contraseña_segura_aqui
N8N_ENCRYPTION_KEY=# generar con: openssl rand -hex 32
FLOW_API_KEY=...
FLOW_SECRET_KEY=...
FLOW_API_URL=https://sandbox.flow.cl/api      # sandbox para pruebas
PRECIO_CLP=2990
```

### Paso 3 — Crear las tablas en Supabase

1. Ir a supabase.com → Dashboard del proyecto del cliente
2. Menú izquierdo → SQL Editor → New query
3. Pegar el contenido de `sql/setup.sql`
4. Hacer clic en "Run"
5. Verificar que aparezcan las tablas: `documents`, `injection_attempts`, `pagos`, `usuarios`

### Paso 4 — Levantar n8n con Docker

```bash
docker compose up -d
```

Verificar que n8n está corriendo:
```bash
docker compose logs -f   # ver logs en tiempo real (Ctrl+C para salir)
```

Abrir `http://localhost:5678` en el navegador → debería aparecer el login de n8n.

Credenciales: las mismas `N8N_USER` y `N8N_PASSWORD` del `.env`.

### Paso 5 — Exponer el webhook temporalmente con ngrok

El webhook de WhatsApp necesita una URL pública. Para desarrollo usamos ngrok.

```bash
# Si no tienes ngrok instalado:
# Descargar desde ngrok.com → descomprimir → agregar al PATH

ngrok http 5678
```

Copiar la URL `https://xxxx.ngrok-free.app` que aparece y actualizar en `.env`:
```
N8N_WEBHOOK_URL=https://xxxx.ngrok-free.app
```

Reiniciar n8n para que tome el nuevo valor:
```bash
docker compose restart
```

### Paso 6 — Crear la API Key de n8n

1. En n8n (`http://localhost:5678`) → menú izquierdo → Settings → API
2. Botón "Create API Key" → dar nombre "Lexiora Dev"
3. Copiar la clave generada

Esa clave se usa para ejecutar `crear_workflows.py`. No va al `.env` del docker-compose.

### Paso 7 — Configurar credenciales en n8n

Las API keys de OpenAI, Supabase y WhatsApp se configuran una vez en el panel de credenciales de n8n, **no** dentro de los workflows directamente.

En n8n → menú izquierdo → Credentials → Add credential:

**OpenAI:**
- Tipo: "OpenAI API"
- API Key: el valor de `OPENAI_API_KEY`
- Nombre: "OpenAI Lexiora"

**Supabase:**
- Tipo: "Supabase API" (o "Header Auth" si no aparece el nodo Supabase)
- Host: el valor de `SUPABASE_URL`
- Service Role Secret: el valor de `SUPABASE_SERVICE_KEY`
- Nombre: "Supabase Lexiora"

**WhatsApp (HTTP Header Auth):**
- Tipo: "Header Auth"
- Name: `Authorization`
- Value: `Bearer <WHATSAPP_API_TOKEN>`
- Nombre: "WhatsApp Lexiora"

### Paso 8 — Crear los 3 workflows

```bash
set N8N_API_KEY=<clave_del_paso_6>
set N8N_API_URL=http://localhost:5678
python crear_workflows.py
```

En Windows PowerShell usar `$env:` en vez de `set`:
```powershell
$env:N8N_API_KEY = "<clave_del_paso_6>"
$env:N8N_API_URL = "http://localhost:5678"
python crear_workflows.py
```

El script creará los workflows `lexiora-whatsapp-rag`, `lexiora-payment-webhook` y `lexiora-ingest`.

Verificar en n8n → Workflows que aparecen los 3. **Activarlos manualmente** con el toggle.

> **Nota**: Si algún nodo muestra error de credenciales, ir al nodo → cambiar la credencial al nombre que configuraste en el paso 7.

### Paso 9 — Ingestar documentos de prueba

Instalar dependencias Python (solo la primera vez):
```bash
pip install requests beautifulsoup4 pdfplumber python-docx
```

Preparar documentos desde la BCN (ejemplo con el Código del Trabajo):
```bash
python preparar_documentos.py \
  --url "https://www.bcn.cl/leychile/navegar?idNorma=207436" \
  --fuente "Código del Trabajo" \
  --numero "DFL-1" \
  --materia "derecho_laboral" \
  --salida "codigo_trabajo_chunks.json"
```

O usar los documentos de ejemplo incluidos:
```bash
# Los JSON en documentos_ejemplo/ ya tienen el formato correcto
# Copiarlos a la carpeta que el workflow lexiora-ingest está configurado para leer
```

Luego en n8n → Workflows → `lexiora-ingest` → ejecutar manualmente (botón "Execute Workflow").

### Paso 10 — Test de punta a punta

1. Abrir WhatsApp con el número configurado en `WHATSAPP_PHONE_NUMBER_ID`
2. Enviar un mensaje de texto con una pregunta legal
3. Verificar en n8n → Executions que el workflow se ejecutó
4. Verificar que llegó respuesta al WhatsApp

---

## PARTE 2 — Verificación del webhook de WhatsApp

El webhook de WhatsApp necesita verificarse en Meta for Developers antes de poder recibir mensajes.

### Paso a paso:

1. En n8n → Workflow `lexiora-whatsapp-rag` → hacer clic en el nodo "Webhook WhatsApp"
2. Copiar la URL de producción que aparece (ej: `https://n8n.lexiora.cl/webhook/whatsapp`)
3. En Meta for Developers → Tu App → WhatsApp → Configuration → Webhooks:
   - Webhook URL: la URL copiada
   - Verify Token: cualquier string aleatorio (ej: `lexiora_verify_2024`)
   - Suscribir a: `messages`
4. Meta enviará una petición de verificación al webhook → n8n responde automáticamente con el `hub.challenge`
5. Si la verificación es exitosa, el webhook queda activo

> El nodo Webhook de n8n maneja la verificación automáticamente. No se necesita código adicional.

---

## PARTE 3 — Despliegue en producción (VPS DigitalOcean del cliente)

### Prerequisitos
- El cliente entrega: IP del Droplet, usuario `root`, contraseña
- Dominio configurado con registro DNS A apuntando a la IP (ej: `n8n.lexiora.cl` → IP)
- El registro DNS debe estar propagado antes de solicitar el SSL

### Paso 1 — Conectarse al servidor

```bash
ssh root@<IP_DEL_SERVIDOR>
```

### Paso 2 — Instalar Docker en el servidor

```bash
apt-get update
apt-get install -y docker.io docker-compose-plugin
systemctl enable docker
systemctl start docker

# Verificar instalación
docker --version
docker compose version
```

### Paso 3 — Instalar Nginx y Certbot

```bash
apt-get install -y nginx certbot python3-certbot-nginx
```

### Paso 4 — Subir el proyecto al servidor

Opción A — Desde un repositorio privado de GitHub:
```bash
# En el servidor
git clone https://github.com/<usuario>/<repo>.git
cd workflow_Lexiora
```

Opción B — Copiar directamente desde tu máquina local:
```bash
# En tu máquina local (fuera del SSH)
scp -r ./workflow_Lexiora root@<IP_DEL_SERVIDOR>:/root/
```

### Paso 5 — Crear el `.env` en el servidor

```bash
# En el servidor
cd /root/workflow_Lexiora
cp .env.example .env
nano .env   # editar con las credenciales reales del cliente
```

Cambios respecto al `.env` de desarrollo:
- `N8N_WEBHOOK_URL=https://n8n.lexiora.cl`  (dominio real, sin ngrok)
- `FLOW_API_URL=https://www.flow.cl/api`     (producción, no sandbox)

### Paso 6 — Configurar Nginx

```bash
cp nginx/lexiora.conf /etc/nginx/sites-available/lexiora

# Editar el archivo para reemplazar el dominio de ejemplo
nano /etc/nginx/sites-available/lexiora
# Reemplazar "n8n.tudominio.cl" por el dominio real, ej: "n8n.lexiora.cl"

# Activar el sitio
ln -s /etc/nginx/sites-available/lexiora /etc/nginx/sites-enabled/lexiora

# Quitar el sitio default de nginx para evitar conflictos
rm -f /etc/nginx/sites-enabled/default

# Verificar configuración
nginx -t

# Reiniciar nginx
systemctl restart nginx
```

### Paso 7 — Obtener SSL con Let's Encrypt

```bash
certbot --nginx -d n8n.lexiora.cl
```

Certbot pedirá un email para notificaciones y aceptar los términos. Luego configura HTTPS automáticamente.

El SSL se renueva automáticamente (Certbot instala un cron job). Para verificar:
```bash
certbot renew --dry-run
```

### Paso 8 — Levantar n8n en producción

```bash
cd /root/workflow_Lexiora
docker compose up -d
```

Verificar:
```bash
docker compose ps       # debe mostrar n8n como "Up"
docker compose logs -f  # ver logs
```

Abrir `https://n8n.lexiora.cl` en el navegador para confirmar que funciona.

### Paso 9 — Configurar n8n en producción

Repetir los pasos 6, 7 y 8 de la Parte 1 (API Key, credenciales, crear workflows), esta vez en la instancia de producción.

```bash
# Instalar Python y dependencias en el servidor
apt-get install -y python3 python3-pip
pip3 install requests beautifulsoup4 pdfplumber python-docx

# Crear workflows (ejecutar desde el servidor o desde tu máquina apuntando a producción)
N8N_API_KEY=<clave_produccion> N8N_API_URL=https://n8n.lexiora.cl python3 crear_workflows.py
```

### Paso 10 — Ingestar documentos en producción

```bash
python3 preparar_documentos.py \
  --url "https://www.bcn.cl/leychile/navegar?idNorma=207436" \
  --fuente "Código del Trabajo" \
  --numero "DFL-1" \
  --materia "derecho_laboral" \
  --salida "codigo_trabajo_chunks.json"
```

Luego ejecutar `lexiora-ingest` manualmente desde n8n.

---

## PARTE 4 — Mantenimiento del servidor

### Ver logs de n8n
```bash
docker compose logs -f
```

### Reiniciar n8n
```bash
docker compose restart
```

### Actualizar n8n a la última versión
```bash
docker compose pull
docker compose up -d
```

### Backup manual
```bash
docker compose down
tar -czf backup_$(date +%Y%m%d_%H%M).tar.gz n8n_data/
docker compose up -d
```

### Ver uso de disco y memoria
```bash
df -h       # disco
free -h     # memoria RAM
docker stats # uso por contenedor (tiempo real)
```

### Monitorear el SSL
```bash
certbot renew --dry-run   # simular renovación sin aplicar
```

---

## Resumen de URLs y puertos

| Servicio | URL / Puerto | Descripción |
|---|---|---|
| n8n (local) | `http://localhost:5678` | Panel de administración |
| n8n (producción) | `https://n8n.lexiora.cl` | Panel en el servidor |
| Supabase | `https://xxxx.supabase.co` | Dashboard de la BD |
| Webhook WhatsApp | `https://n8n.lexiora.cl/webhook/whatsapp` | Recibe mensajes |
| Webhook pagos | `https://n8n.lexiora.cl/webhook/payment` | Recibe confirmaciones Flow |

---

## Checklist de entrega al cliente

- [ ] `.env` configurado con credenciales reales en el servidor
- [ ] SQL ejecutado en Supabase (4 tablas + 2 funciones RPC)
- [ ] n8n corriendo con HTTPS en `n8n.lexiora.cl`
- [ ] 3 workflows creados y **activos** en n8n
- [ ] Credenciales de OpenAI, Supabase y WhatsApp configuradas en n8n
- [ ] Webhook verificado en Meta for Developers
- [ ] Documentos jurídicos ingestados en Supabase
- [ ] Test de mensaje WhatsApp → respuesta correcta
- [ ] Términos de uso y política de privacidad con textos finales
