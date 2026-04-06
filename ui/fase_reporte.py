import streamlit as st
import pandas as pd
from database import obtener_resultados
from io import BytesIO

def render_reporte():
    st.title("Fase 3: Reporte Final")

    if "sesion_id" not in st.session_state:
        st.error("No hay una sesión activa.")
        return

    st.write(f"Resultados de la sesión: **{st.session_state.nombre_prueba}**")

    resultados = obtener_resultados(st.session_state.sesion_id)

    if not resultados:
        st.warning("No se encontraron resultados guardados para esta sesión.")
    else:
        df = pd.DataFrame(resultados)

        df_display = df[["nombre_estudiante", "puntaje_total"]].copy()
        df_display["estado"] = "Revisado"

        st.subheader("Consolidado de Notas")
        st.dataframe(df_display, width="stretch")

        col1, col2 = st.columns(2)

        with col1:
            csv = df_display.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Descargar Reporte CSV",
                data=csv,
                file_name=f"reporte_{st.session_state.sesion_id}.csv",
                mime="text/csv",
            )

        with col2:
            try:
                output = BytesIO()
                with pd.ExcelWriter(output, engine="openpyxl") as writer:
                    df_display.to_excel(writer, index=False, sheet_name="Resultados")
                excel_data = output.getvalue()
                st.download_button(
                    label="Descargar Reporte Excel",
                    data=excel_data,
                    file_name=f"reporte_{st.session_state.sesion_id}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            except Exception as e:
                st.error(f"No se pudo generar el archivo Excel: {e}")

    st.divider()
    if st.button("Comenzar Nueva Sesión (Configuración)"):
        keys_to_delete = ["sesion_id", "nombre_prueba", "rubrica", "evaluados_count", "lista_evaluados"]
        for key in keys_to_delete:
            if key in st.session_state:
                del st.session_state[key]
        st.session_state.app_mode = "CONFIGURACION"
        st.rerun()
