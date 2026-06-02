from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes import auth, users, payment_methods

app = FastAPI(
    title="Wallet API",
    description="API segura para gestión de métodos de pago",
    version="1.0.0",
)

origins = [o.strip() for o in settings.ALLOWED_ORIGINS.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(payment_methods.router, prefix="/api")


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}
