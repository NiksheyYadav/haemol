from __future__ import annotations

from fastapi import Depends, Header, HTTPException, status

from app.core.config import settings


def verify_admin_metrics_token(authorization: str | None = Header(default=None)) -> None:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    if token != settings.admin_metrics_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid bearer token")


AdminMetricsAuth = Depends(verify_admin_metrics_token)
