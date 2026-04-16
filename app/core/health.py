# app/health.py
import time
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from app.db.session import AsyncSessionLocal
from app.core.app_state import app_state

router = APIRouter()

async def check_db() -> dict:
    start = time.monotonic()
    try:
        db = AsyncSessionLocal()
        await db.execute(text("SELECT 1"))
        await db.close()
        return {
            "status": "ok",
            "latency_ms": round((time.monotonic() - start) * 1000, 2),
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/health", tags=["ops"])
async def health_check():
    db_result  = await check_db()
    app_errors = app_state.get_errors()

    db_ok  = db_result["status"] == "ok"
    app_ok = not app_errors

    # Three-tier status
    if db_ok and app_ok:
        overall, http_status = "healthy", status.HTTP_200_OK
    elif db_ok and not app_ok:
        overall, http_status = "degraded", status.HTTP_200_OK   # ①
    else:
        overall, http_status = "unhealthy", status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=http_status,
        content={
            "status": overall,
            "checks": {
                "database": db_result,
                "application": {
                    "status": "ok" if app_ok else "degraded",
                    "errors": app_errors,
                },
            },
        },
    )
