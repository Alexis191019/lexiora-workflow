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
├── setup.py                    # Importa los workflows en n8n vía API (un solo comando)
├── docker-compose.yml          # Levanta n8n en Docker
├── .env.example                # Plantilla de variables de entorno
├── workflows/
│   ├── lexiora-whatsapp-rag.json  # Workflow principal (RAG + WhatsApp)
│   └── lexiora-ingest.json        # Workflow de ingesta de PDFs
├── nginx/
│   └── lexiora.conf            # Configuración Nginx (reverse proxy + SSL)
├── sql/
│   └── setup.sql               # Tablas, funciones RPC e índices en Supabase
├── REFERENCIA_INGESTA.md       # Cómo usar el chat de ingesta (formato de campos)
├── GUIA_CREDENCIALES.md        # Guía para el cliente: cómo obtener cada credencial
└── CLAUDE.md                   # Contexto del proyecto para Claude Code (IA)
```

---

## Workflows n8n

### `lexiora-whatsapp-rag` — Flujo principal
Recibe mensajes de WhatsApp, aplica el pipeline RAG y responde al usuario.

**Pasos**: webhook → validar mensaje (filtra status events) → lookup/crear usuario → bienvenida si es nuevo → control créditos → descontar crédito → sanitizar pregunta → detectar injection → embedding → búsqueda vectorial → construir contexto → chat completion → alerta créditos bajos → enviar respuesta

### `lexiora-ingest` — Ingesta de documentos
Vectoriza documentos jurídicos y los guarda en Supabase via chat integrado en n8n.

**URL**: `https://n8n.lexiora.cl/webhook/lexiora-ingest-chat/chat`  
**Pasos**: chat trigger → extraer PDF → chunks → embeddings → bulk insert en Supabase

### Pagos — Next.js landing page
Los pagos se procesan desde la landing page (`/pagar`), no desde n8n. Flow envía el webhook de confirmación directamente a Next.js (`/api/confirmar-pago`), que acredita los créditos en Supabase.

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
# Editar .env con todas las credenciales

# 3. Crear tablas y funciones RPC en Supabase
# Supabase Dashboard → SQL Editor → pegar sql/setup.sql → Run

# 4. Levantar n8n
docker compose up -d
# Panel disponible en http://localhost:5678

# 5. Configurar credenciales en n8n → Credentials:
#   - "OpenAI Lexiora"    → tipo: OpenAI API
#   - "WhatsApp Lexiora"  → tipo: HTTP Header Auth (name: Authorization)

# 6. Crear la API Key de n8n
# n8n → Settings → API → Create API Key → copiar el valor

# 7. Importar los workflows (un solo comando)
set N8N_API_KEY=<api-key>           # Windows
# export N8N_API_KEY=<api-key>      # Linux/Mac
python setup.py

# 8. Para desarrollo local, exponer con ngrok antes del paso 7
# ngrok http 5678 → actualizar N8N_WEBHOOK_URL en .env → docker compose restart
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

**Funciones RPC** (todas en `LANGUAGE sql` para evitar ambigüedad de columnas):
- `get_or_create_usuario(p_phone)` — upsert atómico; retorna `is_new=true` si fue recién creado
- `descontar_credito(p_usuario_id)` — descuenta 1 crédito de forma atómica
- `acreditar_creditos(p_usuario_id, p_creditos)` — suma créditos después de un pago
- `match_documents(query_embedding, match_threshold, match_count)` — búsqueda vectorial por similitud coseno

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

- [`GUIA_CREDENCIALES.md`](GUIA_CREDENCIALES.md) — Para el cliente: cómo obtener cada credencial (OpenAI, WhatsApp, Flow, etc.)
- [`REFERENCIA_INGESTA.md`](REFERENCIA_INGESTA.md) — Cómo usar el chat de ingesta: formato de campos y ejemplos
- [`CLAUDE.md`](CLAUDE.md) — Contexto técnico completo del proyecto para sesiones con Claude Code
