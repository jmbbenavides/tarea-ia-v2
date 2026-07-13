# Normalizador de Transacciones Multifuente — v2 (Sistema Agéntico)

Sistema agéntico modular para normalizar, validar, analizar y exportar
transacciones financieras provenientes de múltiples fuentes con formatos
heterogéneos.

---

## Arquitectura

```
main.py
    │
    ▼
TransactionAgent          ← Orquestador central
    │
    ├── SkillRouter        ← Selección automática por palabras clave
    │
    ├── NormalizeSkill     ← Detectar formato + normalizar
    ├── ValidateSkill      ← Validar reglas de negocio
    ├── MetricsSkill       ← Calcular estadísticas
    ├── SearchSkill        ← Búsqueda por ID / moneda / estado
    ├── ExportSkill        ← Generar valid.json + invalid.json
    └── ReportSkill        ← Generar reporte Markdown
           │
           ▼
        services/          ← Lógica de negocio (sin cambios)
        ├── parser.py
        ├── normalizer.py
        ├── validator.py
        └── metrics.py
```

### Estructura de directorios

```
tarea-ia-v2/
├── agent/
│   ├── agent.py          ← TransactionAgent (orquestador)
│   ├── router.py         ← SkillRouter (selector de skills)
│   ├── context.py        ← AgentContext (estado de sesión)
│   └── prompts.py        ← Plantillas de mensajes
├── skills/
│   ├── base.py           ← Clase abstracta BaseSkill
│   ├── normalize/        ← skill.py + SKILL.md
│   ├── validate/         ← skill.py + SKILL.md
│   ├── metrics/          ← skill.py + SKILL.md
│   ├── search/           ← skill.py + SKILL.md
│   ├── export/           ← skill.py + SKILL.md
│   └── report/           ← skill.py + SKILL.md
├── services/             ← Lógica de negocio (sin cambios)
├── models/               ← Transaction, TransactionStatus
├── config/
│   ├── config.py         ← Configuración centralizada
│   └── rules.json        ← Reglas de negocio
├── ui/
│   └── cli.py            ← CLI interactiva (ahora usa el agente)
├── data/                 ← Archivos de entrada/salida
├── tests/                ← Pruebas unitarias e integración
├── main.py               ← Punto de entrada
├── README.md
└── NOTA_TECNICA.md
```

---

## Instalación

```bash
# Clonar el repositorio
git clone <url-del-repo>
cd tarea-ia-v2

# Instalar dependencias
pip install -r requirements.txt
```

### Dependencias

```
colorama   # Colores en la CLI
pytest     # Ejecución de pruebas
```

---

## Ejecución

### Modo interactivo (CLI)

```bash
python main.py
```

Inicia el menú interactivo con 9 opciones:

| Opción | Acción            | Skill invocada   |
|--------|-------------------|------------------|
| 1      | Cargar archivo    | NormalizeSkill + ValidateSkill |
| 2      | Ver todas         | (contexto)       |
| 3      | Filtrar por estado| SearchSkill      |
| 4      | Filtrar por moneda| SearchSkill      |
| 5      | Ver métricas      | MetricsSkill     |
| 6      | Ver inválidas     | (contexto)       |
| 7      | Exportar          | ExportSkill      |
| 8      | Generar reporte   | ReportSkill      |
| 9      | Salir             | —                |

### Modo batch (sin CLI)

```bash
python main.py --proceso
# o
python main.py --batch
```

Ejecuta el pipeline completo vía agente:
1. **NormalizeSkill** → lee `data/sample_transactions.json`
2. **ValidateSkill** → separa válidas e inválidas
3. **MetricsSkill** → calcula estadísticas
4. **ExportSkill** → genera `data/valid.json` y `data/invalid.json`

---

## Skills

### NormalizeSkill
Detecta el formato de cada registro (FormatA–E / Genérico) y lo convierte
al modelo `Transaction`.

**Solicitudes de ejemplo:**
- `"normaliza data/sample_transactions.json"`
- `"procesa el archivo"`

### ValidateSkill
Aplica reglas de negocio: ID no vacío, monto positivo, moneda soportada,
fecha ISO-8601, estado reconocido.

**Solicitudes de ejemplo:**
- `"valida las transacciones"`
- `"verificar errores"`

### MetricsSkill
Calcula totales, distribución por estado y montos por moneda.

**Solicitudes de ejemplo:**
- `"métricas del procesamiento"`
- `"estadísticas"`

### SearchSkill
Búsqueda inteligente por ID, moneda o estado.

**Solicitudes de ejemplo:**
- `"buscar TXN-001"`
- `"filtrar USD"`
- `"buscar pendientes"`

### ExportSkill
Genera `data/valid.json` e `data/invalid.json`.

**Solicitudes de ejemplo:**
- `"exporta los resultados"`
- `"guarda los archivos"`

### ReportSkill
Genera `data/report.md` con resumen ejecutivo en Markdown.

**Solicitudes de ejemplo:**
- `"genera reporte"`
- `"informe markdown"`

---

## Flujo del agente

```
Solicitud en texto
       │
       ▼
  SkillRouter
  (compara keywords)
       │
       ▼
  Skill seleccionada
  (instanciada con AgentContext)
       │
       ▼
  skill.execute(request)
  (usa services/ internamente)
       │
       ▼
  Respuesta + log en contexto
```

---

## Formatos de entrada soportados

| Formato  | Claves principales                                      |
|----------|---------------------------------------------------------|
| FormatA  | `transaction_id`, `amount`, `currency`, `date`, `status`|
| FormatB  | `tx_id`, `tx_amount`, `tx_currency`, `tx_date`, `tx_status` |
| FormatC  | `ref`, `value`, `cur`, `created_at`, `state`           |
| FormatD  | `id`, `amount_cents`, `currency_code`, `created_at`, `status` |
| FormatE  | `uid`, `total`, `money_type`, `datetime`, `transaction_status` |
| Generic  | Detección por heurística de claves comunes             |

---

## Pruebas

```bash
# Ejecutar todas las pruebas
python -m pytest tests/ -v

# Solo pruebas del router
python -m pytest tests/test_router.py -v

# Solo pruebas de skills
python -m pytest tests/test_skills.py -v

# Pruebas de integración del agente
python -m pytest tests/test_agent.py -v

# Pruebas de regresión (código original)
python -m pytest tests/test_normalizer.py tests/test_validator.py tests/test_metrics.py -v
```

Cobertura mínima recomendada: **80%**.

---

## Uso responsable de IA

Este proyecto fue desarrollado con asistencia de herramientas de IA
(ChatGPT, GitHub Copilot, Claude / Antigravity) para:

- Generación de propuestas de arquitectura.
- Revisión de patrones de diseño.
- Generación de plantillas de código.
- Sugerencias de pruebas unitarias.

**Todas las decisiones de diseño fueron revisadas, adaptadas y validadas
manualmente.** Las pruebas se ejecutaron antes de aceptar cualquier
sugerencia generada por IA.
