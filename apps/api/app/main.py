from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.about import router as about_router
from app.api.routes.analyses import router as analyses_router
from app.api.routes.events import router as events_router
from app.api.routes.internal import router as internal_router
from app.api.routes.metrics import router as metrics_router
from app.api.routes.reports import router as reports_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.db.session import Base, engine

configure_logging()
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name, version="3.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(reports_router)
app.include_router(analyses_router)
app.include_router(about_router)
app.include_router(events_router)
app.include_router(metrics_router)
app.include_router(internal_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": "3.0.0"}
