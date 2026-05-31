"""Aggregate API router — sub-routers added per phase."""

from fastapi import APIRouter

router = APIRouter()

# Phase 03+: from app.routers import auth, users, numerology ...
# router.include_router(auth.router, prefix="/auth", tags=["auth"])
