# Nota Técnica — Refactorización a Sistema Agéntico

**Proyecto:** Normalizador de Transacciones Multifuente  
**Versión:** 2.0.0  
**Fecha:** 2026-07

---

## 1. Motivación de la refactorización

La versión original (v1) funcionaba correctamente pero presentaba
limitaciones arquitectónicas que dificultaban su mantenimiento y extensión:

| Problema (v1)                        | Impacto                                         |
|--------------------------------------|-------------------------------------------------|
| CLI llamaba servicios directamente   | Acoplamiento alto; cambiar un servicio rompía la CLI |
| Lógica de decisión dispersa en CLI   | Difícil agregar nuevas funciones sin tocar `cli.py` |
| Sin separación de responsabilidades  | Cada función de menú hacía parse + normalize + validate |
| Sin coordinador central              | No había punto único de control del flujo       |

La refactorización buscó resolver estos problemas adoptando el patrón
**Sistema Agéntico con Skills**, donde un agente coordina capacidades
reutilizables e intercambiables.

---

## 2. Decisiones de diseño

### 2.1 Patrón Agente + Router + Skills

Se adoptó el patrón donde:

- **`TransactionAgent`** actúa como orquestador único: recibe solicitudes,
  delega al router y ejecuta la skill seleccionada.
- **`SkillRouter`** encapsula las reglas de selección de skill. Al estar
  separado del agente, permite cambiar la estrategia de enrutamiento
  (ej. pasar de keywords a un LLM) sin modificar el agente.
- **Cada `Skill`** encapsula exactamente una responsabilidad, lo que
  permite probarla, reutilizarla y modificarla de forma independiente.

### 2.2 AgentContext como memoria de trabajo

En lugar de pasar datos entre funciones como parámetros, se introdujo
`AgentContext`: un objeto de sesión mutable que almacena transacciones,
métricas y el historial de acciones.

**Beneficio:** Las skills pueden leer y escribir en el contexto sin
necesidad de conocerse entre sí. El agente mantiene coherencia de sesión.

### 2.3 Skills como herederas de BaseSkill

Todas las skills implementan la interfaz `BaseSkill.execute(request)`.
Esto garantiza:

- **Polimorfismo:** El agente puede ejecutar cualquier skill sin conocer
  su implementación.
- **Testabilidad:** Cada skill puede probarse de forma aislada.
- **Extensibilidad:** Agregar una nueva skill solo requiere crear la clase
  y registrarla en el agente.

### 2.4 Configuración centralizada

`config/config.py` centraliza:
- Keywords del router.
- Rutas de datos.
- Parámetros de logging.
- Referencia a `rules.json`.

**Beneficio:** Los parámetros del sistema se modifican en un único lugar.

### 2.5 Los servicios NO se modificaron

`services/` (parser, normalizer, validator, metrics) se conservaron
íntegramente. Las skills los consumen como dependencias.

**Beneficio:** Cero riesgo de regresión en la lógica de negocio existente.
Las pruebas de regresión originales (test_normalizer, test_validator,
test_metrics) siguen pasando sin cambios.

---

## 3. Beneficios obtenidos

| Aspecto               | Antes (v1)                    | Después (v2)                     |
|-----------------------|-------------------------------|----------------------------------|
| Acoplamiento          | CLI → services (directo)      | CLI → Agent → Skill → services   |
| Extensibilidad        | Modificar `cli.py` completo   | Agregar clase Skill + keyword    |
| Testabilidad          | Solo servicios probados       | Router + Skills + Agent probados |
| Responsabilidades     | Mezcladas en `cli.py`         | Una por skill                    |
| Configuración         | Hardcoded en múltiples archivos| Centralizada en `config.py`     |
| Documentación técnica | README básico                 | SKILL.md por skill + README v2   |

---

## 4. Limitaciones conocidas

- **Router rule-based:** La selección de skill usa keywords fijas. Para
  solicitudes ambiguas o con vocabulario no previsto, el router devuelve
  `None` y el agente informa al usuario. En el futuro puede sustituirse
  por un LLM clasificador.

- **Contexto en memoria:** El `AgentContext` no persiste entre ejecuciones
  del programa. Si el usuario reinicia, debe volver a cargar el archivo.

- **Sin paralelización:** Las skills se ejecutan secuencialmente. Para
  conjuntos muy grandes de transacciones, podría beneficiarse de
  procesamiento paralelo en `NormalizeSkill`.

---

## 5. Plan de extensión futura

1. **Integrar un LLM como router:** Reemplazar `SkillRouter` por una
   llamada a GPT-4 o Gemini para clasificar la intención.
2. **Persistencia de contexto:** Serializar `AgentContext` a JSON para
   retomar sesiones.
3. **Nuevas skills:** `TranslateSkill` (traducción de campos), `AuditSkill`
   (auditoría de cambios), `FilterSkill` (filtros complejos).
4. **API REST:** Exponer el agente como servicio HTTP con FastAPI.

---

## 6. Uso responsable de inteligencia artificial

Durante el desarrollo de esta refactorización se utilizaron las siguientes
herramientas de IA:

| Herramienta          | Uso                                                  |
|----------------------|------------------------------------------------------|
| Claude / Antigravity | Generación de propuestas de arquitectura, código base de skills y pruebas |
| GitHub Copilot       | Autocompletado de docstrings y fragmentos de código  |

**Proceso de validación aplicado:**

1. Todas las propuestas de código generadas por IA fueron **revisadas
   manualmente** antes de aceptarlas.
2. Se **ejecutaron las pruebas existentes** (test_normalizer, test_validator,
   test_metrics) para verificar que no hubo regresiones.
3. Se ejecutó el **pipeline batch completo** (`python main.py --proceso`)
   para validar el flujo de extremo a extremo.
4. Los **comentarios técnicos** y la documentación fueron revisados para
   asegurar que reflejan las decisiones reales del proyecto.

La IA fue utilizada como **asistente de implementación**, no como autor.
Todas las decisiones de diseño, arquitectura y validación fueron
responsabilidad del estudiante.
