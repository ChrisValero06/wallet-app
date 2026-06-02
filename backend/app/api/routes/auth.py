from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token, blacklist_token
from app.models.user import User
from app.schemas.user import UserRegister, UserLogin, UserResponse
from app.schemas.token import TokenResponse, MessageResponse
from app.api.deps import get_current_user, get_token
from app.services import audit_service

router = APIRouter(prefix="/auth", tags=["auth"])


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    return forwarded.split(",")[0] if forwarded else (request.client.host if request.client else "unknown")


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(body: UserRegister, request: Request, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El email ya está registrado")

    user = User(
        email=body.email,
        full_name=body.full_name,
        hashed_password=hash_password(body.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    audit_service.log(
        db, action="REGISTER", user_id=user.id,
        entity_type="user", entity_id=user.id,
        metadata={"email": user.email},
        ip_address=_client_ip(request),
    )
    return user


@router.post("/login", response_model=TokenResponse)
def login(body: UserLogin, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales incorrectas")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cuenta desactivada")

    token = create_access_token(subject=user.id)
    audit_service.log(
        db, action="LOGIN", user_id=user.id,
        entity_type="user", entity_id=user.id,
        ip_address=_client_ip(request),
    )
    return TokenResponse(access_token=token)


@router.post("/logout", response_model=MessageResponse)
def logout(
    request: Request,
    token: str = Depends(get_token),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    blacklist_token(token)
    audit_service.log(
        db, action="LOGOUT", user_id=current_user.id,
        entity_type="user", entity_id=current_user.id,
        ip_address=_client_ip(request),
    )
    return MessageResponse(message="Sesión cerrada exitosamente")
