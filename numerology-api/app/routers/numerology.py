"""Numerology router assembly — combines paid + free/public sub-routers.

ORCHESTRATOR NOTE: wire in app/main.py with:
    from app.routers.numerology import numerology_router
    app.include_router(numerology_router)

Endpoints exposed:
    GET /api/so-hoc        — paid PDF (auth + quota)
    GET /api/so-hoc-free   — free PDF (public)
    GET /api/la-so         — astrology chart via vietheart.net
    GET /api/              — debug HTML preview
"""

from fastapi import APIRouter

from app.routers.numerology_paid import router as _paid_router
from app.routers.numerology_free import router as _free_router

# Primary router — prefix /api so endpoints are /api/so-hoc, /api/so-hoc-free, etc.
router = APIRouter(prefix='/api', tags=['numerology'])
router.include_router(_paid_router)
router.include_router(_free_router)

# Exported alias for orchestrator wiring in app/main.py
numerology_router = router
