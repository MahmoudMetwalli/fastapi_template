"""Aggregates every context's router under one prefix. Add one line per
context as it's created — mirrors `shared/infrastructure/database/registry.py`.
"""

from fastapi import APIRouter

from app.contexts.catalog.presentation.router import router as catalog_router
from app.contexts.ordering.presentation.router import router as ordering_router

api_router = APIRouter()
api_router.include_router(catalog_router)
api_router.include_router(ordering_router)
