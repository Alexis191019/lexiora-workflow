# Lexiora — Guía de Configuración para el Desarrollador

Guía paso a paso para dejar el sistema corriendo, tanto en desarrollo local como en el servidor de producción del cliente.

---

## Requisitos previos (instalar una sola vez)

| Herramienta | Versión mínima | Instalación |
|---|---|---|
| Docker Desktop | Cualquiera reciente | docker.com/get-started |
| Python | 3.10+ | python.org |
| Git | Cualquiera | git-scm.com |
| Cliente SSH | — | OpenSSH (incluido en Windows 10+), Termius, o similar |

---

## PARTE 1 — Setup en desarrollo local

### Paso 1 — Clonar el repositorio

```bash
git clone https://github.com/Alexis191019/lexiora-workflow
cd lexiora-workflow
```

### Paso 2 — Configurar el `.env`

```bash
cp .env.example .env
```

Abrir `.env` y rellenar:

```
N8N_USER=admin
N8N_PASSWORD=contraseña_segura_aqui
N8N_ENCRYPTION_KEY=   # generar con: openssl rand -hex 32
N8N_WEBHOOK_URL=https://xxxx.ngrok-free.app   # temporal, ver paso 5

SUPABASE_URL=https://XXXX.supabase.co
SUPABASE_SERVICE_KEY=eyJ...

FLOW_API_KEY=...
FLOW_SECRET_KEY=...
FLOW_API_URL=https://sandbox.flow.cl/api
PRECIO_CLP=2990
```

> **Importante**: `OPENAI_API_KEY` y `WHATSAPP_API_TOKEN` NO van en el `.env`. Se configuran en el panel de Credentials de n8n (paso 7), donde quedan cifrados.

### Paso 3 — Crear las tablas en Supabase

1. Ir a supabase.com → Dashboard del proyecto
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

Abrir `http://localhost:5678` → debería aparecer el login de n8n.
Credenciales: las mismas `N8N_USER` y `N8N_PASSWORD` del `.env`.

### Paso 5 — Exponer el webhook temporalmente con ngrok

El webhook de WhatsApp necesita una URL pública.

```bash
ngrok http 5678
```

Copiar la URL `https://xxxx.ngrok-free.app` y actualizar en `.env`:
```
N8N_WEBHOOK_URL=https://xxxx.ngrok-free.app
```

Reiniciar n8n:
```bash
docker compose restart
```

### Paso 6 — Crear la API Key de n8n

1. En n8n → menú izquierdo → Settings → API
2. Botón "Create API Key" → dar nombre "Lexiora Dev"
3. Copiar la clave generada

### Paso 7 — Configurar credenciales en n8n

En n8n → menú izquierdo → Credentials → Add credential:

**OpenAI:**
- Tipo: "OpenAI API"
- API Key: el valor de tu `OPENAI_API_KEY`
- Nombre: `OpenAI Lexiora`

**WhatsApp (HTTP Header Auth):**
- Tipo: "Header Auth"
- Name: `Authorization`
- Value: `Bearer <WHATSAPP_API_TOKEN>`
- Nombre: `WhatsApp Lexiora`

> Supabase y Flow NO necesitan credential en n8n — sus valores se leen directamente desde `$env.SUPABASE_URL`, `$env.FLOW_API_KEY`, etc. en los nodos Code.

### Paso 8 — Crear los 3 workflows

```bash
# Windows CMD
set N8N_API_KEY=<clave_del_paso_6>
set N8N_API_URL=http://localhost:5678
python crear_workflows.py

# Windows PowerShell
$env:N8N_API_KEY = "<clave_del_paso_6>"
$env:N8N_API_URL = "http://localhost:5678"
python crear_workflows.py
```

El script creará: `lexiora-whatsapp-rag`, `lexiora-payment-webhook`, `lexiora-ingest`.

Verificar en n8n → Workflows que aparecen los 3. **Activarlos manualmente** con el toggle.

> Si algún nodo muestra error de credenciales: ir al nodo → cambiar la credencial al nombre que configuraste en el paso 7.

> Para el nodo "Generar Embeddings" en `lexiora-ingest`: abrir el nodo y asignar la credencial `OpenAI Lexiora`.

### Paso 9 — Ingestar documentos de prueba

Con el nuevo workflow `lexiora-ingest` basado en Chat:

1. Activar el workflow `lexiora-ingest` en n8n
2. Abrir la URL del chat: `http://localhost:5678/webhook/lexiora-ingest-chat/chat`
3. Escribir la metadata en el chat:
   ```
   fuente: Código del Trabajo | numero: DFL-1 | materia: derecho_laboral
   ```
4. Adjuntar el PDF y enviar
5. Esperar la confirmación: `✅ X chunks guardados en Supabase.`

> El PDF debe tener texto seleccionable (no escaneado). PDFs de Chile Atiende, BCN descargados manualmente, etc.

### Paso 10 — Test de punta a punta

1. Abrir WhatsApp con el número configurado en `WHATSAPP_PHONE_NUMBER_ID`
2. Enviar un mensaje de texto con una pregunta legal
3. Verificar en n8n → Executions que el workflow se ejecutó
4. Verificar que llegó respuesta al WhatsApp

---

## PARTE 2 — Verificación del webhook de WhatsApp

1. En n8n → Workflow `lexiora-whatsapp-rag` → copiar la URL del nodo "Webhook WhatsApp"
2. En Meta for Developers → Tu App → WhatsApp → Configuration → Webhooks:
   - Webhook URL: `https://n8n.lexiora.cl/webhook/whatsapp`
   - Verify Token: cualquier string aleatorio (ej: `lexiora_verify_2024`)
   - Suscribir a: `messages`
3. Si la verificación es exitosa, el webhook queda activo

> n8n responde automáticamente con el `hub.challenge` — no se necesita código adicional.

---

## PARTE 3 — Despliegue en producción (VPS DigitalOcean)

### Datos del servidor actual
- **IP**: `161.35.132.126`
- **Usuario**: `root`
- **Directorio**: `/root/lexiora-workflow`
- **Dominio**: `n8n.lexiora.cl`

### Paso 1 — Conectarse al servidor

```bash
ssh root@161.35.132.126
```

### Paso 2 — Instalar Docker en el servidor

> ⚠️ **No usar** `apt-get install docker-compose-plugin` directamente — ese paquete no existe en los repos de Ubuntu. Instalar desde el repositorio oficial de Docker:

```bash
apt-get update
apt-get install -y ca-certificates curl gnupg lsb-release

# Agregar la clave GPG oficial de Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
  gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Agregar el repositorio de Docker
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | \
  tee /etc/apt/sources.list.d/docker.list

apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
systemctl enable docker && systemctl start docker

# Verificar
docker --version
docker compose version
```

### Paso 3 — Instalar Nginx y Certbot

```bash
apt-get install -y nginx certbot python3-certbot-nginx
```

### Paso 4 — Subir el proyecto al servidor

```bash
cd /root
git clone https://github.com/Alexis191019/lexiora-workflow
cd lexiora-workflow
```

### Paso 5 — Crear el `.env` en el servidor

```bash
cp .env.example .env
nano .env   # rellenar con las credenciales reales del cliente
```

Diferencias respecto al `.env` de desarrollo:
```
N8N_WEBHOOK_URL=https://n8n.lexiora.cl     # dominio real, sin ngrok
FLOW_API_URL=https://www.flow.cl/api       # producción, no sandbox
```

### Paso 6 — Configurar Nginx y obtener SSL

> ⚠️ **Orden obligatorio**: el certificado SSL debe obtenerse ANTES de activar la config HTTPS.
> Si nginx intenta cargar un certificado que no existe, falla al arrancar.

> ⚠️ **Pre-requisito DNS**: verificar que el dominio apunta a la IP del VPS ANTES de correr Certbot.
> Si el dominio aún apunta a Vercel u otro servicio, Certbot fallará.
> Verificar con: `dig n8n.lexiora.cl +short` (debe mostrar `161.35.132.126`)

**6.1 — Configuración HTTP temporal para validar el dominio:**
```bash
rm -f /etc/nginx/sites-enabled/default

cat > /etc/nginx/sites-available/lexiora << 'EOF'
server {
    listen 80;
    server_name n8n.lexiora.cl;
    location / {
        return 200 'ok';
        add_header Content-Type text/plain;
    }
}
EOF

ln -s /etc/nginx/sites-available/lexiora /etc/nginx/sites-enabled/lexiora
nginx -t && systemctl restart nginx
```

**6.2 — Obtener el certificado SSL:**
```bash
certbot --nginx -d n8n.lexiora.cl
# Certbot pedirá email y aceptar términos.
# Al finalizar el certificado queda en /etc/letsencrypt/live/n8n.lexiora.cl/
```

Verificar renovación automática:
```bash
certbot renew --dry-run
```

**6.3 — Aplicar la configuración nginx definitiva del proyecto:**
```bash
cp /root/lexiora-workflow/nginx/lexiora.conf /etc/nginx/sites-available/lexiora
sed -i 's/n8n.tudominio.cl/n8n.lexiora.cl/g' /etc/nginx/sites-available/lexiora
nginx -t && systemctl restart nginx
```

### Paso 7 — Levantar n8n en producción

```bash
cd /root/lexiora-workflow
docker compose up -d
```

Verificar:
```bash
docker compose ps       # debe mostrar n8n como "Up"
docker compose logs -f  # ver logs
```

Abrir `https://n8n.lexiora.cl` para confirmar que funciona.

### Paso 8 — Configurar n8n en producción

Repetir los pasos 6, 7 y 8 de la Parte 1 (API Key, credenciales, crear workflows):

```bash
apt-get install -y python3 python3-pip
pip3 install requests

# Crear workflows
N8N_API_KEY=<clave_produccion> \
N8N_API_URL=https://n8n.lexiora.cl \
python3 crear_workflows.py
```

### Paso 9 — Ingestar documentos en producción

1. Subir los PDFs al servidor (desde Google Drive con gdown, o via scp):
   ```bash
   pip3 install gdown
   gdown "https://drive.google.com/uc?id=FILE_ID" -O /tmp/documento.pdf
   ```

2. Abrir la URL del chat de ingesta:
   `https://n8n.lexiora.cl/webhook/lexiora-ingest-chat/chat`

3. Escribir la metadata y adjuntar el PDF

---

## PARTE 4 — Actualizar el servidor desde GitHub

El servidor nunca debe editarse directamente. Todos los cambios se hacen en local, se pushean y se actualiza el servidor con `git pull`.

```bash
# En local (tu máquina)
git add .
git commit -m "descripción del cambio"
git push origin master

# En el servidor (VPS)
ssh root@161.35.132.126
cd /root/lexiora-workflow
git pull
docker compose up -d   # si cambió docker-compose.yml o .env
```

### Si `git pull` falla por cambios locales en el servidor

```bash
# Descartar cambios en archivos modificados
git checkout -- nombre_del_archivo.yml

# Descartar archivos eliminados localmente
git clean -f carpeta/

# Ahora sí hacer pull
git pull
```

> Si git pide identidad para commitear, nunca commitear en el servidor.
> Usar siempre `git checkout --` para descartar, no `git commit`.

---

## PARTE 5 — Mantenimiento del servidor

### Ver logs de n8n
```bash
docker compose logs -f
docker compose logs --tail=50   # últimas 50 líneas
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
df -h        # disco
free -h      # memoria RAM
docker stats # uso por contenedor (tiempo real)
```

---

## PARTE 6 — Troubleshooting

### n8n no arranca / muestra `Restarting`
1. Ver el error exacto: `docker compose logs --tail=50`
2. Causas frecuentes:
   - `.env` incompleto o con variables vacías
   - `N8N_ENCRYPTION_KEY` no definida
   - Puerto 5678 ya en uso por otro proceso

### n8n arranca pero no descifra credenciales (`Mismatching encryption keys`)
- Causa: se cambió `N8N_ENCRYPTION_KEY` después de guardar credenciales
- Solución: borrar el volumen (⚠️ se pierden las credenciales guardadas):
  ```bash
  docker compose down
  docker volume rm lexiora-workflow_n8n_data
  docker compose up -d
  ```
- **Prevención**: la `N8N_ENCRYPTION_KEY` no se cambia nunca una vez configurada.

### Nodo Code falla con `Module 'fs' is disallowed`
- Verificar que `docker-compose.yml` tiene `NODE_FUNCTION_ALLOW_BUILTIN=fs,path,crypto`
- `docker compose up -d` para aplicar

### Nodo HTTP Request falla al leer `$env.OPENAI_API_KEY`
- n8n no permite variables de entorno en headers de HTTP Request
- Solución: usar `authentication: "predefinedCredentialType"` y `nodeCredentialType: "openAiApi"` en el nodo
- La credencial debe estar configurada en n8n → Credentials con el nombre `OpenAI Lexiora`

### 502 Bad Gateway en Nginx
1. Verificar que n8n está corriendo: `docker compose ps`
2. Si está en `Restarting`: ver logs con `docker compose logs`
3. Verificar que el puerto está bien en `docker-compose.yml`: `"127.0.0.1:5678:5678"`
4. Verificar que nginx proxy_pass apunta a `http://localhost:5678`

### Certbot falla / dominio apunta a IP incorrecta
1. Verificar la IP resuelta: `dig n8n.lexiora.cl +short`
2. Si muestra una IP de Vercel u otra: hay nameservers incorrectos en el proveedor del dominio
3. En NIC Chile: dejar solo los nameservers de DigitalOcean (`ns1/ns2/ns3.digitalocean.com`)
4. Esperar propagación DNS (puede tardar hasta 30 min)
5. Volver a correr Certbot

---

## Resumen de URLs y puertos

| Servicio | URL / Puerto | Descripción |
|---|---|---|
| n8n (local) | `http://localhost:5678` | Panel de administración |
| n8n (producción) | `https://n8n.lexiora.cl` | Panel en el servidor |
| Chat de ingesta (prod) | `https://n8n.lexiora.cl/webhook/lexiora-ingest-chat/chat` | Subir PDFs |
| Supabase | `https://xxxx.supabase.co` | Dashboard de la BD |
| Webhook WhatsApp | `https://n8n.lexiora.cl/webhook/whatsapp` | Recibe mensajes |
| Webhook pagos | `https://n8n.lexiora.cl/webhook/payment` | Recibe confirmaciones Flow |

---

## Checklist de entrega al cliente

- [ ] `.env` configurado con credenciales reales en el servidor
- [ ] SQL ejecutado en Supabase (4 tablas + 2 funciones RPC)
- [ ] n8n corriendo con HTTPS en `n8n.lexiora.cl`
- [ ] 3 workflows creados y **activos** en n8n
- [ ] Credenciales de OpenAI y WhatsApp configuradas en n8n
- [ ] Nodo "Generar Embeddings" en `lexiora-ingest` con credencial `OpenAI Lexiora` asignada
- [ ] Webhook verificado en Meta for Developers
- [ ] Documentos jurídicos ingestados en Supabase via chat de ingesta
- [ ] Test de mensaje WhatsApp → respuesta correcta
