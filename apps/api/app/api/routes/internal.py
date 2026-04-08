from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from app.services.storage import storage_service

router = APIRouter(prefix="/internal", tags=["internal"])


@router.get("/files")
def get_signed_file(token: str = Query(...)) -> FileResponse:
    try:
        path = storage_service.resolve_signed_token(token)
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=403, detail="Invalid token") from exc
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path)
