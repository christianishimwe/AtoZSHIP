from datetime import timedelta
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, HTTPException, status, Request
from fastapi.templating import Jinja2Templates
from app.api.dependencies import DeliveryPartnerDep, SellerDep, ShipmentServiceDep
from app.database import models
from app.services.shipment import ShipmentService
from app.utils import TEMPLATE_DIR, decode_access_token, decode_url_safe_token
from ..schemas import shipment

router = APIRouter(prefix="/shipment",
                   tags=["shipment"])
templates = Jinja2Templates(TEMPLATE_DIR)


@router.get("/", response_model=shipment.ShipmentRead)
async def get_shipments(id: UUID, service: ShipmentServiceDep, seller: SellerDep):
    ''''
    Notice how we used Depends to inject the database session into our endpoint, this allows us to use the session to interact with the database and perform CRUD operations on the shipments table.
    insted if we just used session = get_session(), this would be given a value at function defintion time, but
    we won't be able to get the cleanups, yields will not work well since the function will no longer be a generator, and we won't be able to use the context manager to manage the database connection, this is why we use Depends to inject the session into our endpoint, this allows us to use the session as a dependency and get the benefits of the context manager and yields.
    '''
    # check for the shipment with the given id
    shipment = await service.get(id)

    if shipment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found")
    return shipment


@router.post("/", status_code=status.HTTP_201_CREATED)
async def submit_shipment(incoming_shipment: shipment.ShipmentCreate, service: ShipmentServiceDep, seller: SellerDep) -> models.Shipment:
    shipment = await service.add(incoming_shipment, seller)
    return shipment

# update shipment
# should only be accessible to allowed delivery partners


@router.patch("/", response_model=shipment.ShipmentRead)
async def update_shipment(
        id: UUID,
        shipment_update: shipment.ShipmentUpdate,
        partner: DeliveryPartnerDep,
        service: ShipmentServiceDep,
):
    update = shipment_update.model_dump(exclude_none=True)
    if not update:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="no data provided to update"
        )

    return await service.update(id, shipment_update, partner)

# cancel a shipment by id


@router.get("/cancel", response_model=shipment.ShipmentRead)
async def cancel_shipment(id: UUID, seller: SellerDep, service: ShipmentServiceDep):
    return await service.cancel(id, seller)

# track details of shipment


@router.get("/track")
async def get_tracking(request: Request, id: UUID, service: ShipmentServiceDep):
    # check for the shipment with the given id
    shipment = await service.get(id)

    context = shipment.model_dump()
    context["partner"] = shipment.delivery_partner.name
    context["timeline"] = shipment.timeline
    return templates.TemplateResponse(
        request=request,
        name="track.html",
        context=context
    )

# SHIPMENT REVIEW


@router.get("/review")
async def review_shipment(request: Request, token: str, service: ShipmentServiceDep):
    data = decode_url_safe_token(
        token, salt="review")
    if not data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )
    shipment = await service.get(UUID(data["shipment_id"]))
    # if this shipment already has a review
    if shipment.review:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Shipment already reviewed"
        )
    context = {
        "content": shipment.content,
        "delivery_partner": shipment.delivery_partner.name,
        "token": token
    }
    # now send the template back to the user
    return templates.TemplateResponse(
        request=request,
        name="review.html",
        context=context
    )


@router.post("/review", status_code=status.HTTP_201_CREATED)
async def submit_review(token: str, review: shipment.ShipmentReview, service: ShipmentServiceDep):
    # decode the access token
    data = decode_url_safe_token(token, salt="review")
    if not data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )
    # use the service to do the review
    await service.rate(UUID(data["shipment_id"]), review)
