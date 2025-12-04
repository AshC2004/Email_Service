import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from app.config import get_settings

settings = get_settings()


async def send_email_smtp(
    to_email: str,
    from_email: str,
    subject: str,
    body_html: Optional[str] = None,
    body_text: Optional[str] = None,
    from_name: Optional[str] = None,
    reply_to: Optional[str] = None,
):
    """Send an email via SMTP."""
    if body_html and body_text:
        message = MIMEMultipart("alternative")
        message.attach(MIMEText(body_text, "plain", "utf-8"))
        message.attach(MIMEText(body_html, "html", "utf-8"))
    elif body_html:
        message = MIMEText(body_html, "html", "utf-8")
    else:
        message = MIMEText(body_text or "", "plain", "utf-8")

    if from_name:
        message["From"] = f"{from_name} <{from_email}>"
    else:
        message["From"] = from_email

    message["To"] = to_email
    message["Subject"] = subject

    if reply_to:
        message["Reply-To"] = reply_to

    await aiosmtplib.send(
        message,
        hostname=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_user,
        password=settings.smtp_pass,
        use_tls=False,
        start_tls=settings.smtp_use_tls,
    )
