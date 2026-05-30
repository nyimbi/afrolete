from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.experience import (
    ProductExperienceCatalogRead,
    ProductExperienceDashboardRead,
    ProductHelpSearchRead,
    ProductTourProgressCreate,
    ProductTourProgressRead,
    ProductTourStepUpdate,
)
from app.services.auth.dependencies import get_current_identity
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService, get_authorization_service
from app.services.experience import (
    list_product_tour_progress,
    product_experience_catalog,
    product_experience_dashboard,
    product_tour_progress_read,
    search_product_help,
    start_product_tour_progress,
    update_product_tour_step,
)

router = APIRouter(prefix="/experience", tags=["experience"])


@router.get("/catalog", response_model=ProductExperienceCatalogRead)
async def product_experience_catalog_route(
    surface: str | None = Query(default=None),
    role: str | None = Query(default=None),
) -> ProductExperienceCatalogRead:
    return ProductExperienceCatalogRead(**product_experience_catalog(surface, role))


@router.post("/tours/progress", response_model=ProductTourProgressRead, status_code=status.HTTP_201_CREATED)
async def start_product_tour_progress_route(
    payload: ProductTourProgressCreate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> ProductTourProgressRead:
    progress = await start_product_tour_progress(db, identity, payload, authz)
    return ProductTourProgressRead(**await product_tour_progress_read(db, progress))


@router.post("/tours/progress/{progress_id}/steps", response_model=ProductTourProgressRead)
async def update_product_tour_step_route(
    progress_id: UUID,
    payload: ProductTourStepUpdate,
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> ProductTourProgressRead:
    progress = await update_product_tour_step(db, identity, progress_id, payload, authz)
    return ProductTourProgressRead(**await product_tour_progress_read(db, progress))


@router.get("/tours/progress", response_model=list[ProductTourProgressRead])
async def list_product_tour_progress_route(
    organization_id: UUID = Query(),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> list[ProductTourProgressRead]:
    return [
        ProductTourProgressRead(**await product_tour_progress_read(db, progress))
        for progress in await list_product_tour_progress(db, identity, organization_id, authz)
    ]


@router.get("/help/search", response_model=ProductHelpSearchRead)
async def search_product_help_route(
    q: str = Query(default="", max_length=500),
    organization_id: UUID | None = Query(default=None),
    surface: str | None = Query(default=None),
    role: str | None = Query(default=None),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
) -> ProductHelpSearchRead:
    return ProductHelpSearchRead(
        **await search_product_help(
            db,
            identity,
            q,
            organization_id=organization_id,
            surface=surface,
            role=role,
        )
    )


@router.get("/dashboard", response_model=ProductExperienceDashboardRead)
async def product_experience_dashboard_route(
    organization_id: UUID = Query(),
    identity: CurrentIdentity = Depends(get_current_identity),
    db: AsyncSession = Depends(get_db),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> ProductExperienceDashboardRead:
    return ProductExperienceDashboardRead(
        **await product_experience_dashboard(db, identity, organization_id, authz)
    )
