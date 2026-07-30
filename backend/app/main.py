from app.composition import build_create_job_use_case, build_get_job_use_case
from app.presentation.api.app import create_api

app = create_api(build_create_job_use_case(), build_get_job_use_case())
