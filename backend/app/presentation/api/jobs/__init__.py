from fastapi import APIRouter

from app.presentation.api.jobs.create_job import router as create_job_router
from app.presentation.api.jobs.get_job import router as get_job_router

router = APIRouter()
router.include_router(create_job_router)
router.include_router(get_job_router)
