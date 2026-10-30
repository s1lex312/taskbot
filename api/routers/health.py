"""Health-check endpoint."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe used by docker, CI and humans."""
    return {"status": "ok"}
