# Lexiora — Asistente Legal por WhatsApp

Sistema de automatización basado en **n8n** que implementa un asistente legal conversacional a través de **WhatsApp Business**. Utiliza un pipeline RAG (Retrieval-Augmented Generation) para responder preguntas sobre normativa legal chilena, consultando una base de datos vectorial en **Supabase** que contiene leyes, dictámenes de Contraloría y otros instrumentos jurídicos.

---

## Arquitectura

```
Usuario (WhatsApp)
       │
       ▼
  [n8n Webhook]
       │
       ├─► Validación: solo mensajes de texto
       │
       ├─► Control de créditos (Supabase)
       │      ├─ Sin créditos → link de pago (Flow) → WhatsApp
       │      └─ Con créditos → continuar
       │
       ▼
  Sanitización + normalización (GPT-4o-mini)
       │
       ├─► Detección prompt injection → bloquear si detectado
       │
       ▼
  Embedding (text-embedding-3-small) → Supabase pgvector
                                              │
                                        Top-5 documentos
                                              │
                                     Chat Completion (GPT-4o)
                                              │
                                    Descontar 1 crédito
                                              │
                                    Alerta si créditos ≤ 3
                                              │
                                    Respuesta → WhatsApp
```

---

## Stack tecnológico

| Componente | Tecnología |
|---|---|
| Orquestación | n8n (self-hosted Docker) |
| Canal | WhatsApp Business API (Meta) |
| Modelo de IA | OpenAI GPT-4o / GPT-4o-mini |
| Embeddings | OpenAI `text-embedding-3-small` (1536 dims) |
| Base de datos vectorial | Supabase (pgvector + HNSW index) |
| Base de datos relacional | Supabase (usuarios, créditos, pagos) |
| Pagos | Flow (flow.cl) — Webpay/Transbank |
| Reverse proxy | Nginx + Let's Encrypt (producción) |
| Infraestructura | Docker en VPS DigitalOcean |

---

## Estructura del repositorio

```
lexiora-workflow/
├── docker-compose.yml          # Levanta n8n en Docker
├── .env.example                # Plantilla de variables de entorno
├── nginx/
│   └── lexiora.conf            # Configuración Nginx (reverse proxy + SSL)
├── sql/
│   └── setup.sql               # Tablas, funciones RPC y índices en Supabase
├── crear_workflows.py          # Crea los 3 workflows en n8n vía API
├── preparar_documentos.py      # Convierte documentos legales a JSON con chunks
├── documentos_ejemplo/
│   ├── ejemplo_legal.json      # Chunks de leyes chilenas (formato de ingesta)
│   └── ejemplo_enfermeria.json # Ejemplo de dominio alternativo
├── GUIA_DESARROLLADOR.md       # Setup completo paso a paso para el desarrollador
├── GUIA_CREDENCIALES.md        # Guía para el cliente: cómo obtener cada credencial
└── CLAUDE.md                   # Contexto del proyecto para Claude Code (IA)
```

---

## Workflows n8n

### `lexiora-whatsapp-rag` — Flujo principal
Recibe mensajes de WhatsApp, aplica el pipeline RAG y responde al usuario.

**Pasos**: webhook → validar tipo → lookup usuario → control créditos → sanitizar pregunta → detectar injection → embedding → búsqueda vectorial → construir contexto → chat completion → descontar crédito → alerta créditos bajos → enviar respuesta

### `lexiora-payment-webhook` — Confirmación de pagos
Recibe el webhook de Flow cuando un pago se confirma y acredita los créditos.

**Pasos**: webhook → validar firma HMAC-SHA256 → lookup usuario → acreditar +20 créditos → registrar en tabla `pagos` → notificar por WhatsApp

### `lexiora-ingest` — Ingesta de documentos
Vectoriza documentos jurídicos y los guarda en Supabase.

**Pasos**: trigger manual → leer JSON de `preparar_documentos.py` → embedding por chunk → guardar en `documents` con metadata

---

## Modelo de negocio freemium

| Evento | Créditos |
|---|---|
| Registro nuevo usuario | +3 gratuitos |
| Pago confirmado (Flow) | +20 |
| Cada pregunta respondida | -1 |

- Al llegar a **0 créditos**: se envía link de pago por WhatsApp
- Al quedar **≤ 3 créditos**: aviso al final de la respuesta

---

## Requisitos previos

- Docker Desktop
- Python 3.10+
- Cuenta en Supabase (proyecto propio del cliente)
- Cuenta en OpenAI con créditos
- WhatsApp Business API configurada en Meta for Developers
- Cuenta en Flow (flow.cl) para pagos

Ver [`GUIA_CREDENCIALES.md`](GUIA_CREDENCIALES.md) para instrucciones paso a paso de cómo el cliente obtiene cada credencial.

---

## Setup rápido (desarrollo local)

```bash
# 1. Clonar el repo
git clone https://github.com/Alexis191019/lexiora-workflow.git
cd lexiora-workflow

# 2. Crear el .env con las variables de infraestructura
cp .env.example .env
# Editar .env: N8N_USER, N8N_PASSWORD, N8N_ENCRYPTION_KEY,
#              FLOW_API_KEY, FLOW_SECRET_KEY, PRECIO_CLP

# 3. Crear tablas en Supabase
# Ir a Supabase Dashboard → SQL Editor → pegar sql/setup.sql → Run

# 4. Levantar n8n
docker compose up -d
# Panel disponible en http://localhost:5678

# 5. Exponer webhook con ngrok (para WhatsApp)
ngrok http 5678
# Copiar la URL https://xxxx.ngrok-free.app → actualizar N8N_WEBHOOK_URL en .env
# Reiniciar: docker compose restart

# 6. Configurar credenciales en n8n
# n8n → Credentials → Add credential:
#   - "OpenAI API"    → API key de OpenAI       → nombre: "OpenAI Lexiora"
#   - "Supabase API"  → URL + service role key   → nombre: "Supabase Lexiora"
#   - "Header Auth"   → Bearer <WHATSAPP_TOKEN>  → nombre: "WhatsApp Lexiora"

# 7. Crear los 3 workflows
set N8N_API_KEY=<api-key-de-n8n>       # n8n → Settings → API → Create API Key
set N8N_API_URL=http://localhost:5678
python crear_workflows.py
# Activar los workflows en n8n con el toggle

# 8. Ingestar documentos de prueba
pip install requests beautifulsoup4 pdfplumber python-docx
python preparar_documentos.py \
  --url "https://www.bcn.cl/leychile/navegar?idNorma=207436" \
  --fuente "Código del Trabajo" --numero "DFL-1" \
  --materia "derecho_laboral" --salida "codigo_trabajo.json"
# Luego ejecutar lexiora-ingest manualmente en n8n
```

Ver [`GUIA_DESARROLLADOR.md`](GUIA_DESARROLLADOR.md) para el proceso completo incluyendo despliegue en producción.

---

## Variables de entorno

El `.env` solo contiene variables de **infraestructura**. Las API keys de servicios externos (OpenAI, Supabase, WhatsApp) se ingresan en el panel de credenciales de n8n, donde quedan cifradas.

| Variable | Descripción | Dónde se usa |
|---|---|---|
| `N8N_USER` | Usuario del panel n8n | Docker |
| `N8N_PASSWORD` | Contraseña del panel n8n | Docker |
| `N8N_ENCRYPTION_KEY` | Cifra las credenciales internas de n8n | Docker |
| `N8N_WEBHOOK_URL` | URL pública de n8n (ngrok en dev, dominio en prod) | Docker |
| `FLOW_API_KEY` | API key de Flow para generar órdenes de pago | Workflow (Code node) |
| `FLOW_SECRET_KEY` | Secret para validar firma HMAC-SHA256 de webhooks | Workflow (Code node) |
| `FLOW_API_URL` | `sandbox.flow.cl` (dev) o `www.flow.cl` (prod) | Workflow (Code node) |
| `PRECIO_CLP` | Precio del paquete de 20 créditos en pesos | Workflow (Code node) |

---

## Base de datos Supabase

El archivo `sql/setup.sql` crea toda la estructura necesaria:

**Tablas**:
- `usuarios` — teléfono, nombre, créditos, total de preguntas
- `pagos` — historial de pagos con estado y proveedor
- `documents` — chunks de documentos jurídicos con embedding `vector(1536)`
- `injection_attempts` — registro de intentos de prompt injection bloqueados

**Funciones RPC**:
- `descontar_credito(p_usuario_id)` — descuenta 1 crédito de forma atómica
- `match_documents(query_embedding, match_threshold, match_count)` — búsqueda vectorial por similitud coseno

---

## Preparar documentos jurídicos

`preparar_documentos.py` convierte documentos al formato JSON que consume `lexiora-ingest`. Detecta automáticamente artículos para leyes y usa chunking por tamaño para dictámenes.

```bash
# Desde la BCN (scraping automático)
python preparar_documentos.py --url "https://www.bcn.cl/leychile/navegar?idNorma=..." \
  --fuente "Nombre de la ley" --numero "Ley 20.123" --materia "materia"

# Desde PDF (dictámenes de Contraloría)
python preparar_documentos.py --pdf dictamen.pdf \
  --fuente "Contraloría General de la República" --numero "12345/2024" --materia "administrativo"

# Procesar carpeta completa de PDFs
python preparar_documentos.py --carpeta ./dictamenes/ \
  --fuente "Contraloría" --materia "administrativo"
```

---

## Seguridad

- **Sanitización pre-embedding**: GPT-4o-mini normaliza la pregunta y detecta intentos de injection antes de que lleguen al pipeline RAG
- **Prompt injection en system prompt**: el system prompt del modelo RAG incluye instrucciones explícitas para ignorar instrucciones embebidas en preguntas
- **Validación HMAC-SHA256**: los webhooks de Flow se validan con firma criptográfica
- **Sin credenciales en el repo**: `.env` está en `.gitignore`; las API keys van cifradas en n8n

---

## Despliegue en producción

1. VPS DigitalOcean (Ubuntu 22.04, $6/mes mínimo recomendado)
2. Docker + Nginx + Certbot (Let's Encrypt)
3. Dominio con registro DNS A apuntando a la IP del VPS

```bash
# En el servidor
apt-get install -y docker.io docker-compose-plugin nginx certbot python3-certbot-nginx
git clone https://github.com/Alexis191019/lexiora-workflow.git
cd lexiora-workflow && cp .env.example .env && nano .env
cp nginx/lexiora.conf /etc/nginx/sites-available/lexiora
ln -s /etc/nginx/sites-available/lexiora /etc/nginx/sites-enabled/lexiora
certbot --nginx -d n8n.tudominio.cl
docker compose up -d
```

Ver [`GUIA_DESARROLLADOR.md`](GUIA_DESARROLLADOR.md) — Parte 3 para el proceso detallado.

---

## Ramas del repositorio

| Rama | Uso |
|---|---|
| `master` | Código estable — refleja lo que está en producción |
| `dev` | Desarrollo activo — probar aquí antes de mergear |

```bash
# Flujo de trabajo
git checkout dev
git add . && git commit -m "feat: descripción"
git push

# Cuando está probado y estable
git checkout master && git merge dev && git push
git checkout dev
```

---

## Documentación adicional

- [`GUIA_DESARROLLADOR.md`](GUIA_DESARROLLADOR.md) — Setup completo local y producción, paso a paso
- [`GUIA_CREDENCIALES.md`](GUIA_CREDENCIALES.md) — Instrucciones para el cliente: cómo obtener cada credencial
- [`CLAUDE.md`](CLAUDE.md) — Contexto completo del proyecto para sesiones con Claude Code
