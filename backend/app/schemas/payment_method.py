from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, field_validator

PaymentMethodType = Literal["card", "bank_account", "clabe", "other"]
PaymentMethodStatus = Literal["active", "inactive"]


class PaymentMethodCreate(BaseModel):
    type: PaymentMethodType
    alias: str
    institution: str
    currency: str
    identifier: str

    @field_validator("alias", "institution")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Este campo es requerido")
        return v.strip()

    @field_validator("currency")
    @classmethod
    def currency_format(cls, v: str) -> str:
        v = v.strip().upper()
        if len(v) != 3:
            raise ValueError("La moneda debe ser un código de 3 letras (ej. MXN, USD)")
        return v

    @field_validator("identifier")
    @classmethod
    def identifier_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("El identificador es requerido")
        return v


class PaymentMethodResponse(BaseModel):
    id: str
    type: str
    alias: str
    institution: str
    currency: str
    identifier_masked: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaymentMethodListItem(BaseModel):
    id: str
    type: str
    alias: str
    institution: str
    currency: str
    identifier_masked: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginatedPaymentMethods(BaseModel):
    items: list[PaymentMethodListItem]
    total: int
    page: int
    page_size: int
    pages: int
