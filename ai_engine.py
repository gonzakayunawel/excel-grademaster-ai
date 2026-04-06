from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

# Configurar API Key (debe estar en el .env)
api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    client = genai.Client(api_key=api_key)
else:
    client = None

def generar_feedback(
    enunciado: str,
    celda: str,
    formula_modelo: str,
    valor_modelo,
    formula_estudiante: str,
    valor_estudiante,
    es_formato_condicional: bool = False,
    rango_esperado: str | None = None,
    color_esperado: str | None = None,
    reglas_estudiante: list[dict] | None = None,
) -> str:
    if not client:
        return "Configuración de IA no disponible (revisa GOOGLE_API_KEY)."

    if es_formato_condicional:
        reglas_str = str(reglas_estudiante) if reglas_estudiante else "Ninguna regla detectada"
        prompt = f"""Actúa como un profesor experto en Excel. Compara la configuración de FORMATO CONDICIONAL del estudiante con el modelo ideal.

- Pregunta: {enunciado}
- Hoja/Celda base: {celda}
- Modelo Esperado: Rango [{rango_esperado}], Condición/Fórmula [{formula_modelo}], Color Hex [{color_esperado}]
- Reglas detectadas en el estudiante: {reglas_str}

Analiza si el estudiante aplicó correctamente el rango, si la lógica de la condición es correcta, y si asignó el color esperado. Genera un feedback motivador y breve de máximo 2 líneas. Si no aplicó nada, indícaselo."""
    else:
        prompt = f"""Actúa como un profesor experto en Excel. Compara la respuesta del estudiante con el modelo ideal.

- Pregunta: {enunciado}
- Celda: {celda}
- Modelo: Fórmula [{formula_modelo}], Valor [{valor_modelo}]
- Estudiante: Fórmula [{formula_estudiante}], Valor [{valor_estudiante}]

Analiza si el error del estudiante es leve (ej: error de referencia), grave (no sabe usar la función) o si el resultado es correcto pero el proceso es ineficiente. Genera un feedback motivador y breve de máximo 2 líneas."""

    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        return f"Error al generar feedback con IA: {str(e)}"
