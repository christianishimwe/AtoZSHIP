from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash

password_hasher = PasswordHash.recommended()
oauth2_scheme_seller = OAuth2PasswordBearer(tokenUrl="/seller/login")
oauth2_scheme_partner = OAuth2PasswordBearer(tokenUrl="/partner/login")
