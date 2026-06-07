
from datetime import datetime, timedelta
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.schemas.seller import SellerCreate
from app.database.models import Seller
from pwdlib import PasswordHash
from .user import UserService

password_hasher = PasswordHash.recommended()
# to prevent timing attacks
DUMMY_HASH = password_hasher.hash("dummy_password")


class SellerService(UserService):
    def __init__(self, session: AsyncSession):
        super().__init__(Seller, session)

    async def get(self, id: UUID):
        seller = self.session.get(Seller, id)

    async def add(self, seller_create: SellerCreate) -> Seller:
        return await self._add_user(seller_create.model_dump(), "seller")

    async def token(self, email, password) -> str | None:
        # validate the credentials
        return await self._generate_token(email, password)
