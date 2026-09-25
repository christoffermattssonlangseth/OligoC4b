# Contributing

## Working Style

- Keep the repository notebook-first, but move repeated logic into reusable functions (`scripts/`) when a pattern appears in multiple notebooks.
- Put pipeline notebooks in `notebooks/build/` (prefix `build_`) and downstream notebooks in `notebooks/analysis/` (prefix `analysis_`). Notebooks read processed data from `../../data/` or the env vars in `.env.example`.
- Commit notebooks *with* outputs so results can be reviewed without re-running; keep figures modest in size.
- Prefer environment variables or repo-relative paths over machine-specific absolute paths.
- Do not commit raw data, secrets, or local cache directories.
- Preserve analytical intent when editing notebooks; avoid cosmetic churn in unrelated cells.

## Local Setup

```bash
conda env create -f environment.yml
conda activate oligoc4b
cp .env.example .env
```

Fill in only the variables needed for the notebooks you intend to run.

## Before Opening a PR

Run:

```bash
python scripts/check_notebooks.py
```

The checker validates notebook JSON, flags hard-coded user-home paths in source cells, rejects malformed environment-variable lookups, and verifies that referenced environment variables are documented in `.env.example`.

## Notebook Conventions

- Use descriptive markdown headers so the analysis story is readable without executing every cell.
- Keep dataset-specific configuration near the top of the notebook.
- If a notebook requires `OPENAI_API_KEY`, call that out in a markdown cell before the relevant code.
- When adding new environment variables, update both `.env.example` and `README.md`.
- When adding a notebook, add a row to `README.md` and a summary to `docs/notebooks.md`; put findings in `docs/complement_findings.md` rather than in the README.
