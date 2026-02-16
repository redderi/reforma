import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader
import aiosmtplib

from reforma_mail.domain.repositories.mail_repository import MailRepository
from reforma_mail.domain.entities.email_message import EmailMessage
from reforma_mail.infrastructure.config.smtp_config import (
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, EMAIL_FROM
)

class SMTPService(MailRepository):

    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(__file__))
        templates_path = os.path.join(base_dir, "templates")
        self.env = Environment(loader=FileSystemLoader(templates_path))

    async def send(self, message: EmailMessage) -> None:
        template = self.env.get_template(message.template)
        html = template.render(**message.context)

        msg = MIMEMultipart()
        msg["From"] = EMAIL_FROM
        msg["To"] = message.to_email
        msg["Subject"] = message.subject
        msg.attach(MIMEText(html, "html"))

        await aiosmtplib.send(
            msg,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            username=SMTP_USER,
            password=SMTP_PASSWORD,
            start_tls=True,
        )
