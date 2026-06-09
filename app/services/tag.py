from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlmodel import col
from app.database.models import ShipmentTagLink, Tag
from app.services.base import BaseService
from sqlalchemy.ext.asyncio import AsyncSession


class TagService(BaseService):
    def __init__(self, session: AsyncSession):
        super().__init__(Tag, session)

    async def get_by_type(self, tag_name: str):
        tag = await self.session.scalar(select(Tag).where(col(Tag.name) == tag_name))
        if not tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tag with type {tag_name} not found"
            )
        return tag

    async def remove_tag_from_shipment(self, shipment_id: UUID, tag_name: str):
        tag = await self.get_by_type(tag_name)
        tag_id = tag.id
        tag_shipment_link = await self.session.scalar(select(ShipmentTagLink).where(
            col(ShipmentTagLink.shipment_id) == shipment_id).where(ShipmentTagLink.tag_id == tag_id))
        if not tag_shipment_link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tag with type {tag_name} not found for shipment with id {shipment_id}"
            )
        await self.session.delete(tag_shipment_link)
        await self.session.commit()

    async def get_all_shipments(self, tag_name: str):
        tag = await self.get_by_type(tag_name)
        return tag.shipments
