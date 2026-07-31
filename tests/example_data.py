from app.core.security import password_hasher
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import models
example_seller = {
    "name": "seller1",
    "email": "seller1@gmail.com",
    "email_verified": True,
    "password_hash": password_hasher.hash("password"),
    "zip_code": 19000
}

example_delivery_partner = {
    "name": "partner1",
    "email": "partner1@gmail.com",
    "email_verified": True,
    "password_hash": password_hasher.hash("password"),
    "max_handling_capacity": 10,
}


async def add_data_to_database(sess: AsyncSession):
    # add the data
    seller = models.Seller(**example_seller)
    partner = models.DeliveryPartner(**example_delivery_partner)
    location = models.Location(zip_code=1, name="Test City")
    partner.serviceable_locations.append(location)
    sess.add_all([seller, partner, location])
    await sess.commit()
