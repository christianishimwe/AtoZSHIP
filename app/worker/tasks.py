import re
from celery import Celery
from asgiref.sync import async_to_sync
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType, NameEmail
from pydantic import EmailStr
from app.config import redis_settings, notification_settings
from app.utils import TEMPLATE_DIR

fastmail = FastMail(
    ConnectionConfig(
        **notification_settings.model_dump(),
        TEMPLATE_FOLDER=TEMPLATE_DIR
    )
)

send_message = async_to_sync(fastmail.send_message)

app = Celery(
    "api_tasks",
    broker=redis_settings.REDIS_URL(9),
    backend=redis_settings.REDIS_URL(9)
)


@app.task
def send_mail(recipients: list[EmailStr], subject: str, body: str):
    send_message(
        message=MessageSchema(
            recipients=[NameEmail(name="", email=r) for r in recipients],
            subject=subject,
            body=body,
            subtype=MessageType.plain
        )
    )
    return "Email sent successfully"


@app.task
def send_mail_with_template(
    recipients: list[EmailStr],
    subject: str,
    context: dict,
    template_name: str
):

    send_message(
        message=MessageSchema(
            recipients=[NameEmail(name="", email=r) for r in recipients],
            subject=subject,
            subtype=MessageType.html,
            template_body=context
        ),
        template_name=template_name
    )
