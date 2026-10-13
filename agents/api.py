"""
FastAPI REST API Server for Lifetable Constructor.
"""
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .base import AuditLogger, PHIGuard
from .models import SystemTaskPayload, ConsensusDossier
from .supervisor import SystemSupervisor
from life_table import construct_life_table

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Lifetable Constructor API",
    description="Enterprise Distributed Component Platform (Clinical & Biomedical AI)",
    version="3.0.0-ENTERPRISE",
)


class ChatRequest(BaseModel):
    query: str


class LifeTableRequest(BaseModel):
    intervals: List[Dict[str, Any]]
    radix: float = 100_000


@app.post("/api/lifetable")
def api_lifetable(request: LifeTableRequest):
    """Compute a period life table without altering the legacy audit service."""
    try:
        table = construct_life_table(request.intervals, radix=request.radix)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"table": table, "age_at_entry": table[0]["age"], "life_expectancy": table[0]["ex"]}



@app.get("/health")
def health():
    return {"status": "HEALTHY", "service": "lifetable-constructor", "domain": "Clinical & Biomedical AI", "standard": "CAP / CLSI / ISO Standards", "version": "3.0.0-ENTERPRISE"}


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "system_status": "NOMINAL_OPTIMAL"
    }


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    dossier = supervisor.process_task(payload)
    return dossier.to_dict()


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        ans = supervisor.query_supervisory_chat(req.query)
        return {"response": ans}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/audit/logs")
def api_audit_logs():
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}
