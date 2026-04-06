# **Documento de Especificaciones: Excel-GradeMaster AI (SDD)**

## **1\. Resumen del Proyecto**

**Excel-GradeMaster AI** es una aplicación diseñada para automatizar y asistir en la corrección de pruebas de Excel. Su valor diferencial radica en la evaluación del **proceso (fórmulas)** además del **resultado (valores)**. Utiliza IA (Google Gemini) para generar retroalimentación pedagógica y permite una supervisión humana constante para validar puntajes y comentarios antes de guardarlos.

## **2\. Stack Tecnológico**

* **Lenguaje:** Python 3.10+  
* **Interfaz de Usuario:** Streamlit (Web Framework)  
* **Motor de Excel:** openpyxl (Lectura de celdas con y sin data\_only)  
* **Base de Datos:** SQLite (Persistencia de rúbricas y resultados finales)  
* **IA Generativa:** Google Gemini API (gemini-1.5-flash)  
* **Gestión de Estado:** Streamlit Session State (para flujo iterativo)

## **3\. Modelo de Datos y Estado**

### **3.1. Persistencia (SQLite)**

Se requiere una base de datos local para mantener la integridad de las sesiones.

* **Tabla SesionRevision**: id, nombre\_prueba, fecha\_creacion.  
* **Tabla ConfiguracionRubrica**: id, sesion\_id, enunciado, celda\_objetivo, formula\_esperada, valor\_esperado, puntos\_formula, puntos\_valor.  
* **Tabla ResultadosEstudiantes**: id, sesion\_id, nombre\_estudiante, puntaje\_total, detalle\_json (almacena el feedback final editado).

### **3.2. Estado de la Aplicación (Session State)**

Para manejar el flujo "estudiante por estudiante" sin perder datos:

* app\_mode: \['CONFIGURACION', 'REVISION', 'REPORTE\_FINAL'\]  
* lista\_evaluados: Lista de objetos con los datos confirmados por el docente.  
* estudiante\_actual: Datos temporales del proceso en curso.

## **4\. Especificaciones Funcionales (El Flujo)**

### **Fase 1: Configuración de la Sesión**

1. El docente define el nombre de la prueba.  
2. El docente ingresa la **Rúbrica de Referencia**. Para cada pregunta se define:  
   * Enunciado.  
   * Celda objetivo (ej: B12).  
   * Fórmula esperada (string de referencia).  
   * Resultado esperado (valor numérico o texto).  
   * Puntaje máximo por fórmula y por resultado.

### **Fase 2: Ciclo de Revisión Individual (Iterativo)**

Para cada estudiante, la aplicación sigue este orden:

1. **Ingreso de Identidad:** El docente escribe el nombre del estudiante.  
2. **Carga de Archivo:** Se sube el archivo .xlsx del estudiante.  
3. **Extracción Dual:**  
   * La app lee la celda en modo **fórmulas** (data\_only=False).  
   * La app lee la celda en modo **valores** (data\_only=True).  
4. **Evaluación Lógica (Scoring Engine):**  
   * Si valor\_estudiante \== valor\_esperado \-\> Otorga puntos de resultado.  
   * Si formula\_estudiante contiene palabras clave de la formula\_esperada \-\> Otorga puntos de proceso.  
5. **Análisis de IA (Gemini):**  
   * Se envía un prompt a Gemini con: Enunciado, fórmulas (modelo vs alumno) y valores (modelo vs alumno).  
   * Gemini devuelve una explicación del error (ej: "Usó suma manual en vez de la función SUMA") y sugiere un puntaje parcial si aplica.  
6. **Validación Humana (Human-in-the-Loop):**  
   * Streamlit muestra el puntaje sugerido y el feedback de la IA en campos editables.  
   * **El docente puede modificar los puntos y el texto.**  
7. **Confirmación:** Al presionar "Guardar y Siguiente", los datos se mueven a la lista de evaluados y se limpia el uploader para el siguiente alumno.

### **Fase 3: Finalización y Reporte**

1. El usuario selecciona "Terminar Sesión".  
2. La app muestra una tabla consolidada con: Nombre, Puntaje Total y Estado.  
3. Opción de exportar los resultados a CSV/Excel.

## **5\. Diseño del Prompt (Gemini)**

El sistema enviará el siguiente contexto a la API para cada pregunta:

"Actúa como un profesor experto en Excel. Compara la respuesta del estudiante con el modelo ideal.

* Pregunta: {enunciado}  
* Celda: {celda}  
* Modelo: Fórmula \[{formula\_modelo}\], Valor \[{valor\_modelo}\]  
* Estudiante: Fórmula \[{formula\_estudiante}\], Valor \[{valor\_estudiante}\]

Analiza si el error del estudiante es leve (ej: error de referencia), grave (no sabe usar la función) o si el resultado es correcto pero el proceso es ineficiente. Genera un feedback motivador y breve de máximo 2 líneas."

## **6\. Criterios de Calificación Automatizada**

La lógica interna debe seguir estrictamente estas reglas:

* **Puntaje Total:** Fórmula Correcta \+ Resultado Correcto.  
* **Puntaje Parcial (Proceso):** Fórmula correcta, pero resultado mal (ej: se equivocó en un dato de entrada pero la lógica es perfecta).  
* **Puntaje Parcial (Resultado):** Resultado bien, pero sin fórmula (ej: escribió el número a mano). La IA debe detectar esto y recomendar penalización.  
* **Error de Arrastre:** Si una celda depende de otra anterior mal calculada, la IA debe intentar identificarlo para no penalizar doblemente.

## **7\. Requerimientos de Interfaz (UI)**

* **Estética:** Limpia, usando el modo oscuro/claro nativo de Streamlit.  
* **Componentes:**  
  * st.sidebar para la configuración de la rúbrica.  
  * st.text\_input para el nombre del alumno.  
  * st.file\_uploader para el Excel.  
  * st.columns para mostrar "Lo que hizo el alumno" vs "Lo que se esperaba".  
  * st.info para mostrar el feedback propuesto por la IA.