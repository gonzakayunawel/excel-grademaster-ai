import re
import math

def _formula_es_correcta(formula_estudiante: str | None, formula_esperada: str | None) -> bool:
    if not formula_estudiante or not formula_esperada:
        return False

    # Si no empieza con "=" no es fórmula (valor hardcodeado)
    if not str(formula_estudiante).startswith("="):
        return False

    # Tokenizar la fórmula esperada manteniendo rangos intactos (ej: A1:A10 es un token)
    tokens = re.findall(r'[A-Z0-9:]+', formula_esperada.upper().replace("=", ""))
    # Descartar tokens que sean solo ":" (artefactos de tokenización)
    tokens = [t for t in tokens if t and not t.startswith(":") and not t.endswith(":")]

    estudiante_upper = str(formula_estudiante).upper()

    # Verificar cada token con lookaheads para evitar falsos positivos
    # (ej: token "A1" no debe coincidir dentro de "A10", token "A1:A10" no en "A1:A100")
    return all(
        re.search(r'(?<![A-Z0-9])' + re.escape(kw) + r'(?![A-Z0-9])', estudiante_upper)
        for kw in tokens
    )

def _valor_es_correcto(valor_estudiante, valor_esperado) -> bool:
    if valor_estudiante is None or valor_esperado is None:
        return False
    # Intentar comparación numérica primero para evitar problemas con "10" vs 10.0
    try:
        return math.isclose(float(valor_estudiante), float(valor_esperado), rel_tol=1e-9)
    except (ValueError, TypeError):
        return str(valor_estudiante).strip().upper() == str(valor_esperado).strip().upper()

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
    formula_ok = _formula_es_correcta(formula_estudiante, formula_esperada)
    valor_ok = _valor_es_correcto(valor_estudiante, valor_esperado)

    puntos_f = 0.0
    puntos_v = 0.0
    caso = "ERROR"

    if formula_ok and valor_ok:
        puntos_f = puntos_formula
        puntos_v = puntos_valor
        caso = "COMPLETO"
    elif formula_ok and not valor_ok:
        puntos_f = puntos_formula
        puntos_v = 0.0
        caso = "PROCESO_OK"
    elif not formula_ok and valor_ok:
        # Valor correcto pero sin fórmula (hardcodeado): penalización del 50%
        puntos_f = 0.0
        puntos_v = puntos_valor * 0.5
        caso = "RESULTADO_OK"
    else:
        puntos_f = 0.0
        puntos_v = 0.0
        caso = "ERROR"

    return {
        "puntos_obtenidos_formula": puntos_f,
        "puntos_obtenidos_valor": puntos_v,
        "puntaje_parcial": puntos_f + puntos_v,
        "caso": caso
    }
