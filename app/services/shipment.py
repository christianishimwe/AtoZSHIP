from datetime import datetime, timedelta
from email.policy import HTTP

from fastapi import HTTPException, status
from app.api.schemas.shipment import ShipmentCreate, ShipmentUpdate, ShipmentReview
from app.database.models import DeliveryPartner, Review, Seller, Shipment, ShipmentStatus, Tag
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any
from uuid import UUID

from app.services.shipment_event import ShipmnentEventService

from .delivery_partner import DeliveryPartnerService

from .base import BaseService


class ShipmentService(BaseService):
    def __init__(
            self,
            session: AsyncSession,
            partner_service: DeliveryPartnerService,
            event_service: ShipmnentEventService,
    ):
        super().__init__(Shipment, session)
        self.partner_service = partner_service
        self.event_service = event_service

    async def get(self, id: UUID) -> Shipment:
        shipment = await self._get(id)
        if not shipment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="shipment not found"
            )
        return shipment

    async def add(self, shipment_create: ShipmentCreate, seller: Seller) -> Shipment:
        new_shipment = Shipment(**shipment_create.model_dump(),
                                estimated_delivery=datetime.now() + timedelta(days=3),
                                seller_id=seller.id
                                )
        # assign delivery partnere to the shipment
        partner = await self.partner_service.assign_shipment(
            new_shipment)

        # add the delivery partner
        new_shipment.delivery_partner_id = partner.id

        shipment = await self._add(new_shipment)

        # add a new event for this shipment
        await self.event_service.add(
            shipment=new_shipment,
            location=seller.zip_code,
            status=ShipmentStatus.placed,
            description=f"assigned to a delivery partner {partner.name}")
        return shipment

    # update an existing shipment
    async def update(self, id: UUID, shipment_update: ShipmentUpdate, partner: DeliveryPartner) -> Shipment | None:
        # validate the logged in partner with assigned partner
        # on teh shipment with given id
        shipment = await self.get(id)

        if not shipment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="shipment not found"
            )
        if shipment.delivery_partner_id != partner.id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authorized"
            )
        update = shipment_update.model_dump(exclude_none=True)

        # update the estimated delivery
        if shipment_update.estimated_delivery:
            shipment.estimated_delivery = shipment_update.estimated_delivery

        # only create an event if there is another update field other than just estimated delivery
        if len(update) > 1 or not shipment_update.estimated_delivery:
            await self.event_service.add(
                shipment=shipment,
                **update,
            )
        return await self._update(shipment)

    async def cancel(self, id: UUID, seller: Seller) -> Shipment:
        # validate if the seller trying to cancel is the one that initiated the shipment
        shipment = await self.get(id)
        if shipment.seller_id != seller.id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not Authorized"
            )
        # create the event
        event = await self.event_service.add(
            shipment=shipment,
            status=ShipmentStatus.cancelled
        )
        shipment.timeline.append(event)
        return shipment

    async def delete(self, id: UUID) -> Shipment | None:
        shipment = await self.get(id)
        if not shipment:
            return None
        return await self._delete(shipment)

    async def rate(self, shipment_id: UUID, review: ShipmentReview):
        # check the token for what shipment to review
        shipment = await self._get(shipment_id)

        # add the review
        shipment_review = Review(
            **review.model_dump(),
            shipment_id=shipment.id
        )

        # now add the review
        self.session.add(shipment_review)
        await self.session.commit()

    async def add_tag(self, shipment_id: UUID, tag: Tag):
        shipment = await self.get(shipment_id)
        # now get the tag list and append this new tag
        shipment.tags.append(tag)
        # now add the tag by refresh
        self.session.add(shipment)
        await self.session.commit()
