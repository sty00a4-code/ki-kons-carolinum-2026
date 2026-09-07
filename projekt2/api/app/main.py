from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import analysis, osce, patients, students, treatment_cases

app = FastAPI(
    title="Leistungsübersicht API",
    description="Backend für die klinische Kompetenz- und Lernverlaufsanalyse.",
    version="0.1.0",
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
app.include_router(patients.router)
app.include_router(treatment_cases.router)
app.include_router(osce.router)
app.include_router(analysis.router)


@app.get("/health")
def health():
    return {"status": "ok"}
