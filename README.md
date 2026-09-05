# Lifetable Constructor

> **Domain:** Clinical Decision Support & Biomedical Computing  
> **Standards:** Standard Clinical Formulations & ISO/IEC Quality Frameworks

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

A clinical decision support system providing:

- **Abridged Life Table Constructor** (Chiang method: qx, lx, dx, ex with variance and 95% CI)
- **Clinical Scoring Modules**: MELD-Na, QTc (Bazett), BMI Z-score, HbA1c/eAG conversion, APRI/FIB-4
- **Enterprise Agent Framework**: Multi-worker consensus system with PHI guard and HMAC-SHA256 audit trail
- **FastAPI REST API** with Prometheus telemetry endpoints

---

## ⚙️ Core Clinical Functions

### MELD-Na Score (`calculate_meld_na`)
Calculates Model for End-Stage Liver Disease score with sodium adjustment.
```python
from lifetable import calculate_meld_na
result = calculate_meld_na(bilirubin=2.5, creatinine=1.2, inr=1.4, sodium=135)
# Returns: {"meld_na": 18.2, "meld_base": 15.4, "severity": "low"}
```

### QTc Interval (`calculate_qtc`)
Corrected QT interval using Bazett's formula.
```python
from lifetable import calculate_qtc
result = calculate_qtc(qt_ms=420, hr_bpm=72)
# Returns: {"qtc_ms": 458.2, "risk": "borderline", ...}
```

### BMI Z-Score (`calculate_bmi_z`)
Body Mass Index with age-adjusted Z-score (CDC/WHO reference).
```python
from lifetable import calculate_bmi_z
result = calculate_bmi_z(weight_kg=70, height_cm=175, age_months=120, sex="M")
# Returns: {"bmi": 22.86, "z_score": 1.24, "category": "normal"}
```

### HbA1c Conversion (`convert_hba1c`)
Converts between HbA1c (%) and estimated average glucose.
```python
from lifetable import convert_hba1c
result = convert_hba1c(hba1c_percent=7.0)
# Returns: {"hba1c_percent": 7.0, "eag_mgdl": 154.2, "eag_mmol_l": 8.57}
```

### APRI/FIB-4 (`calculate_apri_fib4`)
Liver fibrosis assessment scores.
```python
from lifetable import calculate_apri_fib4
result = calculate_apri_fib4(ast_u_l=80, alt_u_l=60, platelets_109=150, age_years=55)
# Returns: {"apri": 1.33, "fib4": 3.56, "fibrosis_risk": "high"}
```

### Row Assessment (`assess_row`)
Auto-detects input type and routes to the appropriate calculator.
```python
from lifetable import assess_row
result = assess_row({"bilirubin": 3.0, "creatinine": 1.5, "inr": 1.2, "sodium": 138})
```

---

## 💻 CLI Usage

### Single Calculation
```bash
# Using JSON input
python -m lifetable single --json '{"bilirubin": 2.5, "creatinine": 1.2, "inr": 1.4}'

# Using direct parameters
python -m lifetable single --bili 2.5 --creat 1.2 --inr 1.4 --na 135

# QTc calculation
python -m lifetable single --qt 420 --hr 72
```

### Batch CSV Processing
```bash
python -m lifetable batch --input sample.csv --output results.csv
```

### Enterprise Supervisor CLI
```bash
# Run audit evaluation
python cli.py audit --task-id TASK-001 --primary 28.5 --secondary 14.2

# Batch processing
python cli.py batch -i input.csv -o output.csv

# Verify audit trail
python cli.py verify-audit

# Launch API server
python cli.py serve --host 127.0.0.1 --port 8000
```

---

## 🛡️ Security Architecture

- **Zero-PHI Outbound Interceptor:** AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers
- **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation
- **Path Traversal Protection:** Input/output path validation prevents directory traversal attacks
- **Secure Defaults:** Audit key must be set via `AUDIT_SECRET_KEY` environment variable in production

### Environment Variables
| Variable | Description | Required |
|:---------|:------------|:---------|
| `AUDIT_SECRET_KEY` | HMAC-SHA256 key for audit trail signing | Recommended |

---

## 🧪 Testing

Run the full test suite:
```bash
pytest -v
```

Run with coverage:
```bash
pytest -v --cov=. --cov-report=term-missing
```

---

## 🐳 Docker Deployment

```bash
docker build -t lifetable-constructor .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY=your-secret-key lifetable-constructor
```

---

## 📁 Project Structure

```
lifetable-constructor/
├── lifetable.py          # Core clinical calculation functions
├── cli.py                # Enterprise CLI with supervisor framework
├── agents/               # Multi-agent consensus system
│   ├── base.py           # PHI guard, audit trail, security
│   ├── models.py         # Pydantic data models
│   ├── supervisor.py     # Orchestrator for worker agents
│   ├── workers.py        # Specialized evaluation workers
│   ├── api.py            # FastAPI REST endpoints
│   ├── metrics.py        # Prometheus metrics collector
│   ├── llm_factory.py    # LLM provider abstraction
│   ├── learning.py       # Bayesian calibration engine
│   └── streamer.py       # WebSocket telemetry broadcaster
├── tests/                # Test suite
├── web/                  # Operations console (HTML)
├── Dockerfile            # Container definition
└── docker-compose.yml    # Multi-service orchestration
```

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.
