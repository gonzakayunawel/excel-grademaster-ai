import streamlit as st
from database import init_db
from ui.fase_configuracion import render_configuracion
from ui.fase_revision import render_revision
from ui.fase_reporte import render_reporte

# Inicializar Base de Datos
init_db()

# Configuración de Página
st.set_page_config(
    page_title="Excel-GradeMaster AI",
    page_icon="📊",
    layout="wide"
)

# Sidebar persistente
with st.sidebar:
    st.title("📊 GradeMaster AI")
    st.caption("Asistente pedagógico para exámenes de Excel")

# Inicializar session_state
if "app_mode" not in st.session_state:
    st.session_state.app_mode = "CONFIGURACION"
if "lista_evaluados" not in st.session_state:
    st.session_state.lista_evaluados = []
if "estudiante_actual" not in st.session_state:
    st.session_state.estudiante_actual = {}

# Router de fases
try:
    if st.session_state.app_mode == "CONFIGURACION":
        render_configuracion()
    elif st.session_state.app_mode == "REVISION":
        render_revision()
    elif st.session_state.app_mode == "REPORTE_FINAL":
        render_reporte()
except Exception as e:
    st.error(f"Se ha producido un error inesperado: {str(e)}")
    if st.button("Reiniciar Aplicación"):
        st.session_state.clear()
        st.rerun()
