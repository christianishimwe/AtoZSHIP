
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from fastapi.templating import Jinja2Templates

from app.api.dependencies import DeliveryPartnerDep, SellerServiceDep, get_seller_access_token
from app.api.schemas.delivery_partner import DeliveryPartnerUpdate
from app.database.models import Seller
from app.database.redis import add_jti_to_blacklist
from app.utils import TEMPLATE_DIR
from ..schemas.seller import SellerCreate, SellerRead
from app.config import app_settings

router = APIRouter(prefix="/seller", tags=["seller"])


@router.post("/signup", response_model=SellerRead)
async def register_seller(seller: SellerCreate, service: SellerServiceDep):
    seller_out = await service.add(seller)
    return seller_out


@router.post("/login")
async def login_seller(request_form: Annotated[OAuth2PasswordRequestForm, Depends()], service: SellerServiceDep):
    # see if the email is verified
    # get the user
    if not await service.check_user_verified(request_form.username):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not verified")
    token = await service.token(request_form.username, request_form.password)
    return {
        "access_token": token,
        "type": "jwt"
    }


@router.get("/logout")
async def logout_seller(token_data: Annotated[dict, Depends(get_seller_access_token)]):
    await add_jti_to_blacklist(token_data["jti"])
    return {
        "detail": "successfully logged out"
    }


@router.get("/", response_model=SellerRead)
async def get_seller(id: UUID, service: SellerServiceDep):
    return await service.get(id)

# update the delivery partner


@router.post("/")
async def update_delivery_partner(partner_update: DeliveryPartnerUpdate, partner: DeliveryPartnerDep, service):
    pass


# VERIFY USER EMAIL
@router.get("/verify")
async def verify_delivery_partner_email(token: str, service: SellerServiceDep):
    await service.verify_email(token)
    return {"detail": "Account Verified"}


# RESET PASSWORD
@router.get("/forgot_password")
async def forgot_password(email: str, service: SellerServiceDep):
    # call the function to reset password from the user service
    await service.send_password_reset_link(email, router.prefix)
    return {
        "message": "successfully sent the link!, check your email"
    }


@router.get("/password_reset_form")
async def get_reset_password_form(token: str, request: Request):
    template = Jinja2Templates(directory=TEMPLATE_DIR)
    return template.TemplateResponse(
        request=request,
        name="reset_password_form.html",
        context={
            "request_url": f"{app_settings.APP_BASE_URL}{router.prefix}/reset_password?token={token}"}
    )


@router.post("/reset_password")
async def reset_password(token: str, password: Annotated[str, Form()], service: SellerServiceDep):
    await service.reset_password(token, password)
    return {"detail": "Password Reset Successful"}
