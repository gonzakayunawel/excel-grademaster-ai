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
    if "siguiente_grupo_id" not in st.session_state:
        st.session_state.siguiente_grupo_id = 1
    if "celdas_pregunta_actual" not in st.session_state:
        st.session_state.celdas_pregunta_actual = []

    # Sidebar: constructor de pregunta
    with st.sidebar:
        st.header("Constructor de Pregunta")
        
        enunciado = st.text_area("Enunciado general de la pregunta", key="input_enunciado")
        
        st.subheader("Añadir celda a la pregunta")
        hoja = st.text_input("Hoja (ej: Hoja1)", value="Hoja1")
        
        es_fc = st.checkbox("¿Es formato condicional?")
        
        if es_fc:
            celda = st.text_input("Rango donde se aplica (ej: A1:A10)", max_chars=20)
            rango_esperado = celda
            formula = st.text_input("Condición / Fórmula esperada")
            color_esperado = st.text_input("Color Hexadecimal esperado (ej: FF0000)")
            valor = ""
        else:
            celda = st.text_input("Celda (ej: B12)", max_chars=10)
            formula = st.text_input("Fórmula esperada")
            valor = st.text_input("Valor esperado")
            rango_esperado = None
            color_esperado = None
        
        col1, col2 = st.columns(2)
        puntos_f = col1.number_input("Pts. Fórmula", min_value=0.0, step=0.5, value=1.0)
        puntos_v = col2.number_input("Pts. Valor", min_value=0.0, step=0.5, value=1.0)

        if st.button("Añadir celda a la pregunta actual"):
            celda_limpia = celda.strip().upper()
            hoja_limpia = hoja.strip()

            if not hoja_limpia:
                st.error("El nombre de la hoja no puede estar vacío.")
            elif not celda_limpia:
                st.error("La celda o rango es obligatorio.")
            elif not es_fc and not _CELDA_RE.match(celda_limpia):
                st.error(f"'{celda_limpia}' no es una referencia válida.")
            elif not formula and not valor and not color_esperado:
                st.error("Indica al menos un criterio (fórmula, valor o color).")
            else:
                st.session_state.celdas_pregunta_actual.append({
                    "hoja_objetivo": hoja_limpia,
                    "celda_objetivo": celda_limpia,
                    "formula_esperada": formula,
                    "valor_esperado": valor,
                    "puntos_formula": puntos_f,
                    "puntos_valor": puntos_v,
                    "es_formato_condicional": es_fc,
                    "rango_esperado": rango_esperado.strip().upper() if rango_esperado else None,
                    "color_esperado_hex": color_esperado.strip() if color_esperado else None
                })
                st.success(f"Elemento añadido a la pregunta actual.")
        
        if st.session_state.celdas_pregunta_actual:
            st.markdown("### Celdas en la pregunta actual:")
            for i, c in enumerate(st.session_state.celdas_pregunta_actual):
                tipo_lbl = "FC" if c.get("es_formato_condicional") else "Normal"
                st.markdown(f"- **[{tipo_lbl}] {c['hoja_objetivo']}!{c['celda_objetivo']}** (F: {c['puntos_formula']}, V: {c['puntos_valor']})")
            
            if st.button("Guardar Pregunta en Rúbrica General", type="primary"):
                if not enunciado.strip():
                    st.error("Debes ingresar un enunciado para la pregunta.")
                else:
                    grupo_id = st.session_state.siguiente_grupo_id
                    st.session_state.siguiente_grupo_id += 1
                    
                    for c in st.session_state.celdas_pregunta_actual:
                        c["enunciado"] = enunciado.strip()
                        c["grupo_id"] = grupo_id
                        st.session_state.rubrica.append(c)
                    
                    st.session_state.celdas_pregunta_actual = []
                    st.success("Pregunta guardada en la rúbrica.")
                    st.rerun()
            
            if st.button("Descartar celdas"):
                st.session_state.celdas_pregunta_actual = []
                st.rerun()

    # Área principal
    nombre_prueba = st.text_input("Nombre de la Prueba / Sesión", value="Examen de Excel 1")

    if st.session_state.rubrica:
        st.subheader("Rúbrica Actual")
        
        # Agrupar rúbrica por grupo_id guardando el índice real en la lista plana
        grupos = {}
        for flat_idx, item in enumerate(st.session_state.rubrica):
            g_id = item.get("grupo_id", 0)
            if g_id not in grupos:
                grupos[g_id] = {
                    "enunciado": item["enunciado"],
                    "celdas": []
                }
            grupos[g_id]["celdas"].append((flat_idx, item))

        for g_id, datos in grupos.items():
            enunciado_corto = datos['enunciado'][:60] + "..." if len(datos['enunciado']) > 60 else datos['enunciado']
            total_pts = sum(c['puntos_formula'] + c['puntos_valor'] for _, c in datos['celdas'])

            with st.expander(f"Pregunta {g_id}: {enunciado_corto} ({len(datos['celdas'])} celdas, {total_pts} pts)", expanded=False):
                st.write(f"**Enunciado completo:** {datos['enunciado']}")

                for flat_idx, c in datos['celdas']:
                    col1, col2 = st.columns([5, 1])
                    with col1:
                        st.write(f"- **{c['hoja_objetivo']}!{c['celda_objetivo']}** | Fórmula: `{c['formula_esperada']}` | Valor: `{c['valor_esperado']}`")
                    with col2:
                        if st.button("Eliminar", key=f"del_{flat_idx}"):
                            st.session_state.rubrica.pop(flat_idx)
                            st.rerun()

        st.divider()
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Reiniciar Rúbrica (Borrar Todo)", type="secondary"):
                st.session_state.rubrica = []
                st.session_state.siguiente_grupo_id = 1
                st.session_state.celdas_pregunta_actual = []
                st.rerun()
        with col2:
            if st.button("Iniciar Sesión de Revisión", type="primary"):
                if st.session_state.celdas_pregunta_actual:
                    st.warning("Hay celdas sin guardar en la pregunta actual. Guarda o descarta la pregunta antes de iniciar la sesión.")
                elif not nombre_prueba.strip():
                    st.error("Por favor, ingresa un nombre para la prueba.")
                else:
                    sesion_id = crear_sesion(nombre_prueba.strip())
                    guardar_rubrica(sesion_id, st.session_state.rubrica)

                    st.session_state.sesion_id = sesion_id
                    st.session_state.nombre_prueba = nombre_prueba.strip()
                    st.session_state.app_mode = "REVISION"
                    st.rerun()
    else:
        st.info("Utiliza el constructor de preguntas en la barra lateral para añadir elementos a la rúbrica.")
