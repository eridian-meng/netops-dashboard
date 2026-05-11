from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .catalog import CatalogError, CatalogService
from .config import get_settings
from .jobs import JobStore, run_job
from .models import CatalogResponse, JobCreateRequest, ProviderName
from .sessions import SessionIdentityMiddleware, get_operator, get_operator_identity
from .providers.registry import build_providers


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="NetOps Automation Dashboard", version="0.1.0")
    app.add_middleware(SessionIdentityMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    catalog_service = CatalogService(settings)
    job_store = JobStore(settings)
    providers = build_providers(settings)

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/session")
    def session(identity=Depends(get_operator_identity)):
        return {
            "operatorKey": identity.key,
            "operatorLabel": identity.label,
            "source": identity.source,
        }

    @app.get("/api/catalog", response_model=CatalogResponse)
    def catalog() -> CatalogResponse:
        try:
            return CatalogResponse(items=catalog_service.load())
        except CatalogError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.get("/api/auth/providers")
    def auth_providers(operator: str = Depends(get_operator)):
        return {"providers": [provider.status(operator) for provider in providers.values()]}

    @app.post("/api/auth/aws/start")
    def start_aws_login(operator: str = Depends(get_operator)):
        return providers[ProviderName.aws].start_login(operator)

    @app.get("/api/auth/aws/status")
    def aws_status(operator: str = Depends(get_operator)):
        return providers[ProviderName.aws].status(operator)

    @app.post("/api/jobs")
    def create_job(
        request: JobCreateRequest,
        background_tasks: BackgroundTasks,
        operator: str = Depends(get_operator),
    ):
        try:
            item = catalog_service.find_item(request.catalogItemId)
            catalog_service.resolve_script(item)
        except CatalogError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        if item.auth.get("required") and item.provider != ProviderName.generic:
            provider = providers.get(item.provider)
            status = provider.status(operator) if provider else None
            if not status or not status.authenticated:
                raise HTTPException(
                    status_code=401,
                    detail=f"{item.provider.value.upper()} authentication is required before running this service.",
                )

        job = job_store.create(item, operator)
        background_tasks.add_task(run_job, job.id, catalog_service, job_store, providers)
        return job

    @app.get("/api/jobs/{job_id}")
    def get_job(job_id: str):
        try:
            return job_store.get(job_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Job not found") from exc

    @app.get("/api/jobs/{job_id}/artifacts/{artifact_id}")
    def download_artifact(job_id: str, artifact_id: str):
        try:
            path = job_store.artifact_path(job_id, artifact_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Artifact not found") from exc
        return FileResponse(path, filename=path.name)

    return app


app = create_app()
