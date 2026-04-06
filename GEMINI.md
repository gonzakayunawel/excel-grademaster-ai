# GEMINI.md - Instructional Context for Excel-GradeMaster AI

## Project Overview
**Excel-GradeMaster AI** is an automated grading assistant for Excel tests. It differentiates itself by evaluating both the **process (formulas)** and the **result (values)**. 

### Key Technologies:
- **Language:** Python 3.11+
- **UI Framework:** [Streamlit](https://streamlit.io/)
- **Excel Engine:** `openpyxl` (for dual extraction of formulas and data)
- **Database:** SQLite (for persistence of rubrics and results)
- **AI Engine:** Google Gemini API (`gemini-1.5-flash`)
- **Dependency Management:** `uv`

### Architecture:
1.  **Phase 1: Configuration**: Teacher defines the rubric (target cells, expected formulas, expected values, and scoring).
2.  **Phase 2: Review Cycle**: 
    - Student file upload.
    - Dual extraction (Formulas vs. Values).
    - Automated scoring based on logic.
    - AI-generated pedagogical feedback via Gemini.
    - **Human-in-the-Loop**: Teacher validates or edits scores and feedback.
3.  **Phase 3: Final Report**: Exporting consolidated results to CSV/Excel.

## Building and Running

### Prerequisites:
- Python 3.11 or higher.
- `uv` installed on your system.

### Setup:
1.  Install dependencies:
    ```bash
    uv sync
    ```

### Running the App:
```bash
uv run streamlit run main.py
```

### Environment Variables:
A `.env` file is required for the Gemini API key (refer to `docs/Especificaciones_Excel_GradeMaster_AI.md` for details if needed).
- `GOOGLE_API_KEY`: Your Gemini API key.

## Development Conventions

### Coding Style:
- Follow standard Python (PEP 8) conventions.
- Use Streamlit's `session_state` for managing the application's multi-step flow.
- Maintain Spanish for UI elements and documentation as per project requirements.

### Excel Processing:
- When using `openpyxl`, ensure dual-loading of workbooks:
    - `load_workbook(filename, data_only=False)` to read formulas.
    - `load_workbook(filename, data_only=True)` to read calculated values.

### Database:
- Use SQLite for persistent storage.
- Tables should include `SesionRevision`, `ConfiguracionRubrica`, and `ResultadosEstudiantes`.

### Testing:
- (TODO: Add testing framework and commands once implemented).

## Key Files:
- `main.py`: Entry point for the Streamlit application.
- `docs/Especificaciones_Excel_GradeMaster_AI.md`: Detailed project specifications and requirements (Spanish).
- `pyproject.toml`: Project metadata and dependencies.
- `uv.lock`: Locked dependency versions.
