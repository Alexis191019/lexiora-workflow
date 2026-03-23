# Guía de Configuración — Lexiora
## Cómo obtener todas las credenciales del sistema

Esta guía explica paso a paso cómo conseguir cada dato necesario para poner en funcionamiento el sistema. Siga el orden indicado ya que algunos pasos dependen de los anteriores.

Al final de cada sección encontrará el dato exacto que debe anotar y entregar al desarrollador para configurar el sistema.

---

## Resumen de lo que necesita

| # | Servicio | Para qué sirve | Costo aproximado |
|---|---|---|---|
| 1 | DigitalOcean | Servidor donde corre el sistema | ~$6 USD/mes |
| 2 | Dominio web | Dirección web del sistema | ~$15 USD/año |
| 3 | OpenAI | La inteligencia artificial que responde | Según uso (~$20-50 USD/mes) |
| 4 | Supabase | Base de datos (ya lo tiene) | Gratis hasta cierto límite |
| 5 | WhatsApp Business API | Canal de mensajería | Gratis hasta 1,000 conversaciones/mes |
| 6 | Flow | Recibir pagos de sus clientes en Chile | ~2% por transacción |

---

## PASO 1 — Contratar el Servidor (DigitalOcean)

El servidor es el computador en internet donde vivirá el sistema las 24 horas.

**1.1** Vaya a [digitalocean.com](https://www.digitalocean.com) y haga clic en **"Sign Up"**

**1.2** Regístrese con su correo o con Google. Necesitará ingresar una **tarjeta de crédito** para verificar su cuenta (no se cobra hasta que cree recursos).

**1.3** Una vez dentro del panel, haga clic en el botón verde **"Create"** en la parte superior y seleccione **"Droplets"**

**1.4** Configure el servidor así:
- **Choose Region**: New York (NYC) o Amsterdam — el más cercano a Chile disponible
- **Choose an image**: Ubuntu → versión **22.04 (LTS) x64**
- **Choose Size**: Basic → Regular (Intel) → **$6/month** (1 GB RAM, 1 CPU)
  - Si en el futuro el sistema crece mucho, puede subir a $12/month
- **Choose Authentication**: seleccione **Password** → ingrese una contraseña segura (guárdela bien)
- **Finalize**: en Hostname escriba `lexiora-server`

**1.5** Haga clic en **"Create Droplet"** y espere 1-2 minutos.

**1.6** Cuando aparezca, verá una dirección IP similar a `143.198.XXX.XXX`

**📋 Datos a guardar y entregar al desarrollador:**
```
IP del servidor: ___________________ (ej: 143.198.45.123)
Usuario:         root
Contraseña:      ___________________ (la que creó en el paso 1.4)
```

---

## PASO 2 — Comprar un Dominio Web

El dominio es la dirección que tendrá su sistema (ej: `lexiora.cl`).

**Opción A — Dominio .cl (recomendado para Chile):**
- Vaya a [nic.cl](https://www.nic.cl) → busque el nombre disponible → regístrelo
- Costo: ~$10.000 CLP/año

**Opción B — Dominio .com (más internacional):**
- Vaya a [namecheap.com](https://www.namecheap.com) → busque → compre
- Costo: ~$15 USD/año

**2.1** Una vez comprado el dominio, debe apuntar la dirección web al servidor:
- En el panel de su dominio busque la opción **"Gestión DNS"** o **"DNS Records"**
- Agregue un registro tipo **A**:
  - **Nombre/Host**: `n8n` (esto creará `n8n.sudominio.cl`)
  - **Valor/Points to**: la IP del servidor del paso 1
  - **TTL**: 3600 (o el valor por defecto)

**📋 Datos a guardar y entregar al desarrollador:**
```
Dominio:    ___________________ (ej: lexiora.cl)
Subdominio: n8n.lexiora.cl
```

---

## PASO 3 — Crear cuenta y API Key en OpenAI

OpenAI es la empresa que provee la inteligencia artificial (ChatGPT).

**3.1** Vaya a [platform.openai.com](https://platform.openai.com) y cree una cuenta con su correo.

**3.2** Una vez dentro, haga clic en su nombre (arriba a la derecha) → **"View API keys"**

**3.3** Haga clic en **"+ Create new secret key"**
- Nombre: `Lexiora`
- Haga clic en **"Create secret key"**

**3.4** ⚠️ **MUY IMPORTANTE**: Aparecerá una clave que comienza con `sk-...` — **cópiela inmediatamente** porque no volverá a mostrarse completa.

**3.5** Agregue un método de pago:
- Menú izquierdo → **"Billing"** → **"Add payment method"**
- Ingrese su tarjeta de crédito
- Recomendado: activar límite de gasto mensual en **"Limits"** (ej: $50 USD/mes)

**📋 Dato a guardar y entregar al desarrollador:**
```
OPENAI_API_KEY=sk-proj-XXXXXXXXXXXXXXXXXXXX...
```

---

## PASO 4 — Obtener credenciales de Supabase

Usted ya tiene su proyecto Supabase creado. Solo necesita copiar dos datos.

**4.1** Vaya a [supabase.com](https://supabase.com) → ingrese a su cuenta → seleccione el proyecto de Lexiora.

**4.2** En el menú izquierdo, haga clic en **"Project Settings"** (ícono de engranaje) → luego en **"API"**

**4.3** Verá dos secciones importantes:
- **Project URL**: una dirección como `https://abcdefghij.supabase.co`
- **Project API keys**: hay dos claves: `anon` y `service_role`

**4.4** Copie la clave **service_role** (haga clic en el ícono de copiar al lado de ella).
> ⚠️ No comparta esta clave con nadie que no sea el desarrollador de confianza. Da acceso total a la base de datos.

**4.5** Ejecute el script SQL que le proporcionará el desarrollador para crear las tablas necesarias:
- En Supabase → menú izquierdo → **"SQL Editor"**
- Pegue el script y haga clic en **"Run"**

**📋 Datos a guardar y entregar al desarrollador:**
```
SUPABASE_URL=https://XXXXXXXXXX.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.XXXXX...
```

---

## PASO 5 — Configurar WhatsApp Business API

Este es el paso más largo. Necesita una cuenta de Facebook/Meta y un número de WhatsApp Business.

### 5.1 Crear cuenta de Meta for Developers

**5.1.1** Vaya a [developers.facebook.com](https://developers.facebook.com) e inicie sesión con su cuenta de Facebook.

**5.1.2** Haga clic en **"My Apps"** (arriba a la derecha) → **"Create App"**

**5.1.3** Seleccione el tipo: **"Business"** → haga clic en Next.

**5.1.4** Complete:
- **App name**: `Lexiora`
- **App contact email**: su correo
- Haga clic en **"Create app"**

### 5.2 Agregar WhatsApp al app

**5.2.1** En el panel del app, busque el producto **"WhatsApp"** y haga clic en **"Set up"**

**5.2.2** Si no tiene una cuenta de WhatsApp Business, créela siguiendo las instrucciones (necesitará un número de teléfono).

**5.2.3** En el menú izquierdo, vaya a **WhatsApp → Getting Started**

**5.2.4** Verá un número de teléfono de prueba y un campo **"To"**. Aquí encontrará:
- El **Phone Number ID** (un número largo como `123456789012345`)

**5.2.5** Más abajo encontrará el **Access Token temporal** (comienza con `EAA...`). Para producción se creará uno permanente, pero por ahora copie este.

### 5.3 Configurar el Webhook (el desarrollador le ayudará con esto)

Esta parte requiere que el servidor ya esté configurado. El desarrollador le dirá qué URL ingresar aquí.

**📋 Datos a guardar y entregar al desarrollador:**
```
WHATSAPP_API_TOKEN=EAAxxxxxxxxxx...
WHATSAPP_PHONE_NUMBER_ID=123456789012345
```

---

## PASO 6 — Crear cuenta en Flow (pagos)

Flow permite recibir pagos con Webpay, tarjetas y transferencias bancarias.

**6.1** Vaya a [flow.cl](https://www.flow.cl) y haga clic en **"Regístrate"**

**6.2** Seleccione el tipo de cuenta: **Empresa** (necesitará RUT de empresa o personal)

**6.3** Complete el proceso de verificación (puede tomar 1-2 días hábiles)

**6.4** Una vez aprobada su cuenta, vaya a:
- **Mi cuenta** (arriba a la derecha) → **"Integración"** o **"API"**
- Copie:
  - **API Key**: una clave larga
  - **Secret Key**: otra clave para seguridad

**6.5** Para hacer pruebas sin cobrar dinero real, solicite acceso al **ambiente Sandbox**:
- En el mismo panel busque **"Sandbox"** o **"Ambiente de pruebas"**
- Le darán credenciales de prueba separadas

**📋 Datos a guardar y entregar al desarrollador:**
```
FLOW_API_KEY=XXXXXXXXXXXXXXXX
FLOW_SECRET_KEY=YYYYYYYYYYYYYYYY
FLOW_API_URL=https://sandbox.flow.cl/api   ← para pruebas
# FLOW_API_URL=https://www.flow.cl/api    ← cambiar a este cuando esté listo para producción
```

---

## PASO 7 — Datos de acceso a n8n (los inventa usted)

n8n es el sistema que orquesta todo. Necesita crear un usuario y contraseña para acceder a su panel.

**7.1** Invente un nombre de usuario (sin espacios):
- Ejemplo: `admin`, `lexiora`, `operador`

**7.2** Cree una contraseña segura (mínimo 12 caracteres, con mayúsculas, números y símbolos):
- Ejemplo: `Lexiora2024#Seguro`

**7.3** Defina el precio en pesos chilenos del paquete de 20 consultas:
- Ejemplo: `2990` (sin puntos ni comas)

**📋 Datos a guardar y entregar al desarrollador:**
```
N8N_USER=admin
N8N_PASSWORD=SuContraseñaSegura123#
PRECIO_CLP=2990
```

> ℹ️ El desarrollador generará la clave de cifrado técnica (`N8N_ENCRYPTION_KEY`) por su cuenta.

---

## Resumen final — Planilla de entrega al desarrollador

Complete esta tabla y envíela al desarrollador de forma segura (no por correo normal, use WhatsApp o una llamada):

```
# ── Servidor ─────────────────────────────────────
IP del servidor:         ___________________________
Contraseña root:         ___________________________

# ── Dominio ──────────────────────────────────────
Dominio:                 ___________________________ (ej: lexiora.cl)

# ── OpenAI ───────────────────────────────────────
OPENAI_API_KEY=          sk-proj-...

# ── Supabase ──────────────────────────────────────
SUPABASE_URL=            https://XXXX.supabase.co
SUPABASE_SERVICE_KEY=    eyJ...

# ── WhatsApp ──────────────────────────────────────
WHATSAPP_API_TOKEN=      EAA...
WHATSAPP_PHONE_NUMBER_ID= 123456...

# ── Flow ──────────────────────────────────────────
FLOW_API_KEY=            ...
FLOW_SECRET_KEY=         ...

# ── n8n ───────────────────────────────────────────
N8N_USER=                ...
N8N_PASSWORD=            ...
PRECIO_CLP=              2990
```

---

## Preguntas frecuentes

**¿Cuánto tardará en estar listo el sistema?**
Una vez que el desarrollador tenga todos estos datos, el sistema puede estar funcionando en 1-2 días hábiles.

**¿Quién paga las APIs?**
Usted paga directamente a cada servicio con su tarjeta. No pasa por el desarrollador.

**¿Qué pasa si olvido una contraseña?**
Cada servicio tiene su propio proceso de recuperación. Guarde todo en un gestor de contraseñas (como Bitwarden, que es gratuito).

**¿Puedo cambiar el precio de las consultas después?**
Sí, basta con cambiar el valor `PRECIO_CLP` y reiniciar el sistema. El desarrollador le explicará cómo.

**¿El desarrollador podrá ver mis contraseñas?**
Las contraseñas viven en su servidor. El desarrollador tiene acceso técnico al servidor para configurarlo, pero una vez entregado el sistema puede revocar ese acceso. Las API keys de OpenAI, Supabase y Flow están bajo su control directo en cada plataforma.
