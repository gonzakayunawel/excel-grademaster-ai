import streamlit as st
import json
from excel_engine import extraer_todas_las_celdas
from scoring import evaluar_pregunta
from ai_engine import generar_feedback
from database import guardar_resultado, obtener_rubrica

def render_revision():
    st.title("Fase 2: Revisión de Estudiantes")

    if "sesion_id" not in st.session_state:
        st.error("No hay una sesión activa. Vuelve a Configuración.")
        if st.button("Ir a Configuración"):
            st.session_state.app_mode = "CONFIGURACION"
            st.rerun()
        return

    if "lista_evaluados" not in st.session_state:
        st.session_state.lista_evaluados = []

    st.write(f"Sesión: **{st.session_state.nombre_prueba}** (ID: {st.session_state.sesion_id})")
    st.write(f"Estudiantes evaluados: **{len(st.session_state.lista_evaluados)}**")

    # Nombre del estudiante
    nombre_estudiante = st.text_input("Nombre del Estudiante")

    # Key dinámico para resetear el file_uploader al avanzar al siguiente estudiante
    if "evaluados_count" not in st.session_state:
        st.session_state.evaluados_count = 0

    archivo = st.file_uploader(
        "Sube el archivo Excel (.xlsx)",
        type="xlsx",
        key=f"uploader_{st.session_state.evaluados_count}"
    )

    if archivo and nombre_estudiante:
        rubrica = st.session_state.get("rubrica") or obtener_rubrica(st.session_state.sesion_id)

        # Reprocesar si cambia el estudiante O el archivo
        cache_invalido = (
            "resultados_actuales" not in st.session_state
            or st.session_state.get("estudiante_nombre_actual") != nombre_estudiante
            or st.session_state.get("archivo_nombre_actual") != archivo.name
        )

        if cache_invalido:
            datos_extraidos = extraer_todas_las_celdas(archivo.getvalue(), rubrica)

            resultados = []
            puntaje_total = 0.0
            progress = st.progress(0, text="Procesando preguntas...")

            for i, item in enumerate(rubrica):
                hoja = item["hoja_objetivo"]
                celda = item["celda_objetivo"]
                clave = f"{hoja}!{celda}"
                extraido = datos_extraidos[clave]

                evaluacion = evaluar_pregunta(
                    extraido["formula"], extraido["valor"],
                    item["formula_esperada"], item["valor_esperado"],
                    item["puntos_formula"], item["puntos_valor"]
                )

                progress.progress(
                    (i + 0.5) / len(rubrica),
                    text=f"Generando feedback para {hoja}!{celda}..."
                )
                feedback = generar_feedback(
                    item["enunciado"], clave,
                    item["formula_esperada"], item["valor_esperado"],
                    extraido["formula"], extraido["valor"]
                )
                progress.progress((i + 1) / len(rubrica), text=f"{hoja}!{celda} completado.")

                resultados.append({
                    "item": item,
                    "extraido": extraido,
                    "evaluacion": evaluacion,
                    "feedback": feedback
                })
                puntaje_total += evaluacion["puntaje_parcial"]

            progress.empty()

            st.session_state.resultados_actuales = resultados
            st.session_state.estudiante_nombre_actual = nombre_estudiante
            st.session_state.archivo_nombre_actual = archivo.name

        # Mostrar resultados
        st.divider()
        st.header(f"Resultados: {nombre_estudiante}")

        # Agrupar resultados por grupo_id
        grupos_res = {}
        for idx, res in enumerate(st.session_state.resultados_actuales):
            g_id = res["item"].get("grupo_id", 0)
            if g_id not in grupos_res:
                grupos_res[g_id] = []
            grupos_res[g_id].append((idx, res))

        for g_id, celdas_res in grupos_res.items():
            enunciado = celdas_res[0][1]["item"]["enunciado"]
            titulo_enunciado = enunciado[:50] + "..." if len(enunciado) > 50 else enunciado
            puntaje_grupo_inicial = sum(float(r[1]["evaluacion"]["puntaje_parcial"]) for r in celdas_res)
            
            with st.expander(
                f"Pregunta {g_id} — {titulo_enunciado} (Suma inicial: {puntaje_grupo_inicial} pts)",
                expanded=True
            ):
                st.write(f"**Enunciado completo:** {enunciado}")
                
                for idx, res in celdas_res:
                    item = res["item"]
                    ext  = res["extraido"]
                    ev   = res["evaluacion"]

                    st.markdown(f"#### 🔸 Celda: {item['hoja_objetivo']}!{item['celda_objetivo']}")
                    
                    # Mostrar advertencia si hubo error de extracción
                    if ext.get("error"):
                        st.error(f"Error de extracción: {ext['error']}")

                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**Estudiante:**")
                        st.code(f"Fórmula: {ext['formula']}")
                        st.write(f"Valor: {ext['valor']}")
                    with col2:
                        st.write("**Esperado:**")
                        st.code(f"Fórmula: {item['formula_esperada']}")
                        st.write(f"Valor: {item['valor_esperado']}")

                    caso_labels = {
                        "COMPLETO": "✅ Completo",
                        "PROCESO_OK": "🔶 Proceso correcto, valor incorrecto",
                        "RESULTADO_OK": "⚠️ Valor correcto sin fórmula (penalización aplicada)",
                        "ERROR": "❌ Error"
                    }
                    st.write(f"**Caso:** {caso_labels.get(ev['caso'], ev['caso'])}")
                    st.success(
                        f"Puntaje sugerido celda: {ev['puntaje_parcial']} pts "
                        f"(Fórmula: {ev['puntos_obtenidos_formula']}, Valor: {ev['puntos_obtenidos_valor']})"
                    )

                    st.info(f"**Feedback IA ({item['hoja_objetivo']}!{item['celda_objetivo']}):** {res['feedback']}")
                    nuevo_feedback = st.text_area(f"Editar feedback celda {item['celda_objetivo']}", value=res['feedback'], key=f"fb_{idx}")
                    res['feedback'] = nuevo_feedback

                    nuevo_puntaje = st.number_input(
                        f"Ajustar puntaje celda {item['celda_objetivo']}",
                        value=float(ev['puntaje_parcial']),
                        step=0.25,
                        key=f"puntos_{idx}"
                    )
                    res['evaluacion']['puntaje_parcial_final'] = nuevo_puntaje
                    st.divider()

        total_final = sum(
            res['evaluacion'].get('puntaje_parcial_final', res['evaluacion']['puntaje_parcial'])
            for res in st.session_state.resultados_actuales
        )
        st.subheader(f"Puntaje Total Final Estudiante: {total_final}")

        if st.button("Guardar Resultado Estudiante", type="primary"):
            detalle_persistencia = []
            for res in st.session_state.resultados_actuales:
                detalle_persistencia.append({
                    "hoja": res["item"]["hoja_objetivo"],
                    "celda": res["item"]["celda_objetivo"],
                    "grupo_id": res["item"].get("grupo_id", 0),
                    "caso": res["evaluacion"]["caso"],
                    "formula_estudiante": res["extraido"]["formula"],
                    "valor_estudiante": str(res["extraido"]["valor"]),
                    "puntos": res["evaluacion"].get("puntaje_parcial_final", res["evaluacion"]["puntaje_parcial"]),
                    "feedback": res["feedback"]
                })

            guardar_resultado(
                st.session_state.sesion_id,
                nombre_estudiante,
                total_final,
                json.dumps(detalle_persistencia, ensure_ascii=False)
            )

            st.session_state.lista_evaluados.append({
                "nombre": nombre_estudiante,
                "puntaje_total": total_final,
                "detalles": detalle_persistencia
            })

            st.session_state.evaluados_count += 1
            del st.session_state.resultados_actuales
            del st.session_state.estudiante_nombre_actual
            del st.session_state.archivo_nombre_actual

            st.success(f"Resultado de {nombre_estudiante} guardado correctamente.")
            st.rerun()

    st.divider()
    if st.button("Finalizar Sesión y Ver Reporte"):
        st.session_state.app_mode = "REPORTE_FINAL"
        st.rerun()
