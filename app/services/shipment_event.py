from app.config import app_settings
from app.database.models import Shipment, ShipmentEvent, ShipmentStatus
from app.services.base import BaseService
from app.utils import generate_url_safe_token
from app.worker.tasks import send_mail_with_template


class ShipmnentEventService(BaseService):
    def __init__(self, session):
        super().__init__(ShipmentEvent, session)

    async def add(
        self,
        shipment: Shipment,
        location: int | None = None,
        status: ShipmentStatus | None = None,
        description: str | None = None,
    ) -> ShipmentEvent:
        # if the location is not provided, find the laterst event's location
        if not location or not status:
            last_event = await self.get_latest_event(shipment)
            location = location if location else last_event.location
            status = status if status else last_event.status

        if not status:
            last_event = await self.get_latest_event(shipment)
            status = last_event.status

        new_event = ShipmentEvent(
            location=location,
            status=status,
            description=description if description else self._generate_description(
                status, location),
            shipment_id=shipment.id
        )
        if status:
            await self._notify(shipment, status)
        return await self._add(new_event)

    async def get_latest_event(self, shipment: Shipment):
        timeline = shipment.timeline
        timeline.sort(key=lambda event: event.created_at)
        return timeline[-1]

    def _generate_description(self, status: ShipmentStatus | None, location: int):
        match status:
            case ShipmentStatus.placed:
                return "assigned delivery partner"
            case ShipmentStatus.shipped:
                return "shipment is shipped"
            case ShipmentStatus.in_transit:
                return "shipment is in transit"
            case ShipmentStatus.delivered:
                return "successfully delivered"
            case ShipmentStatus.cancelled:
                return "cancelled by the seller"
            case _:
                return f"scanned at {location}"

    async def _notify(self, shipment: Shipment, status: ShipmentStatus):
        estimated = shipment.estimated_delivery.strftime("%B %d, %Y")
        match status:
            case ShipmentStatus.placed:
                send_mail_with_template.delay(
                    recipients=[shipment.client_contact_email],
                    subject="Your order is placed",
                    context={
                        "seller": shipment.seller.name,
                        "partner": shipment.delivery_partner.name,
                        "tracking_url": f"{app_settings.APP_BASE_URL}/shipment/track?id={shipment.id}",
                    },
                    template_name="mail_placed.html"
                )
            case ShipmentStatus.shipped:
                send_mail_with_template.delay(
                    recipients=[shipment.client_contact_email],
                    subject="Your order is shipped",
                    context={
                        "seller": shipment.seller.name,
                        "partner": shipment.delivery_partner.name,
                        "content": shipment.content,
                        "estimated_delivery": estimated,
                    },
                    template_name="mail_shipped.html"
                )
            case ShipmentStatus.in_transit:
                await send_mail_with_template.delay(
                    recipients=[shipment.client_contact_email],
                    subject="Your order is in transit",
                    context={
                        "seller": shipment.seller.name,
                        "partner": shipment.delivery_partner.name,
                        "content": shipment.content,
                        "destination": shipment.destination,
                        "estimated_delivery": estimated,
                    },
                    template_name="mail_in_transit.html"
                )
            case ShipmentStatus.delivered:
                # create a token that goes with the review link
                token = generate_url_safe_token(
                    {"shipment_id": str(shipment.id)}, salt="review")
                await send_mail_with_template.delay(
                    recipients=[shipment.client_contact_email],
                    subject="Your order is delivered",
                    context={
                        "seller": shipment.seller.name,
                        "content": shipment.content,
                        "review_url": f"{app_settings.APP_BASE_URL}/shipment/review?token={token}"
                    },
                    template_name="mail_delivered.html"
                )
            case ShipmentStatus.cancelled:
                await send_mail_with_template.delay(
                    recipients=[shipment.client_contact_email],
                    subject="Your order is cancelled",
                    context={
                        "seller": shipment.seller.name,
                        "content": shipment.content,
                    },
                    template_name="mail_cancelled.html"
                )
