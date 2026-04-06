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

                es_fc = item.get("es_formato_condicional", 0) == 1
                
                evaluacion = evaluar_pregunta(
                    formula_estudiante=extraido["formula"], 
                    valor_estudiante=extraido["valor"],
                    formula_esperada=item["formula_esperada"], 
                    valor_esperado=item["valor_esperado"],
                    puntos_formula=item["puntos_formula"], 
                    puntos_valor=item["puntos_valor"],
                    es_formato_condicional=es_fc,
                    rango_esperado=item.get("rango_esperado"),
                    color_esperado=item.get("color_esperado_hex"),
                    reglas_estudiante=extraido.get("reglas_fc")
                )

                progress.progress(
                    (i + 0.5) / len(rubrica),
                    text=f"Generando feedback para {hoja}!{celda}..."
                )
                feedback = generar_feedback(
                    enunciado=item["enunciado"], 
                    celda=clave,
                    formula_modelo=item["formula_esperada"], 
                    valor_modelo=item["valor_esperado"],
                    formula_estudiante=extraido["formula"], 
                    valor_estudiante=extraido["valor"],
                    es_formato_condicional=es_fc,
                    rango_esperado=item.get("rango_esperado"),
                    color_esperado=item.get("color_esperado_hex"),
                    reglas_estudiante=extraido.get("reglas_fc")
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
            # Leer el puntaje ajustado desde el widget state si ya fue modificado por el docente
            puntaje_grupo_actual = sum(
                float(st.session_state.get(f"puntos_{idx}", r["evaluacion"]["puntaje_parcial"]))
                for idx, r in celdas_res
            )

            with st.expander(
                f"Pregunta {g_id} — {titulo_enunciado} ({puntaje_grupo_actual} pts)",
                expanded=True
            ):
                st.write(f"**Enunciado completo:** {enunciado}")
                
                for i, (idx, res) in enumerate(celdas_res):
                    item = res["item"]
                    ext  = res["extraido"]
                    ev   = res["evaluacion"]

                    st.markdown(f"#### 🔸 Celda/Rango: {item['hoja_objetivo']}!{item['celda_objetivo']}")
                    
                    # Mostrar advertencia si hubo error de extracción
                    if ext.get("error"):
                        st.error(f"Error de extracción: {ext['error']}")

                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**Estudiante:**")
                        if item.get("es_formato_condicional"):
                            st.write(f"Reglas detectadas: {len(ext.get('reglas_fc', []))}")
                            for r in ext.get('reglas_fc', []):
                                st.code(f"Rango: {r.get('rango')}\nFórmula: {r.get('formulas')}\nColor: #{r.get('color_hex')}")
                        else:
                            st.code(f"Fórmula: {ext.get('formula')}")
                            st.write(f"Valor: {ext.get('valor')}")
                    with col2:
                        st.write("**Esperado:**")
                        if item.get("es_formato_condicional"):
                            st.write(f"Rango: `{item.get('rango_esperado')}`")
                            st.code(f"Condición: {item.get('formula_esperada')}")
                            color_esperado = item.get("color_esperado_hex")
                            if color_esperado:
                                st.markdown(f"Color: #{color_esperado} <span style='display:inline-block; width:20px; height:20px; background-color:#{color_esperado.replace('#','')}; border:1px solid #000;'></span>", unsafe_allow_html=True)
                            else:
                                st.write("Color: Cualquiera")
                        else:
                            st.code(f"Fórmula: {item.get('formula_esperada')}")
                            st.write(f"Valor: {item.get('valor_esperado')}")

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
                    if i < len(celdas_res) - 1:
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
