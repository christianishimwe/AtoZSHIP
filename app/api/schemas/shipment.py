from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from app.api.schemas.seller import SellerRead
from app.database.models import Review, Seller, ShipmentEvent, ShipmentStatus


class BaseShipment(BaseModel):
    content: str
    weight: float | None = Field(le=25, default=None)
    destination: int


class ShipmentRead(BaseShipment):
    id: UUID
    timeline: list[ShipmentEvent]
    estimated_delivery: datetime
    seller: SellerRead
    review: Review


class ShipmentCreate(BaseShipment):
    client_contact_email: EmailStr
    client_contact_phone: int | None = Field(default=None)


class ShipmentUpdate(BaseModel):
    location: int | None = Field(default=None)
    description: str | None = Field(default=None)
    status: ShipmentStatus | None = Field(default=None)
    estimated_delivery: datetime | None = Field(default=None)


class ShipmentReview(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None)
