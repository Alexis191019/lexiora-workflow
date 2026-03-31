# Referencia — Cómo describir documentos al ingestar

Guía de referencia para rellenar los campos al usar el chat de ingesta
(`https://n8n.lexiora.cl/webhook/lexiora-ingest-chat/chat`).

## Formato del mensaje

```
fuente: [nombre del documento] | numero: [identificador] | materia: [categoría]
```

- `fuente` — **obligatorio** — nombre completo, descriptivo
- `numero` — opcional — número de ley, DFL, dictamen, etc. (dejar vacío si no aplica)
- `materia` — opcional — categoría temática (ver tabla al final)

Luego adjuntar el PDF y enviar.

---

## Tipos de documentos y ejemplos

### Códigos (los grandes cuerpos legales)

Son la excepción, no la norma. Solo hay unos pocos en Chile.

```
fuente: Código del Trabajo | numero: DFL-1 | materia: derecho_laboral
fuente: Código Civil | numero: | materia: derecho_civil
fuente: Código Penal | numero: | materia: derecho_penal
fuente: Código de Procedimiento Civil | numero: | materia: derecho_procesal
fuente: Código de Comercio | numero: | materia: derecho_comercial
fuente: Código Tributario | numero: | materia: derecho_tributario
```

---

### Leyes simples (Ley XXXXX)

La mayoría de la legislación chilena son leyes numeradas, no códigos.

```
fuente: Ley de Protección al Consumidor | numero: Ley 19496 | materia: derecho_consumidor
fuente: Ley de Matrimonio Civil | numero: Ley 19947 | materia: derecho_familia
fuente: Ley de Violencia Intrafamiliar | numero: Ley 20066 | materia: derecho_familia
fuente: Ley de Subcontratación | numero: Ley 20123 | materia: derecho_laboral
fuente: Ley de Tribunales de Familia | numero: Ley 19968 | materia: derecho_familia
fuente: Ley de Arrendamiento | numero: Ley 18101 | materia: derecho_inmobiliario
fuente: Ley de Copropiedad Inmobiliaria | numero: Ley 21442 | materia: derecho_inmobiliario
fuente: Ley de Responsabilidad Penal Juvenil | numero: Ley 20084 | materia: derecho_penal
fuente: Ley del Consumidor Digital | numero: Ley 21398 | materia: derecho_consumidor
```

---

### DFL — Decreto con Fuerza de Ley

Tiene fuerza de ley pero fue dictado por el Ejecutivo con autorización del Congreso.

```
fuente: DFL 1 Código del Trabajo | numero: DFL-1 | materia: derecho_laboral
fuente: DFL 3 Ley General de Bancos | numero: DFL-3 | materia: derecho_financiero
fuente: DFL 2 Viviendas Económicas | numero: DFL-2 | materia: derecho_inmobiliario
fuente: DFL 1 Estatuto Administrativo | numero: DFL-1-29834 | materia: derecho_administrativo
```

---

### DL — Decreto Ley

Dictado durante los gobiernos militares. Siguen vigentes varios.

```
fuente: DL 3500 Sistema de AFP | numero: DL-3500 | materia: derecho_previsional
fuente: DL 3063 Rentas Municipales | numero: DL-3063 | materia: derecho_tributario
fuente: DL 830 Código Tributario | numero: DL-830 | materia: derecho_tributario
```

---

### Reglamentos y Decretos Supremos (DS)

Regulan la aplicación de leyes. Se identifican por número y ministerio.

```
fuente: Reglamento del Seguro de Cesantía | numero: DS-1-2002 | materia: derecho_laboral
fuente: Reglamento de Establecimientos Educacionales | numero: DS-548 | materia: derecho_educacional
fuente: Decreto de Feriados Legales | numero: DS-195 | materia: derecho_laboral
```

---

### Dictámenes de Contraloría General de la República

Son pronunciamientos jurídicos oficiales. Muy relevantes en derecho administrativo y laboral del sector público.

```
fuente: Dictamen Contraloría Jornada Laboral Sector Público | numero: 17432-2023 | materia: derecho_administrativo
fuente: Dictamen Contraloría Subcontratación Municipios | numero: 22100-2022 | materia: derecho_laboral
fuente: Dictamen Contraloría Feriados Funcionarios | numero: 9844-2021 | materia: derecho_administrativo
```

---

### Circulares y Resoluciones de organismos (DT, SII, SUSESO, etc.)

```
fuente: Circular DT Teletrabajo | numero: Circular-101-DT | materia: derecho_laboral
fuente: Circular SII IVA Servicios Digitales | numero: Circular-42-SII | materia: derecho_tributario
fuente: Resolución SUSESO Licencias Médicas | numero: Res-1584-SUSESO | materia: derecho_previsional
```

---

### Documentos propios — FAQ y Preguntas Frecuentes de abogados

Estos documentos no tienen número legal. El `fuente` debe describir el contenido claramente para que el RAG lo cite bien al responder.

```
fuente: FAQ Despido Injustificado | numero: | materia: derecho_laboral
fuente: Preguntas Frecuentes Divorcio Chile | numero: | materia: derecho_familia
fuente: Guía Práctica Arrendamiento Residencial | numero: | materia: derecho_inmobiliario
fuente: FAQ Accidentes del Trabajo | numero: | materia: derecho_laboral
fuente: Preguntas Frecuentes Herencias y Testamentos | numero: | materia: derecho_civil
fuente: Guía Trámites Matrimonio Civil | numero: | materia: derecho_familia
fuente: FAQ Derechos del Consumidor Compras Online | numero: | materia: derecho_consumidor
fuente: Preguntas Frecuentes Pensión Alimenticia | numero: | materia: derecho_familia
```

> **Recomendación para FAQ**: usa nombres descriptivos del contenido, no del formato.
> El modelo citará `fuente` al responder, así que "FAQ Despido Injustificado" es mejor
> que "Preguntas frecuentes elaboradas por el equipo de abogados — Enero 2025".

---

## Tabla de materias disponibles

| Materia | Cuándo usar |
|---|---|
| `derecho_laboral` | Contratos, despidos, jornada, remuneraciones, sindicatos, licencias |
| `derecho_civil` | Contratos, obligaciones, bienes, herencias, responsabilidad civil |
| `derecho_familia` | Matrimonio, divorcio, alimentos, filiación, adopción, violencia intrafamiliar |
| `derecho_penal` | Delitos, sanciones, procedimiento penal |
| `derecho_procesal` | Procedimientos judiciales, recursos, plazos |
| `derecho_comercial` | Sociedades, contratos mercantiles, quiebras |
| `derecho_tributario` | IVA, renta, impuestos, SII |
| `derecho_administrativo` | Funcionarios públicos, contraloría, actos administrativos |
| `derecho_previsional` | AFP, pensiones, ISAPRE, FONASA, licencias médicas |
| `derecho_consumidor` | SERNAC, garantías, compras online, servicios |
| `derecho_inmobiliario` | Arrendamiento, copropiedad, compraventa de inmuebles |
| `derecho_financiero` | Bancos, créditos, CMF |
| `derecho_educacional` | Colegios, universidades, becas |
| `general` | Documentos que cruzan varias áreas (usar como último recurso) |

---

## Notas importantes

**Sobre los códigos**: La mayoría de la legislación chilena son leyes numeradas, no códigos.
Los códigos (Civil, Penal, del Trabajo, etc.) son la excepción. Si tienes dudas,
probablemente es una "Ley XXXXX".

**Sobre el `numero`**: Si el documento no tiene número oficial (FAQ, guías propias),
deja el campo vacío: `fuente: FAQ Despido | numero: | materia: derecho_laboral`.
No inventes un número.

**Sobre el `fuente`**: Este texto aparecerá en las respuestas al usuario cuando el modelo
cita la fuente. Que sea claro y descriptivo. En vez de "Ley 19496" pon
"Ley de Protección al Consumidor (Ley 19496)".

**Sobre PDFs escaneados**: Solo funcionan PDFs con texto seleccionable.
Si el PDF es una foto/scan, el sistema generará un error. Usa Adobe Acrobat o
similar para hacer OCR antes de ingestar.
