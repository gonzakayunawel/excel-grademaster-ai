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

def evaluar_formato_condicional(
    reglas_estudiante: list[dict] | None,
    rango_esperado: str | None,
    formula_esperada: str | None,
    color_esperado: str | None,
    puntos_formula: float,
    puntos_valor: float,
) -> dict:
    if not reglas_estudiante:
        return {
            "puntos_obtenidos_formula": 0.0,
            "puntos_obtenidos_valor": 0.0,
            "puntaje_parcial": 0.0,
            "caso": "ERROR"
        }

    # Búsqueda de una regla que cumpla los criterios
    mejor_puntaje_f = 0.0
    mejor_puntaje_v = 0.0
    mejor_caso = "ERROR"

    # Preparar keywords para la regla
    keywords_esperadas = []
    if formula_esperada:
        keywords_esperadas = [w.upper() for w in formula_esperada.replace("(", " ").replace(")", " ").replace("=", "").split() if w]

    rango_esperado_upper = str(rango_esperado).upper() if rango_esperado else ""
    color_esperado_upper = str(color_esperado).upper().replace("#", "") if color_esperado else ""

    for regla in reglas_estudiante:
        # Validar rango
        rango_ok = False
        if not rango_esperado:
            rango_ok = True
        elif rango_esperado_upper in str(regla.get("rango", "")).upper():
            # Simplificación: comprobamos si el rango esperado es parte del rango aplicado
            rango_ok = True
            
        # Validar fórmula/condición
        formula_ok = False
        if not formula_esperada:
            formula_ok = True
        else:
            formulas_aplicadas = regla.get("formulas", [])
            for f_aplicada in formulas_aplicadas:
                f_upper = str(f_aplicada).upper()
                if all(kw in f_upper for kw in keywords_esperadas):
                    formula_ok = True
                    break

        # Validar color
        color_ok = False
        if not color_esperado:
            color_ok = True
        else:
            color_aplicado = str(regla.get("color_hex", "")).upper().replace("#", "")
            # openpyxl suele devolver colores en formato aRGB (ej: FF00B0F0), podemos comparar ignorando alpha o exacto
            if color_esperado_upper in color_aplicado or color_aplicado in color_esperado_upper:
                 color_ok = True
            elif len(color_aplicado) == 8 and len(color_esperado_upper) == 6:
                 if color_aplicado[2:] == color_esperado_upper:
                     color_ok = True

        puntos_f = 0.0
        puntos_v = 0.0
        caso_actual = "ERROR"

        if rango_ok and formula_ok and color_ok:
            puntos_f = puntos_formula
            puntos_v = puntos_valor
            caso_actual = "COMPLETO"
        elif rango_ok and formula_ok and not color_ok:
            puntos_f = puntos_formula
            puntos_v = 0.0
            caso_actual = "PROCESO_OK"
        elif rango_ok and not formula_ok and color_ok:
            puntos_f = 0.0
            puntos_v = puntos_valor * 0.5
            caso_actual = "RESULTADO_OK"
        
        # Nos quedamos con la mejor regla encontrada
        suma_actual = puntos_f + puntos_v
        suma_mejor = mejor_puntaje_f + mejor_puntaje_v
        
        if suma_actual > suma_mejor or (suma_actual == suma_mejor and caso_actual == "COMPLETO"):
            mejor_puntaje_f = puntos_f
            mejor_puntaje_v = puntos_v
            mejor_caso = caso_actual

    return {
        "puntos_obtenidos_formula": mejor_puntaje_f,
        "puntos_obtenidos_valor": mejor_puntaje_v,
        "puntaje_parcial": mejor_puntaje_f + mejor_puntaje_v,
        "caso": mejor_caso
    }

def evaluar_pregunta(
    formula_estudiante: str | None,
    valor_estudiante,
    formula_esperada: str | None,
    valor_esperado,
    puntos_formula: float,
    puntos_valor: float,
    es_formato_condicional: bool = False,
    rango_esperado: str | None = None,
    color_esperado: str | None = None,
    reglas_estudiante: list[dict] | None = None,
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
    if es_formato_condicional:
        return evaluar_formato_condicional(
            reglas_estudiante=reglas_estudiante,
            rango_esperado=rango_esperado,
            formula_esperada=formula_esperada,
            color_esperado=color_esperado,
            puntos_formula=puntos_formula,
            puntos_valor=puntos_valor
        )

    formula_ok = _formula_es_correcta(formula_estudiante, formula_esperada)
    valor_ok = _valor_es_correcto(valor_estudiante, valor_esperado)

    puntos_f = 0.0
    puntos_v = 0.0
    caso = "ERROR"

    # Si NO se espera formula (rubrica vacia), solo evaluamos el valor sin penalizar
    espera_formula = bool(formula_esperada and formula_esperada.strip())

    if espera_formula:
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
        # Solo evaluamos valor si no se definio formula esperada
        if valor_ok:
            puntos_v = puntos_valor
            caso = "COMPLETO"
        else:
            caso = "ERROR"

    return {
        "puntos_obtenidos_formula": puntos_f,
        "puntos_obtenidos_valor": puntos_v,
        "puntaje_parcial": puntos_f + puntos_v,
        "caso": caso
    }
