import openpyxl
from io import BytesIO

def extraer_todas_las_celdas(archivo_bytes: bytes, items: list[dict]) -> dict[str, dict]:
    """
    Extrae fórmulas y valores calculados para cada ítem de la rúbrica.

    Parámetros:
        archivo_bytes: contenido del .xlsx en bytes.
        items: lista de dicts con 'hoja_objetivo' y 'celda_objetivo'.

    Retorna:
        {"Hoja1!B12": {"formula": ..., "valor": ..., "error": str|None}}
    """
    wb_f = openpyxl.load_workbook(BytesIO(archivo_bytes), data_only=False)
    wb_v = openpyxl.load_workbook(BytesIO(archivo_bytes), data_only=True)

    resultados = {}
    for item in items:
        hoja = item["hoja_objetivo"]
        celda = item["celda_objetivo"]
        clave = f"{hoja}!{celda}"

        if hoja not in wb_f.sheetnames:
            hojas_disponibles = ", ".join(wb_f.sheetnames)
            resultados[clave] = {
                "formula": None,
                "valor": None,
                "error": f"La hoja '{hoja}' no existe en el archivo. Hojas disponibles: {hojas_disponibles}"
            }
            continue

        try:
            ws_f = wb_f[hoja]
            ws_v = wb_v[hoja]
            resultados[clave] = {
                "formula": ws_f[celda].value,
                "valor": ws_v[celda].value,
                "error": None
            }
        except Exception as e:
            resultados[clave] = {
                "formula": None,
                "valor": None,
                "error": f"Error al leer celda {celda}: {str(e)}"
            }

    return resultados
