
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from fastapi.templating import Jinja2Templates

from app.api.dependencies import DeliveryPartnerDep, DeliveryPartnerServiceDep, get_partner_access_token
from app.database.models import DeliveryPartner
from app.database.redis import add_jti_to_blacklist
from app.config import app_settings
from app.utils import TEMPLATE_DIR
from ..schemas.delivery_partner import DeliveryPartnerCreate, DeliveryPartnerRead, DeliveryPartnerUpdate

router = APIRouter(prefix="/partner", tags=["Delivery Partner"])


@router.post("/signup", response_model=DeliveryPartnerRead)
async def register_delivery_partner(delivery_partner: DeliveryPartnerCreate, service: DeliveryPartnerServiceDep):
    DeliveryPartner_out = await service.add(delivery_partner)
    return DeliveryPartner_out


@router.post("/login")
async def login_delivery_partner(request_form: Annotated[OAuth2PasswordRequestForm, Depends()], service: DeliveryPartnerServiceDep,):
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


@router.post("/", response_model=DeliveryPartnerRead)
async def update_delivery_partner(
    partner_update: DeliveryPartnerUpdate,
    partner: DeliveryPartnerDep,
    service: DeliveryPartnerServiceDep,
):
    return await service.update(
        partner.sqlmodel_update(partner_update)
    )


@router.get("/logout")
async def logout_delivery_partner(token_data: Annotated[dict, Depends(get_partner_access_token)]):
    await add_jti_to_blacklist(token_data["jti"])
    return {
        "detail": "successfully logged out"
    }


@router.get("/verify")
async def verify_seller_email(token: str, service: DeliveryPartnerServiceDep):
    await service.verify_email(token)
    return {"detail": "Account Verified"}


# RESET PASSWORD
@router.get("/forgot_password")
async def forgot_password(email: str, service: DeliveryPartnerServiceDep):
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
            "request_url": f"http://{app_settings.APP_BASE_URL}{router.prefix}/reset_password?token={token}"}
    )


@router.post("/reset_password")
async def reset_password(token: str, new_password: Annotated[str, Form()], service: DeliveryPartnerServiceDep):
    await service.reset_password(token, new_password)
    return {"detail": "Password Reset Successful"}
