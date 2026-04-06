# Excel-GradeMaster AI 📊

[**Español**](#español) | [**English**](#english)

---

## Español

**Excel-GradeMaster AI** es un asistente pedagógico inteligente diseñado para automatizar la calificación de pruebas de Microsoft Excel. A diferencia de otros calificadores, este sistema evalúa tanto el **proceso (fórmulas)** como el **resultado (valores)**, proporcionando feedback motivador generado por IA.

### ✨ Características Principales
- **Extracción Dual:** Lee simultáneamente fórmulas y valores calculados usando `openpyxl`.
- **Calificación Flexible:** Sistema de puntuación que diferencia entre errores de lógica y errores de resultado.
- **Feedback con IA:** Integración con Google Gemini para generar comentarios pedagógicos personalizados.
- **Flujo de Trabajo Completo:** Desde la configuración de la rúbrica hasta el reporte final exportable.
- **Interfaz Intuitiva:** Desarrollado con Streamlit para una experiencia de usuario fluida.

### 🚀 Instalación y Uso
1. **Requisitos:** Python 3.11+ y `uv`.
2. **Instalar dependencias:**
   ```bash
   uv sync
   ```
3. **Configurar API Key:** 
   Crea un archivo `.env` con tu clave de Gemini: `GOOGLE_API_KEY=tu_clave_aqui`.
4. **Ejecutar:**
   ```bash
   uv run streamlit run main.py
   ```

---

## English

**Excel-GradeMaster AI** is an intelligent pedagogical assistant designed to automate the grading of Microsoft Excel tests. Unlike other graders, this system evaluates both the **process (formulas)** and the **result (values)**, providing AI-generated motivational feedback.

### ✨ Key Features
- **Dual Extraction:** Simultaneously reads formulas and calculated values using `openpyxl`.
- **Flexible Scoring:** A scoring system that distinguishes between logic errors and result errors.
- **AI Feedback:** Integration with Google Gemini to generate personalized pedagogical comments.
- **Full Workflow:** From rubric configuration to final exportable reports.
- **Intuitive Interface:** Developed with Streamlit for a smooth user experience.

### 🚀 Installation and Usage
1. **Requirements:** Python 3.11+ and `uv`.
2. **Install dependencies:**
   ```bash
   uv sync
   ```
3. **Configure API Key:** 
   Create a `.env` file with your Gemini key: `GOOGLE_API_KEY=your_key_here`.
4. **Run:**
   ```bash
   uv run streamlit run main.py
   ```

### 🛠️ Tech Stack
- **UI:** Streamlit
- **Excel Engine:** openpyxl
- **Database:** SQLite
- **AI:** Google Gemini API
- **Manager:** uv
