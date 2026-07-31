from datetime import datetime
from enum import Enum
from turtle import back

from fastapi import HTTPException, status
from pydantic import EmailStr
from sqlalchemy import Column, select
from sqlmodel import Field, Relationship, SQLModel
from uuid import uuid4, UUID
from sqlalchemy.dialects import postgresql
from sqlalchemy import ARRAY, INTEGER
from sqlalchemy.ext.asyncio import AsyncSession


class ShipmentStatus(str, Enum):
    placed = "placed"
    shipped = "shipped"
    in_transit = "in_transit"
    delivered = "delivered"
    cancelled = "cancelled"


class ShipmentTagLink(SQLModel, table=True):
    __tablename__ = "shipment_tag_link"
    shipment_id: UUID = Field(
        foreign_key="shipment.id",
        primary_key=True
    )
    tag_id: UUID = Field(
        foreign_key="tag.id",
        primary_key=True
    )


class PartnerLocationLink(SQLModel, table=True):
    __tablename__ = "partner_location_link"
    delivery_partner_id: UUID = Field(
        foreign_key="delivery_partner.id",
        primary_key=True
    )
    location_id: int = Field(
        foreign_key="location.zip_code",
        primary_key=True
    )


class Tag(SQLModel, table=True):
    __tablename__ = "tag"
    id: UUID = Field(
        sa_column=Column(
            postgresql.UUID,
            default=uuid4,
            primary_key=True
        )
    )
    name: str
    instructions: str | None = Field(default=None)
    shipments: list["Shipment"] = Relationship(
        back_populates="tags",
        link_model=ShipmentTagLink,
        sa_relationship_kwargs={"lazy": "immediate"}
    )


class Shipment(SQLModel, table=True):
    __tablename__ = "shipment"
    # none here allows us to create a new shipment without providing an id, and the database will auto-generate it
    id: UUID = Field(
        sa_column=Column(
            postgresql.UUID,
            default=uuid4,
            primary_key=True
        )
    )

    client_contact_email: EmailStr | None = Field(default=None)
    cleint_contact_phone: int | None = Field(default=None)

    content: str
    weight: float = Field(le=25)
    destination: int
    estimated_delivery: datetime

    created_at: datetime = Field(
        sa_column=Column(
            postgresql.TIMESTAMP,
            default=datetime.now,
        )
    )
    timeline: list["ShipmentEvent"] = Relationship(
        back_populates="shipment",
        sa_relationship_kwargs={"lazy": "selectin"}
    )
    seller_id: UUID = Field(foreign_key="seller.id")
    seller: "Seller" = Relationship(
        back_populates="shipments",
        sa_relationship_kwargs={"lazy": "selectin"}
    )
    delivery_partner_id: UUID = Field(foreign_key="delivery_partner.id")
    delivery_partner: "DeliveryPartner" = Relationship(
        back_populates="shipments",
        sa_relationship_kwargs={"lazy": "selectin"}
    )
    review: "Review" = Relationship(
        back_populates="shipment",
        sa_relationship_kwargs={"lazy": "selectin"}
    )

    tags: list["Tag"] = Relationship(
        back_populates="shipments",
        link_model=ShipmentTagLink,
        sa_relationship_kwargs={"lazy": "immediate"}
    )

    @property
    def status(self):
        self.timeline[-1].status if len(self.timeline) > 0 else None


class ShipmentEvent(SQLModel, table=True):
    __tablename__ = "shipment_event"
    id: UUID = Field(
        sa_column=Column(
            postgresql.UUID,
            default=uuid4,
            primary_key=True
        )
    )
    created_at: datetime = Field(
        sa_column=Column(
            postgresql.TIMESTAMP,
            default=datetime.now,
        )
    )
    location: int
    status: ShipmentStatus
    description: str | None = Field(default=None)
    shipment_id: UUID = Field(foreign_key="shipment.id")
    shipment: Shipment = Relationship(
        back_populates="timeline",
        sa_relationship_kwargs={"lazy": "selectin"})


class User(SQLModel):
    name: str
    email: EmailStr
    email_verified: bool | None = Field(default=False)
    password_hash: str = Field(exclude=True)


class Seller(User, table=True):
    __tablename__ = "seller"
    id: UUID = Field(
        sa_column=Column(
            postgresql.UUID,
            default=uuid4,
            primary_key=True
        )
    )
    created_at: datetime = Field(
        sa_column=Column(
            postgresql.TIMESTAMP,
            default=datetime.now,
        )
    )
    address: str | None = Field(default=None)
    zip_code: int | None = Field(default=None)
    shipments: list[Shipment] = Relationship(
        back_populates="seller",
        sa_relationship_kwargs={"lazy": "selectin"}
    )


class DeliveryPartner(User, table=True):
    __tablename__ = "delivery_partner"
    id: UUID = Field(
        sa_column=Column(
            postgresql.UUID,
            default=uuid4,
            primary_key=True
        )
    )
    created_at: datetime = Field(
        sa_column=Column(
            postgresql.TIMESTAMP,
            default=datetime.now,
        )
    )
    serviceable_locations: list["Location"] = Relationship(
        back_populates="delivery_partners",
        sa_relationship_kwargs={"lazy": "immediate"},
        link_model=PartnerLocationLink
    )
    max_handling_capacity: int
    shipments: list[Shipment] = Relationship(
        back_populates="delivery_partner",
        sa_relationship_kwargs={"lazy": "selectin"}
    )

    @property
    def active_shipments(self):
        return [
            shipment for shipment in self.shipments
            if shipment.status != ShipmentStatus.delivered
            or shipment.status != ShipmentStatus.cancelled
        ]

    @property
    def current_handling_capacity(self):
        return self.max_handling_capacity - len(self.active_shipments)


class Location(SQLModel, table=True):
    __tablename__ = "location"
    zip_code: int = Field(primary_key=True)
    name: str | None = Field(default=None)
    delivery_partners: list[DeliveryPartner] = Relationship(
        back_populates="serviceable_locations",
        sa_relationship_kwargs={"lazy": "immediate"},
        link_model=PartnerLocationLink
    )


class Review(SQLModel, table=True):
    __tablename__ = "review"
    id: UUID = Field(
        sa_column=Column(
            postgresql.UUID,
            default=uuid4,
            primary_key=True
        )
    )
    created_at: datetime = Field(
        sa_column=Column(
            postgresql.TIMESTAMP,
            default=datetime.now,
        )
    )
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None)
    shipment_id: UUID = Field(foreign_key="shipment.id")
    shipment: Shipment = Relationship(
        back_populates="review",
        sa_relationship_kwargs={"lazy": "selectin"}
    )
