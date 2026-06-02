import math
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.payment_method import PaymentMethod
from app.models.user import User
from app.schemas.payment_method import (
    PaymentMethodCreate, PaymentMethodResponse,
    PaymentMethodListItem, PaginatedPaymentMethods,
)
from app.api.deps import get_current_user
from app.services import audit_service, encryption_service

router = APIRouter(prefix="/payment-methods", tags=["payment-methods"])


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    return forwarded.split(",")[0] if forwarded else (request.client.host if request.client else "unknown")


def _to_response(pm: PaymentMethod) -> PaymentMethodResponse:
    return PaymentMethodResponse(
        id=pm.id,
        type=pm.type,
        alias=pm.alias,
        institution=pm.institution,
        currency=pm.currency,
        identifier_masked=encryption_service.mask_identifier(
            f"{'*' * 12}{pm.identifier_last4}", pm.type
        ),
        status=pm.status,
        created_at=pm.created_at,
        updated_at=pm.updated_at,
    )


def _to_list_item(pm: PaymentMethod) -> PaymentMethodListItem:
    return PaymentMethodListItem(
        id=pm.id,
        type=pm.type,
        alias=pm.alias,
        institution=pm.institution,
        currency=pm.currency,
        identifier_masked=f"**** {pm.identifier_last4}",
        status=pm.status,
        created_at=pm.created_at,
    )


@router.get("", response_model=PaginatedPaymentMethods)
def list_payment_methods(
    page: int = 1,
    page_size: int = 10,
    status_filter: str | None = None,
    type_filter: str | None = None,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if page < 1:
        page = 1
    if page_size < 1 or page_size > 100:
        page_size = 10

    q = db.query(PaymentMethod).filter(
        PaymentMethod.user_id == current_user.id,
        PaymentMethod.is_deleted.is_(False),
    )
    if status_filter:
        q = q.filter(PaymentMethod.status == status_filter)
    if type_filter:
        q = q.filter(PaymentMethod.type == type_filter)

    total = q.count()
    items = q.order_by(PaymentMethod.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return PaginatedPaymentMethods(
        items=[_to_list_item(pm) for pm in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


@router.post("", response_model=PaymentMethodResponse, status_code=status.HTTP_201_CREATED)
def create_payment_method(
    body: PaymentMethodCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    id_hash = encryption_service.hash_identifier(body.identifier)

    existing = db.query(PaymentMethod).filter(
        PaymentMethod.user_id == current_user.id,
        PaymentMethod.type == body.type,
        PaymentMethod.identifier_hash == id_hash,
        PaymentMethod.is_deleted.is_(False),
    ).first()
    if existing:
        audit_service.log(
            db, action="DUPLICATE_ATTEMPT", user_id=current_user.id,
            entity_type="payment_method",
            metadata={"type": body.type, "alias": body.alias},
            ip_address=_client_ip(request),
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un método de pago con ese identificador",
        )

    clean = body.identifier.strip()
    pm = PaymentMethod(
        user_id=current_user.id,
        type=body.type,
        alias=body.alias,
        institution=body.institution,
        currency=body.currency,
        identifier_encrypted=encryption_service.encrypt(clean),
        identifier_hash=id_hash,
        identifier_last4=clean[-4:] if len(clean) >= 4 else clean,
    )
    db.add(pm)
    db.commit()
    db.refresh(pm)

    audit_service.log(
        db, action="CREATE_PAYMENT_METHOD", user_id=current_user.id,
        entity_type="payment_method", entity_id=pm.id,
        metadata={"alias": pm.alias, "type": pm.type, "institution": pm.institution},
        ip_address=_client_ip(request),
    )
    return _to_response(pm)


@router.get("/{pm_id}", response_model=PaymentMethodResponse)
def get_payment_method(
    pm_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    pm = db.get(PaymentMethod, pm_id)
    if not pm or pm.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Método de pago no encontrado")
    if pm.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso no autorizado")

    audit_service.log(
        db, action="VIEW_PAYMENT_METHOD", user_id=current_user.id,
        entity_type="payment_method", entity_id=pm.id,
        metadata={"alias": pm.alias},
        ip_address=_client_ip(request),
    )
    return _to_response(pm)


@router.delete("/{pm_id}", response_model=PaymentMethodResponse)
def delete_payment_method(
    pm_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    pm = db.get(PaymentMethod, pm_id)
    if not pm or pm.is_deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Método de pago no encontrado")
    if pm.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso no autorizado")

    pm.is_deleted = True
    pm.status = "inactive"
    db.commit()
    db.refresh(pm)

    audit_service.log(
        db, action="DELETE_PAYMENT_METHOD", user_id=current_user.id,
        entity_type="payment_method", entity_id=pm.id,
        metadata={"alias": pm.alias, "type": pm.type},
        ip_address=_client_ip(request),
    )
    return _to_response(pm)
