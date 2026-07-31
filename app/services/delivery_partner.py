from typing import Sequence
from fastapi import HTTPException, status
from sqlmodel import select, col
from sqlmodel import any_
from app.api.schemas.delivery_partner import DeliveryPartnerCreate
from app.database.models import DeliveryPartner, Shipment, PartnerLocationLink, Location
from .user import UserService


class DeliveryPartnerService(UserService):
    def __init__(self, session):
        super().__init__(DeliveryPartner, session)

    async def add(self, delivery_partner: DeliveryPartnerCreate):
        # first add the zip codes to the link model
        partner: DeliveryPartner = await self._add_user(
            delivery_partner.model_dump(exclude={"serviceable_zip_codes"}),
            "partner"
        )
        # refresh
        # await self.session.refresh(partner)

        # all_links = [PartnerLocationLink(location_id=zip_code, delivery_partner_id=partner.id)
        #             for zip_code in delivery_partner.serviceable_zip_codes]
        # self.session.add_all(all_links)
        for zip_code in delivery_partner.serviceable_zip_codes:
            partner_location = await self.session.get(Location, zip_code)
            partner.serviceable_locations.append(
                partner_location if partner_location else Location(zip_code=zip_code))
        # commmit the changes
        return await self._update(partner)

    async def update(self, partner: DeliveryPartner):
        return await self._update(partner)

    async def get_partners_by_zipcode(self, zipcode: int) -> Sequence[DeliveryPartner]:
        '''
        return (await self.session.scalars(
            select(DeliveryPartner).where(
                zipcode == any_(DeliveryPartner.serviceable_zip_codes))
        )).all()
        '''
        # get this location
        location = await self.session.get(Location, zipcode)
        if not location:
            return []
        return location.delivery_partners

    async def assign_shipment(self, shipment: Shipment):
        eligible_partners = await self.get_partners_by_zipcode(shipment.destination)
        for partner in eligible_partners:
            if partner.current_handling_capacity > 0:
                partner.shipments.append(shipment)
                return partner
        # no eligible partners were found, or all partners handling capacity was hit
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="No delivery partner available"
        )

    async def token(self, email, password) -> str | None:
        return await self._generate_token(email, password)
