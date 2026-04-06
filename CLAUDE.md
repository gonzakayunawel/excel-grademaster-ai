# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Excel-GradeMaster AI** is a Streamlit web app that automates grading of Excel-based tests. Its key differentiator is evaluating both **process (formulas)** and **result (values)** — a student can get partial credit for correct logic even with a wrong answer, and be penalized for hardcoding results without formulas.

## Commands

```bash
# Install dependencies
uv sync

# Run the app
uv run streamlit run main.py
```

No test framework is configured yet.

## Environment

Requires a `.env` file with:
```
GOOGLE_API_KEY=your_gemini_api_key
```

## Architecture

The app follows a three-phase flow controlled via `st.session_state`:

- **`app_mode`** drives the UI phase: `'CONFIGURACION'` → `'REVISION'` → `'REPORTE_FINAL'`
- **`lista_evaluados`**: accumulates confirmed student results
- **`estudiante_actual`**: holds in-progress data for the current student being reviewed

### Phase 1 — Configuration
Teacher defines a rubric per question: target cell (e.g. `B12`), expected formula string, expected value, and point weights for formula vs. value.

### Phase 2 — Review Cycle (per student)
For each student file uploaded:
1. **Dual extraction** using `openpyxl`: load twice — `data_only=False` for formulas, `data_only=True` for computed values.
2. **Scoring engine**: award formula points if student formula contains expected keywords; award value points if values match exactly.
3. **Gemini feedback**: send a structured prompt (see spec) to `gemini-1.5-flash`; the model returns 2-line pedagogical feedback in Spanish.
4. **Human-in-the-loop**: teacher sees editable fields for score and feedback before confirming.

### Phase 3 — Report
Consolidated table exported to CSV/Excel.

### Persistence (SQLite)
Three tables:
- `SesionRevision` — session metadata
- `ConfiguracionRubrica` — rubric per question per session
- `ResultadosEstudiantes` — final confirmed results with `detalle_json` storing edited feedback

## Conventions

- **Language**: UI text, documentation, variable names, and database fields are in **Spanish**.
- **UI layout**: `st.sidebar` for rubric config; `st.columns` for student vs. expected comparison; `st.info` for AI feedback.
- **openpyxl dual-load** is mandatory for every student file — load once with `data_only=False` and once with `data_only=True` to capture both formulas and calculated values.
- **Scoring edge cases** (per spec): partial credit for correct formula with wrong value; penalize hardcoded values without formula; detect carry-over errors to avoid double penalization.

## Key Files

- `main.py` — Streamlit entry point (currently a stub)
- `docs/Especificaciones_Excel_GradeMaster_AI.md` — Full Spanish-language spec with data model, UI requirements, and Gemini prompt template
- `pyproject.toml` — Dependencies (`streamlit`, `openpyxl`, and `google-genai` to be added)
