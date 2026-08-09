"""
Application entrypoint. Kept thin on purpose — wiring only, no business
logic. Routers are added here as we build each feature in later stages.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.action_items import router as action_items_router
from app.api.auth import router as auth_router
from app.api.emails import router as emails_router
from app.api.health import router as health_router
from app.core.config import settings
from app.core.logging import configure_logging

configure_logging()

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix=settings.api_v1_prefix)
app.include_router(auth_router, prefix=settings.api_v1_prefix)
app.include_router(emails_router, prefix=settings.api_v1_prefix)
app.include_router(action_items_router, prefix=settings.api_v1_prefix)
