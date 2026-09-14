from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import engine
from .routers import (
    analysis,
    assignments,
    classes,
    osce,
    patients,
    semesters,
    students,
    treatment_cases,
)
from .schema_updates import ensure_schema


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Ergänzt beim Start fehlende Spalten und Tabellen (siehe schema_updates.py)."""
    ensure_schema(engine)
    yield


app = FastAPI(
    title="Leistungsübersicht API",
    description="Backend für die klinische Kompetenz- und Lernverlaufsanalyse.",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS: solange UI und API auf demselben Host laufen ist das nicht zwingend
# nötig, aber für lokale Entwicklung (Streamlit auf anderem Port) hilfreich.
# Für Produktion auf die tatsächliche UI-Domain einschränken.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(students.router)
app.include_router(classes.router)
app.include_router(semesters.router)
app.include_router(patients.router)
app.include_router(assignments.router)
app.include_router(treatment_cases.router)
app.include_router(osce.router)
app.include_router(analysis.router)


@app.get("/health")
def health():
    return {"status": "ok"}
