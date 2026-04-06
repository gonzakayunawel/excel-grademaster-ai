# Plan de Implementación: Excel-GradeMaster AI

## Visión General

El plan está dividido en **5 etapas** progresivas. Cada etapa produce código funcional e integrable, siguiendo un enfoque de menor a mayor complejidad.

---

## Etapa 1 — Estructura base y base de datos

**Objetivo:** Establecer la arquitectura de archivos y la capa de persistencia.

### 1.1 Dependencias adicionales

Agregar a `pyproject.toml`:
```
openpyxl
google-generativeai
python-dotenv
pandas
```
Luego ejecutar `uv sync`.

### 1.2 Estructura de archivos

```
excel_grademaster_ai/
├── main.py              # Entry point de Streamlit
├── database.py          # Capa SQLite (CRUD)
├── excel_engine.py      # Extracción dual con openpyxl
├── scoring.py           # Motor de calificación lógica
├── ai_engine.py         # Integración con Gemini
├── ui/
│   ├── fase_configuracion.py
│   ├── fase_revision.py
│   └── fase_reporte.py
└── .env                 # GOOGLE_API_KEY (no versionar)
```

### 1.3 Módulo `database.py`

Crear las tres tablas SQLite al inicializar:

```sql
CREATE TABLE IF NOT EXISTS SesionRevision (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_prueba TEXT NOT NULL,
    fecha_creacion TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ConfiguracionRubrica (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sesion_id INTEGER NOT NULL,
    enunciado TEXT,
    celda_objetivo TEXT NOT NULL,
    formula_esperada TEXT,
    valor_esperado TEXT,
    puntos_formula REAL NOT NULL,
    puntos_valor REAL NOT NULL,
    FOREIGN KEY (sesion_id) REFERENCES SesionRevision(id)
);

CREATE TABLE IF NOT EXISTS ResultadosEstudiantes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sesion_id INTEGER NOT NULL,
    nombre_estudiante TEXT NOT NULL,
    puntaje_total REAL,
    detalle_json TEXT,
    FOREIGN KEY (sesion_id) REFERENCES SesionRevision(id)
);
```

Funciones requeridas en `database.py`:
- `init_db()` — crea las tablas si no existen
- `crear_sesion(nombre_prueba) -> int` — retorna el `sesion_id`
- `guardar_rubrica(sesion_id, items: list[dict])` — inserta todas las filas de la rúbrica
- `obtener_rubrica(sesion_id) -> list[dict]`
- `guardar_resultado(sesion_id, nombre, puntaje_total, detalle_json)`
- `obtener_resultados(sesion_id) -> list[dict]`

---

## Etapa 2 — Motor de Excel (`excel_engine.py`)

**Objetivo:** Extraer fórmulas y valores calculados de un archivo `.xlsx` subido.

### Lógica de doble carga

```python
import openpyxl
from io import BytesIO

def extraer_celda(archivo_bytes: bytes, celda: str) -> dict:
    """
    Retorna {'formula': str|None, 'valor': Any}
    para la celda indicada (ej: 'B12').
    """
    wb_formula = openpyxl.load_workbook(BytesIO(archivo_bytes), data_only=False)
    wb_valor   = openpyxl.load_workbook(BytesIO(archivo_bytes), data_only=True)

    ws_f = wb_formula.active
    ws_v = wb_valor.active

    formula = ws_f[celda].value  # Retorna la fórmula como string o valor si no es fórmula
    valor   = ws_v[celda].value  # Retorna el valor calculado (puede ser None si el archivo no fue recalculado)

    return {"formula": formula, "valor": valor}

def extraer_todas_las_celdas(archivo_bytes: bytes, celdas: list[str]) -> dict[str, dict]:
    """
    Extrae un dict {celda: {'formula': ..., 'valor': ...}} para una lista de celdas.
    Solo carga el archivo una vez por modo.
    """
    wb_f = openpyxl.load_workbook(BytesIO(archivo_bytes), data_only=False)
    wb_v = openpyxl.load_workbook(BytesIO(archivo_bytes), data_only=True)
    ws_f, ws_v = wb_f.active, wb_v.active

    return {
        celda: {"formula": ws_f[celda].value, "valor": ws_v[celda].value}
        for celda in celdas
    }
```

> **Nota:** `data_only=True` solo devuelve el valor calculado si el archivo fue guardado después del último cálculo en Excel. Si el valor es `None`, informar al docente.

---

## Etapa 3 — Motor de calificación (`scoring.py`)

**Objetivo:** Implementar las reglas de puntuación descritas en la sección 6 del spec.

### Función principal

```python
def evaluar_pregunta(
    formula_estudiante: str | None,
    valor_estudiante,
    formula_esperada: str | None,
    valor_esperado,
    puntos_formula: float,
    puntos_valor: float,
) -> dict:
    """
    Retorna:
    {
        'puntos_obtenidos_formula': float,
        'puntos_obtenidos_valor': float,
        'puntaje_parcial': float,
        'caso': str  # 'COMPLETO' | 'PROCESO_OK' | 'RESULTADO_OK' | 'ERROR'
    }
    """
```

### Reglas de scoring

| Caso | Condición | Puntos |
|---|---|---|
| **COMPLETO** | Fórmula correcta Y valor correcto | `puntos_formula + puntos_valor` |
| **PROCESO_OK** | Fórmula correcta, valor incorrecto | `puntos_formula` (parcial de proceso) |
| **RESULTADO_OK** | Sin fórmula (valor hardcodeado) pero valor correcto | `puntos_valor * 0.5` (penalización sugerida) |
| **ERROR** | Ni fórmula ni valor correctos | `0` |

### Detección de fórmula correcta

Comparación flexible: la `formula_esperada` se tokeniza en palabras clave (nombre de función, rango de celdas), y se verifica si todas están presentes en la `formula_estudiante` (case-insensitive).

```python
def _formula_es_correcta(formula_estudiante: str | None, formula_esperada: str | None) -> bool:
    if not formula_estudiante or not formula_esperada:
        return False
    keywords = [w.upper() for w in formula_esperada.replace("(", " ").replace(")", " ").split()]
    estudiante_upper = str(formula_estudiante).upper()
    return all(kw in estudiante_upper for kw in keywords)
```

---

## Etapa 4 — Motor de IA (`ai_engine.py`)

**Objetivo:** Conectar con Gemini para generar feedback pedagógico por pregunta.

### Setup

```python
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-flash")
```

### Función de feedback

```python
def generar_feedback(
    enunciado: str,
    celda: str,
    formula_modelo: str,
    valor_modelo,
    formula_estudiante: str,
    valor_estudiante,
) -> str:
    prompt = f"""Actúa como un profesor experto en Excel. Compara la respuesta del estudiante con el modelo ideal.

- Pregunta: {enunciado}
- Celda: {celda}
- Modelo: Fórmula [{formula_modelo}], Valor [{valor_modelo}]
- Estudiante: Fórmula [{formula_estudiante}], Valor [{valor_estudiante}]

Analiza si el error del estudiante es leve (ej: error de referencia), grave (no sabe usar la función) o si el resultado es correcto pero el proceso es ineficiente. Genera un feedback motivador y breve de máximo 2 líneas."""

    response = model.generate_content(prompt)
    return response.text.strip()
```

> Llamar esta función de forma asíncrona o con `st.spinner` para no bloquear la UI.

---

## Etapa 5 — Interfaz de usuario (`main.py` y módulos `ui/`)

**Objetivo:** Ensamblar todo en la aplicación Streamlit con el flujo de tres fases.

### `main.py` — Entry point

```python
import streamlit as st
from database import init_db
from ui.fase_configuracion import render_configuracion
from ui.fase_revision import render_revision
from ui.fase_reporte import render_reporte

init_db()

# Inicializar session_state
if "app_mode" not in st.session_state:
    st.session_state.app_mode = "CONFIGURACION"
if "lista_evaluados" not in st.session_state:
    st.session_state.lista_evaluados = []
if "estudiante_actual" not in st.session_state:
    st.session_state.estudiante_actual = {}

# Router de fases
if st.session_state.app_mode == "CONFIGURACION":
    render_configuracion()
elif st.session_state.app_mode == "REVISION":
    render_revision()
elif st.session_state.app_mode == "REPORTE_FINAL":
    render_reporte()
```

---

### `ui/fase_configuracion.py`

Responsabilidades:
- `st.sidebar`: formulario para agregar preguntas a la rúbrica (enunciado, celda, fórmula esperada, valor esperado, puntos fórmula, puntos valor).
- Área principal: `st.text_input` para nombre de la prueba.
- Botón "Iniciar Sesión de Revisión": guarda la sesión y la rúbrica en SQLite, cambia `app_mode` a `'REVISION'`.
- Mostrar la rúbrica cargada como tabla (`st.dataframe`).

**Variables de session_state que gestiona:**
- `st.session_state.sesion_id`
- `st.session_state.rubrica` (lista de dicts)

---

### `ui/fase_revision.py`

Responsabilidades:
1. `st.text_input` — nombre del estudiante.
2. `st.file_uploader` — archivo `.xlsx`.
3. Al cargar el archivo:
   - Llamar `extraer_todas_las_celdas()` con todas las celdas de la rúbrica.
   - Para cada pregunta, llamar `evaluar_pregunta()` y `generar_feedback()` (con `st.spinner`).
4. Mostrar resultados con `st.columns(2)`:
   - Columna izquierda: "Lo que hizo el estudiante" (fórmula + valor extraído).
   - Columna derecha: "Lo que se esperaba" (fórmula + valor del modelo).
5. Feedback de IA en `st.info` con `st.text_area` editable debajo.
6. `st.number_input` editable para ajustar puntos por pregunta.
7. Botón "Guardar y Siguiente": persiste en SQLite, agrega a `lista_evaluados`, limpia `estudiante_actual` y resetea el file uploader.
8. Botón "Terminar Sesión": cambia `app_mode` a `'REPORTE_FINAL'`.

**Truco para resetear el file_uploader:** usar un `key` dinámico en `st.file_uploader` (ej: `key=f"uploader_{len(lista_evaluados)}`).

---

### `ui/fase_reporte.py`

Responsabilidades:
- Leer resultados desde SQLite con `obtener_resultados(sesion_id)`.
- Mostrar tabla consolidada con `st.dataframe`.
- Botón "Exportar a CSV": `st.download_button` con `pandas.DataFrame.to_csv()`.
- Botón "Exportar a Excel": `st.download_button` con `pandas.DataFrame.to_excel()` usando `openpyxl` como engine.

---

## Resumen de Dependencias por Módulo

| Módulo | Depende de |
|---|---|
| `main.py` | `database`, `ui/*` |
| `ui/fase_configuracion.py` | `database` |
| `ui/fase_revision.py` | `excel_engine`, `scoring`, `ai_engine`, `database` |
| `ui/fase_reporte.py` | `database`, `pandas` |
| `scoring.py` | — (pura lógica) |
| `ai_engine.py` | `google-generativeai`, `python-dotenv` |
| `excel_engine.py` | `openpyxl` |
| `database.py` | `sqlite3` (stdlib) |

---

## Orden de Implementación Recomendado

1. `database.py` + `init_db()` — base para todo lo demás
2. `excel_engine.py` — validar extracción dual con un archivo de prueba
3. `scoring.py` — lógica pura, fácil de probar manualmente
4. `ai_engine.py` — validar conexión con la API
5. `ui/fase_configuracion.py` — primera pantalla funcional
6. `ui/fase_revision.py` — ciclo principal (el más complejo)
7. `ui/fase_reporte.py` — exportación final
8. Integración en `main.py`
