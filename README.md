# Lifetable Constructor

A reproducible **abridged period life-table calculator** from age-specific central mortality rates. Includes a standalone browser app, Python command-line engine, and the repository's existing clinical-calculator and audit services.

## Life-table calculation

Supply a CSV with `age,mx` and optionally `ax`:

```csv
age,mx,ax
0,0.005,0.1
1,0.0005,
5,0.0002,
15,0.0007,
25,0.001,
35,0.002,
45,0.004,
55,0.009,
65,0.02,
75,0.05,
85,0.12,
```

`age` denotes each interval's start, `mx` the central death rate per person-year, and optional `ax` the mean time lived in the interval by people dying there. Ages must increase strictly; interval widths are inferred from successive ages. Blank `ax` defaults to half the closed interval width. The final row is **open-ended** and must have `mx > 0` and blank `ax`. The default radix is 100,000.

The Chiang-type calculation uses `qx = n·mx / [1 + (n−ax)·mx]` (capped at 1), `dx = lx·qx`, `Lx = n·l(x+n) + ax·dx`, `Tx = sum(Ly)` for `y ≥ x`, and `ex = Tx/lx`. For the final open interval, `qx = 1` and `Lx = lx/mx`. Results include `age,width,mx,ax,qx,lx,dx,Lx,Tx,ex`. A blank `ex` means no life-table survivors remain.

These are **period-life-table estimates**, not individual mortality predictions. Half-interval defaults (particularly for infancy) may not suit all datasets; supply empirically justified `ax` values when available. Confidence intervals are not estimated because age-specific rates alone do not determine their sampling uncertainty.

## Browser app

Open `web/index.html` through a static web server (or use the GitHub Pages deployment when enabled). Paste or upload a CSV, calculate a life table, inspect the survival plot and table, and download CSV results. All calculations and uploaded data remain in the browser; no external services are contacted. The browser implementation uses vanilla JavaScript; **Pyodide is not required**.

## Python

Python 3.10+; no third-party packages are required for the life-table engine:

```bash
python -m life_table mortality.csv results.csv
python -m life_table mortality.csv results.csv --radix 100000
```

To serve the browser interface locally:

```bash
python -m http.server 8001 --directory web
# Visit http://localhost:8001/
```

The original clinical scoring CLI remains in `lifetable.py` (`python -m lifetable --help`), and the existing audit CLI/API remains in `cli.py` (`python cli.py --help`). These legacy modules are **separate** from the period life-table method; their output is not a life table. The API also offers `POST /api/lifetable` with JSON `{"intervals":[{"age":0,"mx":0.02},{"age":5,"mx":0.02}],"radix":100000}`.

## Backend and tests

The optional FastAPI service needs FastAPI, Uvicorn and Pydantic v2:

```bash
python -m pip install 'fastapi>=0.111,<1' 'uvicorn>=0.30,<1' 'pydantic>=2,<3' pytest
python -m pytest -q
node --test web/test-app.mjs   # Node.js 22+
python cli.py serve --host 127.0.0.1 --port 8000
```

A Docker image is also provided. Set `AUDIT_SECRET_KEY` to a securely generated value in the environment before running `docker compose up --build`. The API's `/health` endpoint can be used for readiness checks. A missing audit key results in a random, runtime-only key and audit-chain verification will not persist across restarts.

## Privacy, limitations and compatibility

The browser life-table calculator works in current Chromium, Firefox and Safari-compatible browsers with JavaScript enabled. Files are not uploaded. The separate API processes data server-side and should not be exposed publicly without access controls. The existing regex-based identifier filter is **not** a HIPAA de-identification guarantee. The old mock-audit and clinical-scoring modules are preserved for compatibility but are not validated medical decision systems.

## License

MIT — see [LICENSE](LICENSE).