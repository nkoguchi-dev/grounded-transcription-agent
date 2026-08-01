from fastapi import APIRouter

from app.presentation.api.artifacts.complete_upload import router as complete_router
from app.presentation.api.artifacts.create_download_url import (
    router as download_url_router,
)
from app.presentation.api.artifacts.get_artifact import router as get_router
from app.presentation.api.artifacts.start_upload import router as start_router

router = APIRouter()
router.include_router(start_router)
router.include_router(complete_router)
router.include_router(get_router)
router.include_router(download_url_router)
