-- ============================================================
-- Lexiora — Script de configuración de base de datos Supabase
-- ============================================================
-- Instrucciones:
--   1. Abrir supabase.com → Dashboard → SQL Editor
--   2. Pegar todo este script y hacer clic en "Run"
--   3. Verificar que aparezcan las tablas en Table Editor
-- ============================================================


-- ── Extensión pgvector (necesaria para embeddings) ──────────
CREATE EXTENSION IF NOT EXISTS vector;


-- ── Tabla: usuarios ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS usuarios (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  phone            VARCHAR(20) UNIQUE NOT NULL,  -- número WhatsApp (ej: 56912345678)
  nombre           VARCHAR(100),
  creditos         INT NOT NULL DEFAULT 3,        -- 3 gratis al registrarse
  total_preguntas  INT NOT NULL DEFAULT 0,
  creado_en        TIMESTAMPTZ DEFAULT now(),
  ultimo_mensaje   TIMESTAMPTZ
);

-- Índice para búsquedas por teléfono (las más frecuentes)
CREATE INDEX IF NOT EXISTS idx_usuarios_phone ON usuarios(phone);


-- ── Tabla: pagos ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS pagos (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  usuario_id          UUID REFERENCES usuarios(id),
  proveedor           VARCHAR(20) NOT NULL,        -- 'flow' | 'mercadopago'
  monto               INT NOT NULL,                -- en CLP
  creditos_otorgados  INT NOT NULL DEFAULT 20,
  referencia_externa  VARCHAR(100),                -- ID de la orden en el proveedor de pago
  estado              VARCHAR(20) DEFAULT 'pendiente',  -- 'pendiente' | 'pagado' | 'fallido'
  creado_en           TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_pagos_usuario ON pagos(usuario_id);
CREATE INDEX IF NOT EXISTS idx_pagos_referencia ON pagos(referencia_externa);


-- ── Tabla: documents (base vectorial RAG) ───────────────────
CREATE TABLE IF NOT EXISTS documents (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  content    TEXT NOT NULL,                        -- texto del fragmento de documento
  metadata   JSONB DEFAULT '{}',                   -- {fuente, titulo, numero, fecha, materia}
  embedding  VECTOR(1536),                         -- vector de text-embedding-3-small (1536 dims)
  creado_en  TIMESTAMPTZ DEFAULT now()
);

-- Índice HNSW para búsqueda vectorial eficiente (similitud coseno)
CREATE INDEX IF NOT EXISTS idx_documents_embedding
  ON documents USING hnsw (embedding vector_cosine_ops);


-- ── Tabla: injection_attempts (registro de intentos maliciosos) ──
CREATE TABLE IF NOT EXISTS injection_attempts (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  phone           VARCHAR(20),
  texto_original  TEXT,
  fecha           TIMESTAMPTZ DEFAULT now()
);


-- ── Función RPC: descontar_credito ───────────────────────────
-- Descuenta 1 crédito e incrementa total_preguntas de forma atómica.
-- Retorna el registro actualizado con el saldo restante.
CREATE OR REPLACE FUNCTION descontar_credito(p_usuario_id UUID)
RETURNS TABLE(id UUID, phone VARCHAR, creditos INT, total_preguntas INT)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  UPDATE usuarios
  SET
    creditos        = creditos - 1,
    total_preguntas = total_preguntas + 1
  WHERE usuarios.id = p_usuario_id
    AND creditos > 0
  RETURNING
    usuarios.id,
    usuarios.phone,
    usuarios.creditos,
    usuarios.total_preguntas;
END;
$$;


-- ── Función RPC: match_documents ─────────────────────────────
-- Búsqueda vectorial: retorna los documentos más similares al embedding de consulta.
-- Llamada desde n8n: POST /rest/v1/rpc/match_documents
CREATE OR REPLACE FUNCTION match_documents(
  query_embedding  VECTOR(1536),
  match_threshold  FLOAT DEFAULT 0.70,
  match_count      INT   DEFAULT 5
)
RETURNS TABLE(
  id         UUID,
  content    TEXT,
  metadata   JSONB,
  similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    documents.id,
    documents.content,
    documents.metadata,
    1 - (documents.embedding <=> query_embedding) AS similarity
  FROM documents
  WHERE 1 - (documents.embedding <=> query_embedding) > match_threshold
  ORDER BY documents.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;


-- ── Row Level Security (RLS) ──────────────────────────────────
-- El sistema usa la service_role key que bypasea RLS.
-- Activamos RLS como buena práctica pero no bloqueará el sistema.
ALTER TABLE usuarios          ENABLE ROW LEVEL SECURITY;
ALTER TABLE pagos             ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents         ENABLE ROW LEVEL SECURITY;
ALTER TABLE injection_attempts ENABLE ROW LEVEL SECURITY;


-- ── Verificación ──────────────────────────────────────────────
-- Ejecute estas consultas para confirmar que todo se creó correctamente:
--
-- SELECT table_name FROM information_schema.tables
--   WHERE table_schema = 'public'
--   ORDER BY table_name;
--
-- Debería mostrar: documents, injection_attempts, pagos, usuarios
