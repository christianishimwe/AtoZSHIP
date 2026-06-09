from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from uuid import UUID
from app.api.schemas.seller import SellerRead
from app.database.models import Review, ShipmentEvent, ShipmentStatus, Tag


class BaseShipment(BaseModel):
    content: str
    weight: float | None = Field(le=25, default=None)
    destination: int


class ShipmentRead(BaseShipment):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    timeline: list[ShipmentEvent]
    estimated_delivery: datetime
    seller: SellerRead
    review: Review | None
    tags: list[Tag]


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


class ShipmentTagCreate(BaseModel):
    shipment_id: UUID
    tag_name: str
