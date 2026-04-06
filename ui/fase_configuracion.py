import re
import streamlit as st
import pandas as pd
from database import crear_sesion, guardar_rubrica

# Patrón válido para referencias de celda Excel (ej: B12, AA100)
_CELDA_RE = re.compile(r'^[A-Za-z]{1,3}\d{1,7}$')

def render_configuracion():
    st.title("Fase 1: Configuración de la Rúbrica")

    if "rubrica" not in st.session_state:
        st.session_state.rubrica = []

    # Sidebar: formulario para agregar preguntas
    with st.sidebar:
        st.header("Nueva Pregunta")
        enunciado = st.text_area("Enunciado de la pregunta")
        hoja = st.text_input("Nombre de la hoja (ej: Hoja1)", value="Hoja1")
        celda = st.text_input("Celda objetivo (ej: B12)", max_chars=10)
        formula = st.text_input("Fórmula esperada (ej: =SUMA(A1:A10))")
        valor = st.text_input("Valor esperado")
        puntos_f = st.number_input("Puntos por fórmula", min_value=0.0, step=0.5, value=1.0)
        puntos_v = st.number_input("Puntos por valor", min_value=0.0, step=0.5, value=1.0)

        if st.button("Agregar a la rúbrica"):
            celda_limpia = celda.strip().upper()
            hoja_limpia = hoja.strip()

            if not hoja_limpia:
                st.error("El nombre de la hoja no puede estar vacío.")
            elif not celda_limpia:
                st.error("La celda objetivo es obligatoria.")
            elif not _CELDA_RE.match(celda_limpia):
                st.error(f"'{celda_limpia}' no es una referencia de celda válida (ej: B12, AA100).")
            elif not formula and not valor:
                st.error("Debes indicar al menos una fórmula o un valor esperado.")
            else:
                st.session_state.rubrica.append({
                    "enunciado": enunciado,
                    "hoja_objetivo": hoja_limpia,
                    "celda_objetivo": celda_limpia,
                    "formula_esperada": formula,
                    "valor_esperado": valor,
                    "puntos_formula": puntos_f,
                    "puntos_valor": puntos_v
                })
                st.success(f"Celda {hoja_limpia}!{celda_limpia} agregada.")

    # Área principal
    nombre_prueba = st.text_input("Nombre de la Prueba / Sesión", value="Examen de Excel 1")

    if st.session_state.rubrica:
        st.subheader("Rúbrica Actual")
        df = pd.DataFrame(st.session_state.rubrica)
        st.dataframe(df, width="stretch")

        if st.button("Limpiar Rúbrica"):
            st.session_state.rubrica = []
            st.rerun()

        if st.button("Iniciar Sesión de Revisión", type="primary"):
            if nombre_prueba.strip():
                sesion_id = crear_sesion(nombre_prueba.strip())
                guardar_rubrica(sesion_id, st.session_state.rubrica)

                st.session_state.sesion_id = sesion_id
                st.session_state.nombre_prueba = nombre_prueba.strip()
                st.session_state.app_mode = "REVISION"
                st.rerun()
            else:
                st.error("Por favor, ingresa un nombre para la prueba.")
    else:
        st.info("Agrega preguntas en la barra lateral para comenzar.")
