

from typing import Annotated

from fastapi.security import OAuth2PasswordBearer
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import Depends, HTTPException, status

from app.database.models import DeliveryPartner, Seller
from app.database.redis import is_jti_blacklisted
from app.database.session import get_session
from app.services.delivery_partner import DeliveryPartnerService
from app.services.seller import SellerService
from app.services.shipment import ShipmentService
from app.services.shipment_event import ShipmnentEventService
from app.services.tag import TagService
from app.utils import decode_access_token
from app.core.security import oauth2_scheme_seller, oauth2_scheme_partner


SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_shipment_service(session: SessionDep) -> ShipmentService:
    return ShipmentService(
        session,
        DeliveryPartnerService(session),
        ShipmnentEventService(session),
    )


def get_seller_service(session: SessionDep):
    return SellerService(session)


async def _get_token_data(token: str) -> dict:
    data = decode_access_token(token)
    if data is None or await is_jti_blacklisted(data["jti"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Access Token")
    return data


async def get_seller_access_token(token: Annotated[str, Depends(oauth2_scheme_seller)]):
    return await _get_token_data(token)


async def get_partner_access_token(token: Annotated[str, Depends(oauth2_scheme_partner)]):
    return await _get_token_data(token)


async def get_current_seller(token_data: Annotated[dict, Depends(get_seller_access_token)], session: SessionDep) -> Seller | None:

    seller = await session.get(Seller, UUID(token_data["user"]["id"]))
    if seller is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not Authorized"
        )
    return seller


async def get_current_partner(token_data: Annotated[dict, Depends(get_partner_access_token)], session: SessionDep) -> DeliveryPartner | None:
    partner = await session.get(DeliveryPartner, UUID(token_data["user"]["id"]))
    if partner is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not Authorized"
        )
    return partner
# delivery partner service dep


def get_delivery_partner_service(session: SessionDep):
    return DeliveryPartnerService(session)


def get_tag_service(session: SessionDep):
    return TagService(session)


TagServiceDep = Annotated[TagService, Depends(get_tag_service)]
DeliveryPartnerServiceDep = Annotated[DeliveryPartnerService, Depends(
    get_delivery_partner_service)]
DeliveryPartnerDep = Annotated[DeliveryPartner, Depends(get_current_partner)]
SellerDep = Annotated[Seller, Depends(get_current_seller)]
ShipmentServiceDep = Annotated[ShipmentService, Depends(get_shipment_service)]
SellerServiceDep = Annotated[SellerService, Depends(get_seller_service)]
